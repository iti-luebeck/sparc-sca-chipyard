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
    .byte 0x11, 0x68, 0x50, 0xac
    .byte 0x9b, 0x0d, 0xf0, 0x06
    .byte 0x4b, 0xe8, 0xdd, 0x53
    .byte 0x50, 0xbc, 0xa7, 0xfb

  .globl aes_state_mask
aes_state_mask:
    .byte 0xe5, 0x30, 0xc1, 0xe2
    .byte 0xb4, 0xb3, 0x28, 0x0d
    .byte 0xa0, 0xa1, 0x84, 0xf3
    .byte 0x3b, 0x95, 0x5f, 0x72

  .globl aes_ciphertext
aes_ciphertext:
    .space 16

  .globl aes_context
aes_context:
    .space 176
