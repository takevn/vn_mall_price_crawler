# Hướng Dẫn Setup Google Drive Upload

Để tự động upload file build lên Google Drive sau khi workflow chạy xong, bạn cần setup Google Drive API credentials.

## Bước 1: Tạo Google Cloud Project và Service Account

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo project mới hoặc chọn project hiện có
3. Vào **APIs & Services** > **Library**
4. Tìm và enable **Google Drive API**
5. Vào **APIs & Services** > **Credentials**
6. Click **Create Credentials** > **Service Account**
7. Điền thông tin:
   - Service account name: `github-actions-uploader`
   - Service account ID: tự động tạo
   - Click **Create and Continue**
8. Bỏ qua phần Grant access (không cần)
9. Click **Done**

## Bước 2: Tạo và Download Key

1. Trong danh sách Service Accounts, click vào service account vừa tạo
2. Vào tab **Keys**
3. Click **Add Key** > **Create new key**
4. Chọn **JSON**
5. Click **Create** - file JSON sẽ được tải về

## Bước 3: Share Google Drive Folder với Service Account

1. Mở file JSON vừa tải, copy **client_email** (có dạng: `xxx@xxx.iam.gserviceaccount.com`)
2. Mở Google Drive folder: https://drive.google.com/drive/folders/1nKs_BQqje1WT5cOMNf0S_1Tu1gx5PnP3
3. Click **Share** (Chia sẻ)
4. Paste email service account vào
5. Chọn quyền **Editor** (Người chỉnh sửa)
6. Click **Send**

## Bước 4: Thêm Credentials vào GitHub Secrets

1. Vào GitHub repository
2. Vào **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Name: `GDRIVE_CREDENTIALS`
5. Value: Copy toàn bộ nội dung file JSON vừa tải (bao gồm cả dấu `{}`)
6. Click **Add secret**

## Bước 5: Kiểm tra

1. Push code hoặc chạy workflow thủ công
2. Workflow sẽ tự động upload file build lên Google Drive folder
3. Kiểm tra folder Google Drive để xem file đã được upload

## Lưu ý

- File JSON credentials chứa thông tin nhạy cảm, **KHÔNG** commit vào git
- Nếu không setup credentials, workflow vẫn chạy bình thường nhưng sẽ bỏ qua bước upload
- File sẽ được upload với tên: `SupermarketPriceCrawler-Windows.zip`

## Troubleshooting

### Lỗi: "Permission denied"
- Đảm bảo đã share folder Google Drive với service account email
- Kiểm tra quyền của service account (phải là Editor hoặc Owner)

### Lỗi: "Invalid credentials"
- Kiểm tra lại nội dung JSON trong GitHub Secrets
- Đảm bảo đã enable Google Drive API

### Lỗi: "File not found"
- Kiểm tra đường dẫn SOURCE_DIR trong workflow
- Đảm bảo build step đã chạy thành công

