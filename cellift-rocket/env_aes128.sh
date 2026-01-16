#!/bin/bash
# Environment configuration for AES-128 tainted key scenario - Rocket Core
# Source this file before running CellIFT simulation

# Path to this cellift-rocket directory
CELLIFT_ROCKET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Trace output file
export TRACEFILE=$CELLIFT_ROCKET_DIR/traces/aes128_sim.fst

# Binary to load
export SIMSRAMELF=$CELLIFT_ROCKET_DIR/sw/scenario_aes128_tainted_key/build/app.elf

# Taint configuration - marks the AES key as tainted (16 bytes at 0x80001000)
export SIMSRAMTAINT=$CELLIFT_ROCKET_DIR/taint_data/scenario_aes128_tainted_key/taint_data.txt

# Simulation length (cycles)
# Rocket is more complex than Ibex - may need more cycles
# AES-128 should complete within 5000 cycles on Rocket
export SIMLEN=5000

echo "=== AES-128 Tainted Key Scenario (Rocket Core) ==="
echo "Binary:     $SIMSRAMELF"
echo "Taint data: $SIMSRAMTAINT"
echo "Trace file: $TRACEFILE"
echo "Sim length: $SIMLEN cycles"
echo ""
echo "To run CellIFT simulation:"
echo "  make run_cellift_trace_fst   # With waveform tracing (slow)"
echo "  make run_cellift_notrace     # Without tracing (fast)"
echo ""
echo "To view waveforms after trace run:"
echo "  gtkwave traces/aes128_sim.fst"
