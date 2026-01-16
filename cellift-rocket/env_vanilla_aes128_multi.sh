#!/bin/bash
# Environment setup for AES-128 Multi-Vector scenario (vanilla simulation)
# Runs multiple AES encryptions with configurable test vectors

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export CELLIFT_ROCKET_DIR="$SCRIPT_DIR"

# Path to the AES-128 multi-vector binary
export SIMSRAMELF=$CELLIFT_ROCKET_DIR/sw/scenario_aes128_multi/build/app.elf

# No taint needed for vanilla simulation
export SIMSRAMTAINT=/dev/null

# VCD trace output file
export TRACEFILE=$CELLIFT_ROCKET_DIR/traces/vanilla_aes128_multi.vcd

# Simulation length in cycles
# 4 test vectors * ~1000 cycles each = ~4000, add margin
export SIMLEN=100000

# Path to the vanilla simulator with trace support
export VANILLA_SIM=$CELLIFT_ROCKET_DIR/build/run_vanilla_trace_0.1/default-verilator/Vtop_tiny_soc

echo "=========================================="
echo "AES-128 Multi-Vector Scenario (Vanilla)"
echo "=========================================="
echo "ELF file: $SIMSRAMELF"
echo "VCD file: $TRACEFILE"
echo "Sim length: $SIMLEN cycles"
echo "Simulator: $VANILLA_SIM"
echo ""
echo "Test vectors defined in: sw/scenario_aes128_multi/test_vectors.h"
echo "Configuration in: sw/scenario_aes128_multi/aes_config.h"
echo ""
echo "To build the software:"
echo "  cd $CELLIFT_ROCKET_DIR/sw/scenario_aes128_multi && make"
echo ""
echo "To run the simulation:"
echo "  \$VANILLA_SIM"
