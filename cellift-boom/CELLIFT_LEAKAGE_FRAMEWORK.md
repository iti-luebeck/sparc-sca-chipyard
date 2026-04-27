# CellIFT Side-Channel Leakage Detection Framework for BOOM

## Overview

This framework detects **key-dependent information leakage** in an out-of-order
RISC-V BOOM core running masked AES-128, using CellIFT (Cell-level Information
Flow Tracking). It works at the RTL level: Yosys instruments every gate in the
design with taint propagation logic, and a Verilator simulation tracks which
flip-flops carry information derived from a secret key. The leakage signals are
then analyzed with TVLA (Test Vector Leakage Assessment) and per-instruction
profiling to pinpoint exactly where and how much the implementation leaks.

### Key results

| Experiment                          | Max |t| | Verdict                        |
|-------------------------------------|---------|--------------------------------|
| Different keys (fixed vs random)    | 91.00   | KEY-DEPENDENT LEAKAGE DETECTED |
| Same key, different plaintext       | 0.00    | No leakage (validates tool)    |

Top leaking instruction: `lbu a6,256(a6)` (AES S-box table lookup), at
-2.40 Hamming weight bits/execution differential between keys.

---

## Architecture

```
 ┌───────────────┐      Yosys CellIFT       ┌─────────────────────┐
 │ boom_mem_top   │ ──── instrumentation ───> │ boom_mem_top         │
 │ (vanilla RTL)  │                           │ + _t0 taint signals  │
 └───────────────┘                           │ + _leak0 leak ports  │
                                              └──────────┬──────────┘
                                                         │
                                              ┌──────────▼──────────┐
                                              │ top_tiny_soc_with_  │
                                              │ leakage.sv          │
                                              │                     │
                                              │ • Connects all 53   │
                                              │   leak0 ports       │
                                              │ • $countones() on   │
                                              │   3 signal groups   │
                                              │ • Accumulates       │
                                              │   Hamming weight    │
                                              └──────────┬──────────┘
                                                         │ VCD trace
                                                         ▼
                                              ┌──────────────────────┐
                                              │ Python analysis      │
                                              │                      │
                                              │ • tvla_hamming.py    │
                                              │ • instruction_       │
                                              │   leakage.py         │
                                              └──────────────────────┘
```

### Signal flow

1. **Taint injection**: The simulator loads `taint_data.txt` at startup, marking
   the AES key share region (16 bytes at `0x80010000`) as tainted in SRAM.
2. **Taint propagation**: CellIFT-instrumented gates propagate taint through
   the BOOM pipeline. Every `_leak0` output port exposes which bits on that
   interface carry information derived from the tainted key.
3. **Hamming weight**: The wrapper computes `$countones()` across all leak
   signals every cycle, giving a per-cycle leakage amplitude (0-544 bits).
4. **VCD capture**: The Verilator simulation dumps all signals including the
   Hamming weight accumulators and BOOM's commit PC trace.
5. **Analysis**: Python scripts extract the Hamming weight trace from VCD and
   apply Welch's t-test (TVLA) or cross-reference with committed instructions.

---

## Directory Structure

