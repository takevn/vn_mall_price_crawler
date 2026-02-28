# Phân Tích File run_crawler.py

## 📋 Tổng Quan

File `run_crawler.py` là một **wrapper script** (script bọc ngoài) để chạy Supermarket Price Crawler từ command line với các tùy chọn linh hoạt.

## 🔍 Phân Tích Chi Tiết

### 1. **Import và Setup (Dòng 6-14)**

```python
import sys, os, argparse
from pathlib import Path

crawler_dir = Path(__file__).parent / "Supermarket Price Crawler"
```

**Chức năng:**
- Import các thư viện cần thiết
- Tự động tìm thư mục `Supermarket Price Crawler` 
- Thêm vào Python path để có thể import modules

**Giải thích:**
- `Path(__file__).parent`: Lấy thư mục chứa file hiện tại
- `sys.path.insert(0, ...)`: Thêm đường dẫn vào đầu danh sách để ưu tiên import

---

### 2. **Argument Parser - Các Tham Số Command Line (Dòng 17-61)**

Script hỗ trợ 5 tham số:

#### a) `--config` (Dòng 29-34)
```python
parser.add_argument('--config', type=str, default='config/DATA.csv', ...)
```
- **Mục đích:** Chỉ định file cấu hình DATA.csv
- **Mặc định:** `config/DATA.csv`
- **Ví dụ:** `python run_crawler.py --config "Supermarket Price Crawler/config/DATA.csv"`

#### b) `--output` (Dòng 36-41)
```python
parser.add_argument('--output', type=str, default='output_prices.csv', ...)
```
- **Mục đích:** Tên file output cho kết quả crawl
- **Mặc định:** `output_prices.csv`
- **Ví dụ:** `python run_crawler.py --output "results_2024.csv"`

#### c) `--stores` (Dòng 43-47)
```python
parser.add_argument('--stores', nargs='+', ...)
```
- **Mục đích:** Chọn các store cụ thể để crawl
- **`nargs='+'`:** Cho phép nhập nhiều giá trị
- **Ví dụ:** `python run_crawler.py --stores phongvu nguyenkim dienmayxanh`

#### d) `--fix-merge` (Dòng 49-53)
```python
parser.add_argument('--fix-merge', action='store_true', ...)
```
- **Mục đích:** Tự động áp dụng fix cho lỗi Model column
- **`action='store_true'`:** Chỉ cần có flag là True, không cần giá trị
- **Ví dụ:** `python run_crawler.py --fix-merge`

#### e) `--verbose` (Dòng 55-59)
```python
parser.add_argument('--verbose', action='store_true', ...)
```
- **Mục đích:** Hiển thị log chi tiết khi có lỗi
- **Ví dụ:** `python run_crawler.py --verbose`

---

### 3. **Logic Tìm File Crawler (Dòng 64-73)**

```python
main_script = Path("Supermarket Price Crawler.py")
if not main_script.exists():
    main_script = crawler_dir / "Supermarket Price Crawler.py"
```

**Quy trình:**
1. Tìm file `Supermarket Price Crawler.py` ở thư mục hiện tại
2. Nếu không có, tìm trong subdirectory `Supermarket Price Crawler/`
3. Nếu vẫn không có → Báo lỗi và thoát

**Lý do:** Hỗ trợ cả 2 cấu trúc thư mục:
- File ở root: `./Supermarket Price Crawler.py`
- File ở subdirectory: `./Supermarket Price Crawler/Supermarket Price Crawler.py`

---

### 4. **Xử Lý Fix Merge (Dòng 80-82) - ĐÃ CẢI THIỆN**

**Trước (chỉ in thông báo):**
```python
if args.fix_merge:
    print("Applying merge fix for Model column...")
    # The fix should be applied in the main script
```

**Sau (thực sự load module):**
```python
if args.fix_merge:
    print("Applying merge fix for Model column...")
    try:
        from fix_merge_issue import safe_merge
        print("Fix module loaded successfully")
    except ImportError:
        print("Warning: fix_merge_issue.py not found...")
```

**Cải thiện:** Script sẽ thực sự import module fix thay vì chỉ in thông báo.

