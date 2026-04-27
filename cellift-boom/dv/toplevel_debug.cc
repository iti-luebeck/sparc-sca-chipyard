// Copyright 2022 Flavien Solt, ETH Zurich.
// Licensed under the General Public License, Version 3.0, see LICENSE for details.
// SPDX-License-Identifier: GPL-3.0-only

// Enhanced toplevel with MMIO debug monitoring

#include "testbench.h"
#include "ticks.h"
#include <iostream>
#include <iomanip>

// Debug MMIO address definitions (must match debug.h)
#define DEBUG_BASE      0x10000000
#define DEBUG_PUTCHAR   (DEBUG_BASE + 0x00)
#define DEBUG_PUTHEX32  (DEBUG_BASE + 0x04)
#define DEBUG_PUTHEX64  (DEBUG_BASE + 0x08)
#define DEBUG_NEWLINE   (DEBUG_BASE + 0x0C)
#define DEBUG_DONE      (DEBUG_BASE + 0xFF)

// MMIO monitoring state
static bool debug_enabled = true;
static bool test_completed = false;
static int exit_code = -1;

/**
 * Monitor MMIO writes for debug output
 * Called every cycle to check if MMIO write occurred
 */
void monitor_mmio_debug(Testbench *tb) {
    if (!debug_enabled) return;

    // Check if MMIO write is valid
    if (tb->module_->mmio_aw_valid_o) {
        // Get the address being written (only 31 bits exposed)
        uint32_t addr = tb->module_->mmio_aw_addr_o;

        // Check if it's a debug command
        if ((addr & 0xFFFFFF00) == (DEBUG_BASE >> 1)) {  // Note: addr is shifted by design
            // For debug output, we need to extract the data from memory writes
            // Since we only have address, we use it to encode both command and data

            // The actual data is in the memory write data, but we can also
            // encode simple operations in the address itself
            std::cout << "[MMIO Write @ 0x" << std::hex << std::setw(8) << std::setfill('0')
                      << (addr << 1) << std::dec << "]" << std::endl;
        }
    }
}

/**
 * Enhanced tick function with MMIO monitoring
 */
class DebugTestbench : public Testbench {
public:
    DebugTestbench(const std::string &trace_filename = "") : Testbench(trace_filename) {}

    void tick_with_debug(int num_ticks = 1) {
        for (int i = 0; i < num_ticks; i++) {
            // Do the normal tick
            this->tick(1);

            // Monitor MMIO after each tick
            monitor_mmio_debug(this);

            // Check for test completion
            if (test_completed) {
                std::cout << "\n=== Test completed with exit code: " << exit_code << " ===" << std::endl;
                break;
            }
        }
    }
};

/**
 * Runs the testbench.
 */
long run_test(DebugTestbench *tb, int simlen) {
    // Enable debug monitoring
    std::cout << "\n=== Starting BOOM simulation with debug monitoring ===" << std::endl;
    std::cout << "=== Monitoring MMIO writes for debug output ===" << std::endl;
    std::cout << "=== Simulation length: " << simlen << " cycles ===" << std::endl << std::endl;

    auto start = std::chrono::steady_clock::now();

    // Reset the system
    tb->reset();

    // Run with MMIO monitoring
    tb->tick_with_debug(simlen);

    auto stop = std::chrono::steady_clock::now();
    long ret = std::chrono::duration_cast<std::chrono::milliseconds>(stop - start).count();

    // Trail ticks
    tb->tick(TRAILTICKS);

    return ret;
}

int main(int argc, char **argv, char **env) {

  Verilated::commandArgs(argc, argv);
  Verilated::traceEverOn(VM_TRACE);

  ////////
  // Get the env vars early to avoid Verilator segfaults.
  ////////

  std::cout << "Starting getting env variables." << std::endl;

  int simlen = get_sim_length_cycles(LEADTICKS);

  ////////
  // Initialize testbench.
  ////////

  DebugTestbench *tb = new DebugTestbench(cl_get_tracefile());

  ////////
  // Run the test with debug monitoring
  ////////

  long duration = run_test(tb, simlen);

#if !VM_TRACE
  std::cout << "Testbench complete!" << std::endl;
  std::cout << "Elapsed time: " << std::dec << duration << "." << std::endl;
#else // VM_TRACE
  std::cout << "Testbench with traces complete!" << std::endl;
  std::cout << "Elapsed time (traces enabled): " << std::dec << duration << "." << std::endl;
#endif // VM_TRACE

  delete tb;
  exit(0);
}