```
cellift-boom/
├── src/
│   ├── top_tiny_soc_with_leakage.sv   # Leakage wrapper (Hamming weight tracking)
│   ├── boom_mem_top.sv                 # CellIFT-instrumented BOOM core
│   ├── ift_sram_mem.sv                 # Taint-aware SRAM model
│   └── ...
│
├── sw/
│   ├── scenario_aes128_masked_key/     # Fixed key scenario (FIPS-197 key)
│   │   ├── main.S                      # Entry point + data definitions
│   │   ├── aes128_masked.c             # Masked AES-128 in C (shared)
│   │   ├── link.ld                     # Linker: .tainted_data at 0x80010000
│   │   ├── taint_data.txt              # Taint config: 16 bytes at 0x80010000
│   │   ├── Makefile
│   │   └── build/app.elf               # Compiled binary + .dump
│   │
│   ├── scenario_aes128_random_key/     # Random key scenario (TVLA partner)
│   │   ├── main.S                      # Different key: 0xDEADBEEF...
│   │   └── ...                         # Same structure as above
│   │
│   └── scenario_aes128_same_key_diff_pt/  # Negative control
│       ├── main.S                      # Same key, different plaintext
│       └── ...
│
├── analysis/
│   ├── tvla_hamming.py                 # TVLA t-test on Hamming weight traces
│   ├── instruction_leakage.py          # Per-instruction leakage profiling
│   ├── tvla_cellift.py                 # Earlier boolean-counter TVLA (superseded)
│   ├── tvla_detailed.py                # Earlier detailed TVLA (superseded)
│   ├── tvla_hamming.png                # TVLA results plot (different keys)
│   ├── tvla_hamming_results.npz        # Saved numpy arrays
│   ├── instruction_leakage.png         # Instruction-level plots
│   ├── instruction_leakage_report.txt  # Text report
│   └── tvla_negative_control/          # Same-key validation results
│       ├── tvla_hamming.png
│       └── tvla_hamming_results.npz
│
├── traces/                             # VCD simulation traces
│   ├── aes_100k_fixed_hw.vcd          # Fixed key, 100k cycles (Hamming weight)
│   ├── aes_100k_random_hw.vcd         # Random key, 100k cycles (Hamming weight)
│   └── aes_100k_samekey_diffpt.vcd    # Negative control, 100k cycles
│
├── build/
│   └── run_cellift_trace_leakage_0.1/  # Verilator build
│       ├── default-verilator/
│       │   └── Vtop_tiny_soc           # Simulator binary
│       └── src/.../
│           └── top_tiny_soc_with_leakage.sv  # Build copy of wrapper
│
├── run_tvla_experiment.sh              # Automation script (early version)
└── Makefile                            # Top-level design Makefile
```

---

## Hardware: Leakage Wrapper

**File**: `src/top_tiny_soc_with_leakage.sv`

The wrapper instantiates the CellIFT-instrumented `boom_mem_top` and connects
all 53 `_leak0` output ports. These are grouped into three categories and fed
through `$countones()` for per-cycle Hamming weight computation:

| Group       | Signal examples                                    | Bits |
|-------------|----------------------------------------------------|------|
| **Data**    | `mem_wdata_leak0[63:0]`, `axi4_w_data_leak0[63:0]` | 256  |
| **Address** | `mem_addr_leak0[31:0]`, `axi4_ar_addr_leak0[31:0]` | 190  |
| **Control** | `mem_req_leak0`, `axi4_ar_valid_leak0`, etc.        | ~98  |

Output registers (visible in VCD):

| Signal                 | Width | Description                                   |
|------------------------|-------|-----------------------------------------------|
| `leakage_hamming_t0`   | 32    | Cumulative Hamming weight (main analysis signal)|
| `leakage_counter_t0`   | 32    | Boolean counter: +1 per leaking cycle (legacy) |
| `leak_hw_data_t0`      | 16    | Per-cycle data path Hamming weight              |
| `leak_hw_addr_t0`      | 16    | Per-cycle address path Hamming weight           |
| `leak_hw_ctrl_t0`      | 16    | Per-cycle control path Hamming weight           |

The Hamming weight approach captures leakage **amplitude** (how many bits leak),
not just presence (boolean). This is critical because two different AES keys
trigger leakage at the same cycles, but the *number* of leaking bits differs.

---

## Software Scenarios

All scenarios share the same masked AES-128 implementation (`aes128_masked.c`)
and linker script (`link.ld`). They differ only in the key material defined in
`main.S`.

### Taint configuration

All scenarios use the same `taint_data.txt`:
```
0 80010000 10 FFFFFFFFFFFFFFFFFFFFFFFF
```
Format: `<taint_id> <start_addr_hex> <size_hex> <taint_mask_hex>`

This marks 16 bytes at `0x80010000` (the `.tainted_data` section) with full
taint. The linker script places `aes_key_share0` at this address.

### Masked AES key structure

The AES key is split into two shares for first-order masking:
```
key_share0 = key XOR key_mask    (placed in .tainted_data → tainted)
key_mask                          (placed in .data → NOT tainted)
```

The AES implementation reconstructs the key as `key_share0 XOR key_mask` during
key expansion, and processes intermediate states in masked form.

### Scenario details

| Scenario                        | Key (128-bit)                         | Plaintext          | Purpose             |
|---------------------------------|---------------------------------------|--------------------|---------------------|
| `scenario_aes128_masked_key`    | `0x2B7E151628AED2A6ABF7158809CF4F3C`  | FIPS-197 Appendix B| Fixed reference      |
| `scenario_aes128_random_key`    | `0xDEADBEEFCAFEBABE0123456789ABCDEF`  | FIPS-197 Appendix B| TVLA partner         |
| `scenario_aes128_same_key_diff_pt`| `0x2B7E151628AED2A6ABF7158809CF4F3C`| `0x00112233...EEFF` | Negative control     |

