#!/usr/bin/env python3
"""
Data Converter Automation Script
Convert data between formats: CSV, JSON, XML, Excel, YAML.
"""

import argparse
import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def csv_to_json(csv_file, json_file):
    """Convert CSV to JSON."""
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        data = list(reader)
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Converted {csv_file} -> {json_file}")
    return json_file


def json_to_csv(json_file, csv_file):
    """Convert JSON to CSV."""
    with open(json_file, 'r') as f:
        data = json.load(f)
    if not data:
        print("No data found in JSON file.")
        return
    keys = data[0].keys()
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    print(f"Converted {json_file} -> {csv_file}")
    return csv_file


def csv_to_xml(csv_file, xml_file, root_name='records', row_name='record'):
    """Convert CSV to XML."""
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        root = ET.Element(root_name)
        for row in reader:
            row_elem = ET.SubElement(root, row_name)
            for key, value in row.items():
                field = ET.SubElement(row_elem, key.strip())
                field.text = value
    tree = ET.ElementTree(root)
    ET.indent(tree, space='  ')
    tree.write(xml_file, encoding='unicode', xml_declaration=True)
    print(f"Converted {csv_file} -> {xml_file}")
    return xml_file


def xml_to_csv(xml_file, csv_file, record_xpath='.//record'):
    """Convert XML to CSV."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    records = root.findall(record_xpath)
    if not records:
        print("No records found in XML.")
        return
    headers = [child.tag for child in records[0]]
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for record in records:
            writer.writerow([record.find(h).text or '' for h in headers])
    print(f"Converted {xml_file} -> {csv_file}")
    return csv_file


def csv_to_excel(csv_file, excel_file, sheet_name='Sheet1'):
    """Convert CSV to Excel."""
    if HAS_PANDAS:
        df = pd.read_csv(csv_file)
        df.to_excel(excel_file, sheet_name=sheet_name, index=False)
        print(f"Converted {csv_file} -> {excel_file}")
    else:
        print("Error: pandas and openpyxl required for Excel conversion.")
    return excel_file


def excel_to_csv(excel_file, csv_file, sheet_name=0):
    """Convert Excel to CSV."""
    if HAS_PANDAS:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        df.to_csv(csv_file, index=False)
        print(f"Converted {excel_file} -> {csv_file}")
    else:
        print("Error: pandas and openpyxl required for Excel conversion.")
    return csv_file


def json_to_xml(json_file, xml_file, root_name='records', row_name='item'):
    """Convert JSON to XML."""
    with open(json_file, 'r') as f:
        data = json.load(f)
    root = ET.Element(root_name)
    for item in data:
        row_elem = ET.SubElement(root, row_name)
        for key, value in item.items():
            field = ET.SubElement(row_elem, str(key))
            field.text = str(value) if value is not None else ''
    tree = ET.ElementTree(root)
    ET.indent(tree, space='  ')
    tree.write(xml_file, encoding='unicode', xml_declaration=True)
    print(f"Converted {json_file} -> {xml_file}")
    return xml_file


def convert(input_file, output_file):
    """Auto-detect and convert between formats."""
    in_ext = Path(input_file).suffix.lower()
    out_ext = Path(output_file).suffix.lower()

    conversion_map = {
        ('.csv', '.json'): csv_to_json,
        ('.json', '.csv'): json_to_csv,
        ('.csv', '.xml'): csv_to_xml,
        ('.xml', '.csv'): xml_to_csv,
        ('.csv', '.xlsx'): csv_to_excel,
        ('.csv', '.xls'): csv_to_excel,
        ('.xlsx', '.csv'): excel_to_csv,
        ('.xls', '.csv'): excel_to_csv,
        ('.json', '.xml'): json_to_xml,
    }

    converter = conversion_map.get((in_ext, out_ext))
    if converter:
        converter(input_file, output_file)
    else:
        print(f"Conversion from {in_ext} to {out_ext} is not supported.")
        print(f"Supported conversions: {', '.join([f'{a}->{b}' for a, b in conversion_map.keys()])}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert data between formats')
    parser.add_argument('input_file', help='Input file path')
    parser.add_argument('output_file', help='Output file path')
    parser.add_argument('--root-name', default='records', help='XML root element name')
    parser.add_argument('--row-name', default='record', help='XML row element name')
    parser.add_argument('--sheet-name', default='Sheet1', help='Excel sheet name')

    args = parser.parse_args()
    convert(args.input_file, args.output_file)
