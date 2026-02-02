/*
 * Gemmini Matrix Multiplication Test (CellIFT-enabled)
 * 
 * This test performs a DIMxDIM matrix multiplication using
 * Gemmini's RoCC instructions: C = A * B
 * 
 * For CellIFT taint tracking:
 * - Matrices are loaded from DRAM at 0x80002000 (matrix A)
 * - This address is marked as tainted in sram_taint_data.txt
 * - The CPU loads the data from DRAM (getting tainted)
 * - Data is then DMA'd to Gemmini scratchpad
 * - Taint propagates through the systolic array to results
 *
 * The test uses the Weight-Stationary (WS) dataflow where:
 * 1. Matrix B (weights) is preloaded into the systolic array
 * 2. Matrix A (inputs, tainted) flows through the array
 * 3. Results accumulate in the accumulator
 */

#include <stdint.h>
#include <stddef.h>
#include "gemmini.h"

// Matrices are provided by matrix_N.h (included at compile time)
// These define: test_matrix_A[DIM][DIM], test_matrix_B[DIM][DIM], test_expected_C[DIM][DIM]

// DRAM locations where matrices will be copied for CellIFT taint tracking
// Address 0x80001000 is marked as TAINTED in sram_taint_data.txt
#define DRAM_MATRIX_A ((int8_t *)0x80001000)
#define DRAM_MATRIX_B ((int8_t *)0x80001400)
#define DRAM_EXPECTED_C ((int32_t *)0x80002000)

// Result matrix (in main DRAM)
static int32_t result_C[16][16] __attribute__((aligned(64)));

// Scratchpad addresses (same as in gemmini_matmul single test)
#define SPAD_A 0
#define SPAD_B (1 * 16)  // After A's max size (16x16 = 256 bytes)
#define ACC_C ((1 << 31) | 0)

// Copy data from source to destination
static void memcpy_simple(void *dst, const void *src, size_t size) {
    uint8_t *d = (uint8_t *)dst;
    const uint8_t *s = (const uint8_t *)src;
    for (size_t i = 0; i < size; i++) {
        d[i] = s[i];
    }
}

// Simple output via tohost
static void print_char(char c) {
    volatile uint64_t *tohost = (volatile uint64_t *)0x80001000;
    *tohost = (0x0101UL << 48) | c;
}

static void print_str(const char *s) {
    while (*s) {
        print_char(*s++);
    }
}

static void print_hex(uint64_t val) {
    const char hex[] = "0123456789ABCDEF";
    print_str("0x");
    for (int i = 60; i >= 0; i -= 4) {
        print_char(hex[(val >> i) & 0xF]);
    }
}

static void print_int(int32_t val) {
    if (val < 0) {
        print_char('-');
        val = -val;
    }
    char buf[12];
    int i = 0;
    if (val == 0) {
        print_char('0');
        return;
    }
    do {
        buf[i++] = '0' + (val % 10);
        val /= 10;
    } while (val > 0);
    while (--i >= 0) {
        print_char(buf[i]);
    }
}

static void print_newline(void) {
    print_char('\n');
}

// Verify result matches expected within tolerance
static int verify_result(void) {
    int errors = 0;
    // Use expected values from DRAM that was copied in main()
    const int32_t *expected_C = DRAM_EXPECTED_C;
    
    for (int i = 0; i < DIM; i++) {
        for (int j = 0; j < DIM; j++) {
            int32_t actual = result_C[i][j];
            int32_t expected = expected_C[i * DIM + j];  // Linear indexing from DRAM
            // Allow some tolerance for fixed-point rounding
            int32_t diff = actual - expected;
            if (diff < 0) diff = -diff;
            if (diff > 1) {  // Tolerance of 1
                if (errors == 0) {
                    print_str("First mismatch at [");
                    print_int(i);
                    print_str("][");
                    print_int(j);
                    print_str("]: got ");
                    print_int(actual);
                    print_str(", expected ");
                    print_int(expected);
                    print_newline();
                }
                errors++;
            }
        }
    }
    return errors;
}

// Profiling counter
static uint64_t read_mcycle(void) {
    uint64_t cycle;
    asm volatile("csrr %0, mcycle" : "=r"(cycle));
    return cycle;
}

void main(void) {
    print_str("=== Gemmini Matrix Multiply (");
    print_int(DIM);
    print_str("x");
    print_int(DIM);
    print_str(") Test ");
    print_int(MATRIX_INDEX);
    print_str(" ===\n");
    
    // For CellIFT taint tracking:
    // Copy test matrices to DRAM locations marked as tainted
    // This allows taint to propagate from DRAM through CPU loads to the accelerator
    
    print_str("Copying matrices to DRAM for taint propagation...\n");
    
    // Calculate matrix sizes in bytes
    int matrix_size_bytes_A = DIM * DIM * sizeof(int8_t);
    int matrix_size_bytes_B = DIM * DIM * sizeof(int8_t);
    int matrix_size_bytes_C = DIM * DIM * sizeof(int32_t);
    
    // Copy matrices to DRAM locations (marked as tainted in sram_taint_data.txt)
    memcpy_simple(DRAM_MATRIX_A, test_matrix_A, matrix_size_bytes_A);
    memcpy_simple(DRAM_MATRIX_B, test_matrix_B, matrix_size_bytes_B);
    memcpy_simple(DRAM_EXPECTED_C, test_expected_C, matrix_size_bytes_C);
    
    // Flush any pending operations
    gemmini_flush(0);
    
    // Configure for weight-stationary dataflow
    gemmini_config_ex(WEIGHT_STATIONARY, NO_ACTIVATION, 0, 0);
    
    // Configure load stride (row stride in bytes)
    gemmini_config_ld(DIM * sizeof(int8_t));
    
    // Configure store stride
    gemmini_config_st(DIM * sizeof(int32_t));
    
    // Record start cycle
    uint64_t start = read_mcycle();
    
    // Step 1: Move matrix A from DRAM (tainted) to scratchpad
    // This loads from the DRAM location marked as tainted, propagating taint
    gemmini_mvin((uint64_t)DRAM_MATRIX_A, SPAD_A);
    
    // Step 2: Move matrix B from DRAM to scratchpad  
    gemmini_mvin((uint64_t)DRAM_MATRIX_B, SPAD_B);
    
    // Step 3: Preload B (weights) into systolic array
    // Output will go to accumulator at ACC_C
    gemmini_preload(SPAD_B, ACC_C);
    
    // Step 4: Compute A * B
    // Feed A (tainted) through the array, result accumulates in ACC_C
    gemmini_compute_preloaded(SPAD_A, GARBAGE_ADDR);
    
    // Step 5: Move result from accumulator to result_C
    gemmini_mvout((uint64_t)result_C, ACC_C);
    
    // Fence to ensure all operations complete
    gemmini_fence();
    
    // Record end cycle
    uint64_t end = read_mcycle();
    
    print_str("Matmul completed in ");
    print_int((int32_t)(end - start));
    print_str(" cycles\n");
    
    // Verify result
    print_str("Verifying result...\n");
    int errors = verify_result();
    if (errors == 0) {
        print_str("SUCCESS: Matrix multiplication correct!\n");
    } else {
        print_str("FAIL: ");
        print_int(errors);
        print_str(" mismatches found\n");
    }
    
    print_str("=== Test Complete ===\n");
    
    // Infinite loop to signal end of test
    while (1) {
        asm volatile("nop");
    }
}
