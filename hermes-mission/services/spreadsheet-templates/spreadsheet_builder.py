#!/usr/bin/env python3
"""
Custom Spreadsheet Template Builder
Generates custom Excel templates based on client input descriptions.

Usage:
    python3 spreadsheet_builder.py --input client_request.json --output template.xlsx
    python3 spreadsheet_builder.py --interactive
"""

import json
import argparse
import sys
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

# Style constants
HEADER_FONT = Font(name='Calibri', bold=True, size=12, color='FFFFFF')
HEADER_FILL = PatternFill(start_color='2F5496', end_color='2F5496', fill_type='solid')
SUBHEADER_FILL = PatternFill(start_color='D6E4F0', end_color='D6E4F0', fill_type='solid')
INPUT_FILL = PatternFill(start_color='FFF2CC', end_color='FFF2CC', fill_type='solid')
CALC_FILL = PatternFill(start_color='E2EFDA', end_color='E2EFDA', fill_type='solid')
THIN_BORDER = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)
CENTER_ALIGN = Alignment(horizontal='center', vertical='center')
LEFT_ALIGN = Alignment(horizontal='left', vertical='center', wrap_text=True)


def create_budget_template(wb, config):
    """Create a personal/business budget spreadsheet."""
    ws = wb.active
    ws.title = "Budget"
    
    # Title
    ws.merge_cells('A1:F1')
    ws['A1'] = config.get('title', 'Monthly Budget Tracker')
    ws['A1'].font = Font(name='Calibri', bold=True, size=16, color='2F5496')
    ws['A1'].alignment = Alignment(horizontal='center')
    
    # Headers
    headers = ['Category', 'Item', 'Planned Amount', 'Actual Amount', 'Difference', 'Notes']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER_ALIGN
        cell.border = THIN_BORDER
    
    # Default categories
    categories = config.get('categories', [
        'Housing', 'Transportation', 'Food', 'Utilities', 
        'Insurance', 'Savings', 'Entertainment', 'Other'
    ])
    
    row = 4
    for cat in categories:
        ws.cell(row=row, column=1, value=cat).font = Font(bold=True)
        ws.cell(row=row, column=1).fill = SUBHEADER_FILL
        ws.cell(row=row, column=1).border = THIN_BORDER
        for col in range(2, 7):
            ws.cell(row=row, column=col).border = THIN_BORDER
            ws.cell(row=row, column=col).fill = SUBHEADER_FILL
        row += 1
        # Add 2-3 item rows per category
        for _ in range(3):
            ws.cell(row=row, column=2).border = THIN_BORDER
            ws.cell(row=row, column=3).border = THIN_BORDER
            ws.cell(row=row, column=3).fill = INPUT_FILL
            ws.cell(row=row, column=4).border = THIN_BORDER
            ws.cell(row=row, column=4).fill = INPUT_FILL
            # Difference formula
            ws.cell(row=row, column=5, value=f'=C{row}-D{row}')
            ws.cell(row=row, column=5).fill = CALC_FILL
            ws.cell(row=row, column=5).border = THIN_BORDER
            ws.cell(row=row, column=6).border = THIN_BORDER
            row += 1
    
    # Totals row
    ws.cell(row=row, column=1, value='TOTALS').font = Font(bold=True, size=11)
    ws.cell(row=row, column=1).fill = HEADER_FILL
    ws.cell(row=row, column=1).font = HEADER_FONT
    for col in range(3, 6):
        col_letter = get_column_letter(col)
        ws.cell(row=row, column=col, value=f'=SUM({col_letter}4:{col_letter}{row-1})')
        ws.cell(row=row, column=col).font = Font(bold=True)
        ws.cell(row=row, column=col).fill = CALC_FILL
        ws.cell(row=row, column=col).border = THIN_BORDER
    
    # Column widths
    widths = [15, 25, 15, 15, 15, 30]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    
    # Add summary sheet
    ws2 = wb.create_sheet("Summary")
    ws2['A1'] = "Budget Summary"
    ws2['A1'].font = Font(name='Calibri', bold=True, size=14, color='2F5496')
    ws2['A3'] = "Total Planned"
    ws2['B3'] = "=Budget!C" + str(row)
    ws2['B3'].font = Font(bold=True)
    ws2['A4'] = "Total Actual"
    ws2['B4'] = "=Budget!D" + str(row)
    ws2['B4'].font = Font(bold=True)
    ws2['A5'] = "Net Difference"
    ws2['B5'] = "=B3-B4"
    ws2['B5'].font = Font(bold=True)
    ws2['B5'].fill = CALC_FILL
    ws2.column_dimensions['A'].width = 18
    ws2.column_dimensions['B'].width = 15


