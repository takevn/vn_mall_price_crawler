# Hướng Dẫn Cài Đặt Dependencies

## ✅ Đã Cài Đặt Thành Công!

Tất cả các packages cần thiết đã được cài đặt:
- ✅ pandas
- ✅ requests
- ✅ beautifulsoup4
- ✅ lxml
- ✅ tqdm
- ✅ gooey

## 📦 Packages Đã Cài

```
pandas>=2.3.3
requests>=2.32.4
beautifulsoup4>=4.14.3
lxml>=6.0.2
tqdm>=4.67.1
gooey>=1.0.8.1
```

## 🚀 Chạy Script

Bây giờ bạn có thể chạy crawler:

```bash
# Method 1: Chạy trực tiếp
python "Supermarket Price Crawler.py"

# Method 2: Dùng wrapper
python run_crawler.py

# Method 3: Dùng batch file
run_crawler.bat
```

## 🔧 Nếu Cần Cài Lại

Nếu cần cài đặt lại các packages:

```bash
# Cài đặt từ requirements.txt
python -m pip install -r requirements.txt

# Hoặc cài đặt thủ công
python -m pip install pandas requests beautifulsoup4 lxml tqdm gooey
```

## ⚠️ Lưu Ý

- Python version: 3.13 (hiện tại)
- Tất cả packages được cài vào user site-packages
- Nếu gặp lỗi, thử upgrade pip: `python -m pip install --upgrade pip`

## 📝 File requirements.txt

File `requirements.txt` đã được tạo với danh sách đầy đủ dependencies.






