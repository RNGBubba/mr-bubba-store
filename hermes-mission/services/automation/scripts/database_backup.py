#!/usr/bin/env python3
"""
Database Backup Automation Script
Backup MySQL/PostgreSQL/SQLite databases on schedule.
"""

import argparse
import subprocess
import shutil
import gzip
from pathlib import Path
from datetime import datetime


def backup_sqlite(db_file, output_dir='backups', compress=True):
    """Backup a SQLite database."""
    db_path = Path(db_file)
    if not db_path.exists():
        print(f"Error: Database file '{db_file}' not found.")
        return None

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = output_path / f"{db_path.stem}_backup_{timestamp}.db"

    # Use SQLite's backup API via command line
    import sqlite3
    source = sqlite3.connect(db_file)
    dest = sqlite3.connect(str(backup_file))
    source.backup(dest)
    source.close()
    dest.close()

    if compress:
        compressed_file = backup_file.with_suffix('.db.gz')
        with open(backup_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        backup_file.unlink()
        backup_file = compressed_file

    print(f"SQLite backup created: {backup_file}")
    return str(backup_file)


def backup_mysql(host, user, password, database, output_dir='backups', compress=True):
    """Backup a MySQL database using mysqldump."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = output_path / f"{database}_backup_{timestamp}.sql"

    cmd = [
        'mysqldump',
        f'--host={host}',
        f'--user={user}',
        f'--password={password}',
        '--single-transaction',
        '--routines',
        '--triggers',
        database
    ]

    with open(backup_file, 'w') as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return None

    if compress:
        compressed_file = backup_file.with_suffix('.sql.gz')
        with open(backup_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        backup_file.unlink()
        backup_file = compressed_file

    print(f"MySQL backup created: {backup_file}")
    return str(backup_file)


def backup_postgresql(host, user, password, database, output_dir='backups', compress=True):
    """Backup a PostgreSQL database using pg_dump."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = output_path / f"{database}_backup_{timestamp}.sql"

    cmd = [
        'pg_dump',
        f'--host={host}',
        f'--username={user}',
        f'--dbname={database}',
        '--format=plain',
        f'--file={backup_file}'
    ]

    env = {'PGPASSWORD': password}
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None

    if compress:
        compressed_file = backup_file.with_suffix('.sql.gz')
        with open(backup_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        backup_file.unlink()
        backup_file = compressed_file

    print(f"PostgreSQL backup created: {backup_file}")
    return str(backup_file)


def cleanup_old_backups(output_dir='backups', keep_days=30):
    """Remove backup files older than specified days."""
    output_path = Path(output_dir)
    if not output_path.exists():
        return

    now = datetime.now().timestamp()
    cutoff = keep_days * 86400
    removed = 0

    for backup_file in output_path.iterdir():
        if backup_file.is_file() and 'backup' in backup_file.name:
            age = now - backup_file.stat().st_mtime
            if age > cutoff:
                backup_file.unlink()
                removed += 1
                print(f"Removed old backup: {backup_file.name}")

    print(f"\nCleaned up {removed} old backup files.")
    return removed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Database backup automation')
    subparsers = parser.add_subparsers(dest='command')

    # SQLite
    sqlite_parser = subparsers.add_parser('sqlite', help='Backup SQLite database')
    sqlite_parser.add_argument('database', help='SQLite database file')
    sqlite_parser.add_argument('-o', '--output-dir', default='backups')
    sqlite_parser.add_argument('--no-compress', action='store_true')

    # MySQL
    mysql_parser = subparsers.add_parser('mysql', help='Backup MySQL database')
    mysql_parser.add_argument('--host', default='localhost')
    mysql_parser.add_argument('--user', required=True)
    mysql_parser.add_argument('--password', required=True)
    mysql_parser.add_argument('--database', required=True)
    mysql_parser.add_argument('-o', '--output-dir', default='backups')
    mysql_parser.add_argument('--no-compress', action='store_true')

    # PostgreSQL
    pg_parser = subparsers.add_parser('postgresql', help='Backup PostgreSQL database')
    pg_parser.add_argument('--host', default='localhost')
    pg_parser.add_argument('--user', required=True)
    pg_parser.add_argument('--password', required=True)
    pg_parser.add_argument('--database', required=True)
    pg_parser.add_argument('-o', '--output-dir', default='backups')
    pg_parser.add_argument('--no-compress', action='store_true')

    # Cleanup
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean old backups')
    cleanup_parser.add_argument('-o', '--output-dir', default='backups')
    cleanup_parser.add_argument('--keep-days', type=int, default=30)

    args = parser.parse_args()

    if args.command == 'sqlite':
        backup_sqlite(args.database, args.output_dir, not args.no_compress)
    elif args.command == 'mysql':
        backup_mysql(args.host, args.user, args.password, args.database,
                     args.output_dir, not args.no_compress)
    elif args.command == 'postgresql':
        backup_postgresql(args.host, args.user, args.password, args.database,
                          args.output_dir, not args.no_compress)
    elif args.command == 'cleanup':
        cleanup_old_backups(args.output_dir, args.keep_days)
    else:
        parser.print_help()
