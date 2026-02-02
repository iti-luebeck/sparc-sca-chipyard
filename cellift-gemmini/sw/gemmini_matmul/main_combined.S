# Combined test: Gemmini matmul followed by CPU load of tainted data
# This tests if:
# 1. Gemmini can perform matmul correctly
# 2. CPU can still load tainted data and propagate taint
#
# If taint propagates for CPU loads but not Gemmini DMA,
# we know the Gemmini DMA taint path is the issue.

  .section ".text.init","ax",@progbits
  .globl _start
  .align 2

_start:
    # =========================================
    # PHASE 1: Gemmini Matrix Multiplication
    # =========================================
    
    # Configure Gemmini (flush first)
    # gemmini_flush(0) - custom3 opcode (funct=7)
    li a0, 0
    li a1, 0
    .insn r 0x7b, 7, 7, x0, a0, a1    # GEMMINI_FLUSH
    
    # gemmini_config_ex - configure execution
    # rs1 = (1<<16) | (dataflow<<2) | CONFIG_EX
    # rs2 = (1<<48) | (relu6_shift<<32) | sys_shift
    li a0, 0x00010004
    li a1, 0x0001000000000000
    .insn r 0x7b, 7, 0, x0, a0, a1    # CONFIG_EX
    
    # gemmini_config_ld - configure load stride
    # rs1 = (DIM<<16) | (1<<8) | CONFIG_LD, rs2 = stride
    li a0, 0x00040101
    li a1, 4
    .insn r 0x7b, 7, 0, x0, a0, a1    # CONFIG_LD (mvin)
    
    # gemmini_config_st - configure store stride
    # rs1 = CONFIG_ST, rs2 = stride
    li a0, 2
    li a1, 4
    .insn r 0x7b, 7, 0, x0, a0, a1    # CONFIG_ST (mvout)
    
    # Move matrix A to scratchpad row 0
    # rs2 = (rows<<48) | (cols<<32) | spad_addr
    la a0, matrix_A
    li a1, 0x0004000400000000
    .insn r 0x7b, 7, 2, x0, a0, a1    # MVIN
    
    # Move matrix B to scratchpad row 4
    la a0, matrix_B
    li a1, 0x0004000400000004
    .insn r 0x7b, 7, 2, x0, a0, a1    # MVIN
    
    # Preload B from scratchpad to systolic array
    # rs1 = (rows<<48) | (cols<<32) | BD
    # rs2 = (rows<<48) | (cols<<32) | C (acc)
    li a0, 0x0004000400000004
    li a1, 0x0004000480000000
    .insn r 0x7b, 7, 6, x0, a0, a1    # PRELOAD
    
    # Compute A*B, accumulate to C
    # rs1 = (rows<<48) | (cols<<32) | A
    # rs2 = (rows<<48) | (cols<<32) | BD (garbage)
    li a0, 0x0004000400000000
    li a1, 0x00040004FFFFFFFF
    .insn r 0x7b, 7, 4, x0, a0, a1    # COMPUTE_PRELOADED
    
    # Move result from accumulator to memory
    # rs2 = (rows<<48) | (cols<<32) | acc_addr
    la a0, matrix_C
    li a1, 0x0004000480000000
    .insn r 0x7b, 7, 3, x0, a0, a1    # MVOUT
    
    # Fence to wait for Gemmini to complete
    fence
    
    # =========================================
    # PHASE 2: CPU Load of Tainted Data
    # =========================================
    
    # Load tainted data using regular CPU instructions
    # This data will be at tainted_data address
    la t0, tainted_data
    
    # Load 8 bytes (should be tainted)
    ld t1, 0(t0)       # Load first 8 bytes - TAINTED
    ld t2, 8(t0)       # Load next 8 bytes - TAINTED
    
    # Do some computation with tainted data
    add t3, t1, t2     # Add tainted values
    xor t4, t1, t2     # XOR tainted values
    
    # Store results to verify taint propagation
    la t5, cpu_result
    sd t1, 0(t5)       # Store tainted value
    sd t2, 8(t5)       # Store tainted value  
    sd t3, 16(t5)      # Store computed result
    sd t4, 24(t5)      # Store computed result
    
    # Also load and check Gemmini result
    la t6, matrix_C
    ld a0, 0(t6)       # Load Gemmini result
    
    # Store to show we read it
    la a1, gemmini_check
    sd a0, 0(a1)

infinite_loop:
    j infinite_loop

# =========================================
# Data section
# =========================================
  .section ".data"
  .align 6

# Matrix A for Gemmini (4x4, int8) - NOT tainted
  .globl matrix_A
matrix_A:
    .byte 1, 2, 3, 4
    .byte 5, 6, 7, 8
    .byte 9, 10, 11, 12
    .byte 13, 14, 15, 16

# Matrix B for Gemmini (4x4, int8, identity) - NOT tainted
  .globl matrix_B  
matrix_B:
    .byte 1, 0, 0, 0
    .byte 0, 1, 0, 0
    .byte 0, 0, 1, 0
    .byte 0, 0, 0, 1

  .align 6
# Result from Gemmini (4x4, int8)
  .globl matrix_C
matrix_C:
    .space 64

  .align 6
# Data to be tainted (will be loaded by CPU)
# Place this at a known address for taint file
  .globl tainted_data
tainted_data:
    .byte 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x11, 0x22
    .byte 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0x00

  .align 6
# CPU computation results
  .globl cpu_result
cpu_result:
    .space 32

  .align 3
# Place to store Gemmini check value
  .globl gemmini_check  
gemmini_check:
    .space 8
