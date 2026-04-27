/*
 * AES-128 Tainted Key Scenario - Rocket Core (RV64G)
 * 
 * Main entry point and data definitions for the AES-128 test.
 * The key bytes are placed in a tainted section for CellIFT tracking.
 */

  .section ".text.init","ax",@progbits
  .globl _start
  .align 2

_start:
    /* Set up stack pointer */
    la sp, _stack_top

    /* 
     * Call AES-128 encryption
     * 
     * Arguments (RV64 calling convention):
     *   a0 = pointer to AES context (for expanded keys)
     *   a1 = pointer to 16-byte key (TAINTED)
     *   a2 = pointer to 16-byte plaintext
     *   a3 = pointer to 16-byte ciphertext output
     */
    la a0, aes_context
    la a1, aes_key          /* THIS IS THE TAINT SOURCE */
    la a2, aes_plaintext
    la a3, aes_ciphertext
    
    /* Call the AES encryption function */
    call aes128_encrypt
    
    /* Done - infinite loop */
infinite_loop:
    j infinite_loop


/*
 * ============================================================================
 * DATA SECTION - Tainted Key
 * ============================================================================
 * The AES key is placed in a special .tainted_data section at 0x80001000.
 * In CellIFT simulation, mark this memory region as tainted.
 */

  .section ".tainted_data","aw",@progbits
  .align 4

/*
 * AES-128 Secret Key (16 bytes) - TAINT SOURCE
 * 
 * This is the FIPS-197 Appendix B test vector key.
 * Located at 0x80001000 - mark these 16 bytes as tainted.
 */
  .globl aes_key
aes_key:
    .byte 0x2b, 0x7e, 0x15, 0x16
    .byte 0x28, 0xae, 0xd2, 0xa6
    .byte 0xab, 0xf7, 0x15, 0x88
    .byte 0x09, 0xcf, 0x4f, 0x3c


/*
 * ============================================================================
 * DATA SECTION - Public Data (not tainted)
 * ============================================================================
 */

  .section ".data","aw",@progbits
  .align 4

/*
 * Plaintext input block (16 bytes) - NOT tainted
 * FIPS-197 Appendix B test vector
 */
  .globl aes_plaintext
aes_plaintext:
    .byte 0xe7, 0x01, 0x47, 0xb6
    .byte 0xb6, 0xf3, 0x95, 0x6b
    .byte 0x1c, 0x35, 0xc5, 0x4e
    .byte 0x86, 0x51, 0x0b, 0x8a


/*
 * Ciphertext output buffer (16 bytes)
 * Expected result: 39 25 84 1d 02 dc 09 fb dc 11 85 97 19 6a 0b 32
 */
  .globl aes_ciphertext
aes_ciphertext:
    .space 16


/*
 * AES context for expanded key schedule (176 bytes for AES-128)
 */
  .globl aes_context
aes_context:
    .space 176
