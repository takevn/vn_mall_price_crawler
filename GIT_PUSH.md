# Chuẩn bị push lên GitHub

## Đã cấu hình .gitignore

Các thứ **sẽ không** bị đẩy lên GitHub (repo sẽ nhẹ):

| Thư mục / file | Dung lượng ước tính | Lý do |
|----------------|---------------------|--------|
| `venv/` | ~315 MB | Môi trường ảo Python — mỗi máy tự tạo |
| `dist/`, `dist.zip` | ~600 MB | Bản build Mac (.app, .dmg) — build lại khi cần |
| `build/` | ~25 MB | Cache PyInstaller |
| `Supermarket Price Crawler/*` **trừ** `config/` | ~158 MB | Build Windows cũ (.exe, .dll, thư viện) — không dùng cho code |
| `output_prices*.csv` | nhỏ | Kết quả chạy thử — giữ local |
| `__pycache__/`, `*.pyc`, `.DS_Store`, `*.swp` | nhỏ | File tạm / hệ thống |

**Chỉ có** `Supermarket Price Crawler/config/` (DATA.csv, class_name.txt, ...) trong thư mục đó được đẩy lên.

---

## Nếu muốn xóa hẳn trên máy cho đỡ nặng

Sau khi đã push (và yên tâm repo đủ file), bạn có thể **xóa local** để tiết kiệm ổ cứng:

1. **Xóa build / cache:**  
   `dist/`, `dist.zip`, `build/`, `*.spec`  
   → Có thể xóa an toàn, khi cần build lại sẽ tạo mới.

2. **Xóa thư mục build Windows cũ (158 MB):**  
   Chỉ xóa **bên trong** `Supermarket Price Crawler/` **trừ** thư mục `config`:
   ```bash
   cd "Supermarket Price Crawler"
   # Xóa mọi thứ trừ config
   find . -maxdepth 1 ! -name config ! -name . ! -name .. -exec rm -rf {} +
   cd ..
   ```
   Hoặc thủ công: xóa toàn bộ file/thư mục trong `Supermarket Price Crawler/` nhưng **giữ nguyên** thư mục `Supermarket Price Crawler/config/` và toàn bộ file bên trong.

**Không xóa:** `venv/` nếu bạn vẫn chạy project trên Mac (hoặc xóa rồi tạo lại: `python3 -m venv venv` và `pip install -r requirements.txt`).

---

## Lần đầu push

```bash
cd "/Users/manh/Projects/Supermarket Price Crawler"
git init
git add .
git status   # Kiểm tra: không có venv, dist, build, Supermarket Price Crawler/* (trừ config)
git commit -m "Initial commit: crawler + config + GitHub Actions build"
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
git push -u origin main
```

Sau khi push, repo trên GitHub chỉ còn cỡ vài MB (code + config), không còn ~1 GB.
