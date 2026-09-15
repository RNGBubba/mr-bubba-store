#!/usr/bin/env python3
"""
Data Visualization Generator
Reads CSV/Excel files and generates professional charts, graphs, and dashboards.

Usage:
    python3 generate_charts.py <input_file> [--output-dir OUTPUT_DIR] [--chart-type TYPE]

Supported chart types: line, bar, scatter, histogram, pie, heatmap, box, area, dashboard
"""

import argparse
import sys
import os
import json
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
from datetime import datetime

# Professional style configuration
sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams.update({
    'figure.figsize': (12, 7),
    'figure.dpi': 150,
    'font.size': 12,
    'axes.titlesize': 16,
    'axes.labelsize': 13,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'figure.facecolor': 'white',
    'axes.facecolor': '#fafafa',
    'axes.grid': True,
    'grid.alpha': 0.3,
    'axes.spines.top': False,
    'axes.spines.right': False,
})

COLORS = ['#2196F3', '#FF9800', '#4CAF50', '#E91E63', '#9C27B0',
          '#00BCD4', '#FF5722', '#607D8B', '#795548', '#3F51B5']


def load_data(filepath):
    """Load data from CSV or Excel file."""
    ext = Path(filepath).suffix.lower()
    if ext == '.csv':
        return pd.read_csv(filepath)
    elif ext in ('.xlsx', '.xls'):
        return pd.read_excel(filepath, engine='openpyxl')
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use CSV or Excel.")


def detect_columns(df):
    """Detect numeric and categorical columns."""
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    return numeric_cols, categorical_cols, datetime_cols


