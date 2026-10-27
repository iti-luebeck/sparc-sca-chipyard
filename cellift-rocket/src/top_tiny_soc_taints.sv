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

  // CellIFT leakage counters, PER CYCLE, taken straight from the instrumented
  // netlist's own top-level outputs -- the counters the cellift pass
  // synthesises and then aggregates bottom-up over every taint-carrying module.
  //
  // These used to be computed HERE instead, by accumulating
  // `tainted_rf_write | tainted_addr`: two hand-picked signals (the
  // register-file write data gated by rf_wen, and the D-cache request
  // address). That was a workaround, and it hid a real defect. The pass chose
  // its top module by taking the last entry of a topological sort, which on
  // this design selected a dead `$paramod...plusarg_reader` leaf -- so the
  // netlist's own HW counter came out tied to 32'd0 and NO HD counter was
  // emitted at all, while `rocket_mem_top` got nothing. With the pass reading
  // Yosys's `top` attribute instead, all 280 modules are instrumented
  // (516324 HW / 490969 HD bits) and aggregate to the ports connected below.
  //
  // Consequence for the analysis: these are PER-CYCLE values now, not running
  // totals, which is what Ibex and Proteus already emitted. `delta()` in
  // tvla_analysis.py detects this per column, so nothing downstream needs a
  // flag -- but a second difference would be taken if it did not, which is why
  // that detection is by monotonicity and not by core name.
  output logic [31:0] leakage_counter_t0,
  output logic [31:0] hamming_weight_counter_t0,
  output logic [31:0] hamming_distance_counter_t0
);

  // Receivers for the instrumented netlist's aggregated counter outputs.
  logic [31:0] core_hw_counter_t0;
  logic [31:0] core_hd_counter_t0;
  logic [31:0] core_leakage_counter_t0;

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
    .data_i_t0(mem_rdata_t0),

    // The pass's own aggregated counters, for the whole instrumented design.
    .hamming_weight_counter_t0(core_hw_counter_t0),
    .hamming_distance_counter_t0(core_hd_counter_t0),
    .leakage_counter_t0(core_leakage_counter_t0)
  );

  assign hamming_weight_counter_t0   = core_hw_counter_t0;
  assign hamming_distance_counter_t0 = core_hd_counter_t0;
  assign leakage_counter_t0          = core_leakage_counter_t0;

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
  // CellIFT leakage counters
  //
  // Nothing is computed here any more. The three counters are the instrumented
  // netlist's own aggregated outputs, connected on the `i_mem_top` instance
  // above and passed straight through.
  //
  // What used to sit here was a hand-written accumulator over
  // `tainted_rf_write | tainted_addr` -- the register-file write data gated by
  // `rf_wen`, OR'd with the D-cache request address taint -- reached through
  // deep hierarchical references into
  // `i_mem_top.i_chip_top.system.tile_prci_domain.tile_reset_domain.tile.core`.
  // It was a reasonable workaround for a netlist whose own counters were
  // broken (see the port comment at the top of this file), and the two signals
  // it chose were well argued: the D-cache request address is exactly the
  // channel a masked lookup table leaks through, since the S-box index is
  // key-dependent whether or not the value is masked.
  //
  // But it measured ~104 bits where the pass now measures 516324, so it was
  // not the framework's HW/HD metric and was not comparable with Ibex's or
  // Proteus's. Any result derived from it is a statement about those two
  // signals alone. Removed rather than kept alongside, so there is exactly one
  // definition of HW/HD per core.
  //
  // The hierarchical paths are also gone, which is a second benefit: they bound
  // this wrapper to one specific Rocket elaboration and broke silently -- as an
  // X, not an error -- whenever the Chisel hierarchy moved.
  ////////////////////////////////////////////////////

endmodule
