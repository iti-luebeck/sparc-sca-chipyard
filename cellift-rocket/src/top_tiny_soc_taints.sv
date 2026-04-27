// Copyright 2022 Flavien Solt, ETH Zurich.
// Licensed under the General Public License, Version 3.0, see LICENSE for details.
// SPDX-License-Identifier: GPL-3.0-only

// Toplevel module with taints.

module top_tiny_soc #(
    parameter int unsigned NumTaints = 1,

    parameter int unsigned NumWords = 1 << 17,
    parameter int unsigned AddrWidth = 32,
    parameter int unsigned DataWidth = 64,

    parameter int unsigned StrbWidth = DataWidth >> 3,
    localparam type addr_t = logic [AddrWidth-1:0],
    localparam type data_t = logic [DataWidth-1:0],
    localparam type strb_t = logic [StrbWidth-1:0]
) (
  input logic clk_i,
  input logic rst_ni,

  // End-of-benchmark signaling interface,
  output logic [30:0] mmio_aw_addr_o,
  output logic mmio_aw_valid_o,

  output data_t mem_rdata_o, // To prevent the whole internal logic from being optimized out.

  // CellIFT cumulative leakage counters (driven from memory-bus taint signals).
  // leakage_counter_t0:          cycles where any taint bit on the memory bus is nonzero.
  // hamming_weight_counter_t0:   cumulative popcount of all memory-bus taint bits per cycle.
  // hamming_distance_counter_t0: cumulative popcount of cycle-to-cycle transitions in taint bits.
  output logic [31:0] leakage_counter_t0,
  output logic [31:0] hamming_weight_counter_t0,
  output logic [31:0] hamming_distance_counter_t0
);

  logic  mem_req;
  logic  mem_gnt;
  addr_t mem_addr;
  data_t mem_wdata;
  strb_t mem_strb;
  logic  mem_we;

  logic  mem_req_t0;
  logic  mem_gnt_t0;
  addr_t mem_addr_t0;
  data_t mem_wdata_t0;
  strb_t mem_strb_t0;
  logic  mem_we_t0;
  data_t mem_rdata_t0;

  rocket_mem_top i_mem_top (
    .clock(clk_i),
    .reset_wire_reset(~rst_ni),

    .mmio_aw_addr(mmio_aw_addr_o),
    .mmio_aw_valid(mmio_aw_valid_o),
    .mmio_aw_addr_t0(),
    .mmio_aw_valid_t0(),
    .mmio_aw_addr_leak0(),
    .mmio_aw_valid_leak0(),

    .req_o(mem_req),
    .req_o_t0(mem_req_t0),
    .we_o(mem_we),
    .we_o_t0(mem_we_t0),
    .addr_o(mem_addr),
    .addr_o_t0(mem_addr_t0),
    .be_o(mem_strb),
    .be_o_t0(mem_strb_t0),
    .data_o(mem_wdata),
    .data_o_t0(mem_wdata_t0),
    .data_i(mem_rdata_o),
    .data_i_t0(mem_rdata_t0)
  );

  ///////////////////////////////
  // Instruction SRAM instance //
  ///////////////////////////////

  ift_sram_mem #(
    .Width(DataWidth),
    .Depth(NumWords),
    .NumTaints(NumTaints),
    .RelocateRequestUp(64'h10000000) // 80000000 >> 3
  ) i_sram (
    .clk_i,
    .rst_ni,

    .req_i(mem_req),
    .write_i(mem_we),
    .addr_i(mem_addr >> 3), // 64-bit words
    .wdata_i(mem_wdata),
    .wmask_i({{8{mem_strb[7]}}, {8{mem_strb[6]}}, {8{mem_strb[5]}}, {8{mem_strb[4]}}, {8{mem_strb[3]}}, {8{mem_strb[2]}}, {8{mem_strb[1]}}, {8{mem_strb[0]}}}),
    .rdata_o(mem_rdata_o),

    .req_i_t0(mem_req_t0),
    .write_i_t0(mem_we_t0),
    .addr_i_t0(mem_addr_t0 >> 3), // 64-bit words
    .wdata_i_t0(mem_wdata_t0),
    .wmask_i_t0({{8{mem_strb_t0[7]}}, {8{mem_strb_t0[6]}}, {8{mem_strb_t0[5]}}, {8{mem_strb_t0[4]}}, {8{mem_strb_t0[3]}}, {8{mem_strb_t0[2]}}, {8{mem_strb_t0[1]}}, {8{mem_strb_t0[0]}}}),
    .rdata_o_t0(mem_rdata_t0)
  );

  ////////////////////////////////////////////////////
  // CellIFT cumulative leakage counters
  //
  // LC  — any taint on the external AXI4 bus OR on the D-cache request interface.
  //
  // HW  — $countones(tainted_access) per cycle, where tainted_access combines:
  //         1. RF write data taint  — rf_MPORT_data & rf_MPORT_data_t0 gated by rf_wen
  //            captures: ALU results on tainted operands, load results from D-cache.
  //         2. D-cache request address taint — io_dmem_req_bits_addr & addr_t0
  //            captures: S-box table-lookup addresses (key ^ state → address).
  //            SOFTWARE MASKING CANNOT HIDE THIS: the S-box index is key-dependent
  //            regardless of whether the data value is masked.
  //            This is the dominant leakage path in masked AES implementations.
  //
  // HD  — transitions in tainted_access between consecutive cycles.
  //
  // Signal paths verified in generated/out/cellift.sv (module Rocket):
  //   output [63:0] rf_MPORT_data        (line 112165)
  //   output [63:0] rf_MPORT_data_t0     (line 112166)
  //   output        rf_wen               (line 112174)
  //   output [39:0] io_dmem_req_bits_addr    (line 111549)
  //   output [39:0] io_dmem_req_bits_addr_t0 (line 111550, = {msb_2_t0, alu_adder_out_t0[38:0]})
  ////////////////////////////////////////////////////

  localparam int unsigned CoreAddrWidth = 40; // Rocket physical address width

  // LC: external AXI4 bus taint (unchanged from original).
  localparam int unsigned TaintWidth = 1 + 1 + AddrWidth + StrbWidth + DataWidth + DataWidth;
  logic [TaintWidth-1:0] taint_state;
  assign taint_state = {mem_req_t0, mem_we_t0, mem_addr_t0, mem_strb_t0, mem_wdata_t0, mem_rdata_t0};

  // tainted_rf_write: register-file write leakage signal, gated by rf_wen.
  logic [DataWidth-1:0] tainted_rf_write;
  logic                 rf_wen_core;

  assign rf_wen_core    = i_mem_top.i_chip_top.system.tile_prci_domain
                            .tile_reset_domain.tile.core.rf_wen;
  assign tainted_rf_write = rf_wen_core
                ? i_mem_top.i_chip_top.system.tile_prci_domain
                  .tile_reset_domain.tile.core.rf_MPORT_data_leak0
                            : '0;

  // tainted_addr: D-cache request address taint (zero-padded to DataWidth).
  // Fires on EVERY memory request where the address is key-dependent —
  // including S-box loads where the index = f(key, state) is never masked.
  logic [DataWidth-1:0] tainted_addr;
  assign tainted_addr = {{(DataWidth-CoreAddrWidth){1'b0}},
                          i_mem_top.i_chip_top.system.tile_prci_domain
                            .tile_reset_domain.tile.core.io_dmem_req_bits_addr[CoreAddrWidth-1:0]
                        & i_mem_top.i_chip_top.system.tile_prci_domain
                            .tile_reset_domain.tile.core.io_dmem_req_bits_addr_t0[CoreAddrWidth-1:0]};

  // tainted_access: combined leakage signal for HW/HD counters.
  logic [DataWidth-1:0] tainted_access;
  logic [DataWidth-1:0] tainted_access_prev;
  assign tainted_access = tainted_rf_write | tainted_addr;

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      leakage_counter_t0          <= '0;
      hamming_weight_counter_t0   <= '0;
      hamming_distance_counter_t0 <= '0;
      tainted_access_prev         <= '0;
    end else begin
      if (|taint_state || |tainted_access)
        leakage_counter_t0 <= leakage_counter_t0 + 32'd1;
      hamming_weight_counter_t0   <= hamming_weight_counter_t0
                                       + 32'($countones(tainted_access));
      hamming_distance_counter_t0 <= hamming_distance_counter_t0
                                       + 32'($countones(tainted_access ^ tainted_access_prev));
      tainted_access_prev <= tainted_access;
    end
  end

endmodule
