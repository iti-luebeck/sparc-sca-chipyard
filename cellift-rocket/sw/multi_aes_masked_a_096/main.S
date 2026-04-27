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
    .byte 0xfa, 0x3b, 0x3e, 0x3a
    .byte 0xfc, 0x41, 0xa2, 0x53
    .byte 0xb1, 0xff, 0x96, 0xf5
    .byte 0x7c, 0x53, 0x72, 0x96

  .globl aes_state_mask
aes_state_mask:
    .byte 0x93, 0x82, 0x7e, 0x86
    .byte 0x18, 0xda, 0xcb, 0xf8
    .byte 0xba, 0x27, 0x3c, 0xdf
    .byte 0x8d, 0x14, 0xd3, 0xe6

  .globl aes_ciphertext
aes_ciphertext:
    .space 16

  .globl aes_context
aes_context:
    .space 176
