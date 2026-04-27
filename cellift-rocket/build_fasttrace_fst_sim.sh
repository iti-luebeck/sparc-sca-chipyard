#!/usr/bin/env bash
#
# build_fasttrace_fst_sim.sh - Build the standalone run_cellift_fasttrace_fst simulator for Rocket.
# Used for long Kyber attribution runs where VCD output would exceed ~4GB.
#
# Usage:
#   ./build_fasttrace_fst_sim.sh [--force]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FT_DIR="${SCRIPT_DIR}/build/run_cellift_fasttrace_fst_0.1/default-verilator"
FT_BIN="${FT_DIR}/Vtop_tiny_soc"
FORCE_REBUILD=0

if [[ "${1:-}" == "--force" ]]; then
    FORCE_REBUILD=1
elif [[ $# -gt 0 ]]; then
    echo "ERROR: unknown option: $1"
    echo "Usage: $0 [--force]"
    exit 1
fi

needs_rebuild=1
if [[ -x "${FT_BIN}" && "${FORCE_REBUILD}" -eq 0 ]]; then
    needs_rebuild=0
    while IFS= read -r src; do
        if [[ "$src" -nt "${FT_BIN}" ]]; then
            needs_rebuild=1
            echo "Rebuild needed: ${src} is newer than ${FT_BIN}"
            break
        fi
    done < <(find "${SCRIPT_DIR}/dv" "${SCRIPT_DIR}/src" -type f \( -name '*.cc' -o -name '*.cpp' -o -name '*.h' -o -name '*.sv' \) | sort)
fi

if [[ "${needs_rebuild}" -eq 0 ]]; then
    echo "fasttrace_fst simulator up to date: ${FT_BIN}"
    exit 0
fi

if [[ "${FORCE_REBUILD}" -eq 1 ]]; then
    echo "Force rebuild requested for standalone fasttrace_fst simulator."
fi
echo "Building standalone fasttrace_fst simulator via FuseSoC..."
source /mnt/nvme1n1p1/cellift-meta-leakage/env.sh >/dev/null 2>&1

rm -f "${SCRIPT_DIR}/fusesoc.conf"
fusesoc library add run_cellift_fasttrace_fst "${SCRIPT_DIR}"
fusesoc \
    --cores-root="${SCRIPT_DIR}" \
    run --build run_cellift_fasttrace_fst

if [[ ! -x "${FT_BIN}" ]]; then
    echo "ERROR: FuseSoC build did not produce ${FT_BIN}"
    exit 1
fi

echo "fasttrace_fst simulator built: ${FT_BIN}"
