#!/usr/bin/env bash
#
# backup.sh - Simple backup script

set -euo pipefail

# Directories/files to back up (edit this)
BACKUP_SOURCES=(
  "/home"          # all home directories
  "/etc"           # system configuration
)

# Where to store backups (must exist or be creatable)
BACKUP_DEST="/mnt/backup"

# Retention (days to keep backups)
RETENTION_DAYS=30

# Derived names
DATE=$(date +%Y-%m-%d)
HOSTNAME_SHORT=$(hostname -s)
ARCHIVE_NAME="${HOSTNAME_SHORT}-${DATE}.tar.gz"
ARCHIVE_PATH="${BACKUP_DEST}/${ARCHIVE_NAME}"

mkdir -p "${BACKUP_DEST}"

echo "Creating backup: ${ARCHIVE_PATH}"
tar -czpf "${ARCHIVE_PATH}" "${BACKUP_SOURCES[@]}"

echo "Pruning backups older than ${RETENTION_DAYS} days in ${BACKUP_DEST}"
find "${BACKUP_DEST}" -type f -name "${HOSTNAME_SHORT}-*.tar.gz" -mtime +${RETENTION_DAYS} -delete

echo "Backup complete."
