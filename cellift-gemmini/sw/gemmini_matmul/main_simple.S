# Simple test to verify CPU load taint propagation
# Then Gemmini RoCC instructions

  .section ".text.init","ax",@progbits
  .globl _start
  .align 2

_start:
    # First, do simple CPU loads from tainted matrix A
    # This should trigger taint propagation
    la t0, matrix_A        # Load address of matrix A
    
    # Load first 8 bytes of A (should be tainted)
    ld t1, 0(t0)           # Load tainted data into t1
    ld t2, 8(t0)           # Load more tainted data into t2
    
    # Store tainted data back to result area
    la t3, result
    sd t1, 0(t3)           # Store tainted value
    sd t2, 8(t3)           # Store tainted value
    
    # Now do some computation with tainted data
    add t4, t1, t2         # Add tainted values
    sd t4, 16(t3)          # Store result
    
infinite_loop:
    j infinite_loop

# Data section
  .section ".data"
  .align 6

  .globl matrix_A
matrix_A:
    .byte 1, 2, 3, 4
    .byte 5, 6, 7, 8
    .byte 9, 10, 11, 12
    .byte 13, 14, 15, 16

  .globl matrix_B  
matrix_B:
    .byte 1, 0, 0, 0
    .byte 0, 1, 0, 0
    .byte 0, 0, 1, 0
    .byte 0, 0, 0, 1

  .align 6
  .globl result
result:
    .space 64
