# Toolchain: $RISCV is set inside Docker and by env.sh.  SPARC_SCA_RISCV_BIN is
# an escape hatch for a toolchain installed elsewhere (e.g. a Chipyard conda
# env); otherwise riscv64-unknown-elf-* is resolved from PATH, so a native
# install works without editing this file.
GCC = $(if $(RISCV),$(RISCV)/bin/riscv64-unknown-elf,$(if $(SPARC_SCA_RISCV_BIN),$(SPARC_SCA_RISCV_BIN)/riscv64-unknown-elf,riscv64-unknown-elf))-gcc
OBJDUMP = $(if $(RISCV),$(RISCV)/bin/riscv64-unknown-elf,$(if $(SPARC_SCA_RISCV_BIN),$(SPARC_SCA_RISCV_BIN)/riscv64-unknown-elf,riscv64-unknown-elf))-objdump
CFLAGS= -std=gnu99 -O2 -fno-common -fno-builtin-printf -Wall
LDFLAGS= -static

include libgloss.mk

PROGRAMS = pwm blkdev accum charcount nic-loopback big-blkdev pingd \
           streaming-passthrough streaming-fir nvdla spiflashread spiflashwrite fft

spiflash.img: spiflash.py
	python3 $<

.DEFAULT_GOAL := default

.PHONY: default
default: $(addsuffix .riscv,$(PROGRAMS)) spiflash.img

.PHONY: dumps
dumps: $(addsuffix .dump,$(PROGRAMS))

%.o: %.S
	$(GCC) $(CFLAGS) -D__ASSEMBLY__=1 -c $< -o $@

%.o: %.c mmio.h spiflash.h
	$(GCC) $(CFLAGS) -c $< -o $@

%.riscv: %.o $(libgloss)
	$(GCC) $(LDFLAGS) $< -o $@

%.dump: %.riscv
	$(OBJDUMP) -D $< > $@


.PHONY: clean
clean:
	rm -f *.riscv *.o *.dump
	$(if $(libgloss),rm -rf $(libgloss_builddir)/)
