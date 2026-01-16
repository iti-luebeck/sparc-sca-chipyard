/* Linker script for AES-128 Multi-Vector Scenario - Rocket Core */

OUTPUT_ARCH(riscv)
ENTRY(_start)

MEMORY
{
    RAM (rwx) : ORIGIN = 0x80000000, LENGTH = 64K
}

SECTIONS
{
    /* Code section */
    .text 0x80000000 : {
        *(.text.start)
        *(.text*)
        *(.rodata*)
    } > RAM

    /* Data section */
    .data : {
        *(.data*)
        *(.sdata*)
    } > RAM

    /* BSS section */
    .bss : {
        __bss_start = .;
        *(.bss*)
        *(.sbss*)
        __bss_end = .;
    } > RAM

    /* Stack grows down from 0x80010000 */
    _stack_top = 0x80010000;
    
    /* Results stored at 0x80002000 */
    /* Status stored at 0x80003000 */
}
