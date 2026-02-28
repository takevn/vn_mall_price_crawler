# Fix Instructions for KeyError: 'Model' Issue

## Problem
The crawler fails with `KeyError: 'Model'` at line 366 during a pandas merge operation. This happens because the scraped DataFrame doesn't have a 'Model' column before merging with the original DATA.csv.

## Solution

### Option 1: Quick Fix (Recommended)
Replace the merge operation at line 366 with the safe merge function:

**Find this code around line 366:**
```python
result = pd.merge(original_df, scraped_df, on='Model', how='left')
```

**Replace with:**
```python
# Import at the top of the file
from fix_merge_issue import safe_merge

# At line 366, replace merge with:
result = safe_merge(original_df, scraped_df, on='Model', how='left')
```

### Option 2: Manual Fix
Add Model column to scraped DataFrame before merging:

**Before line 366, add:**
```python
# Ensure scraped_df has Model column
if 'Model' not in scraped_df.columns:
    # Option A: If you have model list from original data
    if len(scraped_df) == len(original_df):
        scraped_df['Model'] = original_df['Model'].values
    # Option B: If scraped data has URLs, extract model from URLs
    elif 'URL' in scraped_df.columns or any('phongvu' in str(col).lower() for col in scraped_df.columns):
        # Extract model from first URL column
        url_col = [col for col in scraped_df.columns if 'phongvu' in str(col).lower() or 'url' in str(col).lower()][0]
        # Match with original data by URL
        scraped_df = scraped_df.merge(original_df[['Model', url_col]], on=url_col, how='left')
    # Option C: Use index-based matching
    else:
        scraped_df = scraped_df.reset_index(drop=True)
        original_df_indexed = original_df.reset_index(drop=True)
        if len(scraped_df) <= len(original_df_indexed):
            scraped_df['Model'] = original_df_indexed.loc[:len(scraped_df)-1, 'Model'].values
        else:
            raise ValueError("Scraped data has more rows than original data")

# Now perform merge
result = pd.merge(original_df, scraped_df, on='Model', how='left')
```

### Option 3: Debug First
Add debugging code to see what's happening:

```python
# Before line 366, add:
print("Original DataFrame columns:", original_df.columns.tolist())
print("Original DataFrame shape:", original_df.shape)
print("Scraped DataFrame columns:", scraped_df.columns.tolist())
print("Scraped DataFrame shape:", scraped_df.shape)
print("Scraped DataFrame head:")
print(scraped_df.head())

# Check if Model exists
if 'Model' not in scraped_df.columns:
    print("ERROR: 'Model' column missing from scraped_df!")
    print("Available columns:", scraped_df.columns.tolist())
    # Add fix here based on what you see
```

## How to Apply the Fix

1. **Locate the source file**: `Supermarket Price Crawler.py`
   - It should be in the same directory as the executable
   - Or in the parent directory

2. **Backup the file first**:
   ```bash
   copy "Supermarket Price Crawler.py" "Supermarket Price Crawler_backup.py"
   ```

3. **Apply Option 1 (easiest)**:
   - Add `from fix_merge_issue import safe_merge` at the top
   - Replace the merge at line 366 with `safe_merge()`

4. **Test the fix**:
   ```bash
   python "Supermarket Price Crawler.py"
   ```

## Root Cause Analysis

The issue occurs because:
1. The crawler scrapes prices from websites (71 items based on logs)
2. It creates a DataFrame with price columns for each store
3. This DataFrame doesn't include the 'Model' column
4. When trying to merge with original DATA.csv (which has 'Model'), pandas fails

The fix ensures the 'Model' column exists in the scraped DataFrame before merging.






