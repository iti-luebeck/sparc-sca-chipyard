#!/usr/bin/env python3
"""
Correlation Power Analysis (CPA) Attack on AES-128 - LAST ROUND

This script performs a CPA attack on AES-128 targeting the LAST ROUND
using Hamming Weight (HW) or Hamming Distance (HD) traces.

Attack Model (Last Round):
- Target: Last round inverse S-box output (before AddRoundKey)
- Intermediate value: InvSbox[ciphertext[i] XOR last_round_key[i]]
- Power model: HW(InvSbox output) or HD(ciphertext byte, InvSbox output)

The attack recovers the 16-byte LAST ROUND KEY (K10), which can then be
reversed through the key schedule to obtain the original AES key.

Author: Generated for CellIFT/WAL++ trace analysis
"""

import argparse
import os
import sys
import re
import glob
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# Try to import tqdm for progress bars
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    # Simple fallback progress indicator
    class tqdm:
        def __init__(self, iterable=None, total=None, desc=None, unit=None, ncols=None, leave=True):
            self.iterable = iterable
            self.total = total if total else (len(iterable) if iterable else 0)
            self.desc = desc or ''
            self.n = 0
        def __iter__(self):
            for item in self.iterable:
                yield item
                self.n += 1
                self._print_progress()
        def _print_progress(self):
            pct = 100 * self.n / self.total if self.total > 0 else 0
            bar_len = 30
            filled = int(bar_len * self.n / self.total) if self.total > 0 else 0
            bar = '█' * filled + '░' * (bar_len - filled)
            print(f'\r  {self.desc}: |{bar}| {self.n}/{self.total} ({pct:.0f}%)', end='', flush=True)
            if self.n >= self.total:
                print()
        def update(self, n=1):
            self.n += n
            self._print_progress()
        def close(self):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

# AES S-box lookup table
SBOX = np.array([
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16,
], dtype=np.uint8)

# Inverse S-box lookup table (for last-round attack)
INV_SBOX = np.array([
    0x52, 0x09, 0x6a, 0xd5, 0x30, 0x36, 0xa5, 0x38, 0xbf, 0x40, 0xa3, 0x9e, 0x81, 0xf3, 0xd7, 0xfb,
    0x7c, 0xe3, 0x39, 0x82, 0x9b, 0x2f, 0xff, 0x87, 0x34, 0x8e, 0x43, 0x44, 0xc4, 0xde, 0xe9, 0xcb,
    0x54, 0x7b, 0x94, 0x32, 0xa6, 0xc2, 0x23, 0x3d, 0xee, 0x4c, 0x95, 0x0b, 0x42, 0xfa, 0xc3, 0x4e,
    0x08, 0x2e, 0xa1, 0x66, 0x28, 0xd9, 0x24, 0xb2, 0x76, 0x5b, 0xa2, 0x49, 0x6d, 0x8b, 0xd1, 0x25,
    0x72, 0xf8, 0xf6, 0x64, 0x86, 0x68, 0x98, 0x16, 0xd4, 0xa4, 0x5c, 0xcc, 0x5d, 0x65, 0xb6, 0x92,
    0x6c, 0x70, 0x48, 0x50, 0xfd, 0xed, 0xb9, 0xda, 0x5e, 0x15, 0x46, 0x57, 0xa7, 0x8d, 0x9d, 0x84,
    0x90, 0xd8, 0xab, 0x00, 0x8c, 0xbc, 0xd3, 0x0a, 0xf7, 0xe4, 0x58, 0x05, 0xb8, 0xb3, 0x45, 0x06,
    0xd0, 0x2c, 0x1e, 0x8f, 0xca, 0x3f, 0x0f, 0x02, 0xc1, 0xaf, 0xbd, 0x03, 0x01, 0x13, 0x8a, 0x6b,
    0x3a, 0x91, 0x11, 0x41, 0x4f, 0x67, 0xdc, 0xea, 0x97, 0xf2, 0xcf, 0xce, 0xf0, 0xb4, 0xe6, 0x73,
    0x96, 0xac, 0x74, 0x22, 0xe7, 0xad, 0x35, 0x85, 0xe2, 0xf9, 0x37, 0xe8, 0x1c, 0x75, 0xdf, 0x6e,
    0x47, 0xf1, 0x1a, 0x71, 0x1d, 0x29, 0xc5, 0x89, 0x6f, 0xb7, 0x62, 0x0e, 0xaa, 0x18, 0xbe, 0x1b,
    0xfc, 0x56, 0x3e, 0x4b, 0xc6, 0xd2, 0x79, 0x20, 0x9a, 0xdb, 0xc0, 0xfe, 0x78, 0xcd, 0x5a, 0xf4,
    0x1f, 0xdd, 0xa8, 0x33, 0x88, 0x07, 0xc7, 0x31, 0xb1, 0x12, 0x10, 0x59, 0x27, 0x80, 0xec, 0x5f,
    0x60, 0x51, 0x7f, 0xa9, 0x19, 0xb5, 0x4a, 0x0d, 0x2d, 0xe5, 0x7a, 0x9f, 0x93, 0xc9, 0x9c, 0xef,
    0xa0, 0xe0, 0x3b, 0x4d, 0xae, 0x2a, 0xf5, 0xb0, 0xc8, 0xeb, 0xbb, 0x3c, 0x83, 0x53, 0x99, 0x61,
    0x17, 0x2b, 0x04, 0x7e, 0xba, 0x77, 0xd6, 0x26, 0xe1, 0x69, 0x14, 0x63, 0x55, 0x21, 0x0c, 0x7d,
], dtype=np.uint8)

# Hamming weight lookup table
HW_TABLE = np.array([bin(i).count('1') for i in range(256)], dtype=np.uint8)

# AES round constants for key schedule
RCON = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36]


def hamming_weight(x: np.ndarray) -> np.ndarray:
    """Compute Hamming weight of each element."""
    return HW_TABLE[x]


