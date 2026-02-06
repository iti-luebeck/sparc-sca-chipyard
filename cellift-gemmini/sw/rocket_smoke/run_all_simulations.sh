#!/bin/bash
#
# Run Rocket smoke test in vanilla / CellIFT simulators
#
# Usage:
#   ./run_all_simulations.sh              # Run vanilla sim
#   ./run_all_simulations.sh --cellift    # Run CellIFT sim
#   ./run_all_simulations.sh --simlen N   # Custom cycle count
#   ./run_all_simulations.sh --trace FILE # Custom VCD path
#   ./run_all_simulations.sh --no-trace   # Use no-trace simulator
#

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ==========================================================================
# Configuration (mirrors cellift-gemmini defaults)
# ==========================================================================
CELLIFT_GEMMINI_DIR="${CELLIFT_GEMMINI_DIR:-$(realpath "$SCRIPT_DIR/../..")}" 
TOP_EXECUTABLE_NAME="${TOP_EXECUTABLE_NAME:-Vtop_tiny_soc}"

# Simulator paths (FuseSoC build structure)
VANILLA_SIM="$CELLIFT_GEMMINI_DIR/build/run_vanilla_trace_0.1/default-verilator/$TOP_EXECUTABLE_NAME"
CELLIFT_SIM="$CELLIFT_GEMMINI_DIR/build/run_cellift_trace_0.1/default-verilator/$TOP_EXECUTABLE_NAME"
VANILLA_SIM_NOTRACE="$CELLIFT_GEMMINI_DIR/build/run_vanilla_notrace_0.1/default-verilator/$TOP_EXECUTABLE_NAME"
CELLIFT_SIM_NOTRACE="$CELLIFT_GEMMINI_DIR/build/run_cellift_notrace_0.1/default-verilator/$TOP_EXECUTABLE_NAME"

# Test configuration
SIMLEN="${SIMLEN:-50000}"
TRACE_DIR="${TRACE_DIR:-$SCRIPT_DIR/traces}"
TRACEFILE_DEFAULT="$TRACE_DIR/vanilla_rocket_smoke.vcd"
LOGFILE_DEFAULT="$TRACE_DIR/vanilla_rocket_smoke.log"

# CellIFT taint init (optional)
SIMSRAMTAINT="${SIMSRAMTAINT:-$SCRIPT_DIR/sram_taint_data.txt}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Parse args
SIM_TYPE="vanilla"
TRACEFILE=""
LOGFILE=""
NO_TRACE=0

while [[ $# -gt 0 ]]; do
  case $1 in
    --cellift) SIM_TYPE="cellift"; shift ;;
    --vanilla) SIM_TYPE="vanilla"; shift ;;
    --simlen) SIMLEN=$2; shift 2 ;;
    --trace) TRACEFILE=$2; shift 2 ;;
    --no-trace) NO_TRACE=1; shift ;;
    --log) LOGFILE=$2; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--cellift|--vanilla] [--simlen N] [--trace FILE] [--no-trace] [--log FILE]"
      exit 0 ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
 done

mkdir -p "$TRACE_DIR"

# Pick simulator
SIM_BIN="$VANILLA_SIM"
if [ "$SIM_TYPE" = "cellift" ]; then
  SIM_BIN="$CELLIFT_SIM"
fi

if [ "$NO_TRACE" -eq 1 ]; then
  if [ "$SIM_TYPE" = "cellift" ]; then
    SIM_BIN="$CELLIFT_SIM_NOTRACE"
  else
    SIM_BIN="$VANILLA_SIM_NOTRACE"
  fi
fi

ELF_FILE="$SCRIPT_DIR/build/rocket_smoke.elf"

if [ ! -f "$ELF_FILE" ]; then
  echo -e "${YELLOW}Building rocket_smoke...${NC}"
  (cd "$SCRIPT_DIR" && make)
fi

if [ ! -f "$SIM_BIN" ]; then
  echo -e "${RED}Simulator not found:${NC} $SIM_BIN"
  exit 1
fi

if [ "$NO_TRACE" -eq 0 ] && [ -z "$TRACEFILE" ]; then
  if [ "$SIM_TYPE" = "cellift" ]; then
    TRACEFILE="$TRACE_DIR/cellift_rocket_smoke.vcd"
    LOGFILE="${LOGFILE:-$TRACE_DIR/cellift_rocket_smoke.log}"
  else
    TRACEFILE="$TRACEFILE_DEFAULT"
    LOGFILE="${LOGFILE:-$LOGFILE_DEFAULT}"
  fi
elif [ "$NO_TRACE" -eq 1 ]; then
  # For no-trace runs, set default log if not specified
  if [ -z "$LOGFILE" ]; then
    if [ "$SIM_TYPE" = "cellift" ]; then
      LOGFILE="$TRACE_DIR/cellift_rocket_smoke_notrace.log"
    else
      LOGFILE="$TRACE_DIR/vanilla_rocket_smoke_notrace.log"
    fi
  fi
fi

# Run simulation
mkdir -p "$(dirname "$LOGFILE")"
if [ "$NO_TRACE" -eq 0 ]; then
  SIMSRAMELF="$ELF_FILE" \
  TRACEFILE="$TRACEFILE" \
  SIMLEN="$SIMLEN" \
  SIMSRAMTAINT="$SIMSRAMTAINT" \
  "$SIM_BIN" > "$LOGFILE" 2>&1
else
  SIMSRAMELF="$ELF_FILE" \
  SIMLEN="$SIMLEN" \
  SIMSRAMTAINT="$SIMSRAMTAINT" \
  "$SIM_BIN" > "$LOGFILE" 2>&1
fi

if [ "$NO_TRACE" -eq 1 ]; then
  echo -e "${GREEN}OK${NC} (no-trace run)"
else
  if [ -f "$TRACEFILE" ]; then
    echo -e "${GREEN}OK${NC} Trace: $TRACEFILE"
  else
    echo -e "${GREEN}OK${NC} (no trace generated)"
  fi
fi
echo "Log: $LOGFILE"
