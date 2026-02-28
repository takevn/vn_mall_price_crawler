# Build file .exe cho Windows (khi bạn chỉ có Mac)

PyInstaller **không cross-compile**: build trên Mac chỉ ra app macOS, không ra .exe. Có 2 hướng:

---

## Cách 1: Build .exe bằng GitHub Actions (khuyến nghị)

Bạn code trên Mac, push lên GitHub → server Windows của GitHub tự build → tải file .zip chứa .exe về.

### Bước 1: Đưa project lên GitHub

- Tạo repo trên GitHub (ví dụ `your-user/supermarket-price-crawler`).
- Trong terminal (trên Mac):

```bash
cd "/Users/manh/Projects/Supermarket Price Crawler"
git init
git add .
git commit -m "Add GitHub Actions build"
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### Bước 2: Chạy build

- Vào repo trên GitHub → tab **Actions**.
- Workflow **"Build Windows EXE"** sẽ tự chạy mỗi lần push lên `main` (hoặc `master`).
- Hoặc bấm **Actions** → chọn **Build Windows EXE** → **Run workflow**.

### Bước 3: Tải bản đóng gói

- Khi chạy xong, vào lần chạy vừa chạy (workflow run).
- Phần **Artifacts** có file **SupermarketPriceCrawler-Windows**.
- Bấm tải về → giải nén. Trong đó có:
  - `Supermarket Price Crawler.exe`
  - thư mục `Supermarket Price Crawler\config`

Gửi nguyên thư mục (hoặc zip lại) cho máy Windows để dùng. Trên máy Windows cần cài [Python](https://www.python.org/downloads/) và chạy một lần: `python -m playwright install chromium` (nếu dùng tính năng Nguyễn Kim / Pico).

---

## Cách 2: Build trực tiếp trên máy Windows

Nếu có máy Windows (hoặc VM Windows trên Mac):

1. Cài Python 3.11, mở cmd/powerhell tại thư mục project.
2. `pip install -r requirements.txt pyinstaller playwright`  
   `playwright install chromium`
3. Build:

```cmd
pyinstaller --onedir --name "Supermarket Price Crawler" --add-data "Supermarket Price Crawler\config;Supermarket Price Crawler\config" "Supermarket Price Crawler.py"
```

4. Lấy bản đóng gói trong `dist\Supermarket Price Crawler\`.

---

Đã có sẵn workflow trong `.github/workflows/build-windows.yml`; chỉ cần push code lên GitHub là dùng được Cách 1.
