# AES-128 Multi-Executable Scenario Makefile
# For Rocket Core (RV64G)
#
# Builds N separate executables, each performing a single AES encryption
# with a different test vector (same key, different plaintext).
#
# Usage:
#   make                    # Build all executables (uses NUM_VECTORS from test_vectors.h)
#   make NUM_VECTORS=10     # Build 10 executables
#   make single VECTOR_INDEX=5  # Build single executable for vector 5
#   make clean              # Remove all build artifacts

# Toolchain from chipyard
TOOLCHAIN_PREFIX ?= /mnt/nvme1n1p1/chipyard-1.8.1/.conda-env/riscv-tools/bin/riscv64-unknown-elf-

CC = $(TOOLCHAIN_PREFIX)gcc
AS = $(TOOLCHAIN_PREFIX)gcc
LD = $(TOOLCHAIN_PREFIX)gcc
OBJDUMP = $(TOOLCHAIN_PREFIX)objdump
OBJCOPY = $(TOOLCHAIN_PREFIX)objcopy

# Rocket Core is RV64G
ARCH = rv64g
ABI = lp64

# Number of executables to build (auto-detect from header or override)
NUM_VECTORS ?= $(shell grep -oP 'NUM_TEST_VECTORS\s+\K[0-9]+' test_vectors.h 2>/dev/null || echo 10)

# Compiler flags
CFLAGS = -march=$(ARCH) -mabi=$(ABI) -O2 -g
CFLAGS += -fno-builtin -nostdlib -nostartfiles
CFLAGS += -mcmodel=medany -fno-pic
CFLAGS += -Wall -Wextra -Wno-main -Wno-unused-function
CFLAGS += -I.

# Assembler flags
ASFLAGS = -march=$(ARCH) -mabi=$(ABI) -g

# Linker flags
LDFLAGS = -march=$(ARCH) -mabi=$(ABI)
LDFLAGS += -nostdlib -nostartfiles
LDFLAGS += -T link.ld

# Source files
ASM_SRCS = startup.S
C_SRCS = main.c aes128.c

# Output directory
BUILD_DIR = build

# Generate list of targets (app_0.elf, app_1.elf, ...)
INDICES := $(shell seq 0 $$(($(NUM_VECTORS) - 1)))
TARGETS := $(addprefix $(BUILD_DIR)/app_, $(addsuffix .elf, $(INDICES)))

.PHONY: all clean single info help

# Default: build all executables
all: $(BUILD_DIR) $(TARGETS)
	@echo ""
	@echo "Built $(NUM_VECTORS) executables:"
	@ls -la $(BUILD_DIR)/app_*.elf 2>/dev/null | head -20
	@if [ $(NUM_VECTORS) -gt 20 ]; then echo "  ... and more"; fi

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Pattern rule for building each executable
# app_N.elf is built with -include vector_N.h (contains only that vector's data)
$(BUILD_DIR)/app_%.elf: $(ASM_SRCS) $(C_SRCS) vector_%.h | $(BUILD_DIR)
	@echo "Building $@ (vector $*)"
	@$(CC) $(CFLAGS) -include vector_$*.h -c -o $(BUILD_DIR)/main_$*.o main.c
	@$(CC) $(CFLAGS) -c -o $(BUILD_DIR)/aes128_$*.o aes128.c
	@$(AS) $(ASFLAGS) -c -o $(BUILD_DIR)/startup_$*.o startup.S
	@$(LD) $(LDFLAGS) -o $@ $(BUILD_DIR)/startup_$*.o $(BUILD_DIR)/main_$*.o $(BUILD_DIR)/aes128_$*.o
	@$(OBJDUMP) -d -S $@ > $@.dump

# Build a single executable (use: make single VECTOR_INDEX=5)
single: $(BUILD_DIR)
ifndef VECTOR_INDEX
	$(error VECTOR_INDEX is not set. Usage: make single VECTOR_INDEX=N)
endif
	@echo "Building single executable for vector $(VECTOR_INDEX)"
	$(CC) $(CFLAGS) -include vector_$(VECTOR_INDEX).h -c -o $(BUILD_DIR)/main.o main.c
	$(CC) $(CFLAGS) -c -o $(BUILD_DIR)/aes128.o aes128.c
	$(AS) $(ASFLAGS) -c -o $(BUILD_DIR)/startup.o startup.S
	$(LD) $(LDFLAGS) -o $(BUILD_DIR)/app_$(VECTOR_INDEX).elf $(BUILD_DIR)/startup.o $(BUILD_DIR)/main.o $(BUILD_DIR)/aes128.o
	$(OBJDUMP) -d -S $(BUILD_DIR)/app_$(VECTOR_INDEX).elf > $(BUILD_DIR)/app_$(VECTOR_INDEX).elf.dump

clean:
	rm -rf $(BUILD_DIR)

# Clean everything including generated vector headers
distclean: clean
	rm -f vector_*.h

# Show configuration
info:
	@echo "Toolchain: $(TOOLCHAIN_PREFIX)"
	@echo "Architecture: $(ARCH)"
	@echo "ABI: $(ABI)"
	@echo "Number of vectors: $(NUM_VECTORS)"
	@echo "Target executables: app_0.elf through app_$$(($(NUM_VECTORS)-1)).elf"

help:
	@echo "AES-128 Multi-Executable Build System"
	@echo ""
	@echo "Usage:"
	@echo "  make                      Build all $(NUM_VECTORS) executables"
	@echo "  make NUM_VECTORS=10       Build 10 executables"
	@echo "  make single VECTOR_INDEX=5  Build only app_5.elf"
	@echo "  make clean                Remove build artifacts"
	@echo "  make info                 Show build configuration"
	@echo ""
	@echo "Output:"
	@echo "  build/app_N.elf           Executable for test vector N"
	@echo "  build/app_N.elf.dump      Disassembly for debugging"
