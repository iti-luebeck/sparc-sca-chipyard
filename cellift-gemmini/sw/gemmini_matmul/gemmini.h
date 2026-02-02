// Minimal Gemmini header for CellIFT testing
// Provides basic RoCC instruction macros for matrix operations

#ifndef GEMMINI_H
#define GEMMINI_H

#include <stdint.h>
#include <stdbool.h>
#include "gemmini_params.h"
#include "xcustom.h"

// Gemmini instruction opcodes (funct7 field)
#define k_CONFIG 0
#define k_MVIN2 1
#define k_MVIN 2
#define k_MVOUT 3
#define k_COMPUTE_PRELOADED 4
#define k_COMPUTE_ACCUMULATE 5
#define k_PRELOAD 6
#define k_FLUSH 7
#define k_LOOP_WS 8
#define k_LOOP_WS_CONFIG_BOUNDS 9
#define k_LOOP_WS_CONFIG_ADDRS_AB 10
#define k_LOOP_WS_CONFIG_ADDRS_DC 11
#define k_LOOP_WS_CONFIG_STRIDES_AB 12
#define k_LOOP_WS_CONFIG_STRIDES_DC 13
#define k_MVIN3 14

// Configuration sub-commands
#define CONFIG_EX 0
#define CONFIG_LD 1
#define CONFIG_ST 2

// Constants
#define GARBAGE_ADDR ((uint32_t)(-1))
#define OUTPUT_STATIONARY 0
#define WEIGHT_STATIONARY 1
#define NO_ACTIVATION 0
#define RELU 1
#define RELU6 2

// Helper macro for RoCC instructions
#define ROCC_INSTRUCTION_RS1_RS2(x, rs1, rs2, funct) \
  ROCC_INSTRUCTION_0_R_R(x, rs1, rs2, funct)

// acc_scale_t conversion
static inline acc_scale_t_bits acc_scale_t_to_acc_scale_t_bits(acc_scale_t x) {
    union {
        acc_scale_t_bits b;
        acc_scale_t f;
    } un;
    un.f = x;
    return un.b;
}

//==========================================================================
// Gemmini RoCC Instructions
//==========================================================================

// Flush: wait for all pending operations to complete
#define gemmini_flush(skip) \
  ROCC_INSTRUCTION_RS1_RS2(XCUSTOM_ACC, skip, 0, k_FLUSH)

// Fence: memory barrier
#define gemmini_fence() asm volatile("fence")

// Configure execution dataflow
// dataflow: 0=output-stationary, 1=weight-stationary
// sys_act: activation function (0=none, 1=relu, 2=relu6)
// sys_shift: right shift for output
#define gemmini_config_ex(dataflow, sys_act, sys_shift, relu6_shift) \
  { \
    ROCC_INSTRUCTION_RS1_RS2(XCUSTOM_ACC, \
        ((uint64_t)acc_scale_t_to_acc_scale_t_bits((acc_scale_t)ACC_SCALE_IDENTITY) << 32) | \
        ((uint64_t)(1) << 16) | ((sys_act) << 3) | ((dataflow) << 2) | CONFIG_EX, \
        ((uint64_t)(1) << 48) | ((uint64_t)(relu6_shift) << 32) | (sys_shift), \
        k_CONFIG); \
  }

// Configure load stride (for mvin)
#define gemmini_config_ld(stride) \
  ROCC_INSTRUCTION_RS1_RS2(XCUSTOM_ACC, \
      ((uint64_t)(MVIN_SCALE_IDENTITY) << 32) | ((uint64_t)(DIM) << 16) | (1 << 8) | CONFIG_LD, \
      stride, k_CONFIG)

// Configure store stride (for mvout)  
#define gemmini_config_st(stride) \
  ROCC_INSTRUCTION_RS1_RS2(XCUSTOM_ACC, \
      ((uint64_t)acc_scale_t_to_acc_scale_t_bits((acc_scale_t)ACC_SCALE_IDENTITY) << 32) | CONFIG_ST, \
      stride, k_CONFIG)

