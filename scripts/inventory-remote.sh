#!/usr/bin/env bash
set -euo pipefail

# Read-only inventory. It does not copy, deploy, restart, or modify production.
PROJECT_DIR="${PROJECT_DIR:-/var/www/html/django/fgpy}"
SERVICE_NAME="${SERVICE_NAME:-dashboard_fgpy.service}"

test -d "$PROJECT_DIR"
printf 'project=%s\n' "$PROJECT_DIR"
find "$PROJECT_DIR" -xdev -type f \
  ! -path '*/.env' \
  ! -path '*/media/*' \
  ! -name '*.sqlite3' \
  ! -name '*.sql' \
  -printf '%s|%TY-%Tm-%TdT%TH:%TM:%TS|%p\n' | sort
printf 'service='
systemctl is-active "$SERVICE_NAME"
