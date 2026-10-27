# Automated Root-Cause Analysis Report

## Run Configuration

- workload: aes
- seed: 42
- simlen: 3000
- threshold_t: 4.5
- interval_top_k: 8

## Unmasked Attribution Summary

- first_hw_leak_cycle: 337
- intervals analyzed: 12
- intervals with both signal+instruction: 12 (100.00%)

| Counter | Basis | Regime | Interval | Peak cycle | Peak mag | Peak d | Peak t | Signal | Top signals (HW diff) | Instruction | Source |
|---|---|---|---|---:|---:|---:|---:|---|---|---|---|
| hamming_weight_counter_t0 | episode | det_leak | 617-725 | 635 | 108.0 | 1000.0 | n/a | ram[388]_t0 | ram[388]_t0(64), ram[389]_t0(64), ram[388]_t0(64) | sraiw a5,t4,0x2 | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_unmasked_key1/aes128.c:94 |
| hamming_weight_counter_t0 | episode | det_leak | 1282-2932 | 1332 | 107.0 | 1000.0 | n/a | ram[1030]_t0 | ram[1030]_t0(63), ram[1031]_t0(63), ram[1154]_t0(63) | sraiw a5,t4,0x2 | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_unmasked_key1/aes128.c:94 |
| hamming_weight_counter_t0 | episode | det_leak | 838-917 | 866 | 97.0 | 1000.0 | n/a | ram[1030]_t0 | ram[1030]_t0(63), ram[1031]_t0(63), ram[390]_t0(63) | lbu t3,0(a4) | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_unmasked_key1/aes128.c:99 |
| hamming_weight_counter_t0 | episode | det_leak | 337-338 | 337 | 38.0 | 1000.0 | n/a | subsystem_l2_wrapper_auto_coherent_jbar_in_c_bits_data_t0 | subsystem_l2_wrapper_auto_coherent_jbar_in_c_bits_data_t0(63), ram_data[0]_t0... | addi a5,a5,1 | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_unmasked_key1/aes128.c:69 |
| hamming_distance_counter_t0 | episode | det_leak | 1282-1291 | 1283 | 113.0 | 1000.0 | n/a | ram[1030]_t0 | ram[1030]_t0(63), ram[1031]_t0(63), ram[1154]_t0(63) | lbu a1,0(a1) | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_unmasked_key1/aes128.c:90 |
| hamming_distance_counter_t0 | episode | det_leak | 2188-2197 | 2189 | 113.0 | 1000.0 | n/a | ram[1030]_t0 | ram[1030]_t0(63), ram[1031]_t0(63), ram[1154]_t0(63) | lbu a1,0(a1) | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_unmasked_key1/aes128.c:90 |
| hamming_distance_counter_t0 | episode | det_leak | 667-676 | 668 | 110.0 | 1000.0 | n/a | ram[388]_t0 | ram[388]_t0(63), ram[389]_t0(63), ram[390]_t0(63) | lbu a1,0(a1) | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_unmasked_key1/aes128.c:90 |
| hamming_distance_counter_t0 | episode | det_leak | 717-726 | 718 | 108.0 | 1000.0 | n/a | ram[390]_t0 | ram[390]_t0(63), ram[391]_t0(63), ram[52]_t0(63) | lbu a1,0(a1) | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_unmasked_key1/aes128.c:90 |
| hamming_distance_counter_t0 | episode | det_leak | 1332-1341 | 1333 | 108.0 | 1000.0 | n/a | ram[1030]_t0 | ram[1030]_t0(63), ram[1031]_t0(63), ram[1154]_t0(63) | sraiw a5,t4,0x2 | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_unmasked_key1/aes128.c:94 |
| hamming_distance_counter_t0 | episode | det_leak | 617-626 | 618 | 106.0 | 1000.0 | n/a | ram_data[0]_t0 | ram_data[0]_t0(63), c_io_deq_bits_data_leak0(63), subsystem_l2_wrapper_auto_c... | lbu a1,0(a1) | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_unmasked_key1/aes128.c:90 |
| hamming_distance_counter_t0 | episode | det_leak | 2924-2933 | 2925 | 104.0 | 1000.0 | n/a | ram[1030]_t0 | ram[1030]_t0(63), ram[1031]_t0(63), ram[1154]_t0(63) | addi a5,a5,1 | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_unmasked_key1/aes128.c:98 (discriminator 2) |
| hamming_distance_counter_t0 | episode | det_leak | 2874-2883 | 2875 | 102.0 | 1000.0 | n/a | ram[1030]_t0 | ram[1030]_t0(63), ram[1031]_t0(63), ram[1154]_t0(63) | addiw t4,t4,1 | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_unmasked_key1/aes128.c:74 (discriminator 1) |

## Masked Attribution Summary

- first_hw_leak_cycle: 295
- intervals analyzed: 12
- intervals with both signal+instruction: 12 (100.00%)

