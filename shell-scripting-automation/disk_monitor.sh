#!/usr/bin/env bash
#
# disk_monitor.sh - Warn if any filesystem exceeds threshold

set -euo pipefail

THRESHOLD=80          # percent used
MAIL_TO=""            # set to email address to send mail, or leave empty for stdout only

# List filesystems from df and check usage
df -hP | awk 'NR>1 && $1 ~ "^/dev/" {print $1, $5, $6}' | while read -r dev use mount; do
    # Strip % sign
    percent=${use%%%}

    if (( percent >= THRESHOLD )); then
        msg="Warning: ${mount} (${dev}) is at ${percent}% on $(hostname) at $(date)"
        if [[ -n "${MAIL_TO}" ]]; then
            echo "${msg}" | mail -s "Disk alert: $(hostname) ${mount} ${percent}%" "${MAIL_TO}"
        else
            echo "${msg}"
        fi
    else
        echo "OK: ${mount} (${dev}) is at ${percent}%"
    fi
done