---

### 5. **Thực Thi Crawler (Dòng 84-100) - ĐÃ CẢI THIỆN**

**Trước (chỉ in hướng dẫn):**
```python
print("\nTo run the crawler:")
print(f"  python \"{main_script}\"")
```

**Sau (thực sự chạy):**
```python
if main_script.exists() and main_script.suffix == '.py':
    # Chạy Python script
    import subprocess
    result = subprocess.run([sys.executable, str(main_script)], 
                           cwd=str(main_script.parent))
    return result.returncode
elif (crawler_dir / "Supermarket Price Crawler.exe").exists():
    # Chạy executable
    exe_path = crawler_dir / "Supermarket Price Crawler.exe"
    result = subprocess.run([str(exe_path)], 
                           cwd=str(exe_path.parent))
    return result.returncode
```

**Cải thiện:**
- ✅ Tự động phát hiện file .py hoặc .exe
- ✅ Thực sự chạy crawler bằng `subprocess.run()`
- ✅ Trả về exit code để biết thành công/thất bại
- ✅ Chạy từ đúng thư mục (cwd)

---

## 🎯 Cách Sử Dụng

### Cơ Bản
```bash
python run_crawler.py
```

### Với Các Tùy Chọn
```bash
# Chỉ định config file
python run_crawler.py --config "Supermarket Price Crawler/config/DATA.csv"

# Chỉ định output file
python run_crawler.py --output "results.csv"

# Chọn stores cụ thể
python run_crawler.py --stores phongvu nguyenkim

# Áp dụng fix merge
python run_crawler.py --fix-merge

# Kết hợp nhiều tùy chọn
python run_crawler.py --config config/DATA.csv --output results.csv --verbose
```

### Xem Help
```bash
python run_crawler.py --help
```

---

## ⚠️ Hạn Chế Hiện Tại

1. **Chưa truyền arguments vào crawler:**
   - Script nhận `--config`, `--output`, `--stores` nhưng chưa truyền vào crawler
   - Cần modify crawler để nhận arguments hoặc set environment variables

2. **Fix merge chưa tự động:**
   - `--fix-merge` chỉ load module, chưa tự động patch code
   - Cần apply fix thủ công vào source file

3. **Chưa xử lý lỗi chi tiết:**
   - Nếu crawler fail, chỉ trả về exit code
   - Có thể cải thiện để capture và hiển thị error message

---

## 🔧 Đề Xuất Cải Thiện

### 1. Truyền Arguments vào Crawler
```python
# Set environment variables
os.environ['CRAWLER_CONFIG'] = args.config
os.environ['CRAWLER_OUTPUT'] = args.output
if args.stores:
    os.environ['CRAWLER_STORES'] = ','.join(args.stores)
```

### 2. Tự Động Apply Fix
```python
if args.fix_merge:
    # Tự động patch file source
    apply_fix_to_source(main_script)
```

### 3. Better Error Handling
```python
try:
    result = subprocess.run(...)
    if result.returncode != 0:
        print(f"Error: Crawler exited with code {result.returncode}")
except Exception as e:
    print(f"Failed to run crawler: {e}")
```

---

## 📊 Flow Diagram

```
run_crawler.py
    │
    ├─ Parse Arguments (--config, --output, --stores, --fix-merge, --verbose)
    │
    ├─ Tìm File Crawler
    │   ├─ Thư mục hiện tại
    │   └─ Subdirectory "Supermarket Price Crawler"
    │
    ├─ Nếu --fix-merge:
    │   └─ Import fix_merge_issue module
    │
    └─ Thực Thi
        ├─ Nếu là .py → python script
        ├─ Nếu là .exe → chạy executable
        └─ Trả về exit code
```

---

## ✅ Kết Luận

File `run_crawler.py` là một wrapper script hữu ích để:
- ✅ Cung cấp command-line interface cho crawler
- ✅ Hỗ trợ nhiều tùy chọn linh hoạt
- ✅ Tự động tìm và chạy crawler
- ✅ Xử lý cả .py và .exe

**Đã được cải thiện để thực sự chạy crawler thay vì chỉ in hướng dẫn!**






