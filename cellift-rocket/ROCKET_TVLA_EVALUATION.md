# Rocket CellIFT TVLA Evaluation

Target: Rocket RV64G core (`top_tiny_soc`, Chipyard `MySmallVMRocketConfig`)
Scope: TVLA decision + root-cause signal analysis + instruction mapping

## 1) Environment

```bash
source /mnt/nvme1n1p1/cellift-meta-leakage/env.sh
cd /mnt/nvme1n1p1/cellift-designs/cellift-chipyard/cellift-rocket
```

## 2) Rocket vs Ibex/Proteus Differences

| Property | Ibex | Rocket |
|---|---|---|
| Top binary | `Vibex_tiny_soc` | `Vtop_tiny_soc` |
| ISA | RV32IMC | RV64G (64-bit) |
| Compiler flags | `-march=rv32imc -mabi=ilp32` | `-march=rv64g -mabi=lp64 -mcmodel=medany` |
| Toolchain | `chipyard-1.11.0` | `chipyard-1.8.1` |
| Memory env vars | `SIMROMELF SIMSRAMELF SIMROMTAINT SIMSRAMTAINT` | `SIMSRAMELF SIMSRAMTAINT` only |
| Leakage counters | Inserted by CellIFT in generated RTL | Added to `src/top_tiny_soc_taints.sv` from memory-bus taint signals |
| Counter coverage | All tainted bits in core hierarchy | Memory-bus taint signals (req, we, addr, be, wdata, rdata) |

The Rocket CellIFT instrumentation (`generated/out/cellift.sv`) did not include the
cumulative leakage counter insertion pass. The counters are therefore implemented in
`src/top_tiny_soc_taints.sv` using the 170 taint bits visible at the `rocket_mem_top`
memory bus boundary. This captures key-dependent leakage as key data flows through
the load/store interface during AES key expansion and encryption rounds.

## 3) Build the CSV Logger (one-time)

```bash
bash build_csvlog_sim.sh
# Expected: build/run_cellift_csvlog_0.1/default-verilator/Vtop_tiny_soc
```

## 4) Core Entry Point

```bash
./run_full_evaluation.sh --jobs 8 --plot
```

Main options:
- `--n-unmasked N`   traces/group for unmasked AES (default `20`)
- `--n-masked N`     traces/group for masked AES (default `100`)
- `--simlen N`       simulation cycles (default `50000`)
- `--seed N`         matched-pairs random seed (default `42`)
- `--threshold T`    Welch threshold (default `4.5`)
- `--window-len N`   cycles analyzed after first leakage cycle (default `5`)
- `--interval-top-k N` top annotated intervals per counter (default `3`)
- `--results DIR`    output root directory
- `--workload NAME`  scenario-generation profile (default `aes`)
- `--skip-build`     skip FuseSoC rebuild check
- `--skip-preflight` skip environment validation
- `--skip-gen`       skip scenario generation
- `--skip-compile`   skip scenario compilation

## 5) What the Pipeline Runs

1. Preflight checks (`run_eval_preflight.sh`)
2. Scenario generation (`gen_scenarios.py`) — 4 × N matched-pair scenarios
3. Scenario compilation (`compile_scenarios.sh`) — `make` in each `sw/` dir
4. Multi-trace TVLA (`run_multi_trace_tvla.sh` + `multi_tvla_driver.py`)
5. Region discovery — pass 1 (`cycle_leakage_quantifier.py`)
6. Root-cause signal analysis (`run_signal_correlation.sh` + `leakage_signals.py`)
7. Instruction mapping (`pc_at_leakage.py`) — requires PC signal verification (see §9)
8. Per-cycle quantification + annotated plots — pass 2 (`cycle_leakage_quantifier.py`)
9. Run manifest (`results/run_manifest.json`)
10. Consolidated evidence report (`generate_root_cause_report.py` + `generate_publication_summary.py`)

## 6) Output Layout

All outputs written under `results/` (or `--results`).

- `results/unmasked/`
  - `group_a_*.csv`, `group_b_*.csv`
  - `welch_summary.txt`
  - `signals_heatmap.png`, `signals_timeline.png`
  - `leakage_regions.json`, `leakage_regions.csv`
  - `leakage_*_interval_*_annotated.png`
- `results/masked/`  — same structure
- `results/run_manifest.json`
- `results/root_cause_report.md`
- `results/root_cause_report.json`
- `results/publication_summary.md`

