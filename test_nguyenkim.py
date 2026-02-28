#!/usr/bin/env python3
"""Chạy thử lấy giá Nguyễn Kim (headless). In ra giá hoặc lỗi chi tiết."""
import re

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Lỗi: Chưa cài playwright.")
    print("Chạy: python3 -m pip install playwright")
    print("Rồi:  python3 -m playwright install chromium")
    exit(1)

URL = "https://www.nguyenkim.com/may-in-laser-brother-hl-l2366dw.html"

def main():
    print("Đang mở trang Nguyễn Kim (headless)...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(20000)
        # User-Agent giống trình duyệt thật
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        page.goto(URL, wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(5000)  # chờ JS render giá

        text = ""
        for sel in ["div.nk2020-pdp-price", "[class*='pdp-price']", "[class*='product-price']"]:
            try:
                loc = page.locator(sel).first
                loc.wait_for(state="visible", timeout=8000)
                text = loc.inner_text(timeout=5000).strip()
                if text and re.search(r"\d{1,3}[.,]\d{3}[.,]\d{3}", text):
                    print(f"  Tìm thấy text từ selector: {sel}")
                    break
            except Exception as e:
                print(f"  Selector {sel}: {e}")

        if not text or not re.search(r"\d{1,3}[.,]\d{3}[.,]\d{3}", text):
            print("  Lấy toàn bộ body...")
            text = page.inner_text("body", timeout=8000)

        browser.close()

    if not text:
        print("Không lấy được text từ trang.")
        return

    matches = re.findall(r"(\d{1,3}(?:[.,]\d{3}){2,})", text)
    print(f"Số chuỗi giống giá tìm thấy: {len(matches)}")
    for m in matches[:5]:
        digits = re.sub(r"[^\d]", "", m)
        num = int(digits) if digits else 0
        if 50000 <= num <= 500000000:
            print(f"Giá (đ): {num}  <- từ chuỗi {m}")
            return
    if matches:
        digits = re.sub(r"[^\d]", "", matches[0])
        print(f"Giá (đ) lấy số đầu: {int(digits)}  <- từ {matches[0]}")
    else:
        print("Không tìm thấy số nào giống giá trong trang.")

if __name__ == "__main__":
    main()
