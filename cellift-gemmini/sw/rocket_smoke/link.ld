OUTPUT_ARCH(riscv)
ENTRY(_start)

MEMORY
{
    RAM (rwx) : ORIGIN = 0x80000000, LENGTH = 64K
}

SECTIONS
{
    .text 0x80000000 : {
        *(.text.start)
        *(.text*)
        *(.rodata*)
    } > RAM

    .data : {
        *(.data*)
        *(.sdata*)
    } > RAM

    .bss : {
        __bss_start = .;
        *(.bss*)
        *(.sbss*)
        __bss_end = .;
    } > RAM

    _stack_top = 0x80010000;
}
