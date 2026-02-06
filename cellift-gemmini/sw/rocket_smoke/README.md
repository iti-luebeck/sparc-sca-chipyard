# Rocket Smoke Test (bare-metal)

This is a minimal RV64G bare-metal program to validate Rocket CPU execution.

## How It Works

The test has two parts:

**Part 1: CPU Validation**
1. Performs simple arithmetic: `c = a * b + 0x9`
2. Stores results at `0x80004000` for waveform inspection
3. Stores CPU test signature at `0x80004020` (`0xDEADBEEF` = pass, `0xBADC0FFE` = fail)

**Part 2: Gemmini RoCC Validation**
1. Issues `CONFIG_EX` RoCC instruction to Gemmini (configures dataflow)
2. Issues `FENCE` RoCC instruction to ensure completion
3. Stores Gemmini marker at `0x80004028` (`0xDEADF00D` = RoCC executed)
4. Signals success via MMIO write to `0x60000000` (visible in `mmio_aw_addr_o`)

## Build

```bash
make
```

Artifacts:
- `build/rocket_smoke.elf`
- `build/rocket_smoke.elf.dump`

## Run

```bash
./run_all_simulations.sh --vanilla --simlen 5000 --no-trace
```

Or with VCD trace:
```bash
./run_all_simulations.sh --vanilla --simlen 5000
```

## Verification

Since HTIF output isn't supported in this testbench, check success by:

1. **MMIO signal**: Look for `mmio_aw_addr_o == 0x60000000` and `mmio_aw_valid_o == 1` in waveforms
2. **Memory signatures**:
   - `0x80004020`: `0xDEADBEEF` = CPU test passed, `0xBADC0FFE` = CPU test failed
   - `0x80004028`: `0xDEADF00D` = Gemmini RoCC instructions executed
3. **Memory contents** at `0x80004000-0x80004028`:
   - `[0x00]` = 0x1234 (a)
   - `[0x08]` = 0x5678 (b)
   - `[0x10]` = 0x6260FA9 (c = computed result)
   - `[0x18]` = 0x6260FA9 (expected result)
   - `[0x20]` = 0xDEADBEEF (CPU pass signature)
   - `[0x28]` = 0xDEADF00D (Gemmini RoCC executed marker)

