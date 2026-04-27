# AES-128 Tainted Key Scenario - Rocket Core (RV64G)
# Makefile for building the AES-128 encryption test binary

RISCV_PREFIX ?= /mnt/nvme1n1p1/chipyard-1.11.0/.conda-env/riscv-tools/bin/riscv64-unknown-elf

# Rocket uses RV64G (RV64IMAFD)
RV_ARCH_FLAGS ?= -march=rv64g -mabi=lp64
RISCV_GCC_OPTS ?= $(RV_ARCH_FLAGS) -DPREALLOCATE=1 -mcmodel=medany -static -std=gnu99 -O2 -ffast-math -fno-common -fno-builtin-printf -fno-tree-loop-distribute-patterns -gdwarf-2
LDFLAGS = -Tlink.ld -static -nostdlib -nostartfiles -lm -lgcc
RISCV_OBJDUMP ?= $(RISCV_PREFIX)-objdump -d

CC = $(RISCV_PREFIX)-gcc

SOURCES = main.S aes128.c

build/app.elf: $(SOURCES) link.ld | build
	$(CC) $(RISCV_GCC_OPTS) $(filter-out link.ld,$^) -o $@ $(LDFLAGS)
	$(RISCV_OBJDUMP) $@ > $@.dump

build:
	mkdir -p build

.PHONY: clean
clean:
	rm -rf build
