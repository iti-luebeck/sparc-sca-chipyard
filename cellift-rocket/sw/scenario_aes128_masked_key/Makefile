# AES-128 Tainted Key Scenario - Rocket Core (RV64G)
# Makefile for building the AES-128 encryption test binary

# Toolchain: $RISCV is set inside Docker and by env.sh.  SPARC_SCA_RISCV_BIN is
# an escape hatch for a toolchain installed elsewhere (e.g. a Chipyard conda
# env); otherwise riscv64-unknown-elf-* is resolved from PATH, so a native
# install works without editing this file.
RISCV_PREFIX ?= $(if $(RISCV),$(RISCV)/bin/riscv64-unknown-elf,$(if $(SPARC_SCA_RISCV_BIN),$(SPARC_SCA_RISCV_BIN)/riscv64-unknown-elf,riscv64-unknown-elf))

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
