/*
 * Linker Script for AES-128 Tainted Key Scenario - Rocket Core
 *
 * Memory layout for Rocket (RV64G):
 *   - Code starts at 0x80000000 (standard boot address)
 *   - Stack grows downward from high memory
 *   - Tainted key placed at aligned address 0x80001000
 */

OUTPUT_ARCH("riscv")
ENTRY(_start)

MEMORY
{
    /* Main memory region - Rocket uses 0x80000000 as boot address */
    RAM (rwx) : ORIGIN = 0x80000000, LENGTH = 128K
}

SECTIONS
{
    /* Code section */
    . = 0x80000000;
    .text.init : {
        *(.text.init)
    } > RAM

    .text : {
        *(.text)
        *(.text.*)
    } > RAM

    /* Read-only data */
    .rodata : {
        *(.rodata)
        *(.rodata.*)
        *(.srodata)
        *(.srodata.*)
    } > RAM

    /* Tainted data section - AES key placed here */
    /* Force alignment to 0x80001000 for easy taint marking */
    . = 0x80001000;
    .tainted_data 0x80001000 : {
        _tainted_start = .;
        *(.tainted_data)
        _tainted_end = .;
    } > RAM

    /* Regular data section */
    .data : {
        *(.data)
        *(.data.*)
        *(.sdata)
        *(.sdata.*)
    } > RAM

    /* BSS section */
    .bss : {
        _bss_start = .;
        *(.bss)
        *(.bss.*)
        *(.sbss)
        *(.sbss.*)
        _bss_end = .;
    } > RAM

    /* Stack - place at end of RAM, grows downward */
    . = ALIGN(16);
    . = . + 0x2000;  /* 8KB stack */
    _stack_top = .;
}