def create_invoice_template(wb, config):
    """Create an invoice tracking spreadsheet."""
    ws = wb.active
    ws.title = "Invoices"
    
    # Title
    ws.merge_cells('A1:H1')
    ws['A1'] = config.get('title', 'Invoice Tracker')
    ws['A1'].font = Font(name='Calibri', bold=True, size=16, color='2F5496')
    ws['A1'].alignment = Alignment(horizontal='center')
    
    # Company info section
    ws['A3'] = "Company:"
    ws['A3'].font = Font(bold=True)
    ws['B3'] = config.get('company_name', '[Your Company Name]')
    ws['A4'] = "Email:"
    ws['A4'].font = Font(bold=True)
    ws['B4'] = config.get('company_email', '[email@example.com]')
    
    # Headers
    headers = ['Invoice #', 'Client', 'Description', 'Date Issued', 'Due Date', 
               'Amount', 'Status', 'Days Outstanding']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=6, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER_ALIGN
        cell.border = THIN_BORDER
    
    # Sample data rows with formulas
    for row in range(7, 17):
        ws.cell(row=row, column=1).border = THIN_BORDER
        ws.cell(row=row, column=2).border = THIN_BORDER
        ws.cell(row=row, column=3).border = THIN_BORDER
        ws.cell(row=row, column=4).border = THIN_BORDER
        ws.cell(row=row, column=4).fill = INPUT_FILL
        ws.cell(row=row, column=5).border = THIN_BORDER
        ws.cell(row=row, column=5).fill = INPUT_FILL
        ws.cell(row=row, column=6).border = THIN_BORDER
        ws.cell(row=row, column=6).fill = INPUT_FILL
        ws.cell(row=row, column=7).border = THIN_BORDER
        ws.cell(row=row, column=7).fill = INPUT_FILL
        # Days outstanding formula
        ws.cell(row=row, column=8, value=f'=IF(G{row}="Paid","",TODAY()-E{row})')
        ws.cell(row=row, column=8).fill = CALC_FILL
        ws.cell(row=row, column=8).border = THIN_BORDER
    
    # Summary section
    summary_row = 18
    ws.cell(row=summary_row, column=1, value="SUMMARY").font = Font(bold=True, size=12)
    ws.cell(row=summary_row, column=1).fill = SUBHEADER_FILL
    
    ws.cell(row=summary_row+1, column=1, value="Total Outstanding:")
    ws.cell(row=summary_row+1, column=1).font = Font(bold=True)
    ws.cell(row=summary_row+1, column=2, value=f'=SUMIF(G7:G16,"Unpaid",F7:F16)')
    ws.cell(row=summary_row+1, column=2).font = Font(bold=True)
    ws.cell(row=summary_row+1, column=2).fill = CALC_FILL
    
    ws.cell(row=summary_row+2, column=1, value="Total Paid:")
    ws.cell(row=summary_row+2, column=1).font = Font(bold=True)
    ws.cell(row=summary_row+2, column=2, value=f'=SUMIF(G7:G16,"Paid",F7:F16)')
    ws.cell(row=summary_row+2, column=2).font = Font(bold=True)
    ws.cell(row=summary_row+2, column=2).fill = CALC_FILL
    
    ws.cell(row=summary_row+3, column=1, value="Overdue (>30 days):")
    ws.cell(row=summary_row+3, column=1).font = Font(bold=True)
    ws.cell(row=summary_row+3, column=2, value=f'=SUMIFS(F7:F16,G7:G16,"Unpaid",H7:H16,">30")')
    ws.cell(row=summary_row+3, column=2).font = Font(bold=True)
    ws.cell(row=summary_row+3, column=2).fill = CALC_FILL
    
    # Column widths
    widths = [12, 20, 30, 12, 12, 12, 12, 15]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def create_project_tracker(wb, config):
    """Create a project/task tracking spreadsheet."""
    ws = wb.active
    ws.title = "Projects"
    
    # Title
    ws.merge_cells('A1:I1')
    ws['A1'] = config.get('title', 'Project Task Tracker')
    ws['A1'].font = Font(name='Calibri', bold=True, size=16, color='2F5496')
    ws['A1'].alignment = Alignment(horizontal='center')
    
    # Headers
    headers = ['Project', 'Task', 'Assigned To', 'Priority', 'Status', 
               'Start Date', 'Due Date', 'Completion %', 'Days Remaining']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER_ALIGN
        cell.border = THIN_BORDER
    
    # Data rows
    for row in range(4, 24):
        for col in range(1, 10):
            ws.cell(row=row, column=col).border = THIN_BORDER
        # Input cells
        for col in [1, 2, 3, 4, 5, 6, 7]:
            ws.cell(row=row, column=col).fill = INPUT_FILL
        # Completion % with data validation style
        ws.cell(row=row, column=8).fill = INPUT_FILL
        # Days remaining formula
        ws.cell(row=row, column=9, value=f'=IF(H{row}="","",IF(H{row}-TODAY()<0,"OVERDUE",H{row}-TODAY()))')
        ws.cell(row=row, column=9).fill = CALC_FILL
    
    # Summary
    summary_row = 25
    ws.cell(row=summary_row, column=1, value="PROJECT SUMMARY").font = Font(bold=True, size=12)
    ws.cell(row=summary_row, column=1).fill = SUBHEADER_FILL
    
    ws.cell(row=summary_row+1, column=1, value="Total Tasks:")
    ws.cell(row=summary_row+1, column=2, value='=COUNTA(B4:B23)')
    ws.cell(row=summary_row+2, column=1, value="Completed:")
    ws.cell(row=summary_row+2, column=2, value='=COUNTIF(F4:F23,"Complete")')
    ws.cell(row=summary_row+3, column=1, value="In Progress:")
    ws.cell(row=summary_row+3, column=2, value='=COUNTIF(F4:F23,"In Progress")')
    ws.cell(row=summary_row+4, column=1, value="Avg Completion:")
    ws.cell(row=summary_row+4, column=2, value='=AVERAGE(H4:H23)')
    ws.cell(row=summary_row+4, column=2).number_format = '0%'
    
    # Column widths
    widths = [20, 30, 15, 10, 12, 12, 12, 12, 14]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def create_sales_tracker(wb, config):
    """Create a sales pipeline/revenue tracking spreadsheet."""
    ws = wb.active
    ws.title = "Sales Pipeline"
    
    # Title
    ws.merge_cells('A1:G1')
    ws['A1'] = config.get('title', 'Sales Pipeline Tracker')
    ws['A1'].font = Font(name='Calibri', bold=True, size=16, color='2F5496')
    ws['A1'].alignment = Alignment(horizontal='center')
    
    # Headers
    headers = ['Lead Name', 'Company', 'Value', 'Stage', 'Probability', 
               'Expected Revenue', 'Close Date']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER_ALIGN
        cell.border = THIN_BORDER
    
    # Data rows
    for row in range(4, 24):
        for col in range(1, 8):
            ws.cell(row=row, column=col).border = THIN_BORDER
        for col in [1, 2, 3, 4, 5, 7]:
            ws.cell(row=row, column=col).fill = INPUT_FILL
        # Expected revenue formula
        ws.cell(row=row, column=6, value=f'=C{row}*E{row}')
        ws.cell(row=row, column=6).fill = CALC_FILL
        ws.cell(row=row, column=6).number_format = '$#,##0.00'
    
    # Summary
    summary_row = 25
    ws.cell(row=summary_row, column=1, value="PIPELINE SUMMARY").font = Font(bold=True, size=12)
    ws.cell(row=summary_row, column=1).fill = SUBHEADER_FILL
    
    ws.cell(row=summary_row+1, column=1, value="Total Pipeline:")
    ws.cell(row=summary_row+1, column=2, value='=SUM(C4:C23)')
    ws.cell(row=summary_row+1, column=2).number_format = '$#,##0.00'
    ws.cell(row=summary_row+2, column=1, value="Weighted Forecast:")
    ws.cell(row=summary_row+2, column=2, value='=SUM(F4:F23)')
    ws.cell(row=summary_row+2, column=2).number_format = '$#,##0.00'
    ws.cell(row=summary_row+3, column=1, value="Avg Deal Size:")
    ws.cell(row=summary_row+3, column=2, value='=AVERAGE(C4:C23)')
    ws.cell(row=summary_row+3, column=2).number_format = '$#,##0.00'
    ws.cell(row=summary_row+4, column=1, value="Deals in Pipeline:")
    ws.cell(row=summary_row+4, column=2, value='=COUNTA(A4:A23)')
    
    # Column widths
    widths = [20, 20, 15, 15, 12, 16, 12]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def create_inventory_template(wb, config):
    """Create an inventory management spreadsheet."""
    ws = wb.active
    ws.title = "Inventory"
    
    # Title
    ws.merge_cells('A1:H1')
    ws['A1'] = config.get('title', 'Inventory Management')
    ws['A1'].font = Font(name='Calibri', bold=True, size=16, color='2F5496')
    ws['A1'].alignment = Alignment(horizontal='center')
    
    # Headers
    headers = ['SKU', 'Product Name', 'Category', 'Unit Cost', 'Quantity', 
               'Reorder Level', 'Total Value', 'Status']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER_ALIGN
        cell.border = THIN_BORDER
    
    # Data rows
    for row in range(4, 34):
        for col in range(1, 9):
            ws.cell(row=row, column=col).border = THIN_BORDER
        for col in [1, 2, 3, 4, 5, 6]:
            ws.cell(row=row, column=col).fill = INPUT_FILL
        # Total value formula
        ws.cell(row=row, column=7, value=f'=D{row}*E{row}')
        ws.cell(row=row, column=7).fill = CALC_FILL
        ws.cell(row=row, column=7).number_format = '$#,##0.00'
        # Status formula
        ws.cell(row=row, column=8, value=f'=IF(E{row}<=F{row},"REORDER","OK")')
        ws.cell(row=row, column=8).fill = CALC_FILL
    
    # Summary
    summary_row = 35
    ws.cell(row=summary_row, column=1, value="INVENTORY SUMMARY").font = Font(bold=True, size=12)
    ws.cell(row=summary_row, column=1).fill = SUBHEADER_FILL
    
    ws.cell(row=summary_row+1, column=1, value="Total Items:")
    ws.cell(row=summary_row+1, column=2, value='=SUM(E4:E33)')
    ws.cell(row=summary_row+2, column=1, value="Total Value:")
    ws.cell(row=summary_row+2, column=2, value='=SUM(G4:G33)')
    ws.cell(row=summary_row+2, column=2).number_format = '$#,##0.00'
    ws.cell(row=summary_row+3, column=1, value="Items to Reorder:")
    ws.cell(row=summary_row+3, column=2, value='=COUNTIF(H4:H33,"REORDER")')
    
    # Column widths
    widths = [12, 25, 15, 12, 10, 13, 14, 10]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def create_payroll_template(wb, config):
    """Create a payroll calculation spreadsheet."""
    ws = wb.active
    ws.title = "Payroll"
    
    # Title
    ws.merge_cells('A1:I1')
    ws['A1'] = config.get('title', 'Payroll Calculator')
    ws['A1'].font = Font(name='Calibri', bold=True, size=16, color='2F5496')
    ws['A1'].alignment = Alignment(horizontal='center')
    
    # Headers
    headers = ['Employee', 'Position', 'Hourly Rate', 'Hours Worked', 'Overtime Hours',
               'Gross Pay', 'Tax (20%)', 'Net Pay', 'Pay Period']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER_ALIGN
        cell.border = THIN_BORDER
    
    # Data rows
    for row in range(4, 24):
        for col in range(1, 10):
            ws.cell(row=row, column=col).border = THIN_BORDER
        for col in [1, 2, 3, 4, 5, 9]:
            ws.cell(row=row, column=col).fill = INPUT_FILL
        # Gross pay formula (regular + overtime at 1.5x)
        ws.cell(row=row, column=6, value=f'=C{row}*D{row}+C{row}*E{row}*1.5')
        ws.cell(row=row, column=6).fill = CALC_FILL
        ws.cell(row=row, column=6).number_format = '$#,##0.00'
        # Tax formula
        ws.cell(row=row, column=7, value=f'=F{row}*0.2')
        ws.cell(row=row, column=7).fill = CALC_FILL
        ws.cell(row=row, column=7).number_format = '$#,##0.00'
        # Net pay formula
        ws.cell(row=row, column=8, value=f'=F{row}-G{row}')
        ws.cell(row=row, column=8).fill = CALC_FILL
        ws.cell(row=row, column=8).number_format = '$#,##0.00'
    
    # Summary
    summary_row = 25
    ws.cell(row=summary_row, column=1, value="PAYROLL SUMMARY").font = Font(bold=True, size=12)
    ws.cell(row=summary_row, column=1).fill = SUBHEADER_FILL
    
    ws.cell(row=summary_row+1, column=1, value="Total Gross:")
    ws.cell(row=summary_row+1, column=2, value='=SUM(F4:F23)')
    ws.cell(row=summary_row+1, column=2).number_format = '$#,##0.00'
    ws.cell(row=summary_row+2, column=1, value="Total Tax:")
    ws.cell(row=summary_row+2, column=2, value='=SUM(G4:G23)')
    ws.cell(row=summary_row+2, column=2).number_format = '$#,##0.00'
    ws.cell(row=summary_row+3, column=1, value="Total Net:")
    ws.cell(row=summary_row+3, column=2, value='=SUM(H4:H23)')
    ws.cell(row=summary_row+3, column=2).number_format = '$#,##0.00'
    
    # Column widths
    widths = [18, 18, 12, 13, 13, 12, 12, 12, 12]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


