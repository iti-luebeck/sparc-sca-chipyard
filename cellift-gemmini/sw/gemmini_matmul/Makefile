# Makefile for Gemmini Matrix Multiplication Test
# For CellIFT taint tracking experiments

RISCV_PREFIX ?= riscv64-unknown-elf

# Architecture flags for RV64GC with Gemmini (custom3 RoCC)
# Note: Gemmini uses custom3 opcodes which are encoded as RoCC instructions
RV_ARCH_FLAGS ?= -march=rv64gc -mabi=lp64d

# Compiler flags
RISCV_GCC_OPTS ?= $(RV_ARCH_FLAGS) \
	-DBAREMETAL=1 \
	-mcmodel=medany \
	-static \
	-std=gnu99 \
	-O2 \
	-ffast-math \
	-fno-common \
	-fno-builtin-printf \
	-fno-tree-loop-distribute-patterns \
	-I.

# Linker flags
LDFLAGS = -Tlink.ld -static -nostdlib -nostartfiles -lm -lgcc

# Tools
CC = $(RISCV_PREFIX)-gcc
OBJDUMP = $(RISCV_PREFIX)-objdump
OBJCOPY = $(RISCV_PREFIX)-objcopy
SIZE = $(RISCV_PREFIX)-size

# Target
TARGET = gemmini_matmul

# Source files
SRCS = main.c
HEADERS = gemmini.h gemmini_params.h xcustom.h

.PHONY: all clean dump

all: $(TARGET).riscv simple_load.riscv

$(TARGET).riscv: $(SRCS) $(HEADERS) link.ld
	$(CC) $(RISCV_GCC_OPTS) $(SRCS) -o $@ $(LDFLAGS)
	$(OBJDUMP) -d $@ > $@.dump
	$(SIZE) $@
	@echo "Built $@"

# Simple assembly test for taint verification
simple_load.riscv: main_simple.S link.ld
	$(CC) $(RV_ARCH_FLAGS) -static -nostartfiles -nostdlib -Tlink.ld main_simple.S -o $@
	$(OBJDUMP) -d $@ > $@.dump
	$(OBJDUMP) -t $@ | grep -E "matrix_A|matrix_B|result"
	$(SIZE) $@
	@echo "Built $@"

# Combined test: Gemmini matmul + CPU tainted load
combined_test.riscv: main_combined.S link.ld
	$(CC) $(RV_ARCH_FLAGS) -static -nostartfiles -nostdlib -Tlink.ld main_combined.S -o $@
	$(OBJDUMP) -d $@ > $@.dump
	$(OBJDUMP) -t $@ | grep -E "matrix_|tainted_data|cpu_result"
	$(SIZE) $@
	@echo "Built $@"
	@echo ""
	@echo "Taint the 'tainted_data' symbol address in sram_taint_data.txt"

# Generate a flat binary (useful for some simulators)
$(TARGET).bin: $(TARGET).riscv
	$(OBJCOPY) -O binary $< $@

# Just dump disassembly
dump: $(TARGET).riscv
	$(OBJDUMP) -d -S $<

# Show section sizes
size: $(TARGET).riscv
	$(SIZE) $<

clean:
	rm -f $(TARGET).riscv $(TARGET).riscv.dump $(TARGET).bin

# Help target
help:
	@echo "Gemmini Matrix Multiplication Test"
	@echo ""
	@echo "Targets:"
	@echo "  all      - Build the test binary (default)"
	@echo "  clean    - Remove build artifacts"
	@echo "  dump     - Show disassembly"
	@echo "  size     - Show section sizes"
	@echo ""
	@echo "Variables:"
	@echo "  RISCV_PREFIX - Toolchain prefix (default: riscv64-unknown-elf)"
	@echo ""
	@echo "Usage with CellIFT simulator:"
	@echo "  export SIMSRAMELF=\$$(pwd)/gemmini_matmul.riscv"
	@echo "  export SIMLEN=50000"
	@echo "  ./Vtop_tiny_soc"
