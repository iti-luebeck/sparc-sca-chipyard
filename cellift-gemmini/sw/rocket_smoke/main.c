#include <stdint.h>
#include "gemmini.h"

// Memory addresses
#define RESULT_BASE 0x80004000
#define MATRIX_A_BASE 0x80005000
#define MATRIX_B_BASE 0x80005100  
#define MATRIX_C_BASE 0x80005200

int main(void) {
    volatile uint64_t *result_mem = (volatile uint64_t *)RESULT_BASE;
    volatile elem_t *matrix_a = (volatile elem_t *)MATRIX_A_BASE;
    volatile elem_t *matrix_b = (volatile elem_t *)MATRIX_B_BASE;
    volatile elem_t *matrix_c = (volatile elem_t *)MATRIX_C_BASE;
    
    // Part 1: CPU test
    volatile uint64_t a = 0x1234;
    volatile uint64_t b = 0x5678;
    volatile uint64_t c = a * b + 0x9;
    volatile uint64_t expected = 0x6260069;

    result_mem[0] = a;
    result_mem[1] = b;
    result_mem[2] = c;
    result_mem[3] = expected;
    result_mem[4] = (c == expected) ? 0xDEADBEEF : 0xBADC0FFE;

    // Part 2: Gemmini test
    // Initialize Matrix A (4x4): [1,2,3,4; 5,6,7,8; 9,10,11,12; 13,14,15,16]
    for (int i = 0; i < DIM; i++) {
        for (int j = 0; j < DIM; j++) {
            matrix_a[i * DIM + j] = i * DIM + j + 1;
        }
    }
    
    // Initialize Matrix B as identity (so C = A * I = A)
    for (int i = 0; i < DIM; i++) {
        for (int j = 0; j < DIM; j++) {
            matrix_b[i * DIM + j] = (i == j) ? 1 : 0;
        }
    }
    
    // Clear output matrix
    for (int i = 0; i < DIM * DIM; i++) {
        matrix_c[i] = 0;
    }

    // Configure Gemmini using reference implementation
    gemmini_config_ld(DIM * sizeof(elem_t));
    gemmini_config_st(DIM * sizeof(elem_t));
    gemmini_config_ex(WEIGHT_STATIONARY, NO_ACTIVATION, 0, 0);
    
    // Move matrices to scratchpad
    gemmini_mvin(MATRIX_A_BASE, 0);
    gemmini_mvin(MATRIX_B_BASE, DIM);
        gemmini_fence();
    
    // Perform matmul: C = A * B
        gemmini_preload(DIM, 2*DIM);  // Preload B (at spad address DIM) to accumulator, output at 2*DIM
        gemmini_compute_preloaded(0, 2*DIM);  // Compute A (at 0) with preloaded
    gemmini_fence();
    
    // Move result back
        gemmini_mvout(MATRIX_C_BASE, 2*DIM);
    gemmini_fence();
    
    // Verify result
    int matmul_pass = 1;
    for (int i = 0; i < DIM * DIM; i++) {
        if (matrix_c[i] != matrix_a[i]) {
            matmul_pass = 0;
            break;
        }
    }
    
    result_mem[5] = ((uint64_t)matrix_a[0]) | ((uint64_t)matrix_a[1] << 8) | 
                    ((uint64_t)matrix_a[2] << 16) | ((uint64_t)matrix_a[3] << 24);
    result_mem[6] = ((uint64_t)matrix_c[0]) | ((uint64_t)matrix_c[1] << 8) | 
                    ((uint64_t)matrix_c[2] << 16) | ((uint64_t)matrix_c[3] << 24);
    result_mem[7] = matmul_pass ? 0xDEADF00D : 0xBADDA7A;
    
    // Halt
    while (1) { }
    return 0;
}
