# Publication Summary (Refined Root-Cause)

## Headline Metrics

- Unmasked first HW leak cycle: 337
- Masked first HW leak cycle: 295
- Unmasked top-interval coverage (signal+instruction): 12/12
- Masked top-interval coverage (signal+instruction): 12/12

- Unmasked LC max leakage metric: 0 (between-group max Δ, Welch n/a)
- Unmasked HW max leakage metric: 108 (between-group max Δ, Welch n/a)
- Unmasked HD max leakage metric: 113 (between-group max Δ, Welch n/a)
- Masked LC max leakage metric: 0 (between-group max Δ, Welch n/a)
- Masked HW max leakage metric: 110 (between-group max Δ, Welch n/a)
- Masked HD max leakage metric: 116 (between-group max Δ, Welch n/a)

## Refined Interval Table

Full machine-readable table: publication_summary_refined.csv

| Group | Counter | Interval | Peak cycle | Peak |t| | Signal | Instruction | Source |
|---|---|---:|---:|---:|---|---|---|
| unmasked | hamming_weight_counter_t0 | 617-725 | 635 | n/a | ram[388]_t0 | sraiw a5,t4,0x2 | aes128_encrypt (aes128.c:94) |
| unmasked | hamming_weight_counter_t0 | 1282-2932 | 1332 | n/a | ram[1030]_t0 | sraiw a5,t4,0x2 | aes128_encrypt (aes128.c:94) |
| unmasked | hamming_weight_counter_t0 | 838-917 | 866 | n/a | ram[1030]_t0 | lbu t3,0(a4) | aes128_encrypt (aes128.c:99) |
| unmasked | hamming_weight_counter_t0 | 337-338 | 337 | n/a | subsystem_l2_wrapper_auto_coherent_jbar_in_c_bits_data_t0 | addi a5,a5,1 | aes128_encrypt (aes128.c:69) |
| unmasked | hamming_distance_counter_t0 | 1282-1291 | 1283 | n/a | ram[1030]_t0 | lbu a1,0(a1) | aes128_encrypt (aes128.c:90) |
| unmasked | hamming_distance_counter_t0 | 2188-2197 | 2189 | n/a | ram[1030]_t0 | lbu a1,0(a1) | aes128_encrypt (aes128.c:90) |
| unmasked | hamming_distance_counter_t0 | 667-676 | 668 | n/a | ram[388]_t0 | lbu a1,0(a1) | aes128_encrypt (aes128.c:90) |
| unmasked | hamming_distance_counter_t0 | 717-726 | 718 | n/a | ram[390]_t0 | lbu a1,0(a1) | aes128_encrypt (aes128.c:90) |
| unmasked | hamming_distance_counter_t0 | 1332-1341 | 1333 | n/a | ram[1030]_t0 | sraiw a5,t4,0x2 | aes128_encrypt (aes128.c:94) |
| unmasked | hamming_distance_counter_t0 | 617-626 | 618 | n/a | ram_data[0]_t0 | lbu a1,0(a1) | aes128_encrypt (aes128.c:90) |
| unmasked | hamming_distance_counter_t0 | 2924-2933 | 2925 | n/a | ram[1030]_t0 | addi a5,a5,1 | aes128_encrypt (aes128.c:98) |
| unmasked | hamming_distance_counter_t0 | 2874-2883 | 2875 | n/a | ram[1030]_t0 | addiw t4,t4,1 | aes128_encrypt (aes128.c:74) |
| masked | hamming_weight_counter_t0 | 1803-2470 | 2462 | n/a | ram[1078]_t0 | addiw t4,t4,1 | aes128_encrypt (aes128.c:74) |
| masked | hamming_weight_counter_t0 | 1332-1464 | 1364 | n/a | ram[1084]_t0 | addiw t4,t4,1 | aes128_encrypt (aes128.c:74) |
| masked | hamming_weight_counter_t0 | 857-1116 | 1042 | n/a | ram[390]_t0 | lbu a5,256(a5) | aes128_encrypt (aes128.c:94) |
| masked | hamming_weight_counter_t0 | 295-296 | 295 | n/a | core_hw_counter_t0 | lbu t6,0(t5) | mask_loop (main.S:24) |
| masked | hamming_distance_counter_t0 | 857-866 | 858 | n/a | regout_r_t0 | lbu a1,0(a1) | aes128_encrypt (aes128.c:90) |
| masked | hamming_distance_counter_t0 | 907-927 | 908 | n/a | ram[390]_t0 | lbu a1,0(a1) | aes128_encrypt (aes128.c:90) |
| masked | hamming_distance_counter_t0 | 1332-1341 | 1333 | n/a | ram[1084]_t0 | beqz a5,80000650 <aes128_encrypt+0x5e8> | aes128_encrypt (aes128.c:80) |
| masked | hamming_distance_counter_t0 | 2462-2471 | 2463 | n/a | ram[1078]_t0 | addiw t4,t4,1 | aes128_encrypt (aes128.c:74) |
| masked | hamming_distance_counter_t0 | 984-993 | 985 | n/a | logic__leak0 | sb a1,-1(a5) | aes128_encrypt (aes128.c:90) |
| masked | hamming_distance_counter_t0 | 1108-1117 | 1109 | n/a | logic__leak0 | addi t5,t5,4 | aes128_encrypt (aes128.c:74) |
| masked | hamming_distance_counter_t0 | 1364-1373 | 1365 | n/a | ram[1084]_t0 | lbu a1,-16(a5) | aes128_encrypt (aes128.c:99) |
| masked | hamming_distance_counter_t0 | 1456-1465 | 1457 | n/a | ram[1084]_t0 | lbu a1,0(a1) | aes128_encrypt (aes128.c:90) |

## Masking Candidates

Signals with highest key-dependent data divergence (vanilla VCD XOR). Primary targets for hardware masking.

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

## Leakage Narrative

Automatic classification of RTL leakage sources by signal type and cryptographic data-flow role (AES).

### Unmasked Design

*No dominant leakage pattern identified (insufficient attribution data).*

**Masking-boundary signals**: none detected (leakage is confined to datapath/memory, not bus-level).

**Remediation**: Apply appropriate masking at the identified leakage point.

### Masked Design

*No dominant leakage pattern identified (insufficient attribution data).*

**Masking-boundary signals**: none detected (leakage is confined to datapath/memory, not bus-level).

**Remediation**: Apply appropriate masking at the identified leakage point.
