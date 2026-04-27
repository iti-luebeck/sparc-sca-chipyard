/*
 * AES-128 Masked Key Scenario - Rocket Core (RV64G)
 *
 * Plaintext is XORed with aes_state_mask before encryption.
 * gen_scenarios.py randomises both aes_plaintext and aes_state_mask per trace.
 * aes_key is fixed (FIPS-197 key) and is the taint source.
 */

  .section ".text.init","ax",@progbits
  .globl _start
  .align 2

_start:
    la sp, _stack_top

    /* Apply mask: aes_plaintext[i] ^= aes_state_mask[i] */
    la   t1, aes_state_mask
    la   t2, aes_plaintext
    li   t0, 0
mask_loop:
    add  t4, t2, t0
    lbu  t3, 0(t4)
    add  t5, t1, t0
    lbu  t6, 0(t5)
    xor  t3, t3, t6
    sb   t3, 0(t4)
    addi t0, t0, 1
    li   t6, 16
    blt  t0, t6, mask_loop

    la a0, aes_context
    la a1, aes_key
    la a2, aes_plaintext
    la a3, aes_ciphertext
    call aes128_encrypt

infinite_loop:
    j infinite_loop


  .section ".tainted_data","aw",@progbits
  .align 4

  .globl aes_key
aes_key:
    .byte 0x2b, 0x7e, 0x15, 0x16
    .byte 0x28, 0xae, 0xd2, 0xa6
    .byte 0xab, 0xf7, 0x15, 0x88
    .byte 0x09, 0xcf, 0x4f, 0x3c


  .section ".data","aw",@progbits
  .align 4

  .globl aes_plaintext
aes_plaintext:
    .byte 0x96, 0x99, 0x7d, 0x1b
    .byte 0x26, 0x0e, 0xce, 0xbd
    .byte 0xb1, 0x1d, 0xca, 0xf5
    .byte 0x8e, 0xb1, 0xff, 0x6f

  .globl aes_state_mask
aes_state_mask:
    .byte 0x39, 0x03, 0x20, 0x08
    .byte 0x66, 0xdd, 0xf0, 0xf4
    .byte 0xb7, 0xe5, 0x90, 0x0f
    .byte 0xec, 0x89, 0x2e, 0x39

  .globl aes_ciphertext
aes_ciphertext:
    .space 16

  .globl aes_context
aes_context:
    .space 176
