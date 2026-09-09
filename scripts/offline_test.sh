#!/usr/bin/env bash
# ==============================================================================
# Vyoma Offline Medical AI Assistant - Offline Mode Verification Shell Script
# Enforces complete zero-network isolation and executes comprehensive test suite.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "=== Executing Vyoma Offline Verification Suite ==="

# Check if unshare (network namespace) is available for strict isolation
if command -v unshare &> /dev/null && [ "$(id -u)" -eq 0 ]; then
    echo "[*] Running inside isolated network namespace (NO network interfaces except loopback)..."
    unshare -n python3 scripts/offline_test.py
else
    echo "[*] Running with Python-level socket interceptor (blocking all non-localhost outbound sockets)..."
    python3 scripts/offline_test.py 2>/dev/null || python scripts/offline_test.py
fi
