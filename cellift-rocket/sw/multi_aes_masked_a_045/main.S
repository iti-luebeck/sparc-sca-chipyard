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
    .byte 0x08, 0xb1, 0xb8, 0x9d
    .byte 0x1f, 0x45, 0x9f, 0xaa
    .byte 0xb5, 0x9b, 0x5f, 0x95
    .byte 0x1f, 0x22, 0x21, 0x36

  .globl aes_state_mask
aes_state_mask:
    .byte 0x9c, 0x44, 0xdf, 0x97
    .byte 0xfb, 0x76, 0x82, 0x5c
    .byte 0x56, 0x6c, 0x0f, 0xe6
    .byte 0x2f, 0x86, 0xda, 0x80

  .globl aes_ciphertext
aes_ciphertext:
    .space 16

  .globl aes_context
aes_context:
    .space 176
