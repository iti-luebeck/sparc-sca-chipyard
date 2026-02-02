#!/usr/bin/env python3
"""
Parse CellIFT Taint Report and extract signal names for WAL++ processing.

This script extracts tainted signal names from a CellIFT report and outputs
them in a format suitable for WAL++ FAST MODE signal list processing.

Usage:
    python parse_taint_report.py report.txt -o signals.txt
    python parse_taint_report.py report.txt --scope "TOP.top.core" -o signals.txt
    python parse_taint_report.py report.txt --format csv -o signals.csv
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Set, Optional


class TaintReportParser:
    """Parser for CellIFT Taint Propagation Analysis Reports."""
    
    def __init__(self, report_path: str):
        """
        Initialize parser with report file path.
        
        Args:
            report_path: Path to the taint report file
        """
        self.report_path = Path(report_path)
        self.signals: Set[str] = set()
        self.modules: dict[str, List[str]] = {}
        
    def parse(self) -> None:
        """Parse the taint report and extract signal information."""
        current_module = None
        in_signal_list = False
        
        with open(self.report_path, 'r') as f:
            for line in f:
                line = line.rstrip()
                
                # Detect module header (not indented, ends with :, not a separator line)
                if (line and line.endswith(':') and 
                    not line.startswith(' ') and 
                    not line.startswith('-') and 
                    not line.startswith('=')):
                    # Module name ends with colon
                    module_name = line[:-1].strip()
                    if module_name:
                        current_module = module_name
                        self.modules[current_module] = []
                        in_signal_list = False
                        
                # Detect signal list start (indented line with "Tainted signals")
                elif 'Tainted signals' in line and '(' in line and current_module:
                    in_signal_list = True
                    
                # Parse signal name
                elif in_signal_list and line.strip().startswith('- '):
                    signal_name = line.strip()[2:].strip()
                    if signal_name and current_module:
                        # Construct full hierarchical name
                        full_name = f"{current_module}.{signal_name}"
                        self.signals.add(full_name)
                        self.modules[current_module].append(signal_name)
                        
                # End of module section (empty line while in signal list)
                elif in_signal_list and line.strip() == '':
                    in_signal_list = False
                    # Don't reset current_module yet, in case there are more sections
    
    def get_all_signals(self) -> List[str]:
        """Get all tainted signals across all modules."""
        return sorted(list(self.signals))
    
    def get_signals_by_scope(self, scope_prefix: str) -> List[str]:
        """
        Get tainted signals matching a specific scope prefix.
        
        Args:
            scope_prefix: Hierarchical scope prefix (e.g., "TOP.top.core")
            
        Returns:
            List of signal names matching the scope
        """
        return sorted([sig for sig in self.signals if sig.startswith(scope_prefix)])
    
    def get_module_names(self) -> List[str]:
        """Get list of all module names."""
        return sorted(list(self.modules.keys()))
    
    def get_signals_in_module(self, module_name: str) -> List[str]:
        """
        Get signals within a specific module (without full hierarchy).
        
        Args:
            module_name: Full module name
            
        Returns:
            List of signal names in the module
        """
        return self.modules.get(module_name, [])


def write_output(signals: List[str], output_path: str, format: str = 'list') -> None:
    """
    Write signal list to output file.
    
    Args:
        signals: List of signal names
        output_path: Output file path
        format: Output format ('list' or 'csv')
    """
    with open(output_path, 'w') as f:
        if format == 'list':
            # Simple line-separated list
            for signal in signals:
                f.write(f"{signal}\n")
        elif format == 'csv':
            # CSV format with header
            f.write("signal_name\n")
            for signal in signals:
                f.write(f"{signal}\n")
        else:
            raise ValueError(f"Unknown format: {format}")


def main():
    parser = argparse.ArgumentParser(
        description='Parse CellIFT Taint Report and extract signal names for WAL++ FAST MODE',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all tainted signals
  python parse_taint_report.py report.txt -o signals.txt
  
  # Extract signals from specific scope
  python parse_taint_report.py report.txt --scope "TOP.top.core" -o core_signals.txt
  
  # Output in CSV format
  python parse_taint_report.py report.txt --format csv -o signals.csv
  
  # List all modules
  python parse_taint_report.py report.txt --list-modules
  
  # Use with WAL++ FAST MODE
  python parse_taint_report.py report.txt -o signals.txt
  wal --fast-hd-signals signals.txt trace.vcd -o hd_results.csv
        """
    )
    
    parser.add_argument('report', type=str, help='Path to CellIFT taint report file')
    parser.add_argument('-o', '--output', type=str, help='Output file path')
    parser.add_argument('--scope', type=str, help='Filter signals by scope prefix')
    parser.add_argument('--format', choices=['list', 'csv'], default='list',
                       help='Output format (default: list)')
    parser.add_argument('--list-modules', action='store_true',
                       help='List all module names and exit')
    parser.add_argument('--stats', action='store_true',
                       help='Print statistics about tainted signals')
    
    args = parser.parse_args()
    
    # Parse report
    report_parser = TaintReportParser(args.report)
    
    try:
        report_parser.parse()
    except FileNotFoundError:
        print(f"Error: Report file not found: {args.report}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error parsing report: {e}", file=sys.stderr)
        return 1
    
    # Handle --list-modules
    if args.list_modules:
        modules = report_parser.get_module_names()
        print(f"Found {len(modules)} modules with tainted signals:\n")
        for module in modules:
            signal_count = len(report_parser.get_signals_in_module(module))
            print(f"{module} ({signal_count} signals)")
        return 0
    
    # Get signals
    if args.scope:
        signals = report_parser.get_signals_by_scope(args.scope)
        print(f"Found {len(signals)} tainted signals in scope: {args.scope}")
    else:
        signals = report_parser.get_all_signals()
        print(f"Found {len(signals)} total tainted signals")
    
    # Print statistics
    if args.stats:
        modules = report_parser.get_module_names()
        print(f"\nStatistics:")
        print(f"  Total modules: {len(modules)}")
        print(f"  Total signals: {len(signals)}")
        if modules:
            avg_signals = len(signals) / len(modules)
            print(f"  Average signals per module: {avg_signals:.1f}")
    
    # Write output
    if args.output:
        try:
            write_output(signals, args.output, args.format)
            print(f"Signal list written to: {args.output}")
        except Exception as e:
            print(f"Error writing output: {e}", file=sys.stderr)
            return 1
    else:
        # Print to stdout if no output file specified
        for signal in signals:
            print(signal)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
