#!/usr/bin/env python3
"""
Excel Automation Script
Read, write, transform, and analyze Excel files.
"""

import argparse
from pathlib import Path
from datetime import datetime

try:
    import pandas as pd
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def read_excel(input_file, sheet_name=0):
    """Read an Excel file and return a DataFrame."""
    if not HAS_PANDAS:
        print("Error: pandas and openpyxl required for Excel operations.")
        return None
    return pd.read_excel(input_file, sheet_name=sheet_name)


def write_excel(data, output_file, sheet_name='Sheet1', index=False, style=True):
    """Write a DataFrame to Excel with optional styling."""
    if not HAS_PANDAS:
        print("Error: pandas and openpyxl required for Excel operations.")
        return

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        data.to_excel(writer, sheet_name=sheet_name, index=index)

        if style:
            worksheet = writer.sheets[sheet_name]
            # Style header row
            header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            header_font = Font(bold=True, color='FFFFFF')
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center')

            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

    print(f"Excel file saved: {output_file}")
    return output_file


def merge_excel_files(input_files, output_file, on=None, how='inner'):
    """Merge multiple Excel files (or sheets) on a common column."""
    if not HAS_PANDAS:
        print("Error: pandas and openpyxl required for Excel operations.")
        return

    frames = [pd.read_excel(f) for f in input_files]

    if on:
        result = frames[0]
        for frame in frames[1:]:
            result = result.merge(frame, on=on, how=how)
    else:
        result = pd.concat(frames, ignore_index=True)

    write_excel(result, output_file, sheet_name='Merged')
    print(f"Merged {len(input_files)} files into: {output_file}")
    return output_file


def filter_data(input_file, output_file, filters):
    """Filter Excel data based on conditions."""
    if not HAS_PANDAS:
        print("Error: pandas and openpyxl required for Excel operations.")
        return

    df = pd.read_excel(input_file)
    original_count = len(df)

    for column, condition in filters.items():
        if '=' in condition:
            value = condition.split('=', 1)[1]
            df = df[df[column].astype(str).str.lower() == value.lower()]
        elif '>' in condition:
            value = condition.split('>', 1)[1]
            df = df[df[column] > float(value)]
        elif '<' in condition:
            value = condition.split('<', 1)[1]
            df = df[df[column] < float(value)]
        elif 'contains' in condition:
            value = condition.split('contains', 1)[1].strip()
            df = df[df[column].astype(str).str.contains(value, case=False, na=False)]

    write_excel(df, output_file, sheet_name='Filtered')
    print(f"Filtered: {original_count} -> {len(df)} rows")
    return output_file


def add_calculated_column(input_file, output_file, new_column, formula):
    """Add a calculated column to an Excel file."""
    if not HAS_PANDAS:
        print("Error: pandas and openpyxl required for Excel operations.")
        return

    df = pd.read_excel(input_file)

    # Simple column references: "col_a + col_b" -> df['col_a'] + df['col_b']
    # Supports basic arithmetic operations
    df[new_column] = df.eval(formula)

    write_excel(df, output_file, sheet_name='Calculated')
    print(f"Added column '{new_column}' with formula: {formula}")
    return output_file


def create_pivot_table(input_file, output_file, index, columns, values, aggfunc='sum'):
    """Create a pivot table from Excel data."""
    if not HAS_PANDAS:
        print("Error: pandas and openpyxl required for Excel operations.")
        return

    df = pd.read_excel(input_file)
    pivot = pd.pivot_table(df, index=index, columns=columns, values=values, aggfunc=aggfunc)

    write_excel(pivot.reset_index(), output_file, sheet_name='PivotTable')
    print(f"Pivot table created: {output_file}")
    return output_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Excel automation tools')
    subparsers = parser.add_subparsers(dest='command')

    # Merge
    merge_parser = subparsers.add_parser('merge', help='Merge Excel files')
    merge_parser.add_argument('files', nargs='+', help='Excel files to merge')
    merge_parser.add_argument('-o', '--output', default='merged.xlsx')
    merge_parser.add_argument('--on', help='Column to merge on')
    merge_parser.add_argument('--how', default='inner', choices=['inner', 'outer', 'left', 'right'])

    # Filter
    filter_parser = subparsers.add_parser('filter', help='Filter Excel data')
    filter_parser.add_argument('input_file', help='Input Excel file')
    filter_parser.add_argument('-o', '--output', default='filtered.xlsx')
    filter_parser.add_argument('--filter', action='append', required=True,
                               help='Filter condition (e.g., "status=active" or "price>100")')

    # Calculated column
    calc_parser = subparsers.add_parser('calculate', help='Add calculated column')
    calc_parser.add_argument('input_file', help='Input Excel file')
    calc_parser.add_argument('-o', '--output', default='calculated.xlsx')
    calc_parser.add_argument('--column', required=True, help='New column name')
    calc_parser.add_argument('--formula', required=True, help='Formula (e.g., "price * quantity")')

    # Pivot table
    pivot_parser = subparsers.add_parser('pivot', help='Create pivot table')
    pivot_parser.add_argument('input_file', help='Input Excel file')
    pivot_parser.add_argument('-o', '--output', default='pivot.xlsx')
    pivot_parser.add_argument('--index', required=True, help='Index column(s)')
    pivot_parser.add_argument('--columns', help='Columns for pivot')
    pivot_parser.add_argument('--values', required=True, help='Values column')
    pivot_parser.add_argument('--aggfunc', default='sum', help='Aggregation function')

    args = parser.parse_args()

    if args.command == 'merge':
        merge_excel_files(args.files, args.output, args.on, args.how)
    elif args.command == 'filter':
        filters = {}
        for f in args.filter:
            key = f.split('=', 1)[0].split('>', 1)[0].split('<', 1)[0].split('contains', 1)[0].strip()
            filters[key] = f
        filter_data(args.input_file, args.output, filters)
    elif args.command == 'calculate':
        add_calculated_column(args.input_file, args.output, args.column, args.formula)
    elif args.command == 'pivot':
        create_pivot_table(args.input_file, args.output, args.index, args.columns, args.values, args.aggfunc)
    else:
        parser.print_help()
