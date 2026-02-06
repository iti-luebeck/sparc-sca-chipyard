#!/bin/bash
# Environment configuration for Gemmini Matrix Multiplication scenario
# Source this file before running CellIFT simulation

# First, source the cellift-meta environment
CELLIFT_META_DIR="/mnt/nvme1n1p1/cellift-meta"
if [ -f "$CELLIFT_META_DIR/env.sh" ]; then
    source "$CELLIFT_META_DIR/env.sh"
else
    echo "ERROR: Could not find cellift-meta/env.sh at $CELLIFT_META_DIR/env.sh"
    return 1
fi

# Path to this cellift-gemmini directory
CELLIFT_GEMMINI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Simulation mode: "cellift" (default) or "vanilla"
export SIMMODE=${SIMMODE:-cellift}

# Trace output file
export TRACEFILE=$CELLIFT_GEMMINI_DIR/traces/${SIMMODE}_gemmini_test_ws.vcd

# Binary to load - Optimized Gemmini weight-stationary matrix multiplication test
# Uses test_ws.riscv - minimal initialization, direct matmul execution
export SIMSRAMELF=$CELLIFT_GEMMINI_DIR/sw/gemmini_matmul/test_ws.riscv

# Taint configuration - marks input matrix A as tainted (16 bytes at 0x80002000)
# Matrix A is a 4x4 int32 matrix used as input to the matrix multiplication
export SIMSRAMTAINT=$CELLIFT_GEMMINI_DIR/sw/gemmini_matmul/sram_taint_data.txt

# Simulation length (cycles)
# Gemmini accelerator operations need time to complete
# 100000 cycles for comprehensive test with output
export SIMLEN=1000

echo "=== Gemmini Matrix Multiplication Scenario (${SIMMODE}) ==="
echo "Binary:     $SIMSRAMELF"
echo "Taint data: $SIMSRAMTAINT"
echo "Trace file: $TRACEFILE"
echo "Sim length: $SIMLEN cycles"
echo ""
echo "Tainted data:"
echo "  Matrix A (input): 0x80002000 - 16 bytes tainted"
echo "  Matrix B (weights): 0x80002040 - not tainted"
echo "  Matrix C (output): 0x80003000 - result"
echo ""
echo "To use this environment:"
echo "  source /mnt/nvme1n1p1/cellift-designs/cellift-chipyard/cellift-gemmini/env_gemmini_matmul.sh"
echo ""
echo "Then run simulation from cellift-gemmini directory:"
echo "  cd $CELLIFT_GEMMINI_DIR"
echo "  make run_vanilla_trace       # Without CellIFT taint tracking"
echo "  make run_cellift_trace       # With CellIFT taint tracking"
echo ""
echo "After simulation completes, check output:"
echo "  tail -50 logs/simulation.log  # Last 50 lines of simulation"
echo ""
