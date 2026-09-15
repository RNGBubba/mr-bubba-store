#!/usr/bin/env python3
"""
Database Reports Generator for Mr Bubba Services
Generates professional reports with charts, summaries, and insights from CSV or database data.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from sqlalchemy import create_engine, inspect


class DatabaseReportGenerator:
    """Generate professional reports from CSV or database sources."""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.charts_dir = self.output_dir / "charts"
        self.charts_dir.mkdir(exist_ok=True)
        self.chart_paths = []
        self.insights = []

    def load_from_csv(self, filepath: str) -> pd.DataFrame:
        """Load data from a CSV file."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {filepath}")
        df = pd.read_csv(filepath)
        print(f"Loaded {len(df)} rows from {filepath}")
        return df

    def load_from_database(self, connection_string: str, query: str) -> pd.DataFrame:
        """Load data from a database using SQLAlchemy."""
        engine = create_engine(connection_string)
        df = pd.read_sql(query, engine)
        print(f"Loaded {len(df)} rows from database query")
        return df

    def analyze_dataframe(self, df: pd.DataFrame) -> dict:
        """Perform comprehensive analysis on a DataFrame."""
        analysis = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "numeric_summary": {},
            "categorical_summary": {},
            "missing_values": df.isnull().sum().to_dict(),
            "duplicates": df.duplicated().sum(),
        }

        # Numeric column analysis
        numeric_cols = df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            analysis["numeric_summary"][col] = {
                "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                "median": float(df[col].median()) if not df[col].isnull().all() else None,
                "std": float(df[col].std()) if not df[col].isnull().all() else None,
                "min": float(df[col].min()) if not df[col].isnull().all() else None,
                "max": float(df[col].max()) if not df[col].isnull().all() else None,
                "q25": float(df[col].quantile(0.25)) if not df[col].isnull().all() else None,
                "q75": float(df[col].quantile(0.75)) if not df[col].isnull().all() else None,
            }

        # Categorical column analysis
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            value_counts = df[col].value_counts()
            analysis["categorical_summary"][col] = {
                "unique_values": int(df[col].nunique()),
                "top_values": value_counts.head(10).to_dict(),
                "most_common": value_counts.index[0] if len(value_counts) > 0 else None,
            }

        return analysis

    def generate_insights(self, df: pd.DataFrame, analysis: dict) -> list:
        """Generate actionable insights from the data analysis."""
        insights = []

        # Missing data insights
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()
        missing_pct = (missing_cells / total_cells) * 100 if total_cells > 0 else 0
        if missing_pct > 5:
            insights.append(f"⚠️ {missing_pct:.1f}% of data is missing ({missing_cells}/{total_cells} cells). Consider data cleaning before analysis.")
        else:
            insights.append(f"✅ Data quality is good — only {missing_pct:.1f}% missing values.")

        # Duplicate insights
        if analysis["duplicates"] > 0:
            dup_pct = (analysis["duplicates"] / len(df)) * 100
            insights.append(f"⚠️ {analysis['duplicates']} duplicate rows detected ({dup_pct:.1f}% of total).")

        # Numeric insights
        for col, stats in analysis["numeric_summary"].items():
            if stats["std"] and stats["mean"] and stats["mean"] != 0:
                cv = (stats["std"] / abs(stats["mean"])) * 100
                if cv > 100:
                    insights.append(f"📊 '{col}' has high variability (CV={cv:.1f}%). Data is widely dispersed.")
                elif cv < 10:
                    insights.append(f"📊 '{col}' is very consistent (CV={cv:.1f}%). Values cluster tightly.")

        # Skewness insights
        for col in df.select_dtypes(include=['number']).columns:
            skewness = df[col].skew()
            if abs(skewness) > 2:
                direction = "right" if skewness > 0 else "left"
                insights.append(f"📈 '{col}' is heavily {direction}-skewed (skewness={skewness:.2f}). Consider log transformation.")

        # Categorical insights
        for col, stats in analysis["categorical_summary"].items():
            if stats["unique_values"] == len(df):
                insights.append(f"🔑 '{col}' appears to be a unique identifier ({stats['unique_values']} unique values).")
            elif stats["unique_values"] <= 5:
                top = stats["most_common"]
                count = stats["top_values"].get(top, 0)
                pct = (count / len(df)) * 100
                insights.append(f"🏷️ '{col}' has {stats['unique_values']} categories. Most common: '{top}' ({pct:.1f}%).")

        # Correlation insights
        numeric_df = df.select_dtypes(include=['number'])
        if len(numeric_df.columns) >= 2:
            corr_matrix = numeric_df.corr()
            high_corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    corr_val = corr_matrix.iloc[i, j]
                    if abs(corr_val) > 0.8:
                        high_corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_val))
            for col1, col2, corr in high_corr_pairs[:5]:
                insights.append(f"🔗 Strong correlation between '{col1}' and '{col2}' (r={corr:.2f}).")

        return insights

    def create_distribution_chart(self, df: pd.DataFrame, column: str) -> str:
        """Create a histogram/distribution chart for a numeric column."""
        fig, ax = plt.subplots(figsize=(10, 6))
        data = df[column].dropna()
        ax.hist(data, bins=30, color='#2563eb', alpha=0.7, edgecolor='white')
        ax.set_title(f'Distribution of {column}', fontsize=14, fontweight='bold')
        ax.set_xlabel(column, fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.grid(axis='y', alpha=0.3)
        plt.tight_layout()

        chart_path = str(self.charts_dir / f"dist_{column}.png")
        fig.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        self.chart_paths.append(chart_path)
        return chart_path

    def create_bar_chart(self, df: pd.DataFrame, column: str, top_n: int = 15) -> str:
        """Create a bar chart for a categorical column."""
        fig, ax = plt.subplots(figsize=(10, 6))
        value_counts = df[column].value_counts().head(top_n)
        bars = ax.barh(range(len(value_counts)), value_counts.values, color='#2563eb', alpha=0.8)
        ax.set_yticks(range(len(value_counts)))
        ax.set_yticklabels([str(v)[:30] for v in value_counts.index], fontsize=10)
        ax.set_title(f'Top {top_n} Values: {column}', fontsize=14, fontweight='bold')
        ax.set_xlabel('Count', fontsize=12)
        ax.grid(axis='x', alpha=0.3)
        plt.tight_layout()

        chart_path = str(self.charts_dir / f"bar_{column}.png")
        fig.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        self.chart_paths.append(chart_path)
        return chart_path

    def create_correlation_heatmap(self, df: pd.DataFrame) -> str:
        """Create a correlation heatmap for numeric columns."""
        numeric_df = df.select_dtypes(include=['number'])
        if len(numeric_df.columns) < 2:
            return None

        fig, ax = plt.subplots(figsize=(10, 8))
        corr_matrix = numeric_df.corr()
        im = ax.imshow(corr_matrix, cmap='RdBu_r', vmin=-1, vmax=1)
        ax.set_xticks(range(len(corr_matrix.columns)))
        ax.set_yticks(range(len(corr_matrix.columns)))
        ax.set_xticklabels(corr_matrix.columns, rotation=45, ha='right', fontsize=9)
        ax.set_yticklabels(corr_matrix.columns, fontsize=9)
        ax.set_title('Correlation Heatmap', fontsize=14, fontweight='bold')
        fig.colorbar(im, ax=ax, shrink=0.8)
        plt.tight_layout()

        chart_path = str(self.charts_dir / "correlation_heatmap.png")
        fig.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        self.chart_paths.append(chart_path)
        return chart_path

    def create_time_series_chart(self, df: pd.DataFrame, date_col: str, value_col: str) -> str:
        """Create a time series chart."""
        fig, ax = plt.subplots(figsize=(12, 6))
        df_copy = df.copy()
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
        df_copy = df_copy.dropna(subset=[date_col]).sort_values(date_col)
        ax.plot(df_copy[date_col], df_copy[value_col], color='#2563eb', linewidth=1.5, alpha=0.8)
        ax.fill_between(df_copy[date_col], df_copy[value_col], alpha=0.1, color='#2563eb')
        ax.set_title(f'{value_col} over Time', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel(value_col, fontsize=12)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.tick_params(axis='x', rotation=45)
        ax.grid(alpha=0.3)
        plt.tight_layout()

        chart_path = str(self.charts_dir / f"ts_{date_col}_{value_col}.png")
        fig.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        self.chart_paths.append(chart_path)
        return chart_path

    def create_summary_dashboard(self, df: pd.DataFrame, analysis: dict) -> str:
        """Create a summary dashboard image."""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Data Summary Dashboard', fontsize=16, fontweight='bold', y=0.98)

        # 1. Data overview text
        ax = axes[0, 0]
        ax.axis('off')
        overview_text = (
            f"Dataset Overview\n"
            f"{'─' * 30}\n"
            f"Rows: {analysis['total_rows']:,}\n"
            f"Columns: {analysis['total_columns']}\n"
            f"Duplicates: {analysis['duplicates']:,}\n"
            f"Missing Cells: {sum(analysis['missing_values'].values()):,}\n"
        )
        ax.text(0.1, 0.5, overview_text, transform=ax.transAxes, fontsize=12,
                verticalalignment='center', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='#f0f9ff', alpha=0.8))

        # 2. Missing values bar chart
        ax = axes[0, 1]
        missing = pd.Series(analysis['missing_values']).sort_values(ascending=False)
        missing = missing[missing > 0]
        if len(missing) > 0:
            missing.head(10).plot(kind='barh', ax=ax, color='#ef4444', alpha=0.7)
            ax.set_title('Top Missing Values', fontsize=11, fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'No Missing Values!', transform=ax.transAxes,
                    fontsize=14, ha='center', va='center', color='green')
            ax.set_title('Missing Values', fontsize=11, fontweight='bold')
        ax.set_xlabel('Count')

        # 3. Numeric distributions mini
        ax = axes[1, 0]
        numeric_cols = list(analysis['numeric_summary'].keys())[:5]
        if numeric_cols:
            stats_data = []
            for col in numeric_cols:
                s = analysis['numeric_summary'][col]
                stats_data.append([s['min'], s['q25'], s['median'], s['q75'], s['max']])
            stats_df = pd.DataFrame(stats_data, columns=['Min', 'Q1', 'Median', 'Q3', 'Max'],
                                    index=numeric_cols)
            stats_df.boxplot(ax=ax, vert=False)
            ax.set_title('Numeric Ranges', fontsize=11, fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'No Numeric Columns', transform=ax.transAxes,
                    fontsize=12, ha='center', va='center')

        # 4. Data types pie chart
        ax = axes[1, 1]
        dtype_counts = {}
        for dtype in analysis['dtypes'].values():
            base_type = dtype.split('(')[0] if '(' in dtype else dtype
            dtype_counts[base_type] = dtype_counts.get(base_type, 0) + 1
        if dtype_counts:
            ax.pie(dtype_counts.values(), labels=dtype_counts.keys(), autopct='%1.0f%%',
                   startangle=90, colors=['#2563eb', '#16a34a', '#dc2626', '#ca8a04', '#9333ea'])
            ax.set_title('Column Types', fontsize=11, fontweight='bold')

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        chart_path = str(self.charts_dir / "summary_dashboard.png")
        fig.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        self.chart_paths.append(chart_path)
        return chart_path

    def generate_html_report(self, df: pd.DataFrame, analysis: dict, insights: list,
                             client_name: str = "Client", report_title: str = "Data Analysis Report") -> str:
        """Generate a complete HTML report."""

        # Generate charts
        self.create_summary_dashboard(df, analysis)

        for col in df.select_dtypes(include=['number']).columns[:5]:
            self.create_distribution_chart(df, col)

        for col in df.select_dtypes(include=['object', 'category']).columns[:3]:
            self.create_bar_chart(df, col)

        self.create_correlation_heatmap(df)

        # Build HTML report
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        charts_html = ""
        for chart_path in self.chart_paths:
            rel_path = os.path.relpath(chart_path, self.output_dir)
            charts_html += f'    <div class="chart-container"><img src="{rel_path}" alt="Chart"></div>\n'

        insights_html = ""
        for insight in insights:
            insights_html += f'    <li>{insight}</li>\n'

        numeric_summary_html = ""
        for col, stats in analysis["numeric_summary"].items():
            numeric_summary_html += f"""
            <tr>
                <td><strong>{col}</strong></td>
                <td>{stats['mean']:.2f}</td>
                <td>{stats['median']:.2f}</td>
                <td>{stats['std']:.2f}</td>
                <td>{stats['min']:.2f}</td>
                <td>{stats['max']:.2f}</td>
            </tr>"""

        categorical_summary_html = ""
        for col, stats in analysis["categorical_summary"].items():
            top_vals = ", ".join([f"{k} ({v})" for k, v in list(stats['top_values'].items())[:5]])
            categorical_summary_html += f"""
            <tr>
                <td><strong>{col}</strong></td>
                <td>{stats['unique_values']}</td>
                <td>{stats['most_common']}</td>
                <td>{top_vals}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_title} - {client_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1f2937; background: #f3f4f6; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: white; padding: 40px; border-radius: 12px; margin-bottom: 30px; }}
        .header h1 {{ font-size: 2.2em; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; font-size: 1.1em; }}
        .section {{ background: white; border-radius: 12px; padding: 30px; margin-bottom: 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #1e40af; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #e5e7eb; }}
        .insights {{ list-style: none; }}
        .insights li {{ padding: 12px 16px; margin-bottom: 8px; background: #f0f9ff; border-left: 4px solid #2563eb; border-radius: 0 8px 8px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
        th {{ background: #f9fafb; font-weight: 600; color: #374151; }}
        tr:hover {{ background: #f9fafb; }}
        .chart-container {{ text-align: center; margin: 20px 0; }}
        .chart-container img {{ max-width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 20px; border-radius: 10px; text-align: center; }}
        .stat-card .value {{ font-size: 2em; font-weight: bold; color: #1e40af; }}
        .stat-card .label {{ color: #6b7280; font-size: 0.9em; margin-top: 5px; }}
        .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{report_title}</h1>
            <p>Prepared for: <strong>{client_name}</strong> | Generated: {timestamp}</p>
            <p>Mr Bubba Services — Professional Data Analysis & Reporting</p>
        </div>

        <div class="section">
            <h2>📊 Key Metrics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="value">{analysis['total_rows']:,}</div>
                    <div class="label">Total Records</div>
                </div>
                <div class="stat-card">
                    <div class="value">{analysis['total_columns']}</div>
                    <div class="label">Data Columns</div>
                </div>
                <div class="stat-card">
                    <div class="value">{len(analysis['numeric_summary'])}</div>
                    <div class="label">Numeric Fields</div>
                </div>
                <div class="stat-card">
                    <div class="value">{len(analysis['categorical_summary'])}</div>
                    <div class="label">Categorical Fields</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>💡 Key Insights</h2>
            <ul class="insights">
{insights_html}            </ul>
        </div>

        <div class="section">
            <h2>📈 Visualizations</h2>
{charts_html}        </div>

        <div class="section">
            <h2>🔢 Numeric Column Summary</h2>
            <table>
                <thead>
                    <tr><th>Column</th><th>Mean</th><th>Median</th><th>Std Dev</th><th>Min</th><th>Max</th></tr>
                </thead>
                <tbody>
{numeric_summary_html}                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>🏷️ Categorical Column Summary</h2>
            <table>
                <thead>
                    <tr><th>Column</th><th>Unique Values</th><th>Most Common</th><th>Top Values</th></tr>
                </thead>
                <tbody>
{categorical_summary_html}                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>⚠️ Data Quality</h2>
            <p><strong>Duplicate Rows:</strong> {analysis['duplicates']:,}</p>
            <p><strong>Missing Values by Column:</strong></p>
            <ul>
                {"".join([f"<li><strong>{col}:</strong> {count:,} missing ({count/analysis['total_rows']*100:.1f}%)</li>" for col, count in analysis['missing_values'].items() if count > 0]) if any(v > 0 for v in analysis['missing_values'].values()) else "<li>✅ No missing values detected.</li>"}
            </ul>
        </div>

        <div class="footer">
            <p>Report generated by Mr Bubba Services | {timestamp}</p>
            <p>For questions about this report, contact: mrbubba@agentmail.to</p>
        </div>
    </div>
</body>
</html>"""

        report_path = str(self.output_dir / "report.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"HTML report saved to: {report_path}")
        return report_path

    def generate(self, data_source: str, source_type: str = "csv",
                 query: str = None, client_name: str = "Client",
                 report_title: str = "Data Analysis Report") -> dict:
        """Main generation pipeline."""

        # Load data
        if source_type == "csv":
            df = self.load_from_csv(data_source)
        elif source_type == "database":
            df = self.load_from_database(data_source, query)
        else:
            raise ValueError(f"Unknown source type: {source_type}")

        # Analyze
        analysis = self.analyze_dataframe(df)
        insights = self.generate_insights(df, analysis)

        # Generate report
        report_path = self.generate_html_report(df, analysis, insights, client_name, report_title)

        # Save analysis as JSON
        json_path = str(self.output_dir / "analysis.json")
        with open(json_path, 'w') as f:
            json.dump({
                "analysis": analysis,
                "insights": insights,
                "generated_at": datetime.now().isoformat(),
                "source": data_source,
            }, f, indent=2, default=str)

        print(f"\n{'='*50}")
        print(f"Report generation complete!")
        print(f"  HTML Report: {report_path}")
        print(f"  Analysis JSON: {json_path}")
        print(f"  Charts: {len(self.chart_paths)} generated")
        print(f"  Insights: {len(insights)} generated")
        print(f"{'='*50}")

        return {
            "report_path": report_path,
            "json_path": json_path,
            "chart_paths": self.chart_paths,
            "insights": insights,
            "analysis": analysis,
        }


def main():
    parser = argparse.ArgumentParser(description="Generate professional data reports")
    parser.add_argument("source", help="Path to CSV file or database connection string")
    parser.add_argument("--type", choices=["csv", "database"], default="csv",
                        help="Data source type (default: csv)")
    parser.add_argument("--query", help="SQL query (for database type)")
    parser.add_argument("--client", default="Client", help="Client name for the report")
    parser.add_argument("--title", default="Data Analysis Report", help="Report title")
    parser.add_argument("--output", default="reports", help="Output directory")

    args = parser.parse_args()

    generator = DatabaseReportGenerator(output_dir=args.output)
    result = generator.generate(
        data_source=args.source,
        source_type=args.type,
        query=args.query,
        client_name=args.client,
        report_title=args.title,
    )

    print(f"\nDone! Open {result['report_path']} to view the report.")


if __name__ == "__main__":
    main()
