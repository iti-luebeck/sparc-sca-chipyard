#!/usr/bin/env python3
"""
Post-instrumentation patch for TilePRCIDomain taint propagation.
Adds missing taint signal assignments that CellIFT pass doesn't handle.

The CellIFT pass runs on RTL, but buffer_auto_in_* wires are created during synthesis.
This script patches the final netlist to connect taint signals from inputs to buffer internals.
"""

import sys
import re

def patch_tileprcidomain_taint(infile, outfile):
    """Add missing taint assignments in TilePRCIDomain module."""
    
    with open(infile, 'r') as f:
        content = f.read()
    
    # Map of internal wires that need to be assigned from module inputs
    # These are ALL taint signals for Gemmini DMA/AXI interface
    taint_connections = [
        # AXI-A channel (write address/data) - Full set
        ("buffer_auto_in_0_a_valid_t0", "auto_tl_master_clock_xing_out_0_a_valid_t0"),
        ("buffer_auto_in_0_a_ready_t0", "auto_tl_master_clock_xing_out_0_a_ready_t0"),
        ("buffer_auto_in_0_a_bits_address_t0", "auto_tl_master_clock_xing_out_0_a_bits_address_t0"),
        ("buffer_auto_in_0_a_bits_corrupt_t0", "auto_tl_master_clock_xing_out_0_a_bits_corrupt_t0"),
        ("buffer_auto_in_0_a_bits_data_t0", "auto_tl_master_clock_xing_out_0_a_bits_data_t0"),
        ("buffer_auto_in_0_a_bits_mask_t0", "auto_tl_master_clock_xing_out_0_a_bits_mask_t0"),
        ("buffer_auto_in_0_a_bits_opcode_t0", "auto_tl_master_clock_xing_out_0_a_bits_opcode_t0"),
        ("buffer_auto_in_0_a_bits_param_t0", "auto_tl_master_clock_xing_out_0_a_bits_param_t0"),
        ("buffer_auto_in_0_a_bits_size_t0", "auto_tl_master_clock_xing_out_0_a_bits_size_t0"),
        ("buffer_auto_in_0_a_bits_source_t0", "auto_tl_master_clock_xing_out_0_a_bits_source_t0"),
        
        # AXI-D channel (write response/read data) - Full set
        ("buffer_auto_in_0_d_valid_t0", "auto_tl_master_clock_xing_out_0_d_valid_t0"),
        ("buffer_auto_in_0_d_ready_t0", "auto_tl_master_clock_xing_out_0_d_ready_t0"),
        ("buffer_auto_in_0_d_bits_corrupt_t0", "auto_tl_master_clock_xing_out_0_d_bits_corrupt_t0"),
        ("buffer_auto_in_0_d_bits_data_t0", "auto_tl_master_clock_xing_out_0_d_bits_data_t0"),
        ("buffer_auto_in_0_d_bits_opcode_t0", "auto_tl_master_clock_xing_out_0_d_bits_opcode_t0"),
        ("buffer_auto_in_0_d_bits_param_t0", "auto_tl_master_clock_xing_out_0_d_bits_param_t0"),
        ("buffer_auto_in_0_d_bits_size_t0", "auto_tl_master_clock_xing_out_0_d_bits_size_t0"),
        ("buffer_auto_in_0_d_bits_source_t0", "auto_tl_master_clock_xing_out_0_d_bits_source_t0"),
    ]
    
    # Find TilePRCIDomain module
    module_match = re.search(r'module TilePRCIDomain\(.*?\nendmodule', content, re.DOTALL)
    
    if not module_match:
        print("Warning: Could not find TilePRCIDomain module in netlist")
        with open(outfile, 'w') as f:
            f.write(content)
        return
    
    module_text = module_match.group(0)
    module_start = module_match.start()
    module_end = module_match.end()
    
    # Find where to insert assignments - before the last "endmodule"
    insert_pos = module_text.rfind('\nendmodule')
    if insert_pos == -1:
        print("Error: Could not find endmodule in TilePRCIDomain")
        with open(outfile, 'w') as f:
            f.write(content)
        return
    
    # Build assignment statements
    assignments = []
    for dst_wire, src_wire in taint_connections:
        # Check if wires exist in module
        if f' {dst_wire}' in module_text or f'  {dst_wire}' in module_text:
            # Check if assignment already exists (avoid duplicates)
            if f'assign {dst_wire} = {src_wire}' not in module_text:
                assignments.append(f"  assign {dst_wire} = {src_wire};")
    
    if not assignments:
        print("Info: No new taint assignments needed in TilePRCIDomain")
        with open(outfile, 'w') as f:
            f.write(content)
        return
    
    # Insert assignments before endmodule
    assignment_block = "\n" + "\n".join(assignments) + "\n"
    
    new_module = (
        module_text[:insert_pos] + 
        assignment_block +
        module_text[insert_pos:]
    )
    
    # Replace module in content
    new_content = content[:module_start] + new_module + content[module_end:]
    
    # Write output
    with open(outfile, 'w') as f:
        f.write(new_content)
    
    print(f"Added {len(assignments)} taint assignments to TilePRCIDomain")
    for assign in assignments:
        print(f"  {assign.strip()}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input_sv> <output_sv>")
        sys.exit(1)
    
    infile = sys.argv[1]
    outfile = sys.argv[2]
    
    print(f"Patching {infile} -> {outfile}")
    patch_tileprcidomain_taint(infile, outfile)
    print("Done")

