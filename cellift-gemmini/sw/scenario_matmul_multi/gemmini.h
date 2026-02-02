/*
 * Gemmini RoCC Instruction Wrappers
 * 
 * This header provides the core Gemmini RoCC instruction definitions
 * needed for matrix multiplication tests.
 */

#ifndef GEMMINI_H
#define GEMMINI_H

#include <stdint.h>

// Matrix dimension - should be set by compile-time -include matrix_N.h
// #define DIM 4

// Data element type for Gemmini (8-bit)
typedef int8_t elem_t;

// RoCC custom instruction opcode for Gemmini
#define ROCC_OPCODE 0x7b

// Gemmini instruction function codes
#define CONFIG_EX      0
#define CONFIG_LD      0
#define CONFIG_ST      0
#define MVIN           2
#define MVOUT          3
#define COMPUTE_PRELOADED 4
#define PRELOAD        6
#define FLUSH          7

// Dataflow configurations
#define WEIGHT_STATIONARY 0
#define OUTPUT_STATIONARY 1

// Activation functions
#define NO_ACTIVATION 0
#define RELU          1

// Garbage address (for unused outputs)
#define GARBAGE_ADDR 0

// Read the mcycle CSR for profiling
static inline uint64_t read_cycles(void) {
    uint64_t cycle;
    asm volatile("csrr %0, mcycle" : "=r"(cycle));
    return cycle;
}

/*
 * RoCC Instruction Encoding
 * 
 * RISC-V RoCC custom instruction format:
 *   opcode[6:0] = 0x7b (custom-3)
 *   rd[11:7]    = destination register (unused for most Gemmini instructions)
 *   funct7[31:25] = 0 (reserved)
 *   rs2[24:20]  = second operand register
 *   rs1[19:15]  = first operand register
 *   
 * The Gemmini controller reads the full rs1 and rs2 64-bit values and decodes
 * the instruction based on funct within the custom-3 opcode.
 */

// Inline assembly helper for RoCC custom-3 instructions
#define GEMMINI_ROCC(funct, rs1, rs2) \
    ({ \
        register uint64_t rd asm("x1"); \
        asm volatile ( \
            ".word (0x7b | ((" #funct ") << 25) | ((x" #rs2 ") << 20) | ((x" #rs1 ") << 15))" \
            : "=r" (rd) \
            : "r" (rs1), "r" (rs2) \
        ); \
    })

// Alternative: use inline assembly with constraint-based encoding
static inline void gemmini_rocc(int funct, uint64_t rs1, uint64_t rs2) {
    asm volatile(
        ".word %[inst]"
        :
        : [inst] "i" (ROCC_OPCODE | ((funct & 0x7f) << 25)),
          "r" (rs1), "r" (rs2)
        : "memory"
    );
}

/*
 * CONFIG_EX - Configure execution (dataflow, activation, shift amounts)
 * 
 * Parameters in rs1:
 *   [15:0]  = config_ex_t struct:
 *             [0]     = funct (CONFIG_EX = 0)
 *             [1]     = 0
 *             [2]     = dataflow (0=WS, 1=OS)
 *             [8:3]   = reserved
 *             [15:9]  = relu6_shift
 *   [31:16] = 1 (indicates CONFIG_EX)
 *   [47:32] = systolic shift amount
 *   [63:48] = reserved
 * 
 * rs2: unused
 */
static inline void gemmini_config_ex(
    int dataflow,           // WEIGHT_STATIONARY or OUTPUT_STATIONARY
    int activation,         // NO_ACTIVATION or RELU
    int sys_shift,          // Systolic array shift (usually 0)
    int relu6_shift         // ReLU6 shift amount (usually 0)
) {
    uint64_t rs1 = (1UL << 16) |              // Indicates CONFIG_EX
                   ((dataflow & 1) << 2) |    // Dataflow bit
                   ((activation & 0x7f) << 9); // Activation shift
    if (sys_shift > 0) {
        rs1 |= ((sys_shift & 0xffff) << 32);
    }
    
    asm volatile(
        ".word (0x7b | ((0x0) << 25))" 
        :
        : "r" (rs1), "r" (0UL)
    );
}

/*
 * CONFIG_LD - Configure load (stride for reading from DRAM)
 * 
 * rs1:
 *   [15:0]  = stride (in bytes)
 *   [31:16] = DIM (number of rows/cols)
 *   [47:32] = 0 (indicates CONFIG_LD)
 *   
 * rs2: unused
 */
