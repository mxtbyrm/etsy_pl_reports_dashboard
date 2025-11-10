#!/bin/bash
# Fix "Too many open files" error on macOS
# Run this before executing reportsv4_optimized.py

echo "🔧 Fixing file descriptor limits for current session..."

# Check current limits
echo "Current limits:"
ulimit -n

# Set higher limits (for current session only)
ulimit -n 4096

echo "New limits:"
ulimit -n

echo ""
echo "✅ File descriptor limit increased to 4096"
echo ""
echo "⚠️  Note: This only affects the current terminal session."
echo "   To make permanent, add to ~/.zshrc or ~/.bash_profile:"
echo "   ulimit -n 4096"
echo ""
echo "Now run: python reportsv4_optimized.py"