def save_chart(fig, output_dir, name):
    """Save chart to file."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(output_dir, f"{name}.png")
    fig.savefig(filepath, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return filepath


def generate_line_chart(df, numeric_cols, output_dir):
    """Generate line chart for time series or sequential data."""
    fig, ax = plt.subplots()
    x_col = df.columns[0]
    y_cols = numeric_cols[:5] if len(numeric_cols) >= 1 else [numeric_cols[0]]

    for i, col in enumerate(y_cols):
        ax.plot(df[x_col].values[:100], df[col].values[:100],
                marker='o', markersize=3, linewidth=2, color=COLORS[i % len(COLORS)],
                label=col)

    ax.set_title(f'Line Chart: {", ".join(y_cols)}')
    ax.set_xlabel(x_col)
    ax.set_ylabel('Value')
    ax.legend(loc='best')
    plt.xticks(rotation=45)
    fig.tight_layout()
    return save_chart(fig, output_dir, 'line_chart')


def generate_bar_chart(df, numeric_cols, categorical_cols, output_dir):
    """Generate bar chart comparing categories."""
    fig, ax = plt.subplots()
    cat_col = categorical_cols[0] if categorical_cols else df.columns[0]
    num_col = numeric_cols[0]

    # Aggregate if needed
    if cat_col in df.columns and num_col in df.columns:
        data = df.groupby(cat_col)[num_col].mean().sort_values(ascending=False).head(15)
    else:
        data = df[num_col].value_counts().head(15)

    bars = ax.bar(range(len(data)), data.values,
                  color=COLORS[:len(data)], edgecolor='white', linewidth=0.5)

    ax.set_xticks(range(len(data)))
    ax.set_xticklabels(data.index, rotation=45, ha='right')
    ax.set_title(f'Bar Chart: Average {num_col} by {cat_col}')
    ax.set_xlabel(cat_col)
    ax.set_ylabel(num_col)

    # Add value labels on bars
    for bar, val in zip(bars, data.values):
        ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height(),
                f'{val:,.0f}', ha='center', va='bottom', fontsize=9)

    fig.tight_layout()
    return save_chart(fig, output_dir, 'bar_chart')


def generate_scatter_plot(df, numeric_cols, output_dir):
    """Generate scatter plot for correlation analysis."""
    fig, ax = plt.subplots()

    if len(numeric_cols) >= 2:
        x_col, y_col = numeric_cols[0], numeric_cols[1]
        ax.scatter(df[x_col], df[y_col], alpha=0.6, c=COLORS[0],
                   edgecolors='white', linewidth=0.5, s=60)

        # Add trend line
        z = pd.Series(df[y_col]).dropna()
        x_vals = pd.Series(df[x_col]).dropna()
        if len(z) > 1 and len(x_vals) > 1:
            min_len = min(len(z), len(x_vals))
            try:
                import numpy as np
                z_fit = x_vals.values[:min_len]
                w_fit = z.values[:min_len]
                if len(z_fit) > 1:
                    p = np.polyfit(z_fit, w_fit, 1)
                    trend_x = np.linspace(z_fit.min(), z_fit.max(), 100)
                    ax.plot(trend_x, np.polyval(p, trend_x), '--', color=COLORS[3],
                            linewidth=2, alpha=0.7, label='Trend')
                    ax.legend()
            except Exception:
                pass

        ax.set_title(f'Scatter Plot: {x_col} vs {y_col}')
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
    else:
        ax.text(0.5, 0.5, 'Need at least 2 numeric columns', transform=ax.transAxes,
                ha='center', va='center')

    fig.tight_layout()
    return save_chart(fig, output_dir, 'scatter_plot')


def generate_histogram(df, numeric_cols, output_dir):
    """Generate histogram with distribution analysis."""
    fig, ax = plt.subplots()
    col = numeric_cols[0]
    data = df[col].dropna()

    n_bins = min(30, max(10, len(data) // 10))
    n, bins, patches = ax.hist(data, bins=n_bins, color=COLORS[0],
                                edgecolor='white', linewidth=0.5, alpha=0.85)

    # Color gradient
    for i, patch in enumerate(patches):
        patch.set_facecolor(plt.cm.viridis(i / len(patches)))

    # Add statistics
    mean_val = data.mean()
    median_val = data.median()
    ax.axvline(mean_val, color=COLORS[3], linestyle='--', linewidth=2, label=f'Mean: {mean_val:,.2f}')
    ax.axvline(median_val, color=COLORS[1], linestyle='-.', linewidth=2, label=f'Median: {median_val:,.2f}')
    ax.legend()

    ax.set_title(f'Distribution: {col}')
    ax.set_xlabel(col)
    ax.set_ylabel('Frequency')
    fig.tight_layout()
    return save_chart(fig, output_dir, 'histogram')


def generate_pie_chart(df, numeric_cols, categorical_cols, output_dir):
    """Generate pie chart for proportional data."""
    fig, ax = plt.subplots()
    cat_col = categorical_cols[0] if categorical_cols else df.columns[0]
    num_col = numeric_cols[0]

    data = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False).head(8)

    # Combine small categories
    if len(data) > 6:
        top5 = data.head(5)
        other = pd.Series({'Other': data.tail(len(data) - 5).sum()})
        data = pd.concat([top5, other])

    wedges, texts, autotexts = ax.pie(
        data.values, labels=data.index, autopct='%1.1f%%',
        colors=COLORS[:len(data)], startangle=140,
        wedgeprops={'edgecolor': 'white', 'linewidth': 1.5},
        textprops={'fontsize': 10}
    )
    for autotext in autotexts:
        autotext.set_fontsize(9)

    ax.set_title(f'Proportional Breakdown: {num_col} by {cat_col}')
    fig.tight_layout()
    return save_chart(fig, output_dir, 'pie_chart')


def generate_heatmap(df, numeric_cols, output_dir):
    """Generate correlation heatmap."""
    fig, ax = plt.subplots()
    cols = numeric_cols[:10]
    corr_matrix = df[cols].corr()

    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='RdBu_r',
                center=0, square=True, linewidths=0.5,
                annot_kws={'size': 9}, ax=ax)
    ax.set_title('Correlation Heatmap')
    fig.tight_layout()
    return save_chart(fig, output_dir, 'heatmap')


def generate_box_plot(df, numeric_cols, categorical_cols, output_dir):
    """Generate box plot for distribution comparison."""
    fig, ax = plt.subplots()
    num_col = numeric_cols[0]
    cat_col = categorical_cols[0] if categorical_cols else None

    if cat_col:
        top_cats = df[cat_col].value_counts().head(10).index
        plot_data = df[df[cat_col].isin(top_cats)]
        sns.boxplot(data=plot_data, x=cat_col, y=num_col, palette='Set2', ax=ax)
        ax.set_title(f'Box Plot: {num_col} by {cat_col}')
        plt.xticks(rotation=45, ha='right')
    else:
        sns.boxplot(data=df, y=num_col, color=COLORS[0], ax=ax)
        ax.set_title(f'Box Plot: {num_col} Distribution')

    fig.tight_layout()
    return save_chart(fig, output_dir, 'box_plot')


def generate_area_chart(df, numeric_cols, output_dir):
    """Generate area chart for cumulative/overlapping data."""
    fig, ax = plt.subplots()
    y_cols = numeric_cols[:5]
    x_vals = range(len(df))

    ax.stackplot(x_vals, [df[col].values[:100] for col in y_cols],
                 labels=y_cols, colors=COLORS[:len(y_cols)], alpha=0.7)
    ax.set_title(f'Area Chart: {" + ".join(y_cols)}')
    ax.set_xlabel('Index')
    ax.set_ylabel('Value')
    ax.legend(loc='upper left')
    fig.tight_layout()
    return save_chart(fig, output_dir, 'area_chart')


def generate_dashboard(df, numeric_cols, categorical_cols, datetime_cols, output_dir):
    """Generate comprehensive dashboard with multiple chart types."""
    fig = plt.figure(figsize=(20, 14))
    fig.suptitle('Data Dashboard Overview', fontsize=20, fontweight='bold', y=0.98)

    # Summary statistics panel
    ax0 = fig.add_subplot(2, 3, 1)
    ax0.axis('off')
    summary_text = f"""Dataset Summary
{'=' * 30}
Rows: {len(df):,}
Columns: {len(df.columns)}
Numeric: {len(numeric_cols)}
Categorical: {len(categorical_cols)}