| Counter | Basis | Regime | Interval | Peak cycle | Peak mag | Peak d | Peak t | Signal | Top signals (HW diff) | Instruction | Source |
|---|---|---|---|---:|---:|---:|---:|---|---|---|---|
| hamming_weight_counter_t0 | episode | det_leak | 1803-2470 | 2462 | 110.0 | 1000.0 | n/a | ram[1078]_t0 | ram[1078]_t0(63), ram[1079]_t0(63), ram[1084]_t0(63) | addiw t4,t4,1 | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_masked_key/aes128.c:74 (discriminator 1) |
| hamming_weight_counter_t0 | episode | det_leak | 1332-1464 | 1364 | 55.0 | 1000.0 | n/a | ram[1084]_t0 | ram[1084]_t0(63), ram[1085]_t0(63), ram[390]_t0(63) | addiw t4,t4,1 | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_masked_key/aes128.c:74 (discriminator 1) |
| hamming_weight_counter_t0 | episode | det_leak | 857-1116 | 1042 | 52.0 | 1000.0 | n/a | ram[390]_t0 | ram[390]_t0(63), ram[391]_t0(63), ram[54]_t0(63) | lbu a5,256(a5) | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_masked_key/aes128.c:94 |
| hamming_weight_counter_t0 | episode | det_leak | 295-296 | 295 | 38.0 | 1000.0 | n/a | core_hw_counter_t0 | core_hw_counter_t0(3), core_hd_counter_t0(2) | lbu t6,0(t5) | mask_loop /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_masked_key/main.S:24 |
| hamming_distance_counter_t0 | episode | det_leak | 857-866 | 858 | 116.0 | 1000.0 | n/a | regout_r_t0 | regout_r_t0(55), s3_bypass_data_REG_1_leak0(40), bankedStore_io_sourceC_dat_d... | lbu a1,0(a1) | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_masked_key/aes128.c:90 |
| hamming_distance_counter_t0 | episode | det_leak | 907-927 | 908 | 112.0 | 1000.0 | n/a | ram[390]_t0 | ram[390]_t0(64), ram[391]_t0(64), ram[390]_t0(64) | lbu a1,0(a1) | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_masked_key/aes128.c:90 |
| hamming_distance_counter_t0 | episode | det_leak | 1332-1341 | 1333 | 110.0 | 1000.0 | n/a | ram[1084]_t0 | ram[1084]_t0(63), ram[1085]_t0(63), ram[390]_t0(63) | beqz a5,80000650 <aes128_encrypt+0x5e8> | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_masked_key/aes128.c:80 |
| hamming_distance_counter_t0 | episode | det_leak | 2462-2471 | 2463 | 110.0 | 1000.0 | n/a | ram[1078]_t0 | ram[1078]_t0(63), ram[1079]_t0(63), ram[1084]_t0(63) | addiw t4,t4,1 | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_masked_key/aes128.c:74 (discriminator 1) |
| hamming_distance_counter_t0 | episode | det_leak | 984-993 | 985 | 108.0 | 1000.0 | n/a | logic__leak0 | logic__leak0(64), shift_logic_leak0(64), shout_leak0(64) | sb a1,-1(a5) | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_masked_key/aes128.c:90 |
| hamming_distance_counter_t0 | episode | det_leak | 1108-1117 | 1109 | 108.0 | 1000.0 | n/a | logic__leak0 | logic__leak0(64), shift_logic_leak0(64), shout_leak0(64) | addi t5,t5,4 | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_masked_key/aes128.c:74 (discriminator 2) |
| hamming_distance_counter_t0 | episode | det_leak | 1364-1373 | 1365 | 106.0 | 1000.0 | n/a | ram[1084]_t0 | ram[1084]_t0(63), ram[1085]_t0(63), ram[390]_t0(63) | lbu a1,-16(a5) | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_masked_key/aes128.c:99 |
| hamming_distance_counter_t0 | episode | det_leak | 1456-1465 | 1457 | 106.0 | 1000.0 | n/a | ram[1084]_t0 | ram[1084]_t0(63), ram[1085]_t0(63), ram[390]_t0(63) | lbu a1,0(a1) | aes128_encrypt /workspace/designs/chipyard/cellift-rocket/sw/scenario_aes128_masked_key/aes128.c:90 |

## Masking Candidates

Signals with the highest key-dependent data divergence across leaky intervals (from vanilla VCD XOR comparison). These are the primary targets for hardware masking.

| Signal | Width | Cumul HW diff | Leaky intervals |
|---|---:|---:|---:|
| icData_data | 128 | 1005 | 17 |
| mem[512] | 64 | 792 | 24 |
| wmask_i | 64 | 768 | 12 |
| core_io_dmem_s1_data_data | 64 | 760 | 22 |
| minmax | 64 | 760 | 22 |
| out | 64 | 760 | 22 |
| dataArb_io_in_0_bits_wdata | 64 | 760 | 22 |
| dcacheArb_io_mem_s1_data_data | 64 | 760 | 22 |
| dcache_io_cpu_resp_bits_store_data | 64 | 760 | 22 |
| adder_out | 64 | 744 | 22 |
| mem[513] | 64 | 720 | 24 |
| in2_inv | 64 | 607 | 10 |
| mem_rdata_o | 64 | 605 | 19 |
| axi4_mem_0_bits_r_bits_data | 64 | 605 | 19 |
| rdata_o | 64 | 605 | 19 |
| bankedStore_io_sinkD_dat_data | 64 | 601 | 18 |
| ram_data[0] | 64 | 601 | 18 |
| in1_xor_in2 | 64 | 580 | 10 |
| cc_banks_2_RW0_rdata | 64 | 557 | 19 |
| regout_r_2 | 64 | 529 | 18 |

## Efficacy Evidence

- Leakage regions are auto-extracted from TVLA outputs using two definitions (episode and strict Welch).
- Region-level root-cause attribution is automatic and links hardware signals with software instructions.
- Coverage ratios quantify how often intervals have complete signal+instruction attribution.