### Building software

```bash
cd sw/scenario_aes128_masked_key
make
# Produces build/app.elf and build/app.elf.dump
```

Requires the RISC-V toolchain at:
`/mnt/nvme1n1p1/chipyard-1.11.0/.conda-env/riscv-tools/bin/riscv64-unknown-elf-gcc`

---

## Running Simulations

### Prerequisites

```bash
# Source the CellIFT environment (provides correct libstdc++, Verilator paths)
source /mnt/nvme1n1p1/cellift-meta-leakage/env.sh
```

### Running a simulation

```bash
cd /mnt/nvme1n1p1/cellift-designs/cellift-chipyard/cellift-boom

SIMLEN=100000 \
SIMSRAMELF=sw/scenario_aes128_masked_key/build/app.elf \
SIMROMELF=sw/scenario_aes128_masked_key/build/app.elf \
SIMSRAMTAINT=sw/scenario_aes128_masked_key/taint_data.txt \
TRACEFILE=traces/output.vcd \
./build/run_cellift_trace_leakage_0.1/default-verilator/Vtop_tiny_soc
```

Environment variables:
| Variable       | Description                                |
|----------------|--------------------------------------------|
| `SIMLEN`       | Simulation length in clock ticks           |
| `SIMSRAMELF`   | Path to ELF binary (loaded into SRAM)      |
| `SIMROMELF`    | Path to ELF binary (ROM image, same file)  |
| `SIMSRAMTAINT` | Path to taint configuration file           |
| `TRACEFILE`    | Output VCD file path                       |

A 100k-cycle simulation takes ~4 minutes and produces a ~550MB VCD file.

### Rebuilding the simulator

If you modify `top_tiny_soc_with_leakage.sv`, copy it to the build directory
and recompile (no need to re-run Yosys CellIFT synthesis):

```bash
cp src/top_tiny_soc_with_leakage.sv \
   build/run_cellift_trace_leakage_0.1/src/run_cellift_trace_leakage_0.1/src/

cd build/run_cellift_trace_leakage_0.1/default-verilator
make
```

---

## Analysis Scripts

### 1. TVLA Hamming Weight Analysis

**File**: `analysis/tvla_hamming.py`

Compares Hamming weight leakage traces between two VCD files (different keys)
using Welch's t-test. This is the primary analysis tool.

```bash
# Basic usage
python3 analysis/tvla_hamming.py traces/fixed.vcd traces/random.vcd analysis/

# With explicit AES execution window (recommended)
AES_START=348 AES_END=12950 \
python3 analysis/tvla_hamming.py traces/fixed.vcd traces/random.vcd analysis/
```

**What it does:**

1. Parses both VCD files, extracts `leakage_hamming_t0` (cumulative) and per-group
   signals (`leak_hw_data_t0`, `leak_hw_addr_t0`, `leak_hw_ctrl_t0`)
2. Converts cumulative accumulators to per-cycle rates via differencing
3. Determines the AES execution window (auto-detect or via env vars)
4. Applies Welch's t-test with sliding windows (sizes 10, 25, 50, 100)
5. Selects the best window size (most significant detections)
6. Reports all windows where |t| > 4.5 (TVLA threshold)

**Outputs:**
- `tvla_hamming.png` — 6-panel plot (cumulative HW, per-cycle AES zoom,
  difference, per-group difference, t-test, full-trace t-test)
- `tvla_hamming_results.npz` — Numpy archive with all computed arrays

**AES window detection:**
- If `AES_START`/`AES_END` env vars are set, uses those cycle numbers
- Otherwise auto-detects: start = first cycle with HW > 0, end = first cycle
  where the fixed-vs-random difference stays constant for 200 consecutive cycles

### 2. Instruction-Level Leakage Profiling

**File**: `analysis/instruction_leakage.py`

Cross-references the per-cycle Hamming weight leakage with BOOM's commit trace
(PC of retired instructions) to identify which specific instructions leak
key-dependent information.

```bash
python3 analysis/instruction_leakage.py \
    traces/aes_100k_fixed_hw.vcd \
    traces/aes_100k_random_hw.vcd \
    sw/scenario_aes128_masked_key/build/app.elf.dump \
    analysis/
```

**What it does:**