def hamming_distance(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Compute Hamming distance between two arrays."""
    return HW_TABLE[x ^ y]


def expand_key(key: np.ndarray) -> np.ndarray:
    """
    Expand AES-128 key to all 11 round keys.
    
    Args:
        key: 16-byte initial key
    
    Returns:
        176-byte expanded key (11 round keys of 16 bytes each)
    """
    expanded = np.zeros(176, dtype=np.uint8)
    expanded[:16] = key
    
    for i in range(4, 44):
        temp = expanded[(i-1)*4:(i-1)*4+4].copy()
        
        if i % 4 == 0:
            # RotWord
            temp = np.roll(temp, -1)
            # SubWord
            temp = SBOX[temp]
            # XOR with Rcon
            temp[0] ^= RCON[i // 4 - 1]
        
        expanded[i*4:i*4+4] = expanded[(i-4)*4:(i-4)*4+4] ^ temp
    
    return expanded


def inverse_key_schedule(last_round_key: np.ndarray) -> np.ndarray:
    """
    Reverse the AES key schedule to recover the original key from the last round key.
    
    Args:
        last_round_key: 16-byte last round key (K10)
    
    Returns:
        16-byte original key (K0)
    """
    # We need to reverse 10 rounds of key schedule
    # K[i] = K[i-1] XOR transform(K[i-1])
    # So K[i-1] = K[i] XOR transform(K[i-1])
    # But we need K[i-1] to compute transform... we work backwards
    
    expanded = np.zeros(176, dtype=np.uint8)
    expanded[160:176] = last_round_key
    
    # Work backwards from round 10 to round 0
    for i in range(43, 3, -1):
        if i % 4 == 0:
            # This word was created with the complex transformation
            # w[i] = w[i-4] XOR SubWord(RotWord(w[i-1])) XOR Rcon
            # So w[i-4] = w[i] XOR SubWord(RotWord(w[i-1])) XOR Rcon
            temp = expanded[(i-1)*4:(i-1)*4+4].copy()
            temp = np.roll(temp, -1)
            temp = SBOX[temp]
            temp[0] ^= RCON[i // 4 - 1]
            expanded[(i-4)*4:(i-4)*4+4] = expanded[i*4:i*4+4] ^ temp
        else:
            # Simple XOR: w[i] = w[i-4] XOR w[i-1]
            # So w[i-4] = w[i] XOR w[i-1]
            expanded[(i-4)*4:(i-4)*4+4] = expanded[i*4:i*4+4] ^ expanded[(i-1)*4:(i-1)*4+4]
    
    return expanded[:16]


def parse_header_file(header_path: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Parse a vector header file to extract key, plaintext, and expected ciphertext.
    
    Returns: (key, plaintext, ciphertext) as numpy arrays, or None if not found
    """
    try:
        with open(header_path, 'r') as f:
            content = f.read()
        
        def extract_array(pattern: str) -> Optional[np.ndarray]:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                hex_values = re.findall(r'0x([0-9a-fA-F]{2})', match.group(1))
                if hex_values:
                    return np.array([int(h, 16) for h in hex_values], dtype=np.uint8)
            return None
        
        key = extract_array(r'test_key\s*\[\s*\d*\s*\]\s*=\s*\{([^}]+)\}')
        plaintext = extract_array(r'test_plaintext\s*\[\s*\d*\s*\]\s*=\s*\{([^}]+)\}')
        ciphertext = extract_array(r'test_expected_ciphertext\s*\[\s*\d*\s*\]\s*=\s*\{([^}]+)\}')
        
        return key, plaintext, ciphertext
        
    except Exception as e:
        print(f"Warning: Failed to parse {header_path}: {e}")
        return None, None, None


def load_trace(csv_path: str) -> Optional[np.ndarray]:
    """Load a trace from CSV file."""
    try:
        data = []
        with open(csv_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(',')
                try:
                    # Take the last column as the value
                    data.append(float(parts[-1]))
                except (ValueError, IndexError):
                    continue
        
        if data:
            return np.array(data, dtype=np.float64)
        return None
        
    except Exception as e:
        return None


def _load_trace_worker(args):
    """Worker function for parallel trace loading."""
    idx, traces_dir, trace_suffix = args
    
    patterns = [
        f'vanilla_{idx}{trace_suffix}',
        f'trace_vector_{idx}{trace_suffix}',
        f'vector_{idx}{trace_suffix}',
        f'trace_{idx}{trace_suffix}',
        f'{idx}{trace_suffix}',
    ]
    
    trace_file = None
    for pattern in patterns:
        candidate = os.path.join(traces_dir, pattern)
        if os.path.exists(candidate):
            trace_file = candidate
            break
    
    if trace_file is None:
        matches = glob.glob(os.path.join(traces_dir, f'*_{idx}{trace_suffix}'))
        if not matches:
            matches = glob.glob(os.path.join(traces_dir, f'*{idx}*{trace_suffix}'))
        if matches:
            trace_file = matches[0]
    
    if trace_file is None:
        return None
    
    trace = load_trace(trace_file)
    if trace is not None:
        return (idx, trace)
    return None


def align_traces_xcorr(traces: np.ndarray, reference_idx: int = 0, 
                       max_shift: int = 100) -> np.ndarray:
    """
    Align traces using cross-correlation.
    """
    num_traces, trace_len = traces.shape
    reference = traces[reference_idx]
    
    ref_norm = reference - np.mean(reference)
    
    shifts = np.zeros(num_traces, dtype=np.int32)
    
    for i in range(num_traces):
        if i == reference_idx:
            continue
        
        trace = traces[i]
        trace_norm = trace - np.mean(trace)
        
        correlation = np.correlate(trace_norm, ref_norm, mode='full')
        
        zero_lag = len(ref_norm) - 1
        search_start = max(0, zero_lag - max_shift)
        search_end = min(len(correlation), zero_lag + max_shift + 1)
        
        best_idx = search_start + np.argmax(correlation[search_start:search_end])
        shifts[i] = best_idx - zero_lag
    
    max_left_shift = max(0, -np.min(shifts))
    max_right_shift = max(0, np.max(shifts))
    
    new_len = trace_len - max_left_shift - max_right_shift
    if new_len <= 0:
        print("Warning: Alignment would result in zero-length traces. Skipping alignment.")
        return traces
    
    aligned = np.zeros((num_traces, new_len), dtype=traces.dtype)
    
    for i in range(num_traces):
        shift = shifts[i]
        start = max_left_shift + shift
        end = start + new_len
        aligned[i] = traces[i, start:end]
    
    return aligned


def align_traces_peak(traces: np.ndarray, window_start: int = 0, 
                      window_end: int = None, max_shift: int = 100) -> np.ndarray:
    """
    Align traces based on peak position within a window.
    """
    num_traces, trace_len = traces.shape
    
    if window_end is None:
        window_end = min(trace_len, window_start + 1000)
    
    peak_positions = np.zeros(num_traces, dtype=np.int32)
    for i in range(num_traces):
        window = traces[i, window_start:window_end]
        peak_positions[i] = window_start + np.argmax(np.abs(window))
    
    ref_peak = int(np.median(peak_positions))
    shifts = ref_peak - peak_positions
    
    shifts = np.clip(shifts, -max_shift, max_shift)
    
    max_left = max(0, np.max(shifts))
    max_right = max(0, -np.min(shifts))
    new_len = trace_len - max_left - max_right
    
    if new_len <= 0:
        return traces
    
    aligned = np.zeros((num_traces, new_len), dtype=traces.dtype)
    for i in range(num_traces):
        shift = shifts[i]
        if shift >= 0:
            aligned[i] = traces[i, shift:shift + new_len]
        else:
            aligned[i] = traces[i, :new_len]
    
    return aligned


def compute_correlation(traces: np.ndarray, hypotheses: np.ndarray) -> np.ndarray:
    """
    Compute Pearson correlation between traces and hypothetical power values.
    Fully vectorized for speed.
    """
    num_traces, trace_len = traces.shape
    
    h_mean = np.mean(hypotheses)
    h_std = np.std(hypotheses)
    if h_std == 0:
        return np.zeros(trace_len)
    h_norm = (hypotheses - h_mean) / h_std
    
    # Fully vectorized correlation computation
    traces_mean = np.mean(traces, axis=0)
    traces_std = np.std(traces, axis=0)
    traces_std[traces_std == 0] = 1
    
    # Normalize all traces at once: (traces - mean) / std
    traces_norm = (traces - traces_mean) / traces_std
    
    # Correlation is dot product of normalized vectors / n
    correlations = np.dot(h_norm, traces_norm) / num_traces
    
    return correlations


# AES ShiftRows mapping: maps state byte index to ciphertext byte index
# In last round: ciphertext = AddRoundKey(ShiftRows(SubBytes(state)))
# So ciphertext[SHIFT_ROWS[i]] contains the S-box output of state byte i
# AES state is column-major: byte indices are:
#   0  4  8 12
#   1  5  9 13
#   2  6 10 14
#   3  7 11 15
# ShiftRows shifts rows left by row index:
#   Row 0: no shift     -> 0, 4, 8, 12 stay at 0, 4, 8, 12
#   Row 1: shift by 1   -> 1, 5, 9, 13 go to 5, 9, 13, 1
#   Row 2: shift by 2   -> 2, 6, 10, 14 go to 10, 14, 2, 6
#   Row 3: shift by 3   -> 3, 7, 11, 15 go to 15, 3, 7, 11
SHIFT_ROWS = np.array([0, 5, 10, 15, 4, 9, 14, 3, 8, 13, 2, 7, 12, 1, 6, 11], dtype=np.uint8)
# Inverse: maps ciphertext byte index back to state byte index before ShiftRows
INV_SHIFT_ROWS = np.array([0, 13, 10, 7, 4, 1, 14, 11, 8, 5, 2, 15, 12, 9, 6, 3], dtype=np.uint8)


def attack_single_byte_last_round(byte_idx: int, ciphertexts: np.ndarray, traces: np.ndarray,
                                   power_model: str = 'hw', 
                                   precomputed: Optional[Dict] = None,
                                   account_for_shiftrows: bool = True) -> Tuple[int, np.ndarray, np.ndarray]:
    """
    Perform CPA attack on a single LAST ROUND key byte.
    Optimized with vectorized operations for all 256 key hypotheses.
    
    Args:
        byte_idx: Index of the key byte to attack (0-15)
        ciphertexts: Array of ciphertexts (num_traces, 16)
        traces: Array of power traces (num_traces, trace_length)
        power_model: 'hw' for Hamming Weight, 'hd' for Hamming Distance
        precomputed: Optional dict with precomputed normalized traces
        account_for_shiftrows: If True, account for ShiftRows in the attack model
    
    Returns:
        (best_key_byte, all_correlations, max_correlations)
    """
    num_traces = len(ciphertexts)
    trace_len = traces.shape[1]
    
    # Get the ciphertext byte at position byte_idx
    ct_byte = ciphertexts[:, byte_idx]
    
    # Build hypotheses matrix for all 256 key guesses at once (256, num_traces)
    key_guesses = np.arange(256, dtype=np.uint8)
    # XOR each ciphertext byte with all 256 possible keys: (256, num_traces)
    xor_result = ct_byte[np.newaxis, :] ^ key_guesses[:, np.newaxis]
    # Apply inverse S-box to get state before SubBytes
    inv_sbox_out = INV_SBOX[xor_result]
    
    # Compute hypothetical power for all keys at once
    if power_model == 'hw':
        # Hamming Weight of the S-box output (before AddRoundKey in last round)
        # This is the state after SubBytes, before ShiftRows and AddRoundKey
        hypotheses_matrix = HW_TABLE[inv_sbox_out].astype(np.float64)  # (256, num_traces)
    elif power_model == 'hd':
        # Hamming Distance between ciphertext byte and inverse S-box output
        hypotheses_matrix = HW_TABLE[xor_result ^ inv_sbox_out].astype(np.float64)
    elif power_model == 'sbox_out':
        # Target the S-box output directly (state after SubBytes)
        # This is equivalent to hw but we use the forward S-box instead
        # State before SubBytes = InvSbox(InvShiftRows(ciphertext XOR K10))
        # For power model, we want the S-box OUTPUT which is InvShiftRows(ciphertext XOR K10)
        # But since we XOR first then would need InvShiftRows, let's just use HW
        hypotheses_matrix = HW_TABLE[xor_result].astype(np.float64)
    else:
        hypotheses_matrix = HW_TABLE[inv_sbox_out].astype(np.float64)
    
    # Normalize hypotheses: (256, num_traces)
    h_mean = np.mean(hypotheses_matrix, axis=1, keepdims=True)
    h_std = np.std(hypotheses_matrix, axis=1, keepdims=True)
    h_std[h_std == 0] = 1
    h_norm = (hypotheses_matrix - h_mean) / h_std
    
    # Use precomputed normalized traces if available, otherwise compute
    if precomputed is not None and 'traces_norm' in precomputed:
        traces_norm = precomputed['traces_norm']
    else:
        traces_mean = np.mean(traces, axis=0)
        traces_std = np.std(traces, axis=0)
        traces_std[traces_std == 0] = 1
        traces_norm = (traces - traces_mean) / traces_std
    
    # Compute correlations for all 256 keys at once using matrix multiplication
    # h_norm: (256, num_traces), traces_norm: (num_traces, trace_len)
    # Result: (256, trace_len)
    all_correlations = np.dot(h_norm, traces_norm) / num_traces
    
    # Find max absolute correlation for each key
    max_correlations = np.max(np.abs(all_correlations), axis=1)
    
    best_key = np.argmax(max_correlations)
    
    return best_key, all_correlations, max_correlations


def _attack_byte_worker(args):
    """Worker function for parallel byte attack."""
    byte_idx, ciphertexts, traces_norm, num_traces, power_model = args
    
    ct_byte = ciphertexts[:, byte_idx]
    
    # Build hypotheses matrix for all 256 key guesses at once
    key_guesses = np.arange(256, dtype=np.uint8)
    xor_result = ct_byte[np.newaxis, :] ^ key_guesses[:, np.newaxis]
    inv_sbox_out = INV_SBOX[xor_result]
    
    if power_model == 'hw':
        hypotheses_matrix = HW_TABLE[inv_sbox_out].astype(np.float64)
    else:
        hypotheses_matrix = HW_TABLE[xor_result ^ inv_sbox_out].astype(np.float64)
    
    # Normalize hypotheses
    h_mean = np.mean(hypotheses_matrix, axis=1, keepdims=True)
    h_std = np.std(hypotheses_matrix, axis=1, keepdims=True)
    h_std[h_std == 0] = 1
    h_norm = (hypotheses_matrix - h_mean) / h_std
    
    # Compute correlations
    all_correlations = np.dot(h_norm, traces_norm) / num_traces
    max_correlations = np.max(np.abs(all_correlations), axis=1)
    best_key = np.argmax(max_correlations)
    
    return byte_idx, best_key, all_correlations, max_correlations


def cpa_attack_last_round(ciphertexts: np.ndarray, traces: np.ndarray, 
                          power_model: str = 'hw', num_workers: int = 4,
                          known_key: Optional[np.ndarray] = None) -> Dict:
    """
    Perform full CPA attack on all 16 LAST ROUND key bytes.
    Optimized with precomputed normalized traces and optional parallelization.
    
    Args:
        ciphertexts: Array of ciphertexts (num_traces, 16)
        traces: Array of power traces (num_traces, trace_length)
        power_model: 'hw' or 'hd'
        num_workers: Number of parallel workers
        known_key: Known original key for validation (optional)
    
    Returns:
        Dictionary with attack results
    """
    # Compute expected last round key if original key is known
    known_last_round_key = None
    if known_key is not None:
        expanded = expand_key(known_key)
        known_last_round_key = expanded[160:176]
    
    results = {
        'recovered_last_round_key': np.zeros(16, dtype=np.uint8),
        'recovered_original_key': None,
        'correlations': {},
        'max_correlations': {},
        'correct_key_rank': np.zeros(16, dtype=np.int32),
        'success': np.zeros(16, dtype=bool),
    }
    
    print(f"\nAttacking 16 LAST ROUND key bytes using {power_model.upper()} model...")
    print(f"Number of traces: {len(ciphertexts)}")
    print(f"Trace length: {traces.shape[1]} samples")
    print(f"Using {num_workers} parallel workers")
    print()
    
    # Precompute normalized traces ONCE (major optimization)
    print("  Precomputing normalized traces...")
    traces_mean = np.mean(traces, axis=0)
    traces_std = np.std(traces, axis=0)
    traces_std[traces_std == 0] = 1
    traces_norm = (traces - traces_mean) / traces_std
    num_traces = len(ciphertexts)
    print("  Done.")
    
    # Collect results for printing after progress bar
    byte_results = []
    
    if num_workers > 1:
        # Parallel attack on all 16 bytes
        from multiprocessing import Pool
        
        # Prepare arguments for each byte
        args_list = [(i, ciphertexts, traces_norm, num_traces, power_model) for i in range(16)]
        
        with Pool(processes=num_workers) as pool:
            # Use imap to get results as they complete with progress bar
            results_iter = pool.imap(_attack_byte_worker, args_list)
            for byte_idx, best_key, all_corr, max_corr in tqdm(results_iter, total=16, 
                                                                desc='Attacking bytes', 
                                                                unit='byte', ncols=80):
                results['recovered_last_round_key'][byte_idx] = best_key
                results['correlations'][byte_idx] = all_corr
                results['max_correlations'][byte_idx] = max_corr
                
                if known_last_round_key is not None:
                    correct_key = known_last_round_key[byte_idx]
                    sorted_indices = np.argsort(max_corr)[::-1]
                    rank = np.where(sorted_indices == correct_key)[0][0]
                    results['correct_key_rank'][byte_idx] = rank
                    results['success'][byte_idx] = (best_key == correct_key)
                    
                    status = "✓" if best_key == correct_key else "✗"
                    byte_results.append((byte_idx, f"  Byte {byte_idx:2d}: recovered=0x{best_key:02x}, "
                          f"actual=0x{correct_key:02x}, rank={rank:3d}, "
                          f"corr={max_corr[best_key]:.4f} {status}"))
                else:
                    byte_results.append((byte_idx, f"  Byte {byte_idx:2d}: recovered=0x{best_key:02x}, "
                          f"corr={max_corr[best_key]:.4f}"))
    else:
        # Sequential attack (simpler, no multiprocessing overhead)
        precomputed = {'traces_norm': traces_norm}
        byte_iterator = tqdm(range(16), desc='Attacking bytes', unit='byte', ncols=80)
        for byte_idx in byte_iterator:
            best_key, all_corr, max_corr = attack_single_byte_last_round(
                byte_idx, ciphertexts, traces, power_model, precomputed=precomputed
            )
            
            results['recovered_last_round_key'][byte_idx] = best_key
            results['correlations'][byte_idx] = all_corr
            results['max_correlations'][byte_idx] = max_corr
            
            if known_last_round_key is not None:
                correct_key = known_last_round_key[byte_idx]
                sorted_indices = np.argsort(max_corr)[::-1]
                rank = np.where(sorted_indices == correct_key)[0][0]
                results['correct_key_rank'][byte_idx] = rank
                results['success'][byte_idx] = (best_key == correct_key)
                
                status = "✓" if best_key == correct_key else "✗"
                byte_results.append((byte_idx, f"  Byte {byte_idx:2d}: recovered=0x{best_key:02x}, "
                      f"actual=0x{correct_key:02x}, rank={rank:3d}, "
                      f"corr={max_corr[best_key]:.4f} {status}"))
            else:
                byte_results.append((byte_idx, f"  Byte {byte_idx:2d}: recovered=0x{best_key:02x}, "
                      f"corr={max_corr[best_key]:.4f}"))
    
    # Sort and print results by byte index
    byte_results.sort(key=lambda x: x[0])
    print("\nPer-byte attack results:")
    for _, result in byte_results:
        print(result)
    
    # Recover original key from last round key
    results['recovered_original_key'] = inverse_key_schedule(results['recovered_last_round_key'])
    
    return results


def plot_results(results: Dict, output_dir: str, known_key: Optional[np.ndarray] = None,
                 traces: Optional[np.ndarray] = None, downsample: int = 100):
    """
    Generate plots for attack results.
    
    Args:
        results: Attack results dictionary
        output_dir: Directory to save plots
        known_key: Known key for validation
        traces: Power traces (optional, for overlay plot)
        downsample: Downsample factor for correlation traces (default 100)
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.collections import LineCollection
    except ImportError:
        print("Warning: matplotlib not available, skipping plots")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    recovered_key = results['recovered_last_round_key']
    
    # Compute expected last round key if known
    known_last_round_key = None
    if known_key is not None:
        expanded = expand_key(known_key)
        known_last_round_key = expanded[160:176]
    
    # Get trace length and compute downsampling
    trace_len = results['correlations'][0].shape[1]
    ds = max(1, downsample)  # Downsample factor
    x_ds = np.arange(0, trace_len, ds)
    
    # Define plots to generate
    plot_names = ['correlation_traces', 'key_hypotheses', 'attack_summary', 
                  'trace_overlay', 'detailed_byte']
    plot_progress = tqdm(total=len(plot_names), desc='Generating plots', unit='plot', ncols=80)
    
    # ==========================================================================
    # Plot 1: Correlation traces for each key byte (4x4 grid) - OPTIMIZED
    # ==========================================================================
    fig, axes = plt.subplots(4, 4, figsize=(20, 16))
    fig.suptitle('CPA Last-Round Correlation Traces for All Key Bytes', fontsize=14)
    
    for byte_idx in range(16):
        ax = axes[byte_idx // 4, byte_idx % 4]
        all_corr = results['correlations'][byte_idx]
        best_key = recovered_key[byte_idx]
        
        # Downsample and plot only top 20 hypotheses + best + correct (much faster)
        max_corr = results['max_correlations'][byte_idx]
        top_keys = set(np.argsort(max_corr)[-20:])  # Top 20 by correlation
        top_keys.add(best_key)
        if known_last_round_key is not None:
            top_keys.add(known_last_round_key[byte_idx])
        
        # Plot top hypotheses in light gray (downsampled)
        for k in top_keys:
            if k != best_key and (known_last_round_key is None or k != known_last_round_key[byte_idx]):
                ax.plot(x_ds, all_corr[k, ::ds], color='lightgray', alpha=0.5, linewidth=0.5)
        
        # Plot best hypothesis in red
        ax.plot(x_ds, all_corr[best_key, ::ds], color='red', linewidth=1.0, 
                label=f'Best: 0x{best_key:02x}')
        
        # Plot correct key in green if known and different from best
        if known_last_round_key is not None and known_last_round_key[byte_idx] != best_key:
            ax.plot(x_ds, all_corr[known_last_round_key[byte_idx], ::ds], color='green', linewidth=1.0,
                    label=f'Actual: 0x{known_last_round_key[byte_idx]:02x}')
        
        ax.set_title(f'Byte {byte_idx}')
        ax.set_xlabel('Sample')
        ax.set_ylabel('Correlation')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'correlation_traces_last_round.png'), dpi=100)
    plt.close()
    plot_progress.update(1)
    
    # ==========================================================================
    # Plot 2: Maximum correlation per key hypothesis (bar plots)
    # ==========================================================================
    fig, axes = plt.subplots(4, 4, figsize=(20, 16))
    fig.suptitle('Maximum Correlation per Last-Round Key Hypothesis', fontsize=14)
    
    for byte_idx in range(16):
        ax = axes[byte_idx // 4, byte_idx % 4]
        max_corr = results['max_correlations'][byte_idx]
        best_key = recovered_key[byte_idx]
        
        # Create bar colors
        colors = ['lightblue'] * 256
        colors[best_key] = 'red'
        if known_last_round_key is not None:
            colors[known_last_round_key[byte_idx]] = 'green' if known_last_round_key[byte_idx] == best_key else 'orange'
        
        ax.bar(range(256), max_corr, color=colors, width=1.0)
        ax.axvline(x=best_key, color='red', linestyle='--', alpha=0.7)
        
        if known_last_round_key is not None and known_last_round_key[byte_idx] != best_key:
            ax.axvline(x=known_last_round_key[byte_idx], color='green', linestyle='--', alpha=0.7)
        
        ax.set_title(f'Byte {byte_idx}: best=0x{best_key:02x}')
        ax.set_xlabel('Key Hypothesis')
        ax.set_ylabel('Max |Correlation|')
        ax.set_xlim(-1, 256)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'key_hypotheses_last_round.png'), dpi=100)
    plt.close()
    plot_progress.update(1)
    
    # ==========================================================================
    # Plot 3: Key recovery summary
    # ==========================================================================
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Subplot 1: Recovered last round key bytes
    ax = axes[0, 0]
    x = np.arange(16)
    ax.bar(x, recovered_key, color='steelblue', alpha=0.8)
    ax.set_xlabel('Key Byte Index')
    ax.set_ylabel('Recovered Value')
    ax.set_title('Recovered Last Round Key Bytes (K10)')
    ax.set_xticks(x)
    for i, v in enumerate(recovered_key):
        ax.text(i, v + 2, f'0x{v:02x}', ha='center', fontsize=8, rotation=90)
    
    # Subplot 2: Maximum correlations achieved
    ax = axes[0, 1]
    max_corrs = [results['max_correlations'][i][recovered_key[i]] for i in range(16)]
    colors = ['green' if c > 0.5 else 'orange' if c > 0.3 else 'red' for c in max_corrs]
    ax.bar(x, max_corrs, color=colors, alpha=0.8)
    ax.set_xlabel('Key Byte Index')
    ax.set_ylabel('Max Correlation')
    ax.set_title('Correlation Strength per Byte')
    ax.set_xticks(x)
    ax.axhline(y=0.5, color='green', linestyle='--', alpha=0.5, label='Strong')
    ax.axhline(y=0.3, color='orange', linestyle='--', alpha=0.5, label='Moderate')
    ax.legend()
    
    # Subplot 3: Key rank if known
    if known_last_round_key is not None:
        ax = axes[1, 0]
        ranks = results['correct_key_rank']
        colors = ['green' if r == 0 else 'orange' if r < 5 else 'red' for r in ranks]
        ax.bar(x, ranks, color=colors, alpha=0.8)
        ax.set_xlabel('Key Byte Index')
        ax.set_ylabel('Correct Key Rank')
        ax.set_title('Rank of Correct Last-Round Key (0 = recovered correctly)')
        ax.set_xticks(x)
        
        # Subplot 4: Success indicators
        ax = axes[1, 1]
        success = results['success'].astype(int)
        colors = ['green' if s else 'red' for s in success]
        ax.bar(x, success, color=colors, alpha=0.8)
        ax.set_xlabel('Key Byte Index')
        ax.set_ylabel('Success (1=correct)')
        ax.set_title(f'Key Recovery Success: {np.sum(success)}/16 bytes')
        ax.set_xticks(x)
        ax.set_yticks([0, 1])
    else:
        axes[1, 0].text(0.5, 0.5, 'Known key not provided', ha='center', va='center',
                        transform=axes[1, 0].transAxes, fontsize=12)
        axes[1, 0].set_title('Key Rank (N/A)')
        axes[1, 1].text(0.5, 0.5, 'Known key not provided', ha='center', va='center',
                        transform=axes[1, 1].transAxes, fontsize=12)
        axes[1, 1].set_title('Success Rate (N/A)')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'attack_summary_last_round.png'), dpi=100)
    plt.close()
    plot_progress.update(1)
    
    # ==========================================================================
    # Plot 4: Sample trace with correlation overlay (downsampled)
    # ==========================================================================
    if traces is not None:
        fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
        
        # Average trace (downsampled)
        ax = axes[0]
        mean_trace = np.mean(traces, axis=0)
        ax.plot(x_ds, mean_trace[::ds], color='steelblue', linewidth=0.5)
        ax.set_ylabel('Average Trace Value')
        ax.set_title('Average Power Trace')
        ax.grid(True, alpha=0.3)
        
        # Correlation for first byte (best hypothesis, downsampled)
        ax = axes[1]
        corr = results['correlations'][0][recovered_key[0]]
        ax.plot(x_ds, corr[::ds], color='red', linewidth=0.5)
        ax.set_xlabel('Sample')
        ax.set_ylabel('Correlation')
        ax.set_title(f'Correlation Trace for Byte 0 (last-round key=0x{recovered_key[0]:02x})')
        ax.grid(True, alpha=0.3)
        
        # Mark peak correlation
        peak_idx = np.argmax(np.abs(corr))
        ax.axvline(x=peak_idx, color='green', linestyle='--', alpha=0.7)
        ax.annotate(f'Peak @ {peak_idx}', xy=(peak_idx, corr[peak_idx]),
                    xytext=(peak_idx + 100, corr[peak_idx]),
                    arrowprops=dict(arrowstyle='->', color='green'))
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'trace_correlation_overlay_last_round.png'), dpi=100)
        plt.close()
    plot_progress.update(1)
    
    # ==========================================================================
    # Plot 5: Detailed view of best byte (OPTIMIZED - only top keys, downsampled)
    # ==========================================================================
    best_byte_idx = np.argmax([results['max_correlations'][i][recovered_key[i]] 
                               for i in range(16)])
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    all_corr = results['correlations'][best_byte_idx]
    max_corr = results['max_correlations'][best_byte_idx]
    best_key = recovered_key[best_byte_idx]
    
    # Get top 20 keys for plotting
    top_keys = set(np.argsort(max_corr)[-20:])
    top_keys.add(best_key)
    if known_last_round_key is not None:
        top_keys.add(known_last_round_key[best_byte_idx])
    
    # Full correlation trace (downsampled, only top keys)
    ax = axes[0, 0]
    for k in top_keys:
        if k != best_key:
            ax.plot(x_ds, all_corr[k, ::ds], color='lightgray', alpha=0.4, linewidth=0.5)
    ax.plot(x_ds, all_corr[best_key, ::ds], color='red', alpha=1.0, linewidth=1.5)
    ax.set_title(f'Byte {best_byte_idx}: Top Key Correlation Traces')
    ax.set_xlabel('Sample')
    ax.set_ylabel('Correlation')
    
    # Zoomed around peak (full resolution for small window)
    peak_sample = np.argmax(np.abs(all_corr[best_key]))
    zoom_start = max(0, peak_sample - 500)
    zoom_end = min(all_corr.shape[1], peak_sample + 500)
    
    ax = axes[0, 1]
    for k in top_keys:
        if k != best_key:
            ax.plot(range(zoom_start, zoom_end), all_corr[k, zoom_start:zoom_end],
                    color='lightgray', alpha=0.4, linewidth=0.5)
    ax.plot(range(zoom_start, zoom_end), all_corr[best_key, zoom_start:zoom_end],
            color='red', alpha=1.0, linewidth=1.5)
    ax.axvline(x=peak_sample, color='green', linestyle='--', alpha=0.7)
    ax.set_title(f'Zoomed Around Peak (sample {peak_sample})')
    ax.set_xlabel('Sample')
    ax.set_ylabel('Correlation')
    
    # Sorted max correlations
    ax = axes[1, 0]
    sorted_idx = np.argsort(max_corr)[::-1]
    sorted_corr = max_corr[sorted_idx]
    colors = ['red' if sorted_idx[i] == best_key else 'steelblue' 
              for i in range(len(sorted_idx))]
    ax.bar(range(256), sorted_corr, color=colors, width=1.0)
    ax.set_title('Sorted Max Correlations (red = best)')
    ax.set_xlabel('Rank')
    ax.set_ylabel('Max |Correlation|')
    
    # Top 10 candidates
    ax = axes[1, 1]
    top_10_idx = sorted_idx[:10]
    top_10_corr = max_corr[top_10_idx]
    colors = ['red' if k == best_key else 'steelblue' for k in top_10_idx]
    bars = ax.bar(range(10), top_10_corr, color=colors)
    ax.set_title('Top 10 Key Candidates')
    ax.set_xlabel('Rank')
    ax.set_ylabel('Max |Correlation|')
    ax.set_xticks(range(10))
    ax.set_xticklabels([f'0x{k:02x}' for k in top_10_idx], rotation=45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'byte_{best_byte_idx}_detailed_last_round.png'), dpi=100)
    plt.close()
    plot_progress.update(1)
    plot_progress.close()
    
    print(f"All plots saved to: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description='CPA Attack on AES-128 LAST ROUND using WAL++ HD/HW traces',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --traces-dir ./traces/walpp --vectors-dir . --trace-type hw
  %(prog)s --traces-dir ./traces/walpp --vectors-dir . --trace-type hd --align xcorr
  %(prog)s --traces-dir ./traces/walpp --vectors-dir . --num-traces 50 --output ./cpa_last_round_results

Note: This attack targets the LAST ROUND key (K10). The script will automatically
compute the original key (K0) by reversing the key schedule.
        """
    )
    
    parser.add_argument('--traces-dir', required=True,
                        help='Directory containing HD/HW CSV trace files')
    parser.add_argument('--vectors-dir', required=True,
                        help='Directory containing vector_*.h header files')
    parser.add_argument('--trace-type', choices=['hw', 'hd'], default='hw',
                        help='Type of traces: hw (Hamming Weight) or hd (Hamming Distance)')
    parser.add_argument('--power-model', choices=['hw', 'hd'], default=None,
                        help='Power model to use (default: same as trace-type)')
    parser.add_argument('--output', '-o', default='./cpa_last_round_results',
                        help='Output directory for results and plots')
    parser.add_argument('--num-traces', '-n', type=int, default=None,
                        help='Number of traces to use (default: all available)')
    parser.add_argument('--align', choices=['none', 'xcorr', 'peak'], default='none',
                        help='Trace alignment method')
    parser.add_argument('--max-shift', type=int, default=100,
                        help='Maximum shift for alignment (default: 100)')
    parser.add_argument('--trim-start', type=int, default=0,
                        help='Trim this many samples from start of traces')
    parser.add_argument('--trim-end', type=int, default=0,
                        help='Trim this many samples from end of traces')
    parser.add_argument('--no-plots', action='store_true',
                        help='Skip plot generation')
    parser.add_argument('--workers', '-j', type=int, default=4,
                        help='Number of parallel workers')
    
    args = parser.parse_args()
    
    # Default power model to trace type
    if args.power_model is None:
        args.power_model = args.trace_type
    
    print("=" * 70)
    print("CPA Attack on AES-128 - LAST ROUND")
    print("=" * 70)
    print(f"Traces directory: {args.traces_dir}")
    print(f"Vectors directory: {args.vectors_dir}")
    print(f"Trace type: {args.trace_type.upper()}")
    print(f"Power model: {args.power_model.upper()}")
    print(f"Alignment: {args.align}")
    print(f"Output directory: {args.output}")
    print()
    
    # ==========================================================================
    # Step 1: Discover and load vector header files
    # ==========================================================================
    print("Step 1: Loading ciphertext vectors...")
    
    vector_files = sorted(glob.glob(os.path.join(args.vectors_dir, 'vector_*.h')),
                          key=lambda x: int(re.search(r'vector_(\d+)\.h', x).group(1)))
    
    if not vector_files:
        print(f"Error: No vector_*.h files found in {args.vectors_dir}")
        sys.exit(1)
    
    print(f"  Found {len(vector_files)} vector files")
    
    # Limit to first N vectors if requested (to avoid loading unnecessary data)
    if args.num_traces and args.num_traces < len(vector_files):
        vector_files = vector_files[:args.num_traces]
        print(f"  Limiting to first {args.num_traces} vectors")
    
    ciphertexts = []
    known_key = None
    vector_indices = []
    
    for vf in tqdm(vector_files, desc='Parsing vectors', unit='file', ncols=80):
        idx = int(re.search(r'vector_(\d+)\.h', vf).group(1))
        key, pt, ct = parse_header_file(vf)
        
        if ct is None:
            print(f"  Warning: Could not parse ciphertext from {vf}")
            continue
        
        if known_key is None and key is not None:
            known_key = key
        
        ciphertexts.append(ct)
        vector_indices.append(idx)
    
    ciphertexts = np.array(ciphertexts)
    print(f"  Loaded {len(ciphertexts)} ciphertexts")
    
    if known_key is not None:
        print(f"  Known original key (K0): {known_key.tobytes().hex()}")
        expanded = expand_key(known_key)
        known_last_round_key = expanded[160:176]
        print(f"  Expected last-round key (K10): {known_last_round_key.tobytes().hex()}")
    
    # ==========================================================================
    # Step 2: Load trace files (parallel)
    # ==========================================================================
    print("\nStep 2: Loading traces...")
    
    trace_suffix = f'_{args.trace_type}.csv'
    traces_list = []
    trace_indices = []
    
    if args.workers > 1:
        # Parallel trace loading
        from multiprocessing import Pool
        
        args_list = [(idx, args.traces_dir, trace_suffix) for idx in vector_indices]
        
        with Pool(processes=args.workers) as pool:
            results_iter = pool.imap(_load_trace_worker, args_list)
            for result in tqdm(results_iter, total=len(vector_indices), 
                              desc='Loading traces', unit='trace', ncols=80):
                if result is not None:
                    idx, trace = result
                    traces_list.append(trace)
                    trace_indices.append(idx)
    else:
        # Sequential loading
        for idx in tqdm(vector_indices, desc='Loading traces', unit='trace', ncols=80):
            result = _load_trace_worker((idx, args.traces_dir, trace_suffix))
            if result is not None:
                trace_idx, trace = result
                traces_list.append(trace)
                trace_indices.append(trace_idx)
    
    if not traces_list:
        print(f"Error: No trace files found in {args.traces_dir}")
        print(f"  Looking for files matching *{trace_suffix}")
        sys.exit(1)
    
    print(f"  Loaded {len(traces_list)} traces")
    
    # Match traces with ciphertexts
    matched_ciphertexts = []
    matched_traces = []
    
    for idx in trace_indices:
        if idx in vector_indices:
            ct_idx = vector_indices.index(idx)
            matched_ciphertexts.append(ciphertexts[ct_idx])
            trace_idx = trace_indices.index(idx)
            matched_traces.append(traces_list[trace_idx])
    
    if not matched_traces:
        print("Error: Could not match any traces with ciphertexts")
        sys.exit(1)
    
    print(f"  Matched {len(matched_traces)} trace-ciphertext pairs")
    
    # Convert to numpy arrays
    # Find minimum trace length
    min_len = min(len(t) for t in matched_traces)
    print(f"  Minimum trace length: {min_len} samples")
    
    # Truncate all traces to same length
    traces = np.array([t[:min_len] for t in matched_traces])
    ciphertexts = np.array(matched_ciphertexts)
    
    print(f"  Final trace matrix: {traces.shape}")
    
    # ==========================================================================
    # Step 3: Preprocess traces
    # ==========================================================================
    print("\nStep 3: Preprocessing traces...")
    
    # Trim
    if args.trim_start > 0 or args.trim_end > 0:
        end_idx = traces.shape[1] - args.trim_end if args.trim_end > 0 else traces.shape[1]
        traces = traces[:, args.trim_start:end_idx]
        print(f"  After trimming: {traces.shape}")
    
    # Align
    if args.align != 'none':
        print(f"  Aligning traces using {args.align} method...")
        if args.align == 'xcorr':
            traces = align_traces_xcorr(traces, max_shift=args.max_shift)
        else:
            traces = align_traces_peak(traces, max_shift=args.max_shift)
        print(f"  After alignment: {traces.shape}")
    
    # Normalize traces (zero mean, unit variance per trace)
    traces = (traces - np.mean(traces, axis=1, keepdims=True))
    std = np.std(traces, axis=1, keepdims=True)
    std[std == 0] = 1
    traces = traces / std
    
    # ==========================================================================
    # Step 4: Perform CPA attack on LAST ROUND
    # ==========================================================================
    print("\nStep 4: Performing CPA attack on LAST ROUND...")
    
    results = cpa_attack_last_round(ciphertexts, traces, power_model=args.power_model,
                                     num_workers=args.workers, known_key=known_key)
    
    # ==========================================================================
    # Step 5: Output results
    # ==========================================================================
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    recovered_last_round_key = results['recovered_last_round_key']
    recovered_original_key = results['recovered_original_key']
    
    print(f"\nRecovered last-round key (K10): {recovered_last_round_key.tobytes().hex()}")
    print(f"Recovered original key (K0):    {recovered_original_key.tobytes().hex()}")
    
    if known_key is not None:
        expanded = expand_key(known_key)
        known_last_round_key = expanded[160:176]
        
        print(f"\nActual last-round key (K10):    {known_last_round_key.tobytes().hex()}")
        print(f"Actual original key (K0):       {known_key.tobytes().hex()}")
        
        correct_last_round_bytes = np.sum(recovered_last_round_key == known_last_round_key)
        correct_original_bytes = np.sum(recovered_original_key == known_key)
        
        print(f"\nCorrect last-round key bytes: {correct_last_round_bytes}/16")
        print(f"Correct original key bytes:   {correct_original_bytes}/16")
        
        if correct_last_round_bytes == 16:
            print("\n*** FULL LAST-ROUND KEY RECOVERED SUCCESSFULLY! ***")
            if correct_original_bytes == 16:
                print("*** ORIGINAL KEY RECOVERED SUCCESSFULLY! ***")
        else:
            print(f"\nIncorrect last-round key bytes:")
            for i in range(16):
                if recovered_last_round_key[i] != known_last_round_key[i]:
                    rank = results['correct_key_rank'][i]
                    print(f"  Byte {i}: recovered=0x{recovered_last_round_key[i]:02x}, "
                          f"actual=0x{known_last_round_key[i]:02x}, rank={rank}")
    
    # ==========================================================================
    # Step 6: Generate plots
    # ==========================================================================
    if not args.no_plots:
        print("\nStep 5: Generating plots...")
        os.makedirs(args.output, exist_ok=True)
        plot_results(results, args.output, known_key=known_key, traces=traces)
    
    # Save results to file
    os.makedirs(args.output, exist_ok=True)
    results_file = os.path.join(args.output, 'attack_results_last_round.txt')
    with open(results_file, 'w') as f:
        f.write("CPA Attack Results - LAST ROUND\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Number of traces: {len(ciphertexts)}\n")
        f.write(f"Trace length: {traces.shape[1]}\n")
        f.write(f"Trace type: {args.trace_type.upper()}\n")
        f.write(f"Power model: {args.power_model.upper()}\n")
        f.write(f"Alignment: {args.align}\n\n")
        f.write(f"Recovered last-round key (K10): {recovered_last_round_key.tobytes().hex()}\n")
        f.write(f"Recovered original key (K0):    {recovered_original_key.tobytes().hex()}\n")
        if known_key is not None:
            expanded = expand_key(known_key)
            known_last_round_key = expanded[160:176]
            f.write(f"\nActual last-round key (K10):    {known_last_round_key.tobytes().hex()}\n")
            f.write(f"Actual original key (K0):       {known_key.tobytes().hex()}\n")
            f.write(f"\nCorrect last-round key bytes: {np.sum(recovered_last_round_key == known_last_round_key)}/16\n")
            f.write(f"Correct original key bytes: {np.sum(recovered_original_key == known_key)}/16\n\n")
            f.write("Per-byte results (last-round key):\n")
            for i in range(16):
                status = "✓" if recovered_last_round_key[i] == known_last_round_key[i] else "✗"
                f.write(f"  Byte {i:2d}: 0x{recovered_last_round_key[i]:02x} "
                        f"(actual: 0x{known_last_round_key[i]:02x}, rank: {results['correct_key_rank'][i]}) {status}\n")
    
    print(f"\nResults saved to: {results_file}")
    print("\nDone!")
    
    # Return success/failure
    if known_key is not None:
        return 0 if np.all(recovered_original_key == known_key) else 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
