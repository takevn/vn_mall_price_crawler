# Danh Sách Các Siêu Thị

## 📍 Vị Trí Định Nghĩa

Danh sách các siêu thị được định nghĩa ở **2 nơi**:

### 1. Trong Code Python (Dòng 59-70)
File: `Supermarket Price Crawler.py`

```python
STORE_MAPPING = {
    'Phong Vũ': 'phongvu',
    'Nguyễn Kim': 'nguyenkim',
    'Điện máy xanh': 'dienmayxanh',
    'FPT Shop': 'fptshop',
    'Pico': 'pico',
    'Mediamart': 'mediamart',
    'HC': 'hc',
    'Phúc Anh': 'phucanh',
    'CPN': 'cpn',
    'An Phát': 'anphat',
    'Hà Nội Computer': 'hncomputer'
}
```

### 2. Trong File DATA.csv (Dòng 1 - Header)
File: `Supermarket Price Crawler/config/DATA.csv`

Các cột siêu thị trong CSV:
```
Model,Giá tiêu chuẩn,ID,Phong Vũ,Nguyễn Kim,Điện máy xanh,FPT Shop,Pico,Mediamart,HC,Phúc Anh,CPN,An Phát,Hà Nội Computer
```

## 📋 Danh Sách Đầy Đủ (11 Siêu Thị)

1. **Phong Vũ** (`phongvu`)
2. **Nguyễn Kim** (`nguyenkim`)
3. **Điện máy xanh** (`dienmayxanh`)
4. **FPT Shop** (`fptshop`)
5. **Pico** (`pico`)
6. **Mediamart** (`mediamart`)
7. **HC** (`hc`)
8. **Phúc Anh** (`phucanh`)
9. **CPN** (`cpn`)
10. **An Phát** (`anphat`)
11. **Hà Nội Computer** (`hncomputer`)

## 🔧 Cách Thêm/Xóa Siêu Thị

### Thêm Siêu Thị Mới:

1. **Cập nhật STORE_MAPPING** trong `Supermarket Price Crawler.py`:
```python
STORE_MAPPING = {
    # ... các siêu thị hiện có ...
    'Tên Siêu Thị Mới': 'ten-sieu-thi-moi'
}
```

2. **Thêm cột vào DATA.csv**:
   - Mở file `Supermarket Price Crawler/config/DATA.csv`
   - Thêm tên siêu thị vào header (dòng 1)
   - Thêm URL cho mỗi sản phẩm

3. **Thêm CSS selector vào class_name.txt**:
   - Mở file `Supermarket Price Crawler/config/class_name.txt`
   - Thêm cấu hình selector:
   ```
   #ten-sieu-thi-moi
   tag
   class-name
   nested_tag (hoặc -1)
   index (hoặc -1)
   ```

### Xóa Siêu Thị:

1. Xóa khỏi `STORE_MAPPING` trong code
2. Xóa cột khỏi `DATA.csv` (hoặc để trống)
3. Xóa selector khỏi `class_name.txt` (tùy chọn)

## 📝 Lưu Ý

- Tên siêu thị trong `STORE_MAPPING` phải **khớp chính xác** với tên cột trong `DATA.csv`
- Key trong `STORE_MAPPING` (ví dụ: `'phongvu'`) phải khớp với tên trong `class_name.txt` (ví dụ: `#phongvu`)
- Khi thêm siêu thị mới, cần test CSS selector để đảm bảo extract được giá đúng

## 🔍 Kiểm Tra Danh Sách Hiện Tại

Để xem danh sách siêu thị đang được sử dụng:

```python
# Trong code
print(STORE_MAPPING.keys())

# Hoặc từ DATA.csv
import pandas as pd
df = pd.read_csv('Supermarket Price Crawler/config/DATA.csv')
store_columns = [col for col in df.columns if col not in ['Model', 'Giá tiêu chuẩn', 'ID']]
print(store_columns)
```





