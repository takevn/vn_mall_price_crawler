#!/usr/bin/env python3
"""Fetch store pages and find price element (tag + class) for crawler."""
import requests
from bs4 import BeautifulSoup
import re

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36'}

# store_key in class_name.txt : (display_name, url)
SITES = [
    ("nguyenkim", "Nguyễn Kim", "https://www.nguyenkim.com/may-in-laser-trang-den-brother-hl-l2361dn.html"),
    ("fptshop", "FPT Shop", "https://fptshop.com.vn/may-in/may-in-brother-laser-hl-l2321d"),
    ("pico", "Pico", "https://pico.vn/27286/may-in-laser-brother-hll2361dn.html"),
    ("mediamart", "Mediamart", "https://mediamart.vn/may-in/brother/may-in-da-chuc-nang-brother-hl-l2361dn-induplexnetwork.htm"),
    ("hc", "HC", "https://hc.com.vn/ords/p--may-in-laser-brother-hl-l2321d-in-duplex"),
    ("phucanh", "Phúc Anh", "https://www.phucanh.vn/may-in-laser-den-trang-brother-hl-l2321d.html"),
    ("cpn", "CPN", "https://cpn.vn/products/may-in-laser-brother-hl-l2321d.html"),
    ("anphat", "An Phát", "https://www.anphatpc.com.vn/may-in-laser-brother-hl-l2321d-duplex_id17113.html"),
]

def find_price_elements(soup):
    """Find elements that contain a VND price (e.g. 2.900.000 or 3,500,000)."""
    candidates = []
    for el in soup.find_all(string=re.compile(r'\d{1,3}[.,]\d{3}[.,]\d{3}')):
        p = el.parent
        for _ in range(6):
            if not p or not hasattr(p, 'name'):
                break
            if p.name and p.get('class'):
                text = p.get_text(strip=True)
                if re.search(r'\d{1,3}[.,]\d{3}[.,]\d{3}', text) and len(text) < 50:
                    cls = ' '.join(p.get('class', []))
                    candidates.append((p.name, cls, text[:60]))
            p = p.parent
    return candidates

def main():
    for store_key, name, url in SITES:
        print(f"\n{'='*60}\n{name} ({store_key})\nURL: {url}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=12)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, 'lxml')
            cands = find_price_elements(soup)
            if cands:
                # Prefer element with "price" in class or short text
                for tag, cls, text in cands[:3]:
                    print(f"  tag={tag!r} class={cls!r} -> {text!r}")
            else:
                print("  No price-like element found in HTML")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    main()
