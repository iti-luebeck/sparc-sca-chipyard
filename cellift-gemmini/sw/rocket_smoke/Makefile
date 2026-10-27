# Gemmini matrix multiplication test (bare-metal)
# Builds using esp-tools RISC-V toolchain with gemmini headers

# Toolchain: $RISCV is set inside Docker and by env.sh.  SPARC_SCA_RISCV_BIN is
# an escape hatch for a toolchain installed elsewhere (e.g. a Chipyard conda
# env); otherwise riscv64-unknown-elf-* is resolved from PATH, so a native
# install works without editing this file.
TOOLCHAIN_PREFIX ?= $(if $(RISCV),$(RISCV)/bin/riscv64-unknown-elf,$(if $(SPARC_SCA_RISCV_BIN),$(SPARC_SCA_RISCV_BIN)/riscv64-unknown-elf,riscv64-unknown-elf))-

CC = $(TOOLCHAIN_PREFIX)gcc
AS = $(TOOLCHAIN_PREFIX)gcc
LD = $(TOOLCHAIN_PREFIX)gcc
OBJDUMP = $(TOOLCHAIN_PREFIX)objdump

ARCH = rv64g
ABI = lp64

CFLAGS = -march=$(ARCH) -mabi=$(ABI) -O2 -g
CFLAGS += -fno-builtin -nostdlib -nostartfiles -mcmodel=medany -fno-pic
CFLAGS += -Wall -Wextra -Wno-main -Wno-unused-function
CFLAGS += -I.

ASFLAGS = -march=$(ARCH) -mabi=$(ABI) -g

LDFLAGS = -march=$(ARCH) -mabi=$(ABI)
LDFLAGS += -nostdlib -nostartfiles
LDFLAGS += -T link.ld

BUILD_DIR = build
TARGET = $(BUILD_DIR)/rocket_smoke.elf

ASM_SRCS = startup.S
C_SRCS = main.c

.PHONY: all clean

all: $(BUILD_DIR) $(TARGET)
	@echo "Built $(TARGET)"
	@$(OBJDUMP) -d -S $(TARGET) > $(TARGET).dump

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(TARGET): $(ASM_SRCS) $(C_SRCS) | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c -o $(BUILD_DIR)/main.o main.c
	$(AS) $(ASFLAGS) -c -o $(BUILD_DIR)/startup.o startup.S
	$(LD) $(LDFLAGS) -o $@ $(BUILD_DIR)/startup.o $(BUILD_DIR)/main.o

clean:
	rm -rf $(BUILD_DIR)
