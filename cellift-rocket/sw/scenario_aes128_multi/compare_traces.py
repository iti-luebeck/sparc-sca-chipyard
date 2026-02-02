#!/usr/bin/env python3
"""
Compare two WAL++ traces (HD or HW).

Loads two traces, plots both, calculates the difference, and displays
all three in a single figure.

Usage:
    python3 compare_traces.py trace1.csv trace2.csv
    python3 compare_traces.py trace1.csv trace2.csv -o comparison.png
    python3 compare_traces.py tainted_hd.csv all_hd.csv --labels "Tainted" "All Signals"
"""

import argparse
import sys
import os
import numpy as np

def load_trace(filepath):
    """Load a WAL++ CSV trace file."""
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(',')
            try:
                # Handle both single column and multi-column formats
                # Take the last column as the value
                data.append(float(parts[-1]))
            except ValueError:
                continue
    return np.array(data)


def main():
    parser = argparse.ArgumentParser(
        description='Compare two WAL++ traces and plot the difference',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 compare_traces.py tainted_hd.csv all_hd.csv
    python3 compare_traces.py trace1.csv trace2.csv -o comparison.png
    python3 compare_traces.py tainted.csv all.csv --labels "Tainted Signals" "All Signals"
"""
    )
    
    parser.add_argument('trace1', help='First trace CSV file')
    parser.add_argument('trace2', help='Second trace CSV file')
    parser.add_argument('-o', '--output', help='Output plot file (PNG, PDF, etc.)')
    parser.add_argument('--labels', nargs=2, default=None,
                        help='Labels for the two traces (default: filenames)')
    parser.add_argument('--title', default=None, help='Plot title')
    parser.add_argument('--figsize', nargs=2, type=float, default=[14, 10],
                        help='Figure size (width height), default: 14 10')
    parser.add_argument('--dpi', type=int, default=150, help='Output DPI (default: 150)')
    parser.add_argument('--diff-mode', choices=['subtract', 'abs', 'percent'], 
                        default='subtract',
                        help='Difference mode: subtract (T1-T2), abs (|T1-T2|), percent (default: subtract)')
    parser.add_argument('--no-show', action='store_true', 
                        help='Do not display the plot (useful for batch processing)')
    parser.add_argument('--xlim', nargs=2, type=int, default=None,
                        help='X-axis limits (start end cycles)')
    
    args = parser.parse_args()
    
    # Check files exist
    for f in [args.trace1, args.trace2]:
        if not os.path.exists(f):
            print(f"Error: File not found: {f}", file=sys.stderr)
            sys.exit(1)
    
    # Import matplotlib
    try:
        import matplotlib
        if args.no_show or args.output:
            matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("Error: matplotlib is required. Install with: pip install matplotlib", file=sys.stderr)
        sys.exit(1)
    
    # Load traces
    print(f"Loading {args.trace1}...")
    trace1 = load_trace(args.trace1)
    print(f"  Loaded {len(trace1)} samples")
    
    print(f"Loading {args.trace2}...")
    trace2 = load_trace(args.trace2)
    print(f"  Loaded {len(trace2)} samples")
    
    # Handle different lengths
    min_len = min(len(trace1), len(trace2))
    if len(trace1) != len(trace2):
        print(f"Warning: Traces have different lengths ({len(trace1)} vs {len(trace2)})")
        print(f"         Using first {min_len} samples for comparison")
        trace1 = trace1[:min_len]
        trace2 = trace2[:min_len]
    
    # Calculate difference
    if args.diff_mode == 'subtract':
        diff = trace1 - trace2
        diff_label = 'Difference (Trace1 - Trace2)'
    elif args.diff_mode == 'abs':
        diff = np.abs(trace1 - trace2)
        diff_label = 'Absolute Difference |Trace1 - Trace2|'
    elif args.diff_mode == 'percent':
        # Avoid division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            diff = np.where(trace2 != 0, 
                           100 * (trace1 - trace2) / trace2, 
                           np.where(trace1 != 0, 100, 0))
        diff_label = 'Percent Difference (%)'
    
    # Set up labels
    if args.labels:
        label1, label2 = args.labels
    else:
        label1 = os.path.basename(args.trace1)
        label2 = os.path.basename(args.trace2)
    
    # Create figure with 3 subplots
    fig, axes = plt.subplots(3, 1, figsize=tuple(args.figsize), sharex=True)
    
    cycles = np.arange(min_len)
    
    # Apply xlim if specified
    if args.xlim:
        xlim_start, xlim_end = args.xlim
        mask = (cycles >= xlim_start) & (cycles <= xlim_end)
        plot_cycles = cycles[mask]
        plot_trace1 = trace1[mask]
        plot_trace2 = trace2[mask]
        plot_diff = diff[mask]
    else:
        plot_cycles = cycles
        plot_trace1 = trace1
        plot_trace2 = trace2
        plot_diff = diff
    
    # Plot trace 1
    axes[0].plot(plot_cycles, plot_trace1, color='steelblue', linewidth=0.5, alpha=0.8)
    axes[0].set_ylabel(label1)
    axes[0].grid(True, alpha=0.3)
    axes[0].set_title(label1)
    
    # Add stats
    stats1 = f'Mean: {plot_trace1.mean():.2f}, Max: {plot_trace1.max():.0f}, Min: {plot_trace1.min():.0f}'
    axes[0].text(0.98, 0.95, stats1, transform=axes[0].transAxes, fontsize=8,
                 verticalalignment='top', horizontalalignment='right',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Plot trace 2
    axes[1].plot(plot_cycles, plot_trace2, color='darkorange', linewidth=0.5, alpha=0.8)
    axes[1].set_ylabel(label2)
    axes[1].grid(True, alpha=0.3)
    axes[1].set_title(label2)
    
    # Add stats
    stats2 = f'Mean: {plot_trace2.mean():.2f}, Max: {plot_trace2.max():.0f}, Min: {plot_trace2.min():.0f}'
    axes[1].text(0.98, 0.95, stats2, transform=axes[1].transAxes, fontsize=8,
                 verticalalignment='top', horizontalalignment='right',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Plot difference
    # Use red for positive, blue for negative differences
    if args.diff_mode == 'subtract':
        axes[2].fill_between(plot_cycles, 0, plot_diff, 
                            where=(plot_diff >= 0), color='red', alpha=0.5, label='Trace1 > Trace2')
        axes[2].fill_between(plot_cycles, 0, plot_diff, 
                            where=(plot_diff < 0), color='blue', alpha=0.5, label='Trace1 < Trace2')
        axes[2].axhline(y=0, color='black', linewidth=0.5, linestyle='-')
        axes[2].legend(loc='upper right', fontsize=8)
    else:
        axes[2].plot(plot_cycles, plot_diff, color='green', linewidth=0.5, alpha=0.8)
        axes[2].fill_between(plot_cycles, 0, plot_diff, color='green', alpha=0.3)
    
    axes[2].set_ylabel('Difference')
    axes[2].set_xlabel('Cycle')
    axes[2].grid(True, alpha=0.3)
    axes[2].set_title(diff_label)
    
    # Add diff stats
    if args.diff_mode == 'percent':
        stats_diff = f'Mean: {plot_diff.mean():.2f}%, Max: {plot_diff.max():.2f}%, Min: {plot_diff.min():.2f}%'
    else:
        stats_diff = f'Mean: {plot_diff.mean():.2f}, Max: {plot_diff.max():.0f}, Min: {plot_diff.min():.0f}'
    axes[2].text(0.98, 0.95, stats_diff, transform=axes[2].transAxes, fontsize=8,
                 verticalalignment='top', horizontalalignment='right',
                 bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    
    # Overall title
    if args.title:
        fig.suptitle(args.title, fontsize=14, fontweight='bold')
    else:
        fig.suptitle('Trace Comparison', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    # Print summary
    print()
    print("=" * 50)
    print("Comparison Summary")
    print("=" * 50)
    print(f"  {label1}:")
    print(f"    Mean: {trace1.mean():.2f}, Std: {trace1.std():.2f}")
    print(f"    Min: {trace1.min():.0f}, Max: {trace1.max():.0f}")
    print()
    print(f"  {label2}:")
    print(f"    Mean: {trace2.mean():.2f}, Std: {trace2.std():.2f}")
    print(f"    Min: {trace2.min():.0f}, Max: {trace2.max():.0f}")
    print()
    print(f"  Difference ({args.diff_mode}):")
    print(f"    Mean: {diff.mean():.2f}, Std: {diff.std():.2f}")
    print(f"    Min: {diff.min():.2f}, Max: {diff.max():.2f}")
    print(f"    Non-zero samples: {np.count_nonzero(diff)} / {len(diff)} ({100*np.count_nonzero(diff)/len(diff):.1f}%)")
    
    # Correlation
    if trace1.std() > 0 and trace2.std() > 0:
        correlation = np.corrcoef(trace1, trace2)[0, 1]
        print(f"    Correlation: {correlation:.4f}")
    print()
    
    # Save or show
    if args.output:
        plt.savefig(args.output, dpi=args.dpi, bbox_inches='tight')
        print(f"Saved: {args.output}")
    
    if not args.no_show and not args.output:
        plt.show()
    elif not args.no_show:
        plt.show()
    
    plt.close()


if __name__ == '__main__':
    main()
