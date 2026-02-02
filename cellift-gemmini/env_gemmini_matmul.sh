#!/bin/bash
# Environment configuration for Gemmini Matrix Multiplication scenario
# Source this file before running CellIFT simulation

# Path to this cellift-gemmini directory
CELLIFT_GEMMINI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Simulation mode: "cellift" (default) or "vanilla"
export SIMMODE=${SIMMODE:-cellift}

# Trace output file
export TRACEFILE=$CELLIFT_GEMMINI_DIR/traces/${SIMMODE}_gemmini_matmul.vcd

# Binary to load - Gemmini matrix multiplication test (C = A * B)
export SIMSRAMELF=$CELLIFT_GEMMINI_DIR/sw/gemmini_matmul/gemmini_matmul.riscv

# Taint configuration - marks input matrix A as tainted (16 bytes at 0x80002000)
# Matrix A is a 4x4 int8 matrix used as input to the matrix multiplication
export SIMSRAMTAINT=$CELLIFT_GEMMINI_DIR/sw/gemmini_matmul/sram_taint_data.txt

# Simulation length (cycles)
# Gemmini accelerator operations need time to complete
# 10000 cycles should be sufficient for a 4x4 matmul
export SIMLEN=10000

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
echo "To run simulation:"
echo "  if [ \"$SIMMODE\" = \"vanilla\" ]; then"
echo "    make run_vanilla_trace       # With waveform tracing (slow)"
echo "    make run_vanilla_notrace     # Without tracing (fast)"
echo "  else"
echo "    make run_cellift_trace       # With waveform tracing (slow)"
echo "    make run_cellift_notrace     # Without tracing (fast)"
echo "  fi"
echo ""
echo "Or run directly (after sourcing this script):"
echo "  if [ \"$SIMMODE\" = \"vanilla\" ]; then"
echo "    cd build/run_vanilla_trace_0.1/default-verilator && ./Vtop_tiny_soc"
echo "  else"
echo "    cd build/run_cellift_trace_0.1/default-verilator && ./Vtop_tiny_soc"
echo "  fi"
echo ""
echo "To view waveforms after trace run:"
echo "  gtkwave \$TRACEFILE"
echo ""
echo "To analyze taint propagation:"
echo "  python3 scripts/analyze_taint_propagation.py \$TRACEFILE"
