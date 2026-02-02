# Gemmini Matrix Multiplication Multi-Scenario

This directory contains the multi-scenario testing framework for Gemmini matrix multiplication, similar to the AES-128 multi-scenario example.

## Overview

The framework allows you to:
1. **Generate** multiple matrix multiplication test cases with different inputs
2. **Build** separate binaries for each test case
3. **Run** all simulations in parallel using both vanilla and CellIFT simulators

## Quick Start

### 1. Generate Matrix Pairs and Build Binaries

```bash
# Generate 10 4x4 matrix pairs and build binaries
python3 generate_scenario.py -n 10

# Or with custom matrix dimension
python3 generate_scenario.py -n 50 --dim 8

# Or with different value ranges
python3 generate_scenario.py -n 20 --min-val 1 --max-val 127
```

This creates:
- `matrix_0.h` through `matrix_9.h` (or matrix_0.h through matrix_49.h for 50 tests)
- `build/matmul_0.elf` through `build/matmul_9.elf` (compiled binaries)
- `run_all_simulations.sh` (automated simulation runner)

### 2. Run All Simulations

```bash
# Run all vanilla simulations (default)
./run_all_simulations.sh

# Run all CellIFT simulations
./run_all_simulations.sh --cellift

# Run specific tests
./run_all_simulations.sh --range 0 9    # Tests 0-9
./run_all_simulations.sh --single 5     # Only test 5

# Customize simulation
./run_all_simulations.sh --simlen 300000      # 300k cycles instead of 200k
./run_all_simulations.sh --jobs 16            # Run 16 simulations in parallel
```

### 3. View Results

VCD traces are generated in `traces/`:
- `vanilla_matmul_N.vcd` - Vanilla simulator traces
- `cellift_matmul_N.vcd` - CellIFT traces (with taint information)

## Directory Structure

```
scenario_matmul_multi/
├── generate_scenario.py       # Generator script
├── Makefile                   # Build system
├── main.c                     # Matrix multiplication test code
├── gemmini.h                  # Gemmini RoCC instruction wrappers
├── startup.S                  # Assembly entry point
├── link.ld                    # Linker script
├── README.md                  # This file
├── matrix_*.h                 # Generated matrix headers (one per test case)
├── run_all_simulations.sh     # Generated simulation runner script
├── build/                     # Build output directory
│   ├── matmul_0.elf          # Compiled binary for test 0
│   ├── matmul_0.elf.dump     # Disassembly
│   └── ...
└── traces/                    # VCD trace files
    ├── vanilla_matmul_0.vcd
    ├── cellift_matmul_0.vcd
    └── ...
```

## How It Works

### Matrix Generation

Each matrix pair is generated pseudo-randomly with a seeded RNG:
- Test i uses seed 2*i for matrix A and seed 2*i+1 for matrix B
- This ensures reproducibility while varying test inputs
- Expected result C = A*B is computed in Python

### Binary Generation

For each test i:
- `matrix_i.h` is compiled with `main.c` using `-include matrix_i.h`
- The header file provides the test matrices at compile time
- One ELF binary is created per test case
- All binaries are identical except for data sections

### Simulation Execution

The `run_all_simulations.sh` script:
1. Checks that binaries exist (builds if needed)
2. Spawns parallel simulation jobs (limited by --jobs or CPU count)
3. Collects results and reports success/failure
4. Generates trace files in `traces/`

## Matrix Format

Each `matrix_N.h` header defines:

```c
#define MATRIX_INDEX N
#define DIM 4

static const int8_t test_matrix_A[DIM][DIM] = { ... };
static const int8_t test_matrix_B[DIM][DIM] = { ... };
static const int32_t test_expected_C[DIM][DIM] = { ... };
```

- **Matrix A**: Input matrix (considered tainted in CellIFT)
- **Matrix B**: Weight/coefficient matrix
- **Matrix C**: Expected result (A × B with proper scaling)

## Build Configuration

The Makefile automatically:
- Detects DIM from the first generated matrix header
- Auto-detects number of tests from generated matrix_*.h files
- Can be overridden with `make NUM_TESTS=N` or `make DIM=8`

### Toolchain

Uses the RISC-V toolchain from Chipyard:
```
/mnt/nvme1n1p1/chipyard-1.8.1/.conda-env/riscv-tools/bin/riscv64-unknown-elf-
```

Adjust `TOOLCHAIN_PREFIX` in Makefile if using a different installation.

## Gemmini RoCC Instructions

The `gemmini.h` header provides wrappers for:

- `gemmini_config_ex()` - Configure dataflow (Weight-Stationary)
- `gemmini_config_ld()` - Configure load stride
- `gemmini_config_st()` - Configure store stride
- `gemmini_mvin()` - Move data from DRAM to scratchpad
- `gemmini_mvout()` - Move data from accumulator to DRAM
- `gemmini_preload()` - Preload matrix B into systolic array
- `gemmini_compute_preloaded()` - Compute A × B
- `gemmini_fence()` - Wait for completion

## Customization

### Changing Matrix Dimensions

```bash
python3 generate_scenario.py -n 50 --dim 8
```

This generates 50 test cases with 8×8 matrices.

### Custom Value Ranges

```bash
python3 generate_scenario.py -n 100 --min-val 0 --max-val 63
```

Useful for testing with specific bit-widths or value distributions.

### Adding More Tests Later

```bash
python3 generate_scenario.py -n 200  # Generate 200 tests
make NUM_TESTS=200                   # Build all 200
./run_all_simulations.sh --range 100 199  # Run tests 100-199
```

## Debugging Individual Tests

```bash
# Build a specific test
make single TEST_INDEX=5

# Run just that test
cd build/run_vanilla_trace_0.1/default-verilator
SIMSRAMELF=$PWD/../../matmul_5.elf SIMLEN=200000 TRACEFILE=matmul_5.vcd ./Vtop_tiny_soc
```

View the disassembly:
```bash
cat build/matmul_5.elf.dump | less
```

## Performance Analysis

Cycle counts are printed during execution:
```
Matmul completed in 5234 cycles
```

Use this to analyze Gemmini performance with different:
- Matrix dimensions
- Dataflow configurations
- System parameters

## CellIFT Taint Tracking

With `--cellift` mode:
- Matrix A is automatically considered tainted
- Taint propagates through the scratchpad, VSM, and systolic array
- Results in `cellift_matmul_N.vcd` with `_t0` suffix signals for taint bits

This allows you to verify that:
1. Taint reaches the accelerator
2. Data flows through the expected paths
3. Results contain correct taint information

## Troubleshooting

### Build Fails

Ensure you have the Chipyard toolchain installed:
```bash
ls /mnt/nvme1n1p1/chipyard-1.8.1/.conda-env/riscv-tools/bin/
```

### Simulator Not Found

Build the simulators:
```bash
cd /mnt/nvme1n1p1/cellift-designs/cellift-chipyard/cellift-gemmini
make build/run_vanilla_trace_0.1/default-verilator/Vtop_tiny_soc
make build/run_cellift_trace_0.1/default-verilator/Vtop_tiny_soc
```

### Traces Not Generated

Check that `traces/` directory exists and is writable:
```bash
mkdir -p traces
chmod 755 traces
```

## References

- Original single-case Gemmini test: `sw/gemmini_matmul/`
- AES multi-scenario example: `sw/scenario_aes128_multi/`
- CellIFT framework: Documentation in cellift-designs/
