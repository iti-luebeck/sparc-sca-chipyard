#!/usr/bin/env python3
"""
Correlation Power Analysis (CPA) Attack on Gemmini Matrix Multiplication v3

Simplified version that uses direct multiplication values as the power model.
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
    index: int
    A: np.ndarray
    B_expected: Optional[np.ndarray] = None
    C_expected: Optional[np.ndarray] = None

class MatrixHeaderParser:
    @staticmethod
    def parse_header(header_file: str, dim: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        A = None
        B = None
        C = None
        
        with open(header_file, 'r') as f:
            content = f.read()
        
        A_match = re.search(r'static const int8_t test_matrix_A\[.*?\] = \n\{(.*?)\};', content, re.DOTALL)
        if A_match:
            A = MatrixHeaderParser._parse_int_array(A_match.group(1), dim, dim, dtype=np.int8)
        
        B_match = re.search(r'static const int8_t test_matrix_B\[.*?\] = \n\{(.*?)\};', content, re.DOTALL)
        if B_match:
            B = MatrixHeaderParser._parse_int_array(B_match.group(1), dim, dim, dtype=np.int8)
        
        C_match = re.search(r'static const int32_t test_expected_C\[.*?\] = \n\{(.*?)\};', content, re.DOTALL)
        if C_match:
            C = MatrixHeaderParser._parse_int_array(C_match.group(1), dim, dim, dtype=np.int32)
        
        if A is None:
            raise ValueError(f"Could not parse matrix A from {header_file}")
        
        return A, B, C
    
    @staticmethod
    def _parse_int_array(array_str: str, rows: int, cols: int, dtype=np.int8) -> np.ndarray:
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
    @staticmethod
    def load_trace(csv_file: str) -> np.ndarray:
        values = []
        try:
            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                next(reader)
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
    """CPA attack using direct Hamming weight of products as power model"""
    
    def __init__(self, dim: int = 4):
        self.dim = dim
    
    def compute_power_model(self, A: np.ndarray, B_byte_idx: int, B_guess: int) -> np.ndarray:
        """
        Compute power model: Hamming weight of all products A[i,k] * B[k,j]
        for the target byte of B.
        
        This returns a scalar array with one value per matrix element computation.
        """
        B_signed = np.int8(B_guess - 128)
        target_row = B_byte_idx // self.dim
        target_col = B_byte_idx % self.dim
        
        power_model = []
        
        # For each output element
        for out_i in range(self.dim):
            for out_j in range(self.dim):
                # Hamming weight when computing this output with the target B byte
                hw_sum = 0
                
                for k in range(self.dim):
                    a_val = int(A[out_i, k])
                    
                    # Only consider the target B byte
                    if k == target_row and out_j == target_col:
                        b_val = int(B_signed)
                    else:
                        b_val = 0
                    
                    # Hamming weight of this product
                    product = a_val * b_val
                    hw = bin(abs(product) & 0xFFFFFFFF).count('1')
                    hw_sum += hw
                
                power_model.append(float(hw_sum))
        
        return np.array(power_model)
    
    def correlate(self, model: np.ndarray, trace: np.ndarray) -> float:
        """Compute Pearson correlation, handling length mismatches."""
        if len(model) == 0 or len(trace) == 0:
            return 0.0
        
        # Resample trace to match model length if needed
        if len(trace) != len(model):
            if len(trace) > len(model):
                # Downsample trace
                indices = np.linspace(0, len(trace) - 1, len(model)).astype(int)
                trace = trace[indices]
            else:
                # Oversample model or just truncate
                model = model[:len(trace)]
        
        try:
            # Normalize both
            model_norm = (model - np.mean(model))
            trace_norm = (trace - np.mean(trace))
            
            denom = np.sqrt(np.sum(model_norm**2) * np.sum(trace_norm**2))
            if denom == 0:
                return 0.0
            
            corr = np.sum(model_norm * trace_norm) / denom
            return float(corr)
        except:
            return 0.0
    
    def attack_byte(self, A_list: List[np.ndarray], traces: List[np.ndarray],
                   byte_idx: int) -> Tuple[int, List[float]]:
        """Attack a single byte of B."""
        correlations = np.zeros(256)
        
        for guess in range(256):
            # Correlate across all test cases
            corrs_for_guess = []
            
            for A, trace in zip(A_list, traces):
                model = self.compute_power_model(A, byte_idx, guess)
                corr = self.correlate(model, trace)
                corrs_for_guess.append(corr)
            
            correlations[guess] = np.mean(np.abs(corrs_for_guess))
        
        best_byte = np.argmax(correlations)
        return best_byte, correlations.tolist()

def main():
    parser = argparse.ArgumentParser(description='CPA Attack - Gemmini MatMul (v3)')
    parser.add_argument('--traces', required=True, help='Directory with traces')
    parser.add_argument('--matrices', required=True, help='Directory with matrices')
    parser.add_argument('--dim', type=int, default=4, help='Matrix dimension')
    parser.add_argument('--metric', choices=['hd', 'hw'], default='hd', help='Power metric')
    parser.add_argument('--max-traces', type=int, default=None, help='Max traces')
    parser.add_argument('--output', default='recovered_B_v3.txt', help='Output file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("CPA Attack - Gemmini MatMul (v3) - Direct Product Model")
    print("=" * 80)
    print(f"Traces: {args.traces}")
    print(f"Matrices: {args.matrices}")
    print()
    
    # Load traces
    print("Loading traces...")
    pattern = f"*_{args.metric}.csv"
    traces_dict = TraceLoader.load_all_traces(args.traces, pattern, args.max_traces)
    print(f"  Loaded {len(traces_dict)} {args.metric.upper()} traces")
    print()
    
    # Load matrices
    print("Loading matrices...")
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
                    print(f"  Error parsing {mf.name}: {e}")
    
    print(f"  Loaded {len(matrix_pairs)} matrices")
    print()
    
    # Get common indices
    common_idx = sorted(set(traces_dict.keys()) & set(matrix_pairs.keys()))
    if not common_idx:
        print("ERROR: No matching traces and matrices")
        sys.exit(1)
    
    A_list = [matrix_pairs[i].A for i in common_idx]
    trace_list = [traces_dict[i] for i in common_idx]
    
    print(f"Using {len(common_idx)} test cases")
    print()
    
    # Run attack
    print("Running CPA attack (256 guesses × 16 bytes × 100 traces)...")
    attack = CPAAttack(dim=args.dim)
    recovered_B = np.zeros((args.dim, args.dim), dtype=np.int8)
    results = []
    
    for byte_idx in range(args.dim * args.dim):
        print(f"  Byte {byte_idx:2d}/15: ", end='', flush=True)
        
        recovered_val, corrs = attack.attack_byte(A_list, trace_list, byte_idx)
        signed_val = np.int8(recovered_val - 128)
        
        row = byte_idx // args.dim
        col = byte_idx % args.dim
        recovered_B[row, col] = signed_val
        
        top_corr = max(corrs)
        print(f"0x{recovered_val:02x} (corr: {top_corr:.4f})")
        
        results.append({
            'idx': byte_idx,
            'recovered': recovered_val,
            'signed': int(signed_val),
            'corr': top_corr
        })
    
    print()
    print("=" * 80)
    print("Results")
    print("=" * 80)
    print()
    print("Recovered Matrix B (signed):")
    print(recovered_B)
    print()
    print("Recovered Matrix B (unsigned hex):")
    print("  ", end='')
    for i in range(args.dim):
        if i > 0:
            print("  ", end='')
        for j in range(args.dim):
            val = int(recovered_B[i, j])
            unsigned = val if val >= 0 else val + 256
            print(f"0x{unsigned:02x}", end=' ')
        print()
    print()
    
    # Verify
    if all(mp.B_expected is not None for mp in matrix_pairs.values()):
        expected_B = matrix_pairs[common_idx[0]].B_expected
        matches = np.sum(recovered_B == expected_B)
        
        print(f"Verification:")
        print(f"  Expected Matrix B (signed):")
        print(f"  {expected_B}")
        print()
        print(f"  Correct: {matches}/16 ({100*matches/16:.1f}%)")
        print()
    
    # Correlation stats
    corrs = [r['corr'] for r in results]
    print(f"Correlation Statistics:")
    print(f"  Min:  {min(corrs):.6f}")
    print(f"  Max:  {max(corrs):.6f}")
    print(f"  Mean: {np.mean(corrs):.6f}")
    print(f"  Std:  {np.std(corrs):.6f}")
    print()
    
    # Write output
    with open(args.output, 'w') as f:
        f.write("CPA Attack Results (v3)\n")
        f.write("=" * 80 + "\n\n")
        f.write("Recovered Matrix B (signed):\n")
        f.write(f"{recovered_B}\n\n")
        f.write("Byte,Index,Recovered,Signed,MaxCorr\n")
        for r in results:
            row = r['idx'] // args.dim
            col = r['idx'] % args.dim
            f.write(f"B[{row},{col}],{r['idx']},{r['recovered']},{r['signed']},{r['corr']:.8f}\n")
    
    print(f"Results saved to: {args.output}")

if __name__ == '__main__':
    main()
