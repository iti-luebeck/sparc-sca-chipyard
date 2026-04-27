/*
 * Linker Script for Kyber-512 Tainted Key Scenario - Rocket Core (RV64G)
 *
 * Memory layout for Rocket (RV64G):
 *   - Code starts at 0x80000000 (standard boot address)
 *   - Stack grows downward from _stack_top
 *   - Tainted key placed naturally after .bss; read actual VMA with:
 *       riscv64-unknown-elf-objdump -h build/app.elf | grep tainted_data
 *     and update taint_data/scenario_kyber_unmasked_key2/taint_data.txt.
 */

OUTPUT_ARCH("riscv")
ENTRY(_start)

MEMORY
{
    /* Main memory region - Rocket uses 0x80000000 as boot address, 128KB SRAM */
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

    /* Tainted data section - kyber_sk placed here after .bss.
     * Kyber code is ~15KB so .tainted_data lands around 0x80005000-0x80006000. */
    . = ALIGN(0x100);
    .tainted_data : {
        _tainted_start = .;
        *(.tainted_data)
        _tainted_end = .;
    } > RAM

    /* Stack - grows downward from _stack_top.
     * Kyber-512 decapsulation uses ~4.3KB of stack for polynomial ops. */
    . = ALIGN(16);
    . += 0x4000;  /* 16KB stack */
    _stack_top = .;
}