// Move data from DRAM to scratchpad
// dram_addr: source address in DRAM
// spad_addr: destination address in scratchpad
// cols, rows: dimensions of data to move
#define gemmini_extended_mvin(dram_addr, spad_addr, cols, rows) \
  ROCC_INSTRUCTION_RS1_RS2(XCUSTOM_ACC, dram_addr, \
      ((uint64_t)(rows) << (ADDR_LEN + 16)) | ((uint64_t)(cols) << ADDR_LEN) | (spad_addr), \
      k_MVIN)

// Move one DIMxDIM block from DRAM to scratchpad
#define gemmini_mvin(dram_addr, spad_addr) \
  gemmini_extended_mvin(dram_addr, spad_addr, DIM, DIM)

// Move data from scratchpad/accumulator to DRAM
#define gemmini_extended_mvout(dram_addr, spad_addr, cols, rows) \
  ROCC_INSTRUCTION_RS1_RS2(XCUSTOM_ACC, dram_addr, \
      ((uint64_t)(rows) << (ADDR_LEN + 16)) | ((uint64_t)(cols) << ADDR_LEN) | (uint64_t)(spad_addr), \
      k_MVOUT)

// Move one DIMxDIM block from scratchpad to DRAM
#define gemmini_mvout(dram_addr, spad_addr) \
  gemmini_extended_mvout(dram_addr, spad_addr, DIM, DIM)

// Preload B/D matrix into systolic array
// BD: scratchpad address of B or D matrix
// C: accumulator address for result
#define gemmini_extended_preload(BD, C, BD_cols, BD_rows, C_cols, C_rows) \
  ROCC_INSTRUCTION_RS1_RS2(XCUSTOM_ACC, \
      ((uint64_t)(BD_rows) << (ADDR_LEN + 16)) | ((uint64_t)(BD_cols) << ADDR_LEN) | (uint64_t)(BD), \
      ((uint64_t)(C_rows) << (ADDR_LEN + 16)) | ((uint64_t)(C_cols) << ADDR_LEN) | (uint64_t)(C), \
      k_PRELOAD)

#define gemmini_preload(BD, C) \
  gemmini_extended_preload(BD, C, DIM, DIM, DIM, DIM)

#define gemmini_preload_zeros(C) \
  gemmini_preload(GARBAGE_ADDR, C)

// Compute with preloaded B matrix
// A: scratchpad address of A matrix
// BD: scratchpad address of D (bias) matrix, or garbage address
#define gemmini_extended_compute_preloaded(A, BD, A_cols, A_rows, BD_cols, BD_rows) \
  ROCC_INSTRUCTION_RS1_RS2(XCUSTOM_ACC, \
      ((uint64_t)(A_rows) << (ADDR_LEN + 16)) | ((uint64_t)(A_cols) << ADDR_LEN) | (uint64_t)(A), \
      ((uint64_t)(BD_rows) << (ADDR_LEN + 16)) | ((uint64_t)(BD_cols) << ADDR_LEN) | (uint64_t)(BD), \
      k_COMPUTE_PRELOADED)

#define gemmini_compute_preloaded(A, BD) \
  gemmini_extended_compute_preloaded(A, BD, DIM, DIM, DIM, DIM)

// Compute with accumulated result  
#define gemmini_extended_compute_accumulated(A, BD, A_cols, A_rows, BD_cols, BD_rows) \
  ROCC_INSTRUCTION_RS1_RS2(XCUSTOM_ACC, \
      ((uint64_t)(A_rows) << (ADDR_LEN + 16)) | ((uint64_t)(A_cols) << ADDR_LEN) | (uint64_t)(A), \
      ((uint64_t)(BD_rows) << (ADDR_LEN + 16)) | ((uint64_t)(BD_cols) << ADDR_LEN) | (uint64_t)(BD), \
      k_COMPUTE_ACCUMULATE)

#define gemmini_compute_accumulated(A, BD) \
  gemmini_extended_compute_accumulated(A, BD, DIM, DIM, DIM, DIM)

//==========================================================================
// Helper functions
//==========================================================================

// Read cycle counter
static inline uint64_t read_cycles() {
    uint64_t cycles;
    asm volatile ("rdcycle %0" : "=r" (cycles));
    return cycles;
}

#endif // GEMMINI_H
