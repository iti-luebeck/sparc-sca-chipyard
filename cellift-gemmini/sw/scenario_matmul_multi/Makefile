# Gemmini Matrix Multiplication Multi-Scenario Makefile
# For Rocket Core (RV64G)
#
# Builds N separate executables, each performing a single matrix multiplication
# with a different matrix pair.
#
# Usage:
#   make                      # Build all executables (uses NUM_TESTS from generate_scenario.py)
#   make NUM_TESTS=10         # Build 10 executables
#   make single TEST_INDEX=5  # Build single executable for test 5
#   make clean                # Remove all build artifacts

# Toolchain from esp-tools (matches working Gemmini headers)
# Toolchain: $RISCV is set inside Docker and by env.sh.  SPARC_SCA_RISCV_BIN is
# an escape hatch for a toolchain installed elsewhere (e.g. a Chipyard conda
# env); otherwise riscv64-unknown-elf-* is resolved from PATH, so a native
# install works without editing this file.
TOOLCHAIN_PREFIX ?= $(if $(RISCV),$(RISCV)/bin/riscv64-unknown-elf,$(if $(SPARC_SCA_RISCV_BIN),$(SPARC_SCA_RISCV_BIN)/riscv64-unknown-elf,riscv64-unknown-elf))-

CC = $(TOOLCHAIN_PREFIX)gcc
AS = $(TOOLCHAIN_PREFIX)gcc
LD = $(TOOLCHAIN_PREFIX)gcc
OBJDUMP = $(TOOLCHAIN_PREFIX)objdump
OBJCOPY = $(TOOLCHAIN_PREFIX)objcopy

# Rocket Core is RV64G
ARCH = rv64g
ABI = lp64

# Directory containing generated matrix header files
TEST_PATTERNS_DIR ?= test_patterns

# Number of executables to build (auto-detect from matrix headers or override)
NUM_TESTS ?= $(shell ls -1 $(TEST_PATTERNS_DIR)/matrix_*.h 2>/dev/null | wc -l)
ifeq ($(NUM_TESTS),0)
NUM_TESTS := 10
endif

# Get DIM from first matrix header if available (default 4)
DIM ?= 4

# Compiler flags
CFLAGS = -march=$(ARCH) -mabi=$(ABI) -O2 -g
CFLAGS += -fno-builtin -nostdlib -nostartfiles
CFLAGS += -mcmodel=medany -fno-pic
CFLAGS += -Wall -Wextra -Wno-main -Wno-unused-function
CFLAGS += -I. -I$(TEST_PATTERNS_DIR)

# Assembler flags
ASFLAGS = -march=$(ARCH) -mabi=$(ABI) -g

# Linker flags
LDFLAGS = -march=$(ARCH) -mabi=$(ABI)
LDFLAGS += -nostdlib -nostartfiles
LDFLAGS += -T link.ld

# Source files
ASM_SRCS = startup.S
C_SRCS = main.c

# Output directory
BUILD_DIR = build

# Generate list of targets (matmul_0.elf, matmul_1.elf, ...)
INDICES := $(shell seq 0 $(shell expr $(NUM_TESTS) - 1))
TARGETS := $(addprefix $(BUILD_DIR)/matmul_, $(addsuffix .elf, $(INDICES)))

.PHONY: all clean single info help

# Default: build all executables
all: $(BUILD_DIR) $(TARGETS)
	@echo ""
	@echo "Built $(NUM_TESTS) matrix multiplication executables (DIM=$(DIM)):"
	@ls -lh $(BUILD_DIR)/matmul_*.elf 2>/dev/null | head -20
	@if [ $(NUM_TESTS) -gt 20 ]; then echo "  ... and more"; fi

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Pattern rule for building each executable
# matmul_N.elf is built with -include matrix_N.h (contains only that matrix pair)
$(BUILD_DIR)/matmul_%.elf: $(ASM_SRCS) $(C_SRCS) $(TEST_PATTERNS_DIR)/matrix_%.h | $(BUILD_DIR)
	@echo "Building $@ (matrix pair $*)"
	@$(CC) $(CFLAGS) -include $(TEST_PATTERNS_DIR)/matrix_$*.h -c -o $(BUILD_DIR)/main_$*.o main.c
	@$(AS) $(ASFLAGS) -c -o $(BUILD_DIR)/startup_$*.o startup.S
	@$(LD) $(LDFLAGS) -o $@ $(BUILD_DIR)/startup_$*.o $(BUILD_DIR)/main_$*.o
	@$(OBJDUMP) -d -S $@ > $@.dump

# Build a single executable (use: make single TEST_INDEX=5)
single: $(BUILD_DIR)
ifndef TEST_INDEX
	$(error TEST_INDEX is not set. Usage: make single TEST_INDEX=N)
endif
	@echo "Building single executable for matrix pair $(TEST_INDEX)"
	$(CC) $(CFLAGS) -include $(TEST_PATTERNS_DIR)/matrix_$(TEST_INDEX).h -c -o $(BUILD_DIR)/main.o main.c
	$(AS) $(ASFLAGS) -c -o $(BUILD_DIR)/startup.o startup.S
	$(LD) $(LDFLAGS) -o $(BUILD_DIR)/matmul_$(TEST_INDEX).elf $(BUILD_DIR)/startup.o $(BUILD_DIR)/main.o
	$(OBJDUMP) -d -S $(BUILD_DIR)/matmul_$(TEST_INDEX).elf > $(BUILD_DIR)/matmul_$(TEST_INDEX).elf.dump

clean:
	rm -rf $(BUILD_DIR)

# Clean everything including generated matrix headers
distclean: clean
	rm -rf $(TEST_PATTERNS_DIR)

# Show configuration
info:
	@echo "Toolchain: $(TOOLCHAIN_PREFIX)"
	@echo "Architecture: $(ARCH)"
	@echo "ABI: $(ABI)"
	@echo "Matrix dimension: $(DIM)x$(DIM)"
	@echo "Number of test cases: $(NUM_TESTS)"
	@echo "Target executables: matmul_0.elf through matmul_$$(($(NUM_TESTS)-1)).elf"

help:
	@echo "Gemmini Matrix Multiplication Multi-Build System"
	@echo ""
	@echo "Usage:"
	@echo "  make                      Build all $(NUM_TESTS) executables"
	@echo "  make NUM_TESTS=20         Build 20 executables"
	@echo "  make single TEST_INDEX=5  Build only matmul_5.elf"
	@echo "  make clean                Remove build artifacts"
	@echo "  make info                 Show build configuration"
	@echo ""
	@echo "Output:"
	@echo "  build/matmul_N.elf        Executable for test case N"
	@echo "  build/matmul_N.elf.dump   Disassembly for debugging"

