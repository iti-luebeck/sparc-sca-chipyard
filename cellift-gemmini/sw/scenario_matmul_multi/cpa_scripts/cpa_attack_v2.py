#!/usr/bin/env python3
"""
Correlation Power Analysis (CPA) Attack on Gemmini Matrix Multiplication v2

Improved version that correlates the full trace with hypothetical power
based on intermediate values throughout the matrix multiplication.

Usage:
    python3 cpa_attack_v2.py --traces /path/to/traces --matrices /path/to/matrices
    python3 cpa_attack_v2.py --traces traces/ --matrices . --metric hd --dim 4
"""

import argparse
import os
import sys
import csv
import re
import numpy as np
from pathlib import Path
from scipy.stats import pearsonr
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

@dataclass
class MatrixPair:
    """Container for matrix pair with index"""
    index: int
    A: np.ndarray
    B_expected: Optional[np.ndarray] = None
    C_expected: Optional[np.ndarray] = None

class MatrixHeaderParser:
    """Parses matrix header files"""
    
    @staticmethod
    def parse_header(header_file: str, dim: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Parse a matrix header file and extract A, B, C matrices."""
        A = None
        B = None
        C = None
        
        with open(header_file, 'r') as f:
            content = f.read()
        
        # Extract matrix A
        A_match = re.search(r'static const int8_t test_matrix_A\[.*?\] = \n\{(.*?)\};', content, re.DOTALL)
        if A_match:
            A = MatrixHeaderParser._parse_int_array(A_match.group(1), dim, dim, dtype=np.int8)
        
        # Extract matrix B
        B_match = re.search(r'static const int8_t test_matrix_B\[.*?\] = \n\{(.*?)\};', content, re.DOTALL)
        if B_match:
            B = MatrixHeaderParser._parse_int_array(B_match.group(1), dim, dim, dtype=np.int8)
        
        # Extract expected matrix C
        C_match = re.search(r'static const int32_t test_expected_C\[.*?\] = \n\{(.*?)\};', content, re.DOTALL)
        if C_match:
            C = MatrixHeaderParser._parse_int_array(C_match.group(1), dim, dim, dtype=np.int32)
        
        if A is None:
            raise ValueError(f"Could not parse matrix A from {header_file}")
        
        return A, B, C
    
    @staticmethod
    def _parse_int_array(array_str: str, rows: int, cols: int, dtype=np.int8) -> np.ndarray:
        """Parse array from C-style initialization (supports hex and decimal)"""
        numbers = re.findall(r'0x[0-9a-fA-F]+|\b\d+\b|-\d+', array_str)
        
        parsed_nums = []
        for num_str in numbers:
            try:
                if num_str.startswith('0x') or num_str.startswith('0X'):
                    val = int(num_str, 16)
                    if dtype == np.int8 and val > 127:
                        val = val - 256
                    parsed_nums.append(dtype(val))
                else:
                    parsed_nums.append(dtype(int(num_str)))
            except ValueError:
                pass
        
        if len(parsed_nums) != rows * cols:
            raise ValueError(f"Expected {rows*cols} elements, got {len(parsed_nums)}")
        
        return np.array(parsed_nums, dtype=dtype).reshape(rows, cols)

class TraceLoader:
    """Loads HD/HW CSV traces"""
    
    @staticmethod
    def load_trace(csv_file: str) -> np.ndarray:
        """Load a single trace from CSV file."""
        values = []
        try:
            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if row:
                        try:
                            values.append(float(row[-1]))
                        except (ValueError, IndexError):
                            pass
        except Exception as e:
            raise ValueError(f"Error loading trace from {csv_file}: {e}")
        
        return np.array(values, dtype=np.float64)
    
    @staticmethod
    def load_all_traces(traces_dir: str, pattern: str = "*_hd.csv", 
                       max_traces: Optional[int] = None) -> Dict[int, np.ndarray]:
        """Load all matching traces from directory."""
        traces_path = Path(traces_dir)
        trace_files = sorted(traces_path.glob(pattern))
        
        if not trace_files:
            raise FileNotFoundError(f"No trace files matching '{pattern}' found in {traces_dir}")
        
        if max_traces:
            trace_files = trace_files[:max_traces]
        
        traces = {}
        for trace_file in trace_files:
            match = re.search(r'(?:vanilla_|cellift_)?matmul_(\d+)', trace_file.name)
            if match:
                idx = int(match.group(1))
                traces[idx] = TraceLoader.load_trace(str(trace_file))
        
        return traces

class CPAAttack:
    """CPA attack implementation"""
    
    def __init__(self, dim: int = 4):
        self.dim = dim
        self.matrix_size = dim * dim
    
    def compute_hamming_weight(self, A: np.ndarray, B_byte_idx: int, 
                              B_guess: int) -> np.ndarray:
        """
        Compute hypothetical power model based on Hamming weight of 
        intermediate values when computing C = A * B with one byte of B guessed.
        
        Args:
            A: Known input matrix A
            B_byte_idx: Which byte of B to guess
            B_guess: Guessed byte value (unsigned, 0-255)
        
        Returns:
            Power hypothesis (1D array, one value per cycle-like event)
        """
        # Convert unsigned to signed
        B_signed = np.int8(B_guess - 128)
        
        hypothesis = []
        
        # Get row and column of the target byte in matrix B
        target_row = B_byte_idx // self.dim
        target_col = B_byte_idx % self.dim
        
        # Simulate matrix multiplication
        # For each output element C[i][j], compute the dot product
        for out_i in range(self.dim):
            for out_j in range(self.dim):
                accumulator = 0
                
                # Accumulate products A[i][k] * B[k][j]
                for k in range(self.dim):
                    a_val = int(A[out_i, k])
                    
                    # Only include the guessed B value if it affects this output
                    if k == target_row and out_j == target_col:
                        b_val = int(B_signed)
                    else:
                        b_val = 0  # Unknown - we ignore other B values
                    
                    product = a_val * b_val
                    accumulator += product
                    
                    # Record Hamming weight at each step
                    hw = bin(abs(accumulator) & 0xFFFFFFFF).count('1')
                    hypothesis.append(float(hw))
        
        return np.array(hypothesis, dtype=np.float64)
    
    def correlate(self, hypothesis: np.ndarray, measured: np.ndarray) -> float:
        """Compute Pearson correlation."""
        # Align to minimum length
        min_len = min(len(hypothesis), len(measured))
        
        if min_len < 2:
            return 0.0
        
        hypothesis = hypothesis[:min_len]
        measured = measured[:min_len]
        
        try:
            corr, _ = pearsonr(hypothesis, measured)
            return float(corr) if not np.isnan(corr) else 0.0
        except:
            return 0.0
    
    def attack_byte(self, A_list: List[np.ndarray], 
                   measured_traces: List[np.ndarray],
                   byte_idx: int) -> Tuple[int, List[float]]:
        """
        Attack a single byte of matrix B.
        
        Returns:
            (best_byte_guess, correlations_for_all_guesses)
        """
        correlations = []
        best_byte = 0
        best_corr = 0.0
        
        # Try all 256 possible byte values
        for guess in range(256):
            correlations_for_guess = []
            
            # Compute average correlation across all test cases
            for A, trace in zip(A_list, measured_traces):
                hypothesis = self.compute_hamming_weight(A, byte_idx, guess)
                corr = self.correlate(hypothesis, trace)
                correlations_for_guess.append(corr)
            
            avg_corr = np.mean(correlations_for_guess)
            correlations.append(avg_corr)
            
            if abs(avg_corr) > abs(best_corr):
                best_corr = avg_corr
                best_byte = guess
        
        return best_byte, correlations

def main():
    parser = argparse.ArgumentParser(description='CPA Attack on Gemmini MatMul (v2)')
    parser.add_argument('--traces', required=True, help='Directory containing traces')
    parser.add_argument('--matrices', required=True, help='Directory containing matrix_*.h files')
    parser.add_argument('--dim', type=int, default=4, help='Matrix dimension')
    parser.add_argument('--metric', choices=['hd', 'hw'], default='hd', help='Power metric')
    parser.add_argument('--max-traces', type=int, default=None, help='Max traces to use')
    parser.add_argument('--output', default='recovered_B_v2.txt', help='Output file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("CPA Attack - Gemmini MatMul (v2)")
    print("=" * 80)
    print(f"Traces: {args.traces}")
    print(f"Matrices: {args.matrices}")
    print(f"Metric: {args.metric.upper()}")
    print(f"Dimension: {args.dim}x{args.dim}")
    print()
    
    # Load traces
    print("Loading traces...")
    pattern = f"*_{args.metric}.csv"
    traces_dict = TraceLoader.load_all_traces(args.traces, pattern, args.max_traces)
    print(f"  Loaded {len(traces_dict)} traces")
    print()
    
    # Load matrices
    print("Loading matrix files...")
    matrices_path = Path(args.matrices)
    matrix_files = sorted(matrices_path.glob('matrix_*.h'))
    
    matrix_pairs = {}
    for mf in matrix_files:
        match = re.search(r'matrix_(\d+)\.h', mf.name)
        if match:
            idx = int(match.group(1))
            try:
                A, B, C = MatrixHeaderParser.parse_header(str(mf), args.dim)
                matrix_pairs[idx] = MatrixPair(idx, A, B, C)
            except Exception as e:
                if args.verbose:
                    print(f"  Warning: {mf.name}: {e}")
    
    print(f"  Loaded {len(matrix_pairs)} matrices")
    print()
    
    # Find common indices
    common_idx = sorted(set(traces_dict.keys()) & set(matrix_pairs.keys()))
    if not common_idx:
        print("ERROR: No common indices between traces and matrices")
        sys.exit(1)
    
    A_list = [matrix_pairs[i].A for i in common_idx]
    trace_list = [traces_dict[i] for i in common_idx]
    
    print(f"Using {len(common_idx)} test cases")
    print()
    
    # Run attack
    print("Starting CPA attack...")
    attack = CPAAttack(dim=args.dim)
    recovered_B = np.zeros((args.dim, args.dim), dtype=np.int8)
    results = []
    
    for byte_idx in range(args.dim * args.dim):
        if byte_idx % 4 == 0:
            print(f"  Progress: {byte_idx}/{args.dim * args.dim - 1}", end='\r', flush=True)
        
        recovered_val, corrs = attack.attack_byte(A_list, trace_list, byte_idx)
        
        signed_val = np.int8(recovered_val - 128)
        row = byte_idx // args.dim
        col = byte_idx % args.dim
        recovered_B[row, col] = signed_val
        
        max_corr = max(corrs)
        results.append({
            'idx': byte_idx,
            'recovered': recovered_val,
            'signed': int(signed_val),
            'max_corr': max_corr
        })
    
    print()
    print("=" * 80)
    print("Results")
    print("=" * 80)
    print()
    print("Recovered Matrix B:")
    print(recovered_B)
    print()
    
    # Show correlation stats
    corrs = [r['max_corr'] for r in results]
    print(f"Correlation Statistics:")
    print(f"  Min:  {min(corrs):.6f}")
    print(f"  Max:  {max(corrs):.6f}")
    print(f"  Mean: {np.mean(corrs):.6f}")
    print(f"  Std:  {np.std(corrs):.6f}")
    print()
    
    # Verify
    if all(mp.B_expected is not None for mp in matrix_pairs.values()):
        expected_B = matrix_pairs[common_idx[0]].B_expected
        matches = np.sum(recovered_B == expected_B)
        accuracy = (matches / (args.dim * args.dim)) * 100
        
        print(f"Verification:")
        print(f"  Expected B:")
        print(f"  {expected_B}")
        print()
        print(f"  Correct bytes: {matches}/{args.dim * args.dim} ({accuracy:.1f}%)")
        print()
    
    # Write results
    with open(args.output, 'w') as f:
        f.write("CPA Attack Results (v2)\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Matrix: {args.dim}x{args.dim}\n")
        f.write(f"Tests: {len(common_idx)}\n")
        f.write(f"Metric: {args.metric.upper()}\n\n")
        f.write("Recovered Matrix B:\n")
        f.write(f"{recovered_B}\n\n")
        f.write("Byte,Recovered,Signed,Correlation\n")
        for r in results:
            f.write(f"{r['idx']},{r['recovered']},{r['signed']},{r['max_corr']:.8f}\n")
    
    print(f"Results written to: {args.output}")

if __name__ == '__main__':
    main()
