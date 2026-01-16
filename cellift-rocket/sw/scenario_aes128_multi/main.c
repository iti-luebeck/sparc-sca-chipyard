/**
 * AES-128 Single Vector Encryption
 * 
 * Runs a single AES-128 encryption using a single test vector.
 * Build with: -DVECTOR_INDEX=N -include vector_N.h
 * Each vector has its own header file: vector_0.h, vector_1.h, etc.
 */

#include <stdint.h>
#include "aes128.h"
#include "aes_config.h"

/* 
 * The following variables are defined in vector_N.h (force-included via -include):
 *   static const uint8_t test_key[16];
 *   static const uint8_t test_plaintext[16];
 *   static const uint8_t test_expected_ciphertext[16];
 */

/* Result storage */
static volatile uint8_t *results = (volatile uint8_t *)RESULT_BASE_ADDR;
static volatile uint8_t *status = (volatile uint8_t *)STATUS_ADDR;

/* Compare two 16-byte arrays */
static int compare_blocks(const uint8_t *a, const uint8_t *b) {
    for (int i = 0; i < 16; i++) {
        if (a[i] != b[i]) return 0;
    }
    return 1;
}

/* Main encryption function */
void aes_encrypt_single(void) {
    uint8_t ciphertext[16];
    
    /* Mark as running */
    *status = STATUS_RUNNING;
    
    /* Perform single encryption with the test vector from vector_N.h */
    aes128_encrypt(test_plaintext, test_key, ciphertext);
    
    /* Store result */
    for (int i = 0; i < 16; i++) {
        results[i] = ciphertext[i];
    }
    
#if VERIFY_RESULTS
    /* Verify against expected ciphertext */
    if (compare_blocks(ciphertext, test_expected_ciphertext)) {
        *status = STATUS_PASS;
    } else {
        *status = STATUS_FAIL;
    }
#else
    *status = STATUS_PASS;
#endif
}

/* Entry point called from assembly */
void main(void) {
    aes_encrypt_single();
    
    /* Infinite loop to end simulation cleanly */
    while (1) {
        asm volatile ("nop");
    }
}
