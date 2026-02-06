# Gemmini matrix multiplication test (bare-metal)
# Builds using esp-tools RISC-V toolchain with gemmini headers

TOOLCHAIN_PREFIX ?= /mnt/nvme1n1p1/cellift-designs/cellift-chipyard/esp-tools-install/bin/riscv64-unknown-elf-

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
