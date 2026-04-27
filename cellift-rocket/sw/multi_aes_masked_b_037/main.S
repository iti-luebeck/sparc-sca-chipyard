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
    .byte 0x3c, 0xc0, 0x5c, 0x8d
    .byte 0xaa, 0x22, 0xfa, 0x54
    .byte 0xf8, 0x87, 0xf9, 0x73
    .byte 0xed, 0x5b, 0x32, 0x4a

  .globl aes_state_mask
aes_state_mask:
    .byte 0x33, 0x44, 0x07, 0xa7
    .byte 0xcb, 0x69, 0xd7, 0x88
    .byte 0x97, 0xe6, 0x13, 0xc2
    .byte 0xa8, 0xcc, 0xa3, 0x5b

  .globl aes_ciphertext
aes_ciphertext:
    .space 16

  .globl aes_context
aes_context:
    .space 176
