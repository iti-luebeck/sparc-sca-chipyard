/*
 * Gemmini Optimized Matrix Multiplication Test (CellIFT-enabled)
 * 
 * This test performs a single DIMxDIM matrix multiplication using
 * Gemmini's RoCC instructions: C = A * B, then saves result to memory.
 * 
 * For CellIFT taint tracking:
 * - Matrices are loaded from DRAM marked as tainted in sram_taint_data.txt
 * - The CPU loads the data from DRAM (getting tainted)
 * - Data is then DMA'd to Gemmini scratchpad
 * - Taint propagates through the systolic array to results
 *
 * The test uses the Weight-Stationary (WS) dataflow where:
 * 1. Matrix B (weights) is preloaded into the systolic array
 * 2. Matrix A (inputs, tainted) flows through the array
 * 3. Results accumulate in the accumulator and are stored to memory
 *
 * Optimizations:
 * - Removed verbose printing to reduce binary size and simulation overhead
 * - Direct HTIF exit signal followed by self-jump instead of infinite loop
 * - Single pass computation without verification printing
 */

#include <stdint.h>
#include <stddef.h>
#include "gemmini.h"

// Matrices provided by matrix_N.h at compile time:
// test_matrix_A[DIM][DIM], test_matrix_B[DIM][DIM], test_expected_C[DIM][DIM]

// DRAM locations for matrix operands (marked as tainted in sram_taint_data.txt)
#define DRAM_MATRIX_A ((int8_t *)0x80002000)
#define DRAM_MATRIX_B ((int8_t *)0x80002040)
#define RESULT_ADDR   ((int32_t *)0x80010100)
#define STATUS_ADDR   ((volatile uint32_t *)0x80010000)

// Scratchpad addresses
#define SPAD_A 0
#define SPAD_B DIM
#define SPAD_C (2 * DIM)

// Minimal memcpy for matrix loading
static void memcpy_simple(void *dst, const void *src, size_t size) {
    uint8_t *d = (uint8_t *)dst;
    const uint8_t *s = (const uint8_t *)src;
    for (size_t i = 0; i < size; i++) {
        d[i] = s[i];
    }
}

// Verify result matches expected (silent - just returns status)
static int verify_result(int32_t *actual, const int32_t *expected_flat, int dim) {
    for (int i = 0; i < dim; i++) {
        for (int j = 0; j < dim; j++) {
            int32_t a = actual[i * dim + j];
            int32_t e = expected_flat[i * dim + j];
            int32_t diff = a - e;
            if (diff < 0) diff = -diff;
            if (diff > 1) return 0;  // Mismatch
        }
    }
    return 1;  // All correct
}

void main(void) {
    // Calculate matrix sizes
    int matrix_size_bytes_A = DIM * DIM * sizeof(int8_t);
    
    // Copy A to DRAM, but keep B at its original (tainted) location to preserve taint
    memcpy_simple(DRAM_MATRIX_A, test_matrix_A, matrix_size_bytes_A);
    const int8_t *matrix_B_src = (const int8_t *)test_matrix_B;
    
    // Gemmini initialization and computation
    gemmini_flush(0);
    gemmini_config_ex(WEIGHT_STATIONARY, NO_ACTIVATION, 0, 0);
    gemmini_config_ld(DIM * sizeof(int8_t));
    gemmini_config_st(DIM * sizeof(int32_t));
    
    // Load matrices to scratchpad (B source is tainted in SRAM)
    gemmini_mvin((uint64_t)DRAM_MATRIX_A, SPAD_A);
    gemmini_mvin((uint64_t)matrix_B_src, SPAD_B);
    
    // Preload weights and compute (scratchpad addresses)
    gemmini_preload(SPAD_B, SPAD_C);
    gemmini_compute_preloaded(SPAD_A, SPAD_C);
    
    // Store result to memory at RESULT_ADDR
    gemmini_mvout((uint64_t)RESULT_ADDR, SPAD_C);
    gemmini_fence();
    
    // Verify result and set status
    int status = verify_result(RESULT_ADDR, (const int32_t *)test_expected_C, DIM);
    *STATUS_ADDR = status ? 1 : 2;  // 1=pass, 2=fail
    
    // Exit via HTIF
    volatile uint64_t *tohost = (volatile uint64_t *)0x80001000;
    *tohost = 0x1;
    
    // Self-jump to prevent further execution
    asm volatile("j .");
}
