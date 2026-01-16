#!/bin/bash
# Environment setup for running vanilla (clean) Rocket simulation with VCD output
# Use this for running the same SoC without CellIFT taint tracking

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export CELLIFT_ROCKET_DIR="$SCRIPT_DIR"

# Path to the AES128 test binary
export SIMSRAMELF=$CELLIFT_ROCKET_DIR/sw/scenario_aes128_tainted_key/build/app.elf

# No taint file needed for vanilla simulation, but we need to provide something
# The vanilla build doesn't have taint loading, so this is ignored
export SIMSRAMTAINT=/dev/null

# VCD trace output file (vanilla_trace builds use VCD, not FST)
export TRACEFILE=$CELLIFT_ROCKET_DIR/traces/vanilla_aes128_sim.vcd

# Simulation length in cycles (5000 should be enough for AES-128)
export SIMLEN=5000

# Path to the vanilla simulator with trace support
export VANILLA_SIM=$CELLIFT_ROCKET_DIR/build/run_vanilla_trace_0.1/default-verilator/Vtop_tiny_soc

echo "=========================================="
echo "Vanilla Rocket Environment (VCD output)"
echo "=========================================="
echo "ELF file: $SIMSRAMELF"
echo "VCD file: $TRACEFILE"
echo "Sim length: $SIMLEN cycles"
echo "Simulator: $VANILLA_SIM"
echo ""
echo "To run the simulation:"
echo "  cd $CELLIFT_ROCKET_DIR/build/run_vanilla_trace_0.1/default-verilator"
echo "  ./Vtop_tiny_soc"
echo ""
echo "Or simply run:"
echo "  \$VANILLA_SIM"
