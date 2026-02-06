GCC=/mnt/nvme1n1p1/chipyard-1.8.1/.conda-env/riscv-tools/binriscv64-unknown-elf-gcc
OBJDUMP=/mnt/nvme1n1p1/chipyard-1.8.1/.conda-env/riscv-tools/binriscv64-unknown-elf-objdump
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