Key fields from `welch_summary.txt`:
- `first_leaky_cycle`, `leaky_cycle_count`, `max_t`

## 7) AES Scenarios

Reference template scenarios (in `sw/` and `taint_data/`):
- `scenario_aes128_unmasked_key1` — FIPS-197 Appendix B key, plaintext = `aes_plaintext`
- `scenario_aes128_unmasked_key2` — NIST counter key (`00..0f`), same plaintext label
- `scenario_aes128_masked_key`    — key1 + `aes_state_mask` (XORed into plaintext)
- `scenario_aes128_masked_key2`   — key2 + `aes_state_mask`

Taint source: AES key at `0x80001000` (16 bytes), defined in `taint_data/*/taint_data.txt`.

Generated matched-pair scenarios (created on demand):
- `sw/multi_aes_unmasked_a_*`, `sw/multi_aes_unmasked_b_*`
- `sw/multi_aes_masked_a_*`,   `sw/multi_aes_masked_b_*`

Labels patched by `gen_scenarios.py`:
- `aes_plaintext` (16 bytes) — randomized per trace
- `aes_state_mask` (16 bytes, masked only) — randomized per trace
- `aes_key` — **never patched** (fixed per group)

## 8) Quick Single-Pair TVLA

```bash
# Build first if needed
bash build_csvlog_sim.sh

bash run_tvla.sh 50000 results/smoke_tvla \
  scenario_aes128_unmasked_key1 scenario_aes128_unmasked_key2 --plot
```

Expected artifacts:
- `results/smoke_tvla/group_a.csv`, `group_b.csv`
- `results/smoke_tvla/tvla_*.png` (if `--plot`)

## 9) Known Issues and Open Items

### PC Signal Names (instruction mapping)
`pc_at_leakage.py` contains Ibex pipeline signal name placeholders
(`pc_if`, `pc_id`, `pc_wb`, `instr_rdata_id`, `instr_valid_id`).
These must be updated for Rocket before instruction mapping works.

To find the correct names:
```bash
SIMSRAMELF=sw/scenario_aes128_unmasked_key1/build/app.elf \
SIMLEN=100 TRACEFILE=/tmp/rocket_pc.vcd \
build/run_vanilla_trace_0.1/default-verilator/Vtop_tiny_soc
grep -i " pc" /tmp/rocket_pc.vcd | head -20
grep -i "inst" /tmp/rocket_pc.vcd | head -10
```
Then update the signal name constants at the top of `pc_at_leakage.py`.

### VCD Timing Formula
`leakage_signals.py` and `pc_at_leakage.py` use `5 * (7 + cycle)` to map CSV
cycle indices to VCD timestamps. Verify this matches Rocket's testbench.h tick model:
```bash
head -100 /tmp/rocket_pc.vcd   # check $timescale and first posedge timestamp
```

### Counter Coverage
Rocket leakage counters measure taint activity on the memory bus (170 bits) rather
than all internal tainted bits. Key-dependent leakage still shows clearly on the
memory bus during key expansion and AES round computation.

### SIMLEN Tuning
Default SIMLEN=50000. Check when AES finishes by inspecting when counters plateau:
```bash
tail -20 results/smoke_tvla/group_a.csv
```
Reduce SIMLEN to ~10% above the plateau cycle to save simulation time.

## 10) Core Scripts

- `run_full_evaluation.sh`     — master orchestrator
- `run_eval_preflight.sh`      — environment validation
- `build_csvlog_sim.sh`        — FuseSoC build wrapper
- `gen_scenarios.py`           — matched-pair scenario generation
- `compile_scenarios.sh`       — batch scenario compilation
- `run_tvla.sh`                — single-pair TVLA smoke check
- `run_multi_trace_tvla.sh`    — multi-trace TVLA runner
- `multi_tvla_driver.py`       — Welch t-test analysis
- `tvla_analysis.py`           — single-pair leakage analysis
- `run_signal_correlation.sh`  — 4-step root-cause pipeline
- `leakage_signals.py`         — signal-level leakage ranking
- `pc_at_leakage.py`           — instruction mapping (see §9)
- `cycle_leakage_quantifier.py` — per-cycle metrics + regime detection
- `generate_root_cause_report.py` — consolidated evidence report
- `generate_publication_summary.py` — publication-style summary
- `hw_model_test.py`           — HW-model DPA correlation (needs N=256)
- `run_cellift_sim.sh`         — standalone CellIFT VCD wrapper
- `run_vanilla_sim.sh`         — standalone vanilla VCD wrapper
