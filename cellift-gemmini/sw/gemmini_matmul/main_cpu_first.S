# Test: CPU load FIRST, then Gemmini matmul
# This isolates whether the issue is timing or Gemmini-related

  .section ".text.init","ax",@progbits
  .globl _start
  .align 2

_start:
    # =========================================
    # PHASE 1: CPU Load of Tainted Data FIRST
    # =========================================
    
    # Load tainted data using regular CPU instructions
    la t0, tainted_data
    
    # Load 8 bytes (should be tainted)
    ld t1, 0(t0)       # Load first 8 bytes - TAINTED
    ld t2, 8(t0)       # Load next 8 bytes - TAINTED
    
    # Do some computation with tainted data
    add t3, t1, t2     # Add tainted values
    xor t4, t1, t2     # XOR tainted values
    
    # Store results
    la t5, cpu_result
    sd t1, 0(t5)       # Store tainted value
    sd t2, 8(t5)       # Store tainted value  
    sd t3, 16(t5)      # Store computed result
    sd t4, 24(t5)      # Store computed result
    
    # =========================================
    # PHASE 2: Gemmini Matrix Multiplication
    # =========================================
    
    # gemmini_flush(0)
    li a0, 0
    li a1, 0
    .insn r 0x7b, 7, 3, x0, a0, a1
    
    # gemmini_config_ex
    li a0, 0x000100
    li a1, 0
    .insn r 0x7b, 7, 0, x0, a0, a1
    
    # gemmini_config_ld
    li a0, 4
    li a1, 0
    .insn r 0x7b, 7, 1, x0, a0, a1

infinite_loop:
    j infinite_loop

# =========================================
# Data section
# =========================================
  .section ".data"
  .align 6

# Tainted data (will be loaded by CPU FIRST)
  .globl tainted_data
tainted_data:
    .byte 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x11, 0x22
    .byte 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0x00

  .align 6
# CPU computation results
  .globl cpu_result
cpu_result:
    .space 32