1. Parses the objdump disassembly to build a PC-to-instruction map
2. Parses VCD headers to find signal IDs for:
   - `io_commit_arch_valids_0` — 1-bit commit valid from BOOM's ROB
   - `core_io_ifu_get_pc_0_com_pc` — 40-bit committed PC from BOOM's FTQ
   - `leakage_hamming_t0` — Hamming weight accumulator
3. Extracts per-cycle signals from both VCDs (fixed and random key)
4. For each cycle where a commit occurs, records the committed PC and the
   leakage Hamming weight at that cycle
5. Aggregates per-PC: total HW, execution count, average HW per execution
6. Computes differential: `D_avg = avg_HW_fixed - avg_HW_random` per instruction
7. Ranks instructions by |D_avg| (per-execution key-dependent leakage)

**Key implementation details:**

- **PC snapping**: BOOM's FTQ may report PCs that are 2 bytes into a 4-byte
  instruction (VCD sampling alignment). The `snap_pc()` function uses binary
  search to map these to the containing instruction.
- **Signal filtering**: VCD contains both original signals and CellIFT variants
  (`_leak0`, `_t0`). The `pick_non_taint()` function selects the original signal
  when looking for commit valid and PC.
- **Filtering**: Results exclude `infinite_loop`, `_start`, and `unknown`
  functions to focus on AES-relevant instructions only.

**Outputs:**
- `instruction_leakage.png` — 5-panel plot (per-cycle timeline, top-30 bar
  chart, per-function comparison, difference timeline with function regions,
  instruction heatmap)
- `instruction_leakage_report.txt` — Full text report with all instructions

### 3. Legacy scripts (superseded)

- `analysis/tvla_cellift.py` — Original TVLA using boolean `leakage_counter_t0`.
  Produced max |t| = 0.06 (insufficient sensitivity).
- `analysis/tvla_detailed.py` — Intermediate version. Superseded by
  `tvla_hamming.py`.

---

## Validation: Negative Control Experiment

To verify the tool detects only **key-dependent** leakage (not artifacts), we
ran a negative control: same key, different plaintext. Since CellIFT tracks
taint from the key (not plaintext), changing only the plaintext should produce
zero differential.

### Results

| Comparison               | Traces compared                              | Max |t| | Significant windows |
|--------------------------|----------------------------------------------|---------|---------------------|
| Different keys           | `aes_100k_fixed_hw.vcd` vs `aes_100k_random_hw.vcd` | 91.00   | 14 / 2,516          |
| Same key, diff plaintext | `aes_100k_fixed_hw.vcd` vs `aes_100k_samekey_diffpt.vcd` | 0.00    | 0 / 2,516           |

The negative control shows **perfect zero** across all cycles — not just below
threshold, but literally identical traces. This is because:

1. Same key → same taint propagation through identical key schedule
2. Plaintext is not tainted → changing it has zero effect on `_leak0` signals
3. Deterministic simulation → bit-identical execution paths for same key

This validates that the tool correctly measures key-dependent information flow.

---

## Key Findings

### Per-instruction leakage ranking (top 5)

| Rank | PC         | Instruction            | Function              | D_avg (HW/exec) |
|------|------------|------------------------|-----------------------|------------------|
| 1    | 0x800011be | `lbu a6,256(a6)`       | aes128_masked_encrypt | -2.40            |
| 2    | 0x800011ce | `sb a6,0(a3)`          | aes128_masked_encrypt | -1.85            |
| 3    | 0x800011ca | `xor a6,a6,a7`         | aes128_masked_encrypt | -1.85            |
| 4    | 0x800011c6 | `lbu a7,0(a5)`         | aes128_masked_encrypt | -1.84            |
| 5    | 0x800011c2 | `lbu a6,0(a6)`         | aes128_masked_encrypt | -1.83            |

The #1 leaker is the **S-box table lookup** — a classic side-channel vulnerability
where the secret-dependent index into the S-box table causes different cache/memory
access patterns. Even in the masked implementation, CellIFT detects that the
address bits used for the lookup carry taint from the secret key.

### Leakage by function

| Function              | Total HW diff | Avg/exec diff |
|-----------------------|---------------|---------------|
| aes128_masked_encrypt | -3,558        | -1.80         |
| _start                | 0             | 0.00          |

All key-dependent leakage originates from `aes128_masked_encrypt`, specifically
the S-box lookup loop (PC range `0x8000118e`–`0x80001228`). The `mix_columns`
phase shows D_avg = 0.00 (no per-execution key dependence).

