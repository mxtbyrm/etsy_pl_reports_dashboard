# 🔧 Fix: "Too many open files" Error

## Problem

When running with high concurrency, you may see:

```
ERROR - accept error: Too many open files (os error 24)
ERROR - Error fetching ad spend: All connection attempts failed
```

This happens because macOS has a low default limit on open file descriptors (256).

---

## Quick Fix (Recommended)

### Option 1: Run the fix script

```bash
source fix_file_limits.sh
python reportsv4_optimized.py
```

### Option 2: Manual command

```bash
ulimit -n 4096
python reportsv4_optimized.py
```

---

## What We Changed

### 1. Reduced Default Concurrency

- **Before**: `max_concurrent = 5` (too aggressive)
- **After**: `max_concurrent = 3` (safer default)

### 2. Added Small Delays Between Chunks

- Prevents file descriptor exhaustion
- Tiny 10ms pause between processing chunks
- Minimal impact on speed

### 3. Added Retry Logic with Exponential Backoff

- If connection fails, retry up to 3 times
- Delays: 1s → 2s → 4s between retries
- Prevents cascade failures

### 4. Added Startup Warning

- Checks file descriptor limits on startup
- Warns if limit is too low
- Suggests fix command

---

## Permanent Fix (Optional)

To permanently increase the limit, add to your `~/.zshrc` file:

```bash
# Add this line to ~/.zshrc
ulimit -n 4096
```

Then reload:

```bash
source ~/.zshrc
```

---

## Performance Tuning

### For Most Users (Default)

```bash
python reportsv4_optimized.py
# Uses: max_concurrent=3, batch_size=100
```

### For High-Performance Systems

**First, increase file limits:**

```bash
ulimit -n 8192
```

**Then run with higher concurrency:**

```bash
python reportsv4_optimized.py --max-concurrent 5 --batch-size 200
```

### For Systems with Limited Resources

```bash
python reportsv4_optimized.py --max-concurrent 2 --batch-size 50
```

---

## Understanding File Descriptors

Every database connection uses file descriptors:

- Database connection: 1 file descriptor
- Log file: 1 file descriptor
- CSV files: ~10 file descriptors
- HTTP connections (Prisma): Multiple file descriptors

With `max_concurrent=5`:

- 5 parallel tasks × ~3 connections each = ~15 connections
- Plus other system overhead
- Can easily hit 256 limit!

With `max_concurrent=3`:

- 3 parallel tasks × ~3 connections each = ~9 connections
- Much safer margin

---

## Monitoring

### Check Current Limit

```bash
ulimit -n
```

### Check Current Usage (macOS)

```bash
lsof -p $$ | wc -l
```

### Monitor During Execution

```bash
# In another terminal
watch -n 1 'lsof -p $(pgrep -f reportsv4_optimized) | wc -l'
```

---

## Still Having Issues?

### 1. Check Your Database Connection

```bash
# Is it remote or local?
# Remote databases use more file descriptors
```

### 2. Reduce Concurrency Further

```bash
python reportsv4_optimized.py --max-concurrent 2
```

### 3. Check System Limits

```bash
# Soft limit (user changeable)
ulimit -n

# Hard limit (system maximum)
ulimit -Hn
```

### 4. Contact Support

If still failing:

1. Run: `ulimit -n` and share the output
2. Run: `ulimit -Hn` and share the output
3. Share your system: `uname -a`
4. Share database location (local/remote)

---

## Summary

✅ **Reduced concurrency** to 3 (from 5)  
✅ **Added retry logic** with exponential backoff  
✅ **Added small delays** between chunks  
✅ **Added startup check** for file limits  
✅ **Created fix script** for easy setup

**Result**: Should run smoothly without "too many open files" errors!

---

## Before Running

Always run one of these first:

```bash
# Option 1: Use fix script
source fix_file_limits.sh

# Option 2: Manual command
ulimit -n 4096
```

Then:

```bash
python reportsv4_optimized.py
```

🚀 Happy processing!
