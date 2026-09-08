# SQLite Backup & Restore Strategy — Anexo_Risk

**Date:** 2026-09-07  
**Status:** Analysis Complete  
**Database:** `anexo_risk.db`

---

## 1. Backup Strategy

### 1.1 Backup Types

| Type | Description | Frequency | Retention |
|------|-------------|-----------|-----------|
| Full backup | Complete database copy | Daily | 30 days |
| Incremental | WAL-based backup | Hourly | 7 days |
| Snapshot | Point-in-time backup | On deploy | 10 snapshots |

### 1.2 Backup Methods

#### Method 1: File Copy (Simplest)

```bash
# Windows
copy C:\Users\JUAN\Desktop\Proyectos\Nexo\backend\anexo_risk.db C:\backups\anexo_risk_20260907.db

# Linux/Mac
cp /path/to/anexo_risk.db /backups/anexo_risk_20260907.db
```

**Pros:** Simple, fast, no dependencies  
**Cons:** Requires database to be idle or in WAL mode

#### Method 2: SQLite Backup API (Recommended)

```python
import sqlite3
import shutil
from datetime import datetime

def backup_database(source_db: str, backup_db: str):
    """Atomic backup using SQLite backup API."""
    source = sqlite3.connect(source_db)
    backup = sqlite3.connect(backup_db)
    
    try:
        source.backup(backup)
        print(f"Backup created: {backup_db}")
    finally:
        backup.close()
        source.close()

# Usage
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_database('anexo_risk.db', f'backups/anexo_risk_{timestamp}.db')
```

**Pros:** Atomic, consistent, handles concurrent access  
**Cons:** Requires Python

#### Method 3: WAL-Based Backup (Concurrent)

```python
import sqlite3

def wal_backup(source_db: str, backup_dir: str):
    """Backup with WAL mode for concurrent access."""
    source = sqlite3.connect(source_db)
    
    # Enable WAL mode
    source.execute('PRAGMA journal_mode=WAL')
    
    # Copy database
    shutil.copy2(source_db, f'{backup_dir}/anexo_risk.db')
    
    # Copy WAL file
    shutil.copy2(f'{source_db}-wal', f'{backup_dir}/anexo_risk.db-wal')
    
    # Copy SHM file
    shutil.copy2(f'{backup_db}-shm', f'{backup_dir}/anexo_risk.db-shm')
    
    source.close()
```

**Pros:** No downtime, concurrent reads/writes  
**Cons:** More complex, requires WAL mode

---

## 2. Backup Schedule

### 2.1 Automated Backup Script

```python
#!/usr/bin/env python3
"""Automated backup script for Anexo_Risk database."""

import os
import sqlite3
import shutil
from datetime import datetime, timedelta
from pathlib import Path

BACKUP_DIR = Path('C:/Users/JUAN/Desktop/Proyectos/Nexo/backups')
SOURCE_DB = Path('C:/Users/JUAN/Desktop/Proyectos/Nexo/backend/anexo_risk.db')
RETENTION_DAYS = 30

def create_backup():
    """Create a timestamped backup."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = BACKUP_DIR / f'anexo_risk_{timestamp}.db'
    
    # Ensure backup directory exists
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create backup
    source = sqlite3.connect(SOURCE_DB)
    backup = sqlite3.connect(backup_path)
    
    try:
        source.backup(backup)
        print(f"✓ Backup created: {backup_path}")
    finally:
        backup.close()
        source.close()
    
    return backup_path

def cleanup_old_backups():
    """Remove backups older than retention period."""
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    
    for backup in BACKUP_DIR.glob('anexo_risk_*.db'):
        # Extract timestamp from filename
        timestamp_str = backup.stem.replace('anexo_risk_', '')
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            if timestamp < cutoff:
                backup.unlink()
                print(f"✓ Removed old backup: {backup.name}")
        except ValueError:
            continue

def verify_backup(backup_path: Path) -> bool:
    """Verify backup integrity."""
    try:
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        
        # Check database integrity
        cursor.execute('PRAGMA integrity_check')
        result = cursor.fetchone()
        
        if result[0] != 'ok':
            print(f"✗ Integrity check failed: {result[0]}")
            return False
        
        # Check table count
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        
        if table_count < 10:  # Expect at least 10 tables
            print(f"✗ Unexpected table count: {table_count}")
            return False
        
        conn.close()
        print(f"✓ Backup verified: {backup_path.name}")
        return True
        
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False

if __name__ == '__main__':
    # Create backup
    backup_path = create_backup()
    
    # Verify backup
    if verify_backup(backup_path):
        # Cleanup old backups
        cleanup_old_backups()
        print("✓ Backup completed successfully")
    else:
        print("✗ Backup verification failed")
        exit(1)
```

