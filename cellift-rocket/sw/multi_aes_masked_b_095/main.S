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
    .byte 0x00, 0x01, 0x02, 0x03
    .byte 0x04, 0x05, 0x06, 0x07
    .byte 0x08, 0x09, 0x0a, 0x0b
    .byte 0x0c, 0x0d, 0x0e, 0x0f


  .section ".data","aw",@progbits
  .align 4

  .globl aes_plaintext
aes_plaintext:
    .byte 0xef, 0x74, 0xbe, 0xe6
    .byte 0x02, 0xf4, 0x07, 0xa0
    .byte 0x38, 0x38, 0xa8, 0xd9
    .byte 0x39, 0xe6, 0xb6, 0x2e

  .globl aes_state_mask
aes_state_mask:
    .byte 0x02, 0x04, 0x16, 0x90
    .byte 0xb8, 0xa5, 0xdc, 0x66
    .byte 0x42, 0xad, 0x3e, 0xb9
    .byte 0xd2, 0xa5, 0xd2, 0x4d

  .globl aes_ciphertext
aes_ciphertext:
    .space 16

  .globl aes_context
aes_context:
    .space 176
