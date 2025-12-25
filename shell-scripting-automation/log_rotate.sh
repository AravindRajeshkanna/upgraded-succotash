#!/usr/bin/env bash
#
# log_rotate.sh - Size-based rotation for *.log files

set -euo pipefail

LOG_DIR="/var/log/myapp"     # directory with active logs
ARCHIVE_DIR="/var/log/myapp/archive"  # where rotated logs go
MAX_SIZE_MB=10               # rotate if > this size
MAX_ROTATIONS=5              # keep N old versions: file.log.1 ... file.log.N

mkdir -p "${ARCHIVE_DIR}"

rotate_one() {
    local file="$1"

    # current size in MB (base 2)
    local size_mb
    size_mb=$(stat -c "%s" "$file")
    size_mb=$(( size_mb / 1048576 ))

    [[ "${size_mb}" -le "${MAX_SIZE_MB}" ]] && return 0

    local base
    base=$(basename "$file")

    # shift old logs: base.log.(N-1) -> base.log.N
    for ((i=MAX_ROTATIONS; i>=1; i--)); do
        if [[ -f "${ARCHIVE_DIR}/${base}.${i}" ]]; then
            if (( i == MAX_ROTATIONS )); then
                rm -f "${ARCHIVE_DIR}/${base}.${i}"
            else
                mv "${ARCHIVE_DIR}/${base}.${i}" "${ARCHIVE_DIR}/${base}.$((i+1))"
            fi
        fi
    done

    # move current log to .1 and truncate original
    mv "$file" "${ARCHIVE_DIR}/${base}.1"
    : > "$file"

    echo "Rotated ${file} (${size_mb} MB) -> ${ARCHIVE_DIR}/${base}.1"
}

for log in "${LOG_DIR}"/*.log; do
    [[ -e "$log" ]] || continue
    rotate_one "$log"
done
