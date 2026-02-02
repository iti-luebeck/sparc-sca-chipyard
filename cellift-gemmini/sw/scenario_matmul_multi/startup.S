# Gemmini Matrix Multiplication Multi-Scenario Entry Point
# Rocket Core (RV64G)

.section .text.start
.globl _start

_start:
    # Set up stack pointer (use high memory area)
    li      sp, 0x80010000
    
    # Clear BSS section (if any)
    la      t0, __bss_start
    la      t1, __bss_end
1:
    bge     t0, t1, 2f
    sd      zero, 0(t0)
    addi    t0, t0, 8
    j       1b
2:
    
    # Call main C function
    call    main
    
    # Should not return, but if it does, loop forever
_halt:
    j       _halt

.section .bss
.globl __bss_start
__bss_start:
.globl __bss_end
__bss_end:
