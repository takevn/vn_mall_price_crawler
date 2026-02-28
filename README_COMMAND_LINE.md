# Supermarket Price Crawler - Command Line Usage

## Quick Start

### Method 1: Run the Executable
```bash
cd "Supermarket Price Crawler"
.\"Supermarket Price Crawler.exe"
```

### Method 2: Run Python Script (if source available)
```bash
python "Supermarket Price Crawler.py"
```

### Method 3: Use the Wrapper Script
```bash
python run_crawler.py
```

## Command Line Options

### Using run_crawler.py wrapper:

```bash
# Basic usage
python run_crawler.py

# Specify custom config file
python run_crawler.py --config "Supermarket Price Crawler/config/DATA.csv"

# Specify output file
python run_crawler.py --output results.csv

# Crawl specific stores only
python run_crawler.py --stores phongvu nguyenkim dienmayxanh

# Enable verbose output
python run_crawler.py --verbose

# Apply merge fix automatically
python run_crawler.py --fix-merge
```

## Direct Python Execution

If you have the source file `Supermarket Price Crawler.py`:

```bash
# Windows PowerShell
python "Supermarket Price Crawler.py"

# Windows CMD
python "Supermarket Price Crawler.py"

# With arguments (if supported)
python "Supermarket Price Crawler.py" --help
```

## Project Structure

```
Supermarket Price Crawler/
├── Supermarket Price Crawler.exe      # Compiled executable
├── Supermarket Price Crawler.py       # Source file (if available)
├── config/
│   ├── DATA.csv                       # Product data with URLs
│   └── class_name.txt                 # CSS selectors for each store
├── fix_merge_issue.py                 # Fix script for Model column issue
├── run_crawler.py                     # Command-line wrapper
└── README_COMMAND_LINE.md             # This file
```

## Troubleshooting

### Error: KeyError: 'Model'
**Solution**: Apply the fix from `FIX_INSTRUCTIONS.md`

1. Import the fix module:
   ```python
   from fix_merge_issue import safe_merge
   ```

2. Replace line 366 merge with:
   ```python
   result = safe_merge(original_df, scraped_df, on='Model', how='left')
   ```

### Error: Cannot find source file
If `Supermarket Price Crawler.py` is not found:
- The project may be compiled into `.exe` only
- Run the executable directly: `.\"Supermarket Price Crawler.exe"`
- Or extract the source from the executable if needed

### Error: Module not found
Install required dependencies:
```bash
pip install pandas requests beautifulsoup4 lxml gooey
```

## Expected Output

When running successfully, you should see:
- Progress bars showing crawling progress (0/71 to 71/71)
- Output CSV file with prices from all stores
- No KeyError exceptions

## Configuration

### DATA.csv Format
The `config/DATA.csv` file should have:
- First column: `Model` (product model names)
- Second column: `Giá tiêu chuẩn` (standard price)
- Subsequent columns: Store names with URLs

### class_name.txt Format
Contains CSS selectors for each store to extract prices:
```
#phongvu
span
css-htm2b9
-1
```

## Advanced Usage

### Batch Processing
```bash
# Process multiple config files
for file in config/*.csv; do
    python run_crawler.py --config "$file" --output "output_$(basename $file)"
done
```

### Scheduled Runs (Windows Task Scheduler)
1. Create a batch file `run_crawler.bat`:
   ```batch
   @echo off
   cd /d "D:\99. Manh\00.Work\Báo Cáo Giá\Supermarket Price Crawler"
   python run_crawler.py --output "results_%date:~-4,4%%date:~-7,2%%date:~-10,2%.csv"
   ```
2. Schedule it in Task Scheduler

## Support

For issues:
1. Check `FIX_INSTRUCTIONS.md` for common fixes
2. Enable `--verbose` flag for detailed error messages
3. Check that `config/DATA.csv` has the correct format
4. Verify all store URLs in DATA.csv are accessible