### 2.2 Cron Schedule (Linux/Mac)

```bash
# Daily backup at 2:00 AM
0 2 * * * /usr/bin/python3 /path/to/backup_script.py >> /var/log/anexo_backup.log 2>&1

# Hourly WAL backup
0 * * * * /usr/bin/python3 /path/to/wal_backup.py >> /var/log/anexo_wal_backup.log 2>&1
```

### 2.3 Task Scheduler (Windows)

```xml
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-09-07T02:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>python</Command>
      <Arguments>C:\Users\JUAN\Desktop\Proyectos\Nexo\scripts\backup.py</Arguments>
    </Exec>
  </Actions>
</Task>
```

---

## 3. Restore Strategy

### 3.1 Restore from Backup

```python
import sqlite3
import shutil
from pathlib import Path

def restore_database(backup_path: str, target_db: str):
    """Restore database from backup."""
    backup = Path(backup_path)
    target = Path(target_db)
    
    if not backup.exists():
        raise FileNotFoundError(f"Backup not found: {backup_path}")
    
    # Verify backup before restore
    if not verify_backup(backup):
        raise ValueError("Backup verification failed")
    
    # Stop application (if running)
    print("⚠️  Stop the application before restoring")
    input("Press Enter to continue...")
    
    # Backup current database
    if target.exists():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        current_backup = target.parent / f'{target.stem}_pre_restore_{timestamp}{target.suffix}'
        shutil.copy2(target, current_backup)
        print(f"✓ Current database backed up to: {current_backup}")
    
    # Restore backup
    shutil.copy2(backup, target)
    print(f"✓ Database restored from: {backup_path}")

# Usage
restore_database(
    'C:/Users/JUAN/Desktop/Proyectos/Nexo/backups/anexo_risk_20260907_020000.db',
    'C:/Users/JUAN/Desktop/Proyectos/Nexo/backend/anexo_risk.db'
)
```

### 3.2 Restore Process

1. **Stop the application** (if running)
2. **Verify backup** (integrity check)
3. **Backup current database** (safety copy)
4. **Copy backup to target location**
5. **Verify restored database**
6. **Start application**

---

## 4. Backup Verification

### 4.1 Verification Checks

| Check | Description | Method |
|-------|-------------|--------|
| Integrity | Database structure intact | `PRAGMA integrity_check` |
| Table count | Expected tables present | `SELECT COUNT(*) FROM sqlite_master` |
| Row counts | Data not corrupted | `SELECT COUNT(*) FROM table` |
| Checksum | Backup matches source | Compare SHA-256 hashes |

### 4.2 Verification Script

```python
import sqlite3
import hashlib
from pathlib import Path

def verify_backup_integrity(backup_path: str) -> dict:
    """Comprehensive backup verification."""
    results = {
        'path': backup_path,
        'size': Path(backup_path).stat().st_size,
        'checks': {}
    }
    
    conn = sqlite3.connect(backup_path)
    cursor = conn.cursor()
    
    # 1. Integrity check
    cursor.execute('PRAGMA integrity_check')
    result = cursor.fetchone()
    results['checks']['integrity'] = result[0] == 'ok'
    
    # 2. Table count
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
    table_count = cursor.fetchone()[0]
    results['checks']['table_count'] = table_count >= 10
    
    # 3. Key tables exist
    required_tables = ['necesidades', 'resources', 'alertas', 'organizations']
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cursor.fetchall()}
    results['checks']['required_tables'] = required_tables in existing_tables
    
    # 4. Row counts
    for table in ['necesidades', 'resources', 'alertas']:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        results['checks'][f'{table}_rows'] = count
    
    conn.close()
    
    # 5. SHA-256 hash
    with open(backup_path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    results['sha256'] = file_hash
    
    return results
```

