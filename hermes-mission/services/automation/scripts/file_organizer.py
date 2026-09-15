#!/usr/bin/env python3
"""
File Organizer Automation Script
Organizes files in a directory by type, date, or custom rules.
"""

import os
import shutil
import argparse
from pathlib import Path
from datetime import datetime


# File type categories
FILE_CATEGORIES = {
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico'],
    'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx'],
    'Videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'],
    'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'],
    'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
    'Code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.rb', '.go', '.rs'],
    'Data': ['.csv', '.json', '.xml', '.yaml', '.yml', '.sql', '.db'],
}


def organize_by_type(source_dir, dry_run=False):
    """Organize files into folders by file type."""
    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"Error: Directory '{source_dir}' does not exist.")
        return

    moved_files = []
    for file in source_path.iterdir():
        if file.is_file():
            dest_folder = 'Other'
            for category, extensions in FILE_CATEGORIES.items():
                if file.suffix.lower() in extensions:
                    dest_folder = category
                    break

            dest_dir = source_path / dest_folder
            if dry_run:
                print(f"[DRY RUN] Would move: {file.name} -> {dest_dir}/")
            else:
                dest_dir.mkdir(exist_ok=True)
                shutil.move(str(file), str(dest_dir / file.name))
                moved_files.append(file.name)
                print(f"Moved: {file.name} -> {dest_dir}/")

    if not dry_run:
        print(f"\nOrganized {len(moved_files)} files.")
    return moved_files


def organize_by_date(source_dir, date_format='%Y-%m', dry_run=False):
    """Organize files into folders by modification date."""
    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"Error: Directory '{source_dir}' does not exist.")
        return

    moved_files = []
    for file in source_path.iterdir():
        if file.is_file():
            mod_time = datetime.fromtimestamp(file.stat().st_mtime)
            date_folder = mod_time.strftime(date_format)
            dest_dir = source_path / date_folder

            if dry_run:
                print(f"[DRY RUN] Would move: {file.name} -> {dest_dir}/")
            else:
                dest_dir.mkdir(exist_ok=True)
                shutil.move(str(file), str(dest_dir / file.name))
                moved_files.append(file.name)
                print(f"Moved: {file.name} -> {dest_dir}/")

    if not dry_run:
        print(f"\nOrganized {len(moved_files)} files by date.")
    return moved_files


def organize_by_keyword(source_dir, keyword, folder_name=None, dry_run=False):
    """Move files containing a specific keyword in their name."""
    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"Error: Directory '{source_dir}' does not exist.")
        return

    folder_name = folder_name or keyword.capitalize()
    dest_dir = source_path / folder_name
    moved_files = []

    for file in source_path.iterdir():
        if file.is_file() and keyword.lower() in file.name.lower():
            if dry_run:
                print(f"[DRY RUN] Would move: {file.name} -> {dest_dir}/")
            else:
                dest_dir.mkdir(exist_ok=True)
                shutil.move(str(file), str(dest_dir / file.name))
                moved_files.append(file.name)
                print(f"Moved: {file.name} -> {dest_dir}/")

    if not dry_run:
        print(f"\nOrganized {len(moved_files)} files matching '{keyword}'.")
    return moved_files


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Organize files in a directory')
    parser.add_argument('directory', help='Directory to organize')
    parser.add_argument('--method', choices=['type', 'date', 'keyword'], default='type',
                        help='Organization method')
    parser.add_argument('--keyword', help='Keyword for keyword-based organization')
    parser.add_argument('--folder-name', help='Custom folder name for keyword organization')
    parser.add_argument('--date-format', default='%Y-%m', help='Date format for date organization')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without moving files')

    args = parser.parse_args()

    if args.method == 'type':
        organize_by_type(args.directory, args.dry_run)
    elif args.method == 'date':
        organize_by_date(args.directory, args.date_format, args.dry_run)
    elif args.method == 'keyword':
        if not args.keyword:
            print("Error: --keyword is required for keyword organization")
        else:
            organize_by_keyword(args.directory, args.keyword, args.folder_name, args.dry_run)
