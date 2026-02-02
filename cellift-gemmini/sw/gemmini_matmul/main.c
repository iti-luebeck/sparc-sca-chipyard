/*
 * Gemmini Matrix Multiplication Test for CellIFT
 * 
 * This test performs a simple DIMxDIM matrix multiplication using
 * Gemmini's RoCC instructions:
 *   C = A * B
 * 
 * The test uses the Weight-Stationary (WS) dataflow where:
 * 1. Matrix B (weights) is preloaded into the systolic array
 * 2. Matrix A (inputs) flows through the array
 * 3. Results accumulate in the accumulator and are moved out
 * 
 * For CellIFT taint tracking, we taint the input matrix A to observe
 * how tainted data flows through the accelerator.
 */

#include <stdint.h>
#include <stddef.h>
#include "gemmini.h"

// Use volatile to prevent compiler optimizations
#define VOLATILE_ACCESS(x) (*(volatile typeof(x)*)&(x))

// Matrices aligned to scratchpad requirements
// DIM = 4 for our minimal configuration
static elem_t A[DIM][DIM] __attribute__((aligned(64))) = {
    {1, 2, 3, 4},
    {5, 6, 7, 8},
    {9, 10, 11, 12},
    {13, 14, 15, 16}
};

static elem_t B[DIM][DIM] __attribute__((aligned(64))) = {
    {1, 0, 0, 0},
    {0, 1, 0, 0},
    {0, 0, 1, 0},
    {0, 0, 0, 1}
};

// Output matrix (result of A * B)
static elem_t C[DIM][DIM] __attribute__((aligned(64)));

// Expected result: A * I = A
static elem_t expected[DIM][DIM] = {
    {1, 2, 3, 4},
    {5, 6, 7, 8},
    {9, 10, 11, 12},
    {13, 14, 15, 16}
};

// Simple print function for bare metal
static void print_char(char c) {
    // Write to HTIF tohost for simulation output
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

// Print a DIMxDIM matrix
static void print_matrix(const char *name, elem_t mat[DIM][DIM]) {
    print_str(name);
    print_str(":\n");
    for (int i = 0; i < DIM; i++) {
        print_str("  [");
        for (int j = 0; j < DIM; j++) {
            print_int(mat[i][j]);
            if (j < DIM - 1) print_str(", ");
        }
        print_str("]\n");
    }
}

// Verify result matches expected
static int verify_result(void) {
    for (int i = 0; i < DIM; i++) {
        for (int j = 0; j < DIM; j++) {
            if (C[i][j] != expected[i][j]) {
                print_str("MISMATCH at [");
                print_int(i);
                print_str("][");
                print_int(j);
                print_str("]: got ");
                print_int(C[i][j]);
                print_str(", expected ");
                print_int(expected[i][j]);
                print_newline();
                return 1;
            }
        }
    }
    return 0;
}

// Scratchpad addresses
// The scratchpad is organized as banks of rows
// We'll use: A at row 0, B at row DIM
#define SPAD_A 0
#define SPAD_B DIM

// Accumulator address (high bit set)
#define ACC_C ((1 << 31) | 0)

// Place _start in .text.init section to ensure it's at 0x80000000
__attribute__((section(".text.init")))
void _start(void) {
    // Initialize Gemmini
    print_str("=== Gemmini Matrix Multiply Test ===\n");
    print_str("DIM = ");
    print_int(DIM);
    print_newline();
    
    // Print input matrices
    print_matrix("Matrix A (tainted input)", A);
    print_matrix("Matrix B (identity)", B);
    
    // Flush any pending operations
    gemmini_flush(0);
    
    // Configure for weight-stationary dataflow
    // No activation, no shift
    print_str("\nConfiguring Gemmini...\n");
    gemmini_config_ex(WEIGHT_STATIONARY, NO_ACTIVATION, 0, 0);
    
    // Configure load stride (row stride in bytes)
    gemmini_config_ld(DIM * sizeof(elem_t));
    
    // Configure store stride
    gemmini_config_st(DIM * sizeof(elem_t));
    
    // Record start cycle
    uint64_t start = read_cycles();
    
    // Step 1: Move matrix A from DRAM to scratchpad
    print_str("Moving A to scratchpad...\n");
    gemmini_mvin((uint64_t)A, SPAD_A);
    
    // Step 2: Move matrix B from DRAM to scratchpad  
    print_str("Moving B to scratchpad...\n");
    gemmini_mvin((uint64_t)B, SPAD_B);
    
    // Step 3: Preload B (weights) into systolic array
    // Output will go to accumulator at ACC_C
    print_str("Preloading B and computing A*B...\n");
    gemmini_preload(SPAD_B, ACC_C);
    
    // Step 4: Compute A * B
    // Feed A through the array, result accumulates in ACC_C
    gemmini_compute_preloaded(SPAD_A, GARBAGE_ADDR);
    
    // Step 5: Move result from accumulator to DRAM
    print_str("Moving result to DRAM...\n");
    gemmini_mvout((uint64_t)C, ACC_C);
    
    // Fence to ensure all operations complete
    gemmini_fence();
    
    // Record end cycle
    uint64_t end = read_cycles();
    
    // Print result
    print_matrix("Result C = A * B", C);
    
    // Print timing
    print_str("\nCycles: ");
    print_int((int32_t)(end - start));
    print_newline();
    
    // Verify
    print_str("\nVerifying result...\n");
    if (verify_result() == 0) {
        print_str("SUCCESS: Matrix multiplication correct!\n");
    } else {
        print_str("FAILURE: Matrix multiplication incorrect!\n");
    }
    
    print_str("\n=== Test Complete ===\n");
    
    // Signal end of simulation
    // Write to SoC control register to end simulation
    volatile uint64_t *soc_ctrl = (volatile uint64_t *)0x60000000;
    *soc_ctrl = 0;
    
    // Infinite loop (should not reach here in simulation)
    while (1) {
        asm volatile("wfi");
    }
}