# Template registry
TEMPLATES = {
    'budget': create_budget_template,
    'invoice': create_invoice_template,
    'project': create_project_tracker,
    'sales': create_sales_tracker,
    'inventory': create_inventory_template,
    'payroll': create_payroll_template,
}


def generate_template(template_type, config, output_path):
    """Generate a spreadsheet template of the specified type."""
    if template_type not in TEMPLATES:
        raise ValueError(f"Unknown template type: {template_type}. Available: {list(TEMPLATES.keys())}")
    
    wb = Workbook()
    TEMPLATES[template_type](wb, config)
    wb.save(output_path)
    return output_path


def parse_client_description(description):
    """Parse a natural language client description to determine template type and config."""
    desc_lower = description.lower()
    
    # Keywords mapping
    keywords = {
        'budget': ['budget', 'expense', 'spending', 'personal finance', 'cost tracking'],
        'invoice': ['invoice', 'billing', 'client payment', 'accounts receivable', 'money owed'],
        'project': ['project', 'task', 'assignment', 'team', 'deadline', 'milestone'],
        'sales': ['sales', 'pipeline', 'lead', 'deal', 'revenue', 'prospect', 'crm'],
        'inventory': ['inventory', 'stock', 'product', 'sku', 'warehouse', 'supply'],
        'payroll': ['payroll', 'employee', 'salary', 'wage', 'paycheck', 'staff payment'],
    }
    
    # Score each template type
    scores = {}
    for template_type, words in keywords.items():
        scores[template_type] = sum(1 for word in words if word in desc_lower)
    
    # Get best match
    best_match = max(scores, key=scores.get)
    if scores[best_match] == 0:
        best_match = 'budget'  # default
    
    return best_match, {'title': f"Custom {best_match.title()} Template"}