---

## 5. Disaster Recovery

### 5.1 Recovery Scenarios

| Scenario | Recovery Method | RPO | RTO |
|----------|-----------------|-----|-----|
| Database corruption | Restore from backup | 24 hours | 10 minutes |
| Accidental deletion | Restore from backup | 24 hours | 10 minutes |
| Hardware failure | Restore from backup + WAL | 1 hour | 30 minutes |
| Application bug | Restore from pre-deploy backup | 0 (immediate) | 5 minutes |

### 5.2 Recovery Time Objectives

| Metric | Target | Current |
|--------|--------|---------|
| RPO (Recovery Point Objective) | 24 hours | 24 hours |
| RTO (Recovery Time Objective) | 30 minutes | 10 minutes |

### 5.3 Recovery Process

1. **Identify last good backup** (verify integrity)
2. **Stop application** (if running)
3. **Backup current database** (safety copy)
4. **Restore backup**
5. **Apply WAL** (if incremental backup exists)
6. **Verify restored database**
7. **Start application**
8. **Verify application functionality**

---

## 6. Backup Storage

### 6.1 Storage Locations

| Location | Purpose | Retention |
|----------|---------|-----------|
| Local filesystem | Daily backups | 30 days |
| External drive | Weekly backups | 90 days |
| Cloud storage | Monthly backups | 1 year |

### 6.2 Storage Strategy

```
backups/
├── daily/
│   ├── anexo_risk_20260907_020000.db
│   ├── anexo_risk_20260908_020000.db
│   └── ...
├── weekly/
│   ├── anexo_risk_20260901.db
│   ├── anexo_risk_20260908.db
│   └── ...
└── monthly/
    ├── anexo_risk_20260901.db
    └── ...
```

---

## 7. Testing

### 7.1 Backup Test

```python
def test_backup_restore():
    """Test backup and restore process."""
    # 1. Create backup
    backup_path = create_backup()
    
    # 2. Verify backup
    assert verify_backup(backup_path)
    
    # 3. Restore to test database
    test_db = 'test_restore.db'
    restore_database(backup_path, test_db)
    
    # 4. Verify restored database
    assert verify_backup(test_db)
    
    # 5. Compare with original
    original = sqlite3.connect('anexo_risk.db')
    restored = sqlite3.connect(test_db)
    
    # Compare row counts
    for table in ['necesidades', 'resources', 'alertas']:
        original_count = original.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        restored_count = restored.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        assert original_count == restored_count
    
    # Cleanup
    original.close()
    restored.close()
    Path(test_db).unlink()
```

### 7.2 Backup Verification Test

```python
def test_backup_verification():
    """Test backup verification."""
    backup_path = create_backup()
    
    results = verify_backup_integrity(backup_path)
    
    assert results['checks']['integrity'] == True
    assert results['checks']['table_count'] >= 10
    assert results['checks']['required_tables'] == True
    assert 'necesidades' in results['checks']
    assert 'resources' in results['checks']
    assert 'alertas' in results['checks']
```

---

## 8. Conclusion

### 8.1 Backup Strategy

| Component | Recommendation |
|-----------|----------------|
| Primary method | SQLite Backup API (atomic, consistent) |
| Frequency | Daily full backup, hourly WAL backup |
| Retention | 30 days (daily), 90 days (weekly), 1 year (monthly) |
| Verification | Integrity check + table count + row counts |
| Storage | Local filesystem + external drive + cloud |

### 8.2 Restore Strategy

| Component | Recommendation |
|-----------|----------------|
| Primary method | File copy (simplest) |
| Process | Stop app → verify backup → backup current → restore → verify → start app |
| Testing | Monthly restore test to verify backups |

### 8.3 Key Points

1. **Always verify backups** before restoring
2. **Always backup current database** before restoring
3. **Test restores regularly** (monthly)
4. **Keep multiple backup locations** (local + external + cloud)
5. **Document recovery process** for team members