---

## How to Reproduce

### Full TVLA experiment

```bash
source /mnt/nvme1n1p1/cellift-meta-leakage/env.sh
cd /mnt/nvme1n1p1/cellift-designs/cellift-chipyard/cellift-boom

# 1. Build software (if not already built)
(cd sw/scenario_aes128_masked_key && make)
(cd sw/scenario_aes128_random_key && make)

# 2. Run fixed-key simulation
SIMLEN=100000 \
SIMSRAMELF=sw/scenario_aes128_masked_key/build/app.elf \
SIMROMELF=sw/scenario_aes128_masked_key/build/app.elf \
SIMSRAMTAINT=sw/scenario_aes128_masked_key/taint_data.txt \
TRACEFILE=traces/aes_100k_fixed_hw.vcd \
./build/run_cellift_trace_leakage_0.1/default-verilator/Vtop_tiny_soc

# 3. Run random-key simulation
SIMLEN=100000 \
SIMSRAMELF=sw/scenario_aes128_random_key/build/app.elf \
SIMROMELF=sw/scenario_aes128_random_key/build/app.elf \
SIMSRAMTAINT=sw/scenario_aes128_random_key/taint_data.txt \
TRACEFILE=traces/aes_100k_random_hw.vcd \
./build/run_cellift_trace_leakage_0.1/default-verilator/Vtop_tiny_soc

# 4. Run TVLA analysis
AES_START=348 AES_END=12950 \
python3 analysis/tvla_hamming.py \
    traces/aes_100k_fixed_hw.vcd \
    traces/aes_100k_random_hw.vcd \
    analysis/

# 5. Run instruction-level profiling
python3 analysis/instruction_leakage.py \
    traces/aes_100k_fixed_hw.vcd \
    traces/aes_100k_random_hw.vcd \
    sw/scenario_aes128_masked_key/build/app.elf.dump \
    analysis/
```

### Negative control validation

```bash
# Build and simulate same-key-different-plaintext scenario
(cd sw/scenario_aes128_same_key_diff_pt && make)

SIMLEN=100000 \
SIMSRAMELF=sw/scenario_aes128_same_key_diff_pt/build/app.elf \
SIMROMELF=sw/scenario_aes128_same_key_diff_pt/build/app.elf \
SIMSRAMTAINT=sw/scenario_aes128_same_key_diff_pt/taint_data.txt \
TRACEFILE=traces/aes_100k_samekey_diffpt.vcd \
./build/run_cellift_trace_leakage_0.1/default-verilator/Vtop_tiny_soc

# Compare fixed key trace against negative control (expect |t| = 0)
AES_START=348 AES_END=12950 \
python3 analysis/tvla_hamming.py \
    traces/aes_100k_fixed_hw.vcd \
    traces/aes_100k_samekey_diffpt.vcd \
    analysis/tvla_negative_control/
```

---

## Design Decisions and Lessons Learned

1. **Hamming weight vs boolean counter**: The original boolean counter
   (`leakage_counter_t0`) incremented by 1 whenever ANY leak signal was active.
   This produced nearly identical traces for different keys (98,817 vs 98,831)
   because both keys trigger leakage at the same cycles. Switching to Hamming
   weight (`$countones()`) captures the *amplitude* difference, yielding max
   |t| = 91 vs the previous 0.06.

2. **All 53 leak ports must be connected**: The original wrapper only connected
   14 of 53 leak ports (missing all AXI4 interface signals). The unconnected
   ports carried hundreds of additional leak bits that were silently lost.

3. **AES execution window matters**: The post-AES `infinite_loop` generates
   ~42 HW/cycle of residual taint (tainted flip-flop state persists). Including
   ~87k idle cycles inflates the TVLA to |t| = 322 but this is an artifact.
   Restricting to the AES window (cycles 348-12950) gives the true |t| = 91.

4. **Per-execution average, not total**: Ranking instructions by total leakage
   difference is misleading because execution count differences between traces
   accumulate into large totals for frequently-executed instructions. The
   per-execution average (`D_avg = avg_HW_fixed - avg_HW_random`) isolates the
   true key-dependent component.

5. **PC alignment in BOOM**: BOOM's FTQ reports committed PCs that may be
   2 bytes into a 4-byte instruction (due to how the ROB/FTQ encode PC offsets).
   The `snap_pc()` function handles this with binary search over the sorted
   instruction address list.