def interactive_mode():
    """Run in interactive mode to get client input."""
    print("=" * 60)
    print("  Custom Spreadsheet Template Builder")
    print("  Mr Bubba Services")
    print("=" * 60)
    print()
    print("Available template types:")
    for i, t in enumerate(TEMPLATES.keys(), 1):
        print(f"  {i}. {t.title()}")
    print()
    
    template_type = input("Enter template type (or 'auto' to detect from description): ").strip().lower()
    
    config = {}
    
    if template_type == 'auto':
        print("\nDescribe your business/data needs:")
        description = input("> ")
        detected_type, detected_config = parse_client_description(description)
        config.update(detected_config)
        template_type = detected_type
        print(f"\nDetected template type: {template_type.title()}")
    else:
        config['title'] = input("Enter template title (or press Enter for default): ").strip()
    
    # Get additional config
    company = input("Company name (optional): ").strip()
    if company:
        config['company_name'] = company
        config['company_email'] = f"contact@{company.lower().replace(' ', '')}.com"
    
    output_path = input(f"Output filename [template.xlsx]: ").strip()
    if not output_path:
        output_path = "template.xlsx"
    if not output_path.endswith('.xlsx'):
        output_path += '.xlsx'
    
    generate_template(template_type, config, output_path)
    print(f"\n✓ Template generated: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description='Custom Spreadsheet Template Builder')
    parser.add_argument('--type', '-t', choices=list(TEMPLATES.keys()),
                        help='Template type')
    parser.add_argument('--input', '-i', help='JSON config file with template settings')
    parser.add_argument('--output', '-o', default='template.xlsx',
                        help='Output file path (default: template.xlsx)')
    parser.add_argument('--title', help='Template title')
    parser.add_argument('--company', help='Company name')
    parser.add_argument('--description', '-d', help='Natural language description of needs')
    parser.add_argument('--interactive', action='store_true',
                        help='Run in interactive mode')
    
    args = parser.parse_args()
    
    if args.interactive or (not args.type and not args.description and not args.input):
        return interactive_mode()
    
    # Load config from file or build from args
    config = {}
    if args.input:
        with open(args.input, 'r') as f:
            config = json.load(f)
    
    if args.title:
        config['title'] = args.title
    if args.company:
        config['company_name'] = args.company
    
    # Determine template type
    template_type = args.type
    if not template_type and args.description:
        template_type, detected_config = parse_client_description(args.description)
        config.update(detected_config)
    
    if not template_type:
        print("Error: Must specify --type, --description, or --input")
        sys.exit(1)
    
    generate_template(template_type, config, args.output)
    print(f"Template generated: {args.output}")
    return args.output


if __name__ == '__main__':
    main()