static inline void gemmini_config_ld(uint32_t stride) {
    uint64_t rs1 = (1UL << 8) |              // Indicates CONFIG_LD
                   ((DIM & 0xffff) << 16) |  // DIM in upper bits
                   (stride & 0xff);           // Stride in lower bits
    
    asm volatile(
        ".word (0x7b | ((0x0) << 25))"
        :
        : "r" (rs1), "r" (0UL)
    );
}

/*
 * CONFIG_ST - Configure store (stride for writing to DRAM)
 * 
 * rs1:
 *   [15:0]  = config_st_t (usually just 2 for CONFIG_ST opcode)
 *   [63:0]  = stride (in bytes)
 * 
 * rs2: unused
 */
static inline void gemmini_config_st(uint32_t stride) {
    uint64_t rs1 = 2;  // CONFIG_ST indicator
    
    // Note: actual stride is in rs2 for CONFIG_ST
    asm volatile(
        ".word (0x7b | ((0x0) << 25))"
        :
        : "r" (rs1), "r" (stride & 0xffffffff)
    );
}

/*
 * MVIN - Move data from DRAM to scratchpad
 * 
 * rs1: DRAM address
 * rs2:
 *   [15:0]  = scratchpad address (in rows)
 *   [31:16] = number of columns
 *   [47:32] = number of rows
 *   [63:48] = reserved
 */
static inline void gemmini_mvin(uint64_t dram_addr, uint32_t spad_addr) {
    uint64_t rs2 = (((uint64_t)DIM) << 48) |  // rows
                   (((uint64_t)DIM) << 32) |  // cols
                   (spad_addr & 0xffff);       // spad address
    
    asm volatile(
        ".word (0x7b | ((2) << 25))"
        :
        : "r" (dram_addr), "r" (rs2)
    );
}

/*
 * MVOUT - Move data from accumulator to DRAM
 * 
 * rs1: DRAM address
 * rs2:
 *   [15:0]  = accumulator address (high bit set means accumulator)
 *   [31:16] = number of columns
 *   [47:32] = number of rows
 */
static inline void gemmini_mvout(uint64_t dram_addr, uint32_t acc_addr) {
    uint64_t rs2 = (((uint64_t)DIM) << 48) |  // rows
                   (((uint64_t)DIM) << 32) |  // cols
                   (acc_addr & 0xffff);        // acc address
    
    asm volatile(
        ".word (0x7b | ((3) << 25))"
        :
        : "r" (dram_addr), "r" (rs2)
    );
}

/*
 * PRELOAD - Preload matrix B into systolic array
 * 
 * rs1: Scratchpad address of B matrix (BD_spec)
 * rs2: Accumulator address for output (C_spec)
 */
static inline void gemmini_preload(uint32_t b_spad_addr, uint32_t c_acc_addr) {
    uint64_t rs1 = (((uint64_t)DIM) << 48) |
                   (((uint64_t)DIM) << 32) |
                   (b_spad_addr & 0xffff);
    uint64_t rs2 = (((uint64_t)DIM) << 48) |
                   (((uint64_t)DIM) << 32) |
                   (c_acc_addr & 0xffff);
    
    asm volatile(
        ".word (0x7b | ((6) << 25))"
        :
        : "r" (rs1), "r" (rs2)
    );
}

/*
 * COMPUTE_PRELOADED - Compute with preloaded B
 * 
 * rs1: Scratchpad address of A matrix (A_spec)
 * rs2: Unused (garbage spec)
 */
static inline void gemmini_compute_preloaded(uint32_t a_spad_addr, uint32_t unused) {
    uint64_t rs1 = (((uint64_t)DIM) << 48) |
                   (((uint64_t)DIM) << 32) |
                   (a_spad_addr & 0xffff);
    
    asm volatile(
        ".word (0x7b | ((4) << 25))"
        :
        : "r" (rs1), "r" (0UL)
    );
}

/*
 * FENCE - Wait for all pending Gemmini operations to complete
 */
static inline void gemmini_fence(void) {
    asm volatile(
        ".word (0x7b | ((7) << 25))"
        :
        : "r" (0UL), "r" (0UL)
    );
}

/*
 * FLUSH - Flush scratchpad/accumulator (optional, mainly for debugging)
 */
static inline void gemmini_flush(int dummy) {
    asm volatile(
        ".word (0x7b | ((7) << 25))"
        :
        : "r" (0UL), "r" (0UL)
    );
}

#endif /* GEMMINI_H */
