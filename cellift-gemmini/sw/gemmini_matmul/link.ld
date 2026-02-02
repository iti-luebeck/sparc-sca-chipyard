OUTPUT_ARCH( "riscv" )
ENTRY(_start)

SECTIONS
{
  /* Start at DRAM base address */
  . = 0x80000000;
  
  .text.init : { 
    *(.text.init) 
    *(.text*)
  }
  
  . = ALIGN(0x1000);
  
  .rodata : {
    *(.rodata*)
  }
  
  . = ALIGN(0x1000);
  
  .data : {
    *(.data*)
    *(.sdata*)
  }
  
  . = ALIGN(0x1000);
  
  .bss : {
    *(.bss*)
    *(.sbss*)
  }
  
  . = ALIGN(0x1000);
  
  /* HTIF tohost/fromhost for simulation I/O */
  .htif 0x80001000 : {
    PROVIDE(__tohost = .);
    . += 8;
    PROVIDE(__fromhost = .);
    . += 8;
  }
  
  /* Stack at end of first 64KB */
  . = 0x80010000;
  PROVIDE(__stack_top = .);
}
