# Quick Start Guide - Fix & Run Supermarket Price Crawler

## 🚀 Quick Fix (5 minutes)

### Step 1: Apply the Fix

**If you have the source file `Supermarket Price Crawler.py`:**

1. **Open the file** in any text editor
2. **Find line 366** (or search for `pd.merge`)
3. **Add import at the top** (around line 1-20):
   ```python
   from fix_merge_issue import safe_merge
   ```
4. **Replace the merge line** (around line 366):
   ```python
   # OLD:
   result = pd.merge(original_df, scraped_df, on='Model', how='left')
   
   # NEW:
   result = safe_merge(original_df, scraped_df, on='Model', how='left')
   ```
5. **Save the file**

### Step 2: Run the Crawler

**Option A: Using batch file (Windows)**
```cmd
run_crawler.bat
```

**Option B: Using Python directly**
```cmd
python "Supermarket Price Crawler.py"
```

**Option C: Using executable**
```cmd
cd "Supermarket Price Crawler"
"Supermarket Price Crawler.exe"
```

**Option D: Using wrapper script**
```cmd
python run_crawler.py
```

## 📋 What Was Fixed

The error `KeyError: 'Model'` occurred because:
- The crawler scrapes prices and creates a DataFrame
- This DataFrame doesn't include the 'Model' column
- When merging with the original DATA.csv, pandas fails

**The fix:**
- `safe_merge()` function ensures both DataFrames have the 'Model' column before merging
- Automatically handles missing columns and provides helpful error messages

## 📁 Files Created

1. **`fix_merge_issue.py`** - The fix module with `safe_merge()` function
2. **`run_crawler.py`** - Command-line wrapper script
3. **`run_crawler.bat`** - Windows batch file for easy execution
4. **`FIX_INSTRUCTIONS.md`** - Detailed fix instructions
5. **`README_COMMAND_LINE.md`** - Complete command-line documentation
6. **`PATCH_LINE_366.txt`** - Exact patch to apply
7. **`QUICK_START.md`** - This file

## 🔍 Verify the Fix

After applying the fix, you should see:
- ✅ No `KeyError: 'Model'` error
- ✅ Progress bars showing crawling (0/71 to 71/71)
- ✅ Successful completion
- ✅ Output file with prices

## ❓ Troubleshooting

**If you don't have the source file:**
- The project may be compiled into `.exe` only
- You'll need to extract the source or get it from the developer
- Or use a Python decompiler if needed

**If the fix doesn't work:**
1. Check that `fix_merge_issue.py` is in the same directory
2. Verify the import statement is correct
3. Check `PATCH_LINE_366.txt` for alternative fix options
4. Use Option 3 (debug version) to see what's happening

## 📞 Need More Help?

- See `FIX_INSTRUCTIONS.md` for detailed explanations
- See `README_COMMAND_LINE.md` for command-line options
- Check `PATCH_LINE_366.txt` for alternative fix methods






