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
python3:
python3 "Supermarket Price Crawler.py"

python1:
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

## 🍪 Lấy giá Shopee (dùng cookie – Cách 1: file)

Nếu Shopee không trả giá (0%), dùng cookie từ trình duyệt (sau khi đăng nhập Shopee):

### Cách 1: File cookie (mặc định)

1. Mở file **`Supermarket Price Crawler/config/shopee_cookies.txt`** (đã có sẵn trong project).
2. Trong Chrome: F12 → **Application** → **Cookies** → chọn `https://shopee.vn`.
3. Từ bảng Name/Value, ghi vào file **mỗi dòng một cookie**: `Tên=Giá_trị`  
   Ví dụ:
   ```
   SPC_U=848572921
   SPC_SI=xxxx
   SPC_T_ID=xxxx
   csrftoken=...
   ```
   (nên có đủ các cookie `SPC_`).
4. Lưu file, rồi chạy crawler **bình thường** (không cần set biến môi trường):
   ```bash
   python3 "Supermarket Price Crawler.py" --cli --config "Supermarket Price Crawler/config/DATA - LINK.csv" --output out.csv
   ```
   Script tự đọc `config/shopee_cookies.txt` khi crawl Shopee. Nếu bạn để file cookie ở chỗ khác, set `SHOPEE_COOKIE_FILE` trỏ tới đường dẫn đó.

### Cách 2: Chuỗi cookie (một dòng)

Gộp tất cả cookie thành **một dòng**, dạng: `Name1=Value1; Name2=Value2; ...`

- Trong bảng cookie: với mỗi dòng Name/Value, ghi `Name=Value`, rồi nối các dòng bằng `; ` (chấm phẩy + space).
- Đặt vào biến môi trường:
  ```bash
  export SHOPEE_COOKIE="SPC_U=848572921; SPC_SI=...; SPC_T_ID=...; csrftoken=..."
  python3 "Supermarket Price Crawler.py" --cli ...
  ```

Cookie sẽ được dùng cho cả **request API** và **browser headless** khi crawl Shopee.

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