Missing Values: {df.isnull().sum().sum():,}
Duplicates: {df.duplicated().sum():,}
"""
    ax0.text(0.1, 0.5, summary_text, transform=ax0.transAxes,
             fontsize=11, verticalalignment='center', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='#f0f0f0', alpha=0.8))
    ax0.set_title('Summary Statistics', fontweight='bold')

    # Top numeric distributions
    if len(numeric_cols) >= 1:
        ax1 = fig.add_subplot(2, 3, 2)
        sns.histplot(df[numeric_cols[0]].dropna(), kde=True, color=COLORS[0], ax=ax1)
        ax1.set_title(f'Distribution: {numeric_cols[0]}', fontweight='bold')

    if len(numeric_cols) >= 2:
        ax2 = fig.add_subplot(2, 3, 3)
        ax2.scatter(df[numeric_cols[0]], df[numeric_cols[1]],
                    alpha=0.5, c=COLORS[1], edgecolors='white', linewidth=0.3, s=30)
        ax2.set_title(f'{numeric_cols[0]} vs {numeric_cols[1]}', fontweight='bold')
        ax2.set_xlabel(numeric_cols[0])
        ax2.set_ylabel(numeric_cols[1])

    # Bar chart
    if categorical_cols and numeric_cols:
        ax3 = fig.add_subplot(2, 3, 4)
        data = df.groupby(categorical_cols[0])[numeric_cols[0]].mean().sort_values(ascending=True).tail(8)
        data.plot(kind='barh', ax=ax3, color=COLORS[:len(data)], edgecolor='white')
        ax3.set_title(f'Avg {numeric_cols[0]} by {categorical_cols[0]}', fontweight='bold')
        ax3.set_xlabel(numeric_cols[0])

    # Box plot
    if numeric_cols:
        ax4 = fig.add_subplot(2, 3, 5)
        cols_to_plot = numeric_cols[:5]
        df[cols_to_plot].boxplot(ax=ax4, patch_artist=True,
                                 boxprops=dict(facecolor=COLORS[0], alpha=0.7))
        ax4.set_title('Numeric Distributions', fontweight='bold')
        ax4.tick_params(axis='x', rotation=45)

    # Correlation heatmap (top 6 numeric)
    if len(numeric_cols) >= 3:
        ax5 = fig.add_subplot(2, 3, 6)
        cols = numeric_cols[:6]
        corr = df[cols].corr()
        sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
                    square=True, linewidths=0.5, ax=ax5, annot_kws={'size': 8})
        ax5.set_title('Correlation Matrix', fontweight='bold')

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(output_dir, 'dashboard.png')
    fig.savefig(filepath, bbox_inches='tight', facecolor='white', dpi=150)
    plt.close(fig)
    return filepath


def generate_all_charts(df, numeric_cols, categorical_cols, datetime_cols, output_dir):
    """Generate all applicable chart types."""
    generated = []

    if len(numeric_cols) >= 1:
        generated.append(generate_histogram(df, numeric_cols, output_dir))
        generated.append(generate_box_plot(df, numeric_cols, categorical_cols, output_dir))

    if len(numeric_cols) >= 2:
        generated.append(generate_scatter_plot(df, numeric_cols, output_dir))

    if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
        generated.append(generate_bar_chart(df, numeric_cols, categorical_cols, output_dir))
        generated.append(generate_pie_chart(df, numeric_cols, categorical_cols, output_dir))

    if len(numeric_cols) >= 1:
        generated.append(generate_line_chart(df, numeric_cols, output_dir))
        generated.append(generate_area_chart(df, numeric_cols, output_dir))

    if len(numeric_cols) >= 3:
        generated.append(generate_heatmap(df, numeric_cols, output_dir))

    # Always generate dashboard
    generated.append(generate_dashboard(df, numeric_cols, categorical_cols, datetime_cols, output_dir))

    return generated


def main():
    parser = argparse.ArgumentParser(description='Generate professional charts from CSV/Excel data')
    parser.add_argument('input_file', help='Path to input CSV or Excel file')
    parser.add_argument('--output-dir', '-o', default='./charts_output',
                        help='Output directory for generated charts (default: ./charts_output)')
    parser.add_argument('--chart-type', '-t', default='all',
                        choices=['line', 'bar', 'scatter', 'histogram', 'pie',
                                 'heatmap', 'box', 'area', 'dashboard', 'all'],
                        help='Type of chart to generate (default: all)')

    args = parser.parse_args()

    # Validate input
    if not os.path.exists(args.input_file):
        print(f"Error: File '{args.input_file}' not found.")
        sys.exit(1)

    print(f"Loading data from {args.input_file}...")
    df = load_data(args.input_file)
    print(f"Loaded {len(df):,} rows and {len(df.columns)} columns.")

    numeric_cols, categorical_cols, datetime_cols = detect_columns(df)
    print(f"Detected: {len(numeric_cols)} numeric, {len(categorical_cols)} categorical, "
          f"{len(datetime_cols)} datetime columns")

    # Generate charts
    output_dir = os.path.join(args.output_dir, Path(args.input_file).stem)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    chart_map = {
        'line': lambda: generate_line_chart(df, numeric_cols, output_dir),
        'bar': lambda: generate_bar_chart(df, numeric_cols, categorical_cols, output_dir),
        'scatter': lambda: generate_scatter_plot(df, numeric_cols, output_dir),
        'histogram': lambda: generate_histogram(df, numeric_cols, output_dir),
        'pie': lambda: generate_pie_chart(df, numeric_cols, categorical_cols, output_dir),
        'heatmap': lambda: generate_heatmap(df, numeric_cols, output_dir),
        'box': lambda: generate_box_plot(df, numeric_cols, categorical_cols, output_dir),
        'area': lambda: generate_area_chart(df, numeric_cols, output_dir),
        'dashboard': lambda: generate_dashboard(df, numeric_cols, categorical_cols, datetime_cols, output_dir),
    }

    generated = []
    if args.chart_type == 'all':
        generated = generate_all_charts(df, numeric_cols, categorical_cols, datetime_cols, output_dir)
    else:
        if args.chart_type in ['bar', 'pie', 'box'] and not categorical_cols:
            print(f"Warning: {args.chart_type} chart needs categorical columns. Generating histogram instead.")
            generated.append(generate_histogram(df, numeric_cols, output_dir))
        elif args.chart_type == 'heatmap' and len(numeric_cols) < 3:
            print("Warning: heatmap needs 3+ numeric columns. Generating scatter plot instead.")
            generated.append(generate_scatter_plot(df, numeric_cols, output_dir))
        elif args.chart_type == 'scatter' and len(numeric_cols) < 2:
            print("Warning: scatter plot needs 2+ numeric columns. Generating histogram instead.")
            generated.append(generate_histogram(df, numeric_cols, output_dir))
        else:
            generated.append(chart_map[args.chart_type]())

    print(f"\nGenerated {len(generated)} chart(s):")
    for chart_path in generated:
        print(f"  📊 {chart_path}")

    # Save generation report
    report = {
        'timestamp': datetime.now().isoformat(),
        'input_file': args.input_file,
        'output_dir': output_dir,
        'rows': len(df),
        'columns': len(df.columns),
        'numeric_columns': numeric_cols,
        'categorical_columns': categorical_cols,
        'generated_charts': [os.path.basename(p) for p in generated],
    }
    report_path = os.path.join(output_dir, 'generation_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved: {report_path}")

    return generated


if __name__ == '__main__':
    main()
