"""
Supermarket Price Crawler
Crawls prices from multiple Vietnamese e-commerce websites
"""

import warnings

try:
    # Suppress noisy urllib3 LibreSSL warning on macOS (does not affect behavior)
    import urllib3
    from urllib3.exceptions import NotOpenSSLWarning
    warnings.filterwarnings("ignore", category=NotOpenSSLWarning)
except Exception:
    # If urllib3 or the warning class isn't available yet, just continue.
    pass

import sys
import argparse
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import re
import os
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional
from tqdm import tqdm
import time
import subprocess
import platform
from datetime import datetime

# Fix Unicode encoding for Windows console
if platform.system() == 'Windows':
    try:
        # Set UTF-8 encoding for stdout and stderr
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        # Fallback for older Python versions or when reconfigure is not available
        try:
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except:
            pass

# Suppress SSL warnings for sites that require verify=False (e.g. HC)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass

# Safe print function for Unicode characters
def safe_print(*args, **kwargs):
    """Print function that handles Unicode encoding errors gracefully"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: encode to ASCII with replacement for problematic characters
        try:
            encoded_args = []
            for arg in args:
                if isinstance(arg, str):
                    encoded_args.append(arg.encode('ascii', 'replace').decode('ascii'))
                else:
                    encoded_args.append(str(arg).encode('ascii', 'replace').decode('ascii'))
            print(*encoded_args, **kwargs)
        except:
            # Last resort: print as bytes
            print(str(args).encode('ascii', 'replace').decode('ascii'))

try:
    # Optional: used only for headless crawling on some JS-heavy sites (e.g. nguyenkim)
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
try:
    from gooey import Gooey, GooeyParser
    HAS_GOOEY = True
except ImportError:
    HAS_GOOEY = False

try:
    from fix_merge_issue import safe_merge
except ImportError:
    # Fallback merge function if fix_merge_issue not available
    def safe_merge(left_df, right_df, on='Model', how='left', **kwargs):
        """Safe merge with Model column check"""
        if isinstance(on, str):
            on_list = [on]
        else:
            on_list = on
        
        for key in on_list:
            if key not in left_df.columns:
                print(f"Warning: '{key}' not in left DataFrame. Adding from index...")
                left_df = left_df.copy()
                left_df[key] = left_df.index
            if key not in right_df.columns:
                print(f"Warning: '{key}' not in right DataFrame. Adding from index...")
                right_df = right_df.copy()
                if len(right_df) == len(left_df):
                    right_df[key] = left_df[key].values
                else:
                    right_df[key] = [f"Item_{i+1}" for i in range(len(right_df))]
        
        return pd.merge(left_df, right_df, on=on, how=how, **kwargs)

# Configuration paths (hỗ trợ chạy từ .exe / .app khi đóng gói PyInstaller)
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "Supermarket Price Crawler" / "config"
if not CONFIG_DIR.exists():
    CONFIG_DIR = BASE_DIR / "config"

DATA_CSV = CONFIG_DIR / "DATA.csv"
CLASS_NAME_TXT = CONFIG_DIR / "class_name.txt"
MALL_DOMAIN_CSV = CONFIG_DIR / "MALL_DOMAIN.csv"

# Store name mapping
STORE_MAPPING = {
    # Canonical mall names (new)
    'DMX-TGDD': 'dienmayxanh',
    'CellphoneS': 'cellphones',
    'Media Mart': 'mediamart',
    'HACOM': 'hncomputer',
    'Shopee': 'shopee',
    # Existing display names (backwards compatible)
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

# Headers for requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def load_class_selectors():
    """Load CSS selectors from class_name.txt"""
    selectors = {}
    if not CLASS_NAME_TXT.exists():
        print(f"Warning: {CLASS_NAME_TXT} not found")
        return selectors
    
    with open(CLASS_NAME_TXT, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_store = None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('#'):
            current_store = line[1:].strip()
            selectors[current_store] = {}
            i += 1
            continue
        
        if current_store and line:
            if 'tag' not in selectors[current_store]:
                selectors[current_store]['tag'] = line
            elif 'class' not in selectors[current_store]:
                selectors[current_store]['class'] = line
            elif 'nested_tag' not in selectors[current_store]:
                if line != '-1':
                    selectors[current_store]['nested_tag'] = line
                else:
                    selectors[current_store]['nested_tag'] = None
            elif 'index' not in selectors[current_store]:
                selectors[current_store]['index'] = int(line) if line != '-1' else -1
        i += 1
    
    return selectors


def _normalize_domain(domain: str) -> str:
    domain = (domain or "").strip().lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def infer_mall_from_url(url: str, domain_to_mall: dict) -> Optional[str]:
    if not url or pd.isna(url):
        return None
    try:
        parsed = urlparse(str(url).strip())
        host = _normalize_domain(parsed.netloc)
        if not host:
            return None
        # direct match
        if host in domain_to_mall:
            return domain_to_mall[host]
        # subdomain match (e.g. something.hacom.vn)
        for dom, mall in domain_to_mall.items():
            if host == dom or host.endswith("." + dom):
                return mall
        return None
    except Exception:
        return None


def load_mall_domain_map() -> dict:
    """
    Load mall-domain mapping from CONFIG_DIR/MALL_DOMAIN.csv.
    Returns (domain_to_mall, mall_to_store_key).
    """
    if not MALL_DOMAIN_CSV.exists():
        return {}, {}
    try:
        # Use comment='#' so lines starting with '#' are treated as comments
        # Example: "#Shopee,shopee.vn,shopee" will be ignored (disable Shopee).
        df_map = pd.read_csv(MALL_DOMAIN_CSV, encoding="utf-8", comment="#")
        # allow flexible column names
        cols = {c.strip().lower(): c for c in df_map.columns}
        mall_col = cols.get("mall")
        domain_col = cols.get("domain")
        store_key_col = cols.get("storekey") or cols.get("store_key") or cols.get("store key")
        if not mall_col or not domain_col:
            return {}, {}
        domain_to_mall = {}
        mall_to_store_key = {}
        for _, r in df_map.iterrows():
            mall = str(r[mall_col]).strip()
            dom = _normalize_domain(str(r[domain_col]))
            if mall and dom and mall.lower() != "nan" and dom.lower() != "nan":
                domain_to_mall[dom] = mall
                if store_key_col:
                    sk = str(r[store_key_col]).strip().lower()
                    if sk and sk != "nan":
                        mall_to_store_key[mall] = sk
        return domain_to_mall, mall_to_store_key
    except Exception:
        return {}, {}


def extract_price_phongvu(url, soup):
    """Extract price from Phong Vũ using JSON-LD"""
    try:
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            data = json.loads(script.string)
            if isinstance(data, dict) and 'offers' in data:
                if isinstance(data['offers'], dict) and 'price' in data['offers']:
                    price = data['offers']['price']
                    if isinstance(price, (int, float)):
                        return int(price)
                    elif isinstance(price, str):
                        price = re.sub(r'[^\d]', '', price)
                        return int(price) if price else None
    except:
        pass
    return None


def extract_price_dienmayxanh(url, soup):
    """Extract price from Điện Máy Xanh using JSON-LD (more stable than UI price blocks)."""
    try:
        # If product is discontinued, return a clear label instead of None
        page_text = soup.get_text(" ", strip=True)
        # Prefer the full label when present
        if re.search(r"SẢN\s*PHẨM\s*Ngừng\s*kinh\s*doanh", page_text, flags=re.IGNORECASE):
            return "SẢN PHẨM Ngừng kinh doanh"
        # Fallback: accept generic wording (e.g. only "ngừng kinh doanh")
        if re.search(r"ngừng\s*kinh\s*doanh", page_text, flags=re.IGNORECASE):
            return "ngừng kinh doanh"

        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            raw = script.string
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except Exception:
                continue

            objs = data if isinstance(data, list) else [data]
            for obj in objs:
                if not isinstance(obj, dict):
                    continue
                offers = obj.get('offers')
                if not offers:
                    continue
                offer_list = offers if isinstance(offers, list) else [offers]
                for off in offer_list:
                    if not isinstance(off, dict):
                        continue
                    if 'price' not in off:
                        continue
                    price = off.get('price')
                    if isinstance(price, (int, float)):
                        num = int(price)
                    else:
                        digits = re.sub(r'[^\d]', '', str(price))
                        num = int(digits) if digits else None
                    if num and 50000 <= num <= 500000000:
                        return num
    except Exception:
        return None
    return None


def extract_price_dienmayxanh_headless(url):
    """Extract price from Điện Máy Xanh using headless browser when HTML/JSON-LD lacks price (e.g., price=0)."""
    if not HAS_PLAYWRIGHT:
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(20000)
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8"
            })
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(5000)

            price_pattern = re.compile(r"\d{1,3}(?:[.,]\d{3}){2,}")
            text = ""
            for sel in [
                "span.box-price-present",
                "div.box-price",
                "[class*='box-price-present']",
                "[class*='box-price']",
            ]:
                try:
                    loc = page.locator(sel).first
                    loc.wait_for(state="visible", timeout=6000)
                    t = loc.inner_text(timeout=3000).strip()
                    if t and price_pattern.search(t):
                        text = t
                        break
                except Exception:
                    continue

            if not text:
                try:
                    text = page.inner_text("body", timeout=8000)
                except Exception:
                    text = ""

            browser.close()

        if not text:
            return None
        matches = price_pattern.findall(text)
        for m in matches:
            digits = re.sub(r"[^\d]", "", m)
            if not digits:
                continue
            num = int(digits)
            if 50000 <= num <= 500000000:
                return num
        return None
    except Exception:
        return None


def extract_price_nguyenkim_jsonld(url, soup):
    """Extract price from Nguyễn Kim using JSON-LD structured data"""
    try:
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                # Handle both dict and list formats
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and 'offers' in item:
                            offers = item['offers']
                            if isinstance(offers, dict) and 'price' in offers:
                                price = offers['price']
                                if isinstance(price, (int, float)):
                                    return int(price)
                                elif isinstance(price, str):
                                    price = re.sub(r'[^\d]', '', price)
                                    return int(price) if price else None
                elif isinstance(data, dict):
                    # Check if 'offers' is directly in data
                    if 'offers' in data:
                        offers = data['offers']
                        if isinstance(offers, dict) and 'price' in offers:
                            price = offers['price']
                            if isinstance(price, (int, float)):
                                return int(price)
                            elif isinstance(price, str):
                                price = re.sub(r'[^\d]', '', price)
                                return int(price) if price else None
                    # Check if '@graph' contains offers
                    if '@graph' in data and isinstance(data['@graph'], list):
                        for item in data['@graph']:
                            if isinstance(item, dict) and 'offers' in item:
                                offers = item['offers']
                                if isinstance(offers, dict) and 'price' in offers:
                                    price = offers['price']
                                    if isinstance(price, (int, float)):
                                        return int(price)
                                    elif isinstance(price, str):
                                        price = re.sub(r'[^\d]', '', price)
                                        return int(price) if price else None
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
    except Exception:
        pass
    return None


def extract_price_hncomputer(url, soup):
    """Extract price from HACOM (hacom.vn). Page often has price in text/JSON-LD but not in a stable selector."""
    try:
        text = soup.get_text(" ", strip=True)
        # 0) Product discontinued: return exact label when present
        if re.search(r"SẢN\s*PHẨM\s*Ngừng\s*kinh\s*doanh", text, flags=re.IGNORECASE):
            return "SẢN PHẨM Ngừng kinh doanh"
        if re.search(r"ngừng\s*kinh\s*doanh", text, flags=re.IGNORECASE):
            return "ngừng kinh doanh"
        # 1) Try JSON-LD if present
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
                for obj in (data if isinstance(data, list) else [data]):
                    if not isinstance(obj, dict):
                        continue
                    offers = obj.get('offers')
                    if isinstance(offers, dict) and 'price' in offers:
                        p = offers['price']
                        num = int(p) if isinstance(p, (int, float)) else None
                        if not num and isinstance(p, str):
                            digits = re.sub(r'[^\d]', '', p)
                            num = int(digits) if digits else None
                        if num and 50000 <= num <= 500000000:
                            return num
            except Exception:
                continue
        # 2) Scan full page text for formatted VND (site often has price in text but not in selector-visible elements)
        text = soup.get_text(" ", strip=True)
        for m in re.findall(r'(\d{1,3}(?:[.,]\d{3}){2,})', text):
            digits = re.sub(r'[^\d]', '', m)
            if not digits:
                continue
            num = int(digits)
            if 50000 <= num <= 500000000:
                return num
        for m in re.findall(r'(\d{6,})', text.replace(" ", "")):
            try:
                num = int(m)
                if 50000 <= num <= 500000000:
                    return num
            except Exception:
                continue
        # 3) Page shows "Liên hệ" / contact for price (no numeric price in HTML)
        if re.search(r'Liên\s*hệ|Giá\s*đã\s*bao\s*gồm\s*VAT', text, re.IGNORECASE):
            return "Liên hệ"
    except Exception:
        pass
    return None


def extract_price_phucanh(url, soup):
    """Extract price from Phúc Anh (phucanh.vn). Prefer main product promo price."""
    try:
        # 1) Old selector span.detail-product-best-price (backwards compatible)
        price_pattern = re.compile(r"\d{1,3}(?:[.,]\d{3}){2,}")
        elements = soup.find_all("span", class_="detail-product-best-price")
        for el in elements:
            t = el.get_text(" ", strip=True)
            m = price_pattern.search(t)
            if not m:
                continue
            digits = re.sub(r"[^\d]", "", m.group(0))
            if not digits:
                continue
            num = int(digits)
            if 50000 <= num <= 500000000:
                return num

        # 2) Text near 'Giá Khuyến mãi'
        label_re = re.compile(r"giá\s*khuyến\s*mãi", re.IGNORECASE)
        for node in soup.find_all(string=lambda s: isinstance(s, str) and label_re.search(s)):
            parent = node.parent
            if not parent:
                continue
            candidate_texts = [parent.get_text(" ", strip=True)]
            sib = parent.next_sibling
            for _ in range(3):
                if not sib:
                    break
                if hasattr(sib, "get_text"):
                    candidate_texts.append(sib.get_text(" ", strip=True))
                sib = sib.next_sibling
            for text in candidate_texts:
                m = price_pattern.search(text)
                if not m:
                    continue
                digits = re.sub(r"[^\d]", "", m.group(0))
                if not digits:
                    continue
                num = int(digits)
                if 50000 <= num <= 500000000:
                    return num

        # 3) Fallback: first valid price on page
        full_text = soup.get_text(" ", strip=True)
        for m in price_pattern.findall(full_text):
            digits = re.sub(r"[^\d]", "", m)
            if not digits:
                continue
            num = int(digits)
            if 50000 <= num <= 500000000:
                return num
        # 4) No numeric price, but page says price is contact-only
        lowered = full_text.lower()
        if re.search(r"giá\s*bán[^0-9]{0,50}liên\s*hệ", lowered, flags=re.IGNORECASE) or \
           re.search(r"\bliên\s*hệ\b", lowered, flags=re.IGNORECASE):
            return "Liên hệ"
    except Exception:
        pass
    return None


def extract_price_cellphones(url, soup):
    """Extract price from CellphoneS (cellphones.com.vn). Tries JSON-LD then full-page VND scan."""
    try:
        text = soup.get_text(" ", strip=True)
        if re.search(r"SẢN\s*PHẨM\s*Ngừng\s*kinh\s*doanh", text, flags=re.IGNORECASE):
            return "SẢN PHẨM Ngừng kinh doanh"
        if re.search(r"ngừng\s*kinh\s*doanh", text, flags=re.IGNORECASE):
            return "ngừng kinh doanh"
        # 1) JSON-LD offers.price
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
                for obj in (data if isinstance(data, list) else [data]):
                    if not isinstance(obj, dict):
                        continue
                    offers = obj.get('offers')
                    if not offers:
                        continue
                    offer_list = offers if isinstance(offers, list) else [offers]
                    for off in offer_list:
                        if not isinstance(off, dict) or 'price' not in off:
                            continue
                        p = off.get('price')
                        num = int(p) if isinstance(p, (int, float)) else None
                        if not num and isinstance(p, str):
                            digits = re.sub(r'[^\d]', '', p)
                            num = int(digits) if digits else None
                        if num and 50000 <= num <= 500000000:
                            return num
            except Exception:
                continue
        # 2) Full page: formatted VND (e.g. 3.190.000đ)
        for m in re.findall(r'(\d{1,3}(?:[.,]\d{3}){2,})', text):
            digits = re.sub(r'[^\d]', '', m)
            if not digits:
                continue
            num = int(digits)
            if 50000 <= num <= 500000000:
                return num
        for m in re.findall(r'(\d{6,})', text.replace(" ", "")):
            try:
                num = int(m)
                if 50000 <= num <= 500000000:
                    return num
            except Exception:
                continue
        if re.search(r'Liên\s*hệ', text, re.IGNORECASE):
            return "Liên hệ"
    except Exception:
        pass
    return None


def _parse_shopee_url(url):
    """Extract shop_id and item_id from Shopee product URL. Returns (shop_id, item_id) or (None, None)."""
    if not url or pd.isna(url):
        return None, None
    try:
        # Format: ...-i.<shop_id>.<item_id> or ...-i.<shop_id>.<item_id>?...
        m = re.search(r'-i\.(\d+)\.(\d+)(?:\?|$)', str(url).strip())
        if m:
            return m.group(1), m.group(2)
    except Exception:
        pass
    return None, None


def _extract_price_from_shopee_data(data, model_hint=None):
    """From Shopee API-like data dict, get price. Prefer variant matching model_hint if provided."""
    if not isinstance(data, dict):
        return None
    # Multiple possible paths: data.data.item (v4), data.item (v2), item_basic, item
    inner = data.get('data') or {}
    if isinstance(inner, dict):
        item = inner.get('data', {}).get('item') or inner.get('item') or inner.get('item_basic')
    else:
        item = None
    item = item or data.get('item') or data.get('item_basic')
    if not isinstance(item, dict):
        return None
    # Base price: Shopee often returns price in VND; sometimes price/100000 (e.g. 47.13 = 4713000)
    for key in ('price', 'price_min', 'min_price', 'price_max', 'price_min_max'):
        val = item.get(key)
        if val is not None:
            if isinstance(val, (int, float)):
                if 50000 <= val <= 500000000:
                    return int(val)
                if 1 <= val < 50000 and (val * 100000) <= 500000000:
                    return int(val * 100000)
                if val < 10000 and (val * 1000) >= 50000:
                    return int(val * 1000)
            break
    # Models / tier_variations: list of variants with optional price per variant
    models = item.get('models') or item.get('tier_variations') or item.get('tier_variation') or []
    def _norm(s):
        return re.sub(r'\s+', '', (s or '').strip().upper()).replace('-', '')
    if isinstance(models, list) and models and model_hint:
        model_upper = _norm(model_hint)
        for m in models:
            if not isinstance(m, dict):
                continue
            name = _norm(m.get('name') or m.get('option') or m.get('model_name') or '')
            if model_upper in name or name in model_upper:
                p = m.get('price') or m.get('price_before_discount')
                if p is not None:
                    num = int(p) if isinstance(p, (int, float)) else None
                    if not num and isinstance(p, str):
                        num = int(re.sub(r'[^\d]', '', p) or 0)
                    if num and 50000 <= num <= 500000000:
                        return num
    # First model price as fallback
    if isinstance(models, list):
        for m in models:
            if isinstance(m, dict):
                p = m.get('price') or m.get('price_before_discount')
                if p is not None:
                    num = int(p) if isinstance(p, (int, float)) else None
                    if not num and isinstance(p, str):
                        num = int(re.sub(r'[^\d]', '', p) or 0)
                    if num and 50000 <= num <= 500000000:
                        return num
    return None


def extract_price_shopee_from_page_json(soup, model_hint=None):
    """Try to find product price in embedded JSON inside script tags (Shopee sometimes embeds state)."""
    if not soup:
        return None
    try:
        for script in soup.find_all("script", type=re.compile(r"application/(ld\+)?json", re.I)):
            raw = script.string
            if not raw or len(raw) < 100:
                continue
            try:
                data = json.loads(raw)
            except Exception:
                continue
            price = _extract_price_from_shopee_data(data, model_hint)
            if price is not None:
                return price
        for script in soup.find_all("script"):
            raw = script.string
            if not raw or "price" not in raw.lower() or "item" not in raw.lower():
                continue
            for m in re.findall(r'["\']price["\']\s*:\s*(\d+)', raw):
                try:
                    num = int(m)
                    if 50000 <= num <= 500000000:
                        return num
                except Exception:
                    continue
            for m in re.findall(r'(\d{6,})', raw):
                try:
                    num = int(m)
                    if 50000 <= num <= 500000000:
                        return num
                except Exception:
                    continue
    except Exception:
        pass
    return None


def _get_shopee_cookie():
    """Build Cookie header for Shopee. Prefer SHOPEE_COOKIE env; else SHOPEE_COOKIE_FILE; else config/shopee_cookies.txt."""
    raw = os.environ.get("SHOPEE_COOKIE", "").strip()
    if raw:
        return raw
    path = os.environ.get("SHOPEE_COOKIE_FILE", "").strip()
    if not path or not os.path.isfile(path):
        path = str(CONFIG_DIR / "shopee_cookies.txt")
    if not path or not os.path.isfile(path):
        return None
    try:
        parts = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    parts.append(line)
                elif "\t" in line:
                    name, value = line.split("\t", 1)
                    parts.append(f"{name.strip()}={value.strip()}")
        return "; ".join(parts) if parts else None
    except Exception:
        return None


def extract_price_shopee_api(url, model_hint=None):
    """Get price from Shopee API. Tries v2 item/get then v4 get_pc. Uses variant matching model_hint when available.
    Cookie: set env SHOPEE_COOKIE to "Name1=Value1; Name2=Value2; ..." or SHOPEE_COOKIE_FILE to path of a file (one line per cookie: Name=Value)."""
    shop_id, item_id = _parse_shopee_url(url)
    if not shop_id or not item_id:
        return None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://shopee.vn/",
        "Accept": "application/json",
    }
    cookies = _get_shopee_cookie()
    if cookies:
        headers["Cookie"] = cookies
    for api_url in [
        f"https://shopee.vn/api/v2/item/get?itemid={item_id}&shopid={shop_id}",
        f"https://shopee.vn/api/v4/pdp/get_pc?item_id={item_id}&shop_id={shop_id}",
    ]:
        try:
            resp = requests.get(api_url, headers=headers, timeout=12)
            if resp.status_code != 200:
                continue
            data = resp.json()
            price = _extract_price_from_shopee_data(data, model_hint)
            if price is not None:
                return price
        except Exception:
            continue
    return None


def extract_price_shopee_headless(url, model_hint=None):
    """Shopee: load page in browser, capture API response (get_pc/item) for price, else click variant and read DOM."""
    if not HAS_PLAYWRIGHT:
        return None
    captured_api_bodies = []

    def _on_response(response):
        try:
            req_url = (response.url or "").lower()
            if "shopee.vn" not in req_url or "api" not in req_url:
                return
            if "get_pc" not in req_url and "item/get" not in req_url and "/pdp/" not in req_url and "itemid" not in req_url and "item_id" not in req_url:
                return
            if response.status != 200:
                return
            body = response.json()
            if body and isinstance(body, dict):
                captured_api_bodies.append(body)
        except Exception:
            pass

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(
                    headless=True,
                    channel="chrome",
                    args=["--disable-blink-features=AutomationControlled"],
                )
            except Exception:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"],
                )
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                locale="vi-VN",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            cookie_str = _get_shopee_cookie()
            if cookie_str:
                try:
                    cookie_list = []
                    for part in cookie_str.split(";"):
                        part = part.strip()
                        if "=" in part:
                            name, _, value = part.partition("=")
                            name, value = name.strip(), value.strip()
                            if name:
                                cookie_list.append({"name": name, "value": value, "domain": ".shopee.vn", "path": "/"})
                    if cookie_list:
                        context.add_cookies(cookie_list)
                except Exception:
                    pass
            page = context.new_page()
            page.set_default_timeout(30000)
            page.on("response", _on_response)
            page.goto(url, wait_until="domcontentloaded", timeout=35000)
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            page.wait_for_timeout(5000)
            # Prefer price from API response (same data the page uses)
            for data in captured_api_bodies:
                price = _extract_price_from_shopee_data(data, model_hint)
                if price is not None:
                    browser.close()
                    return price
            if model_hint and str(model_hint).strip():
                model_text = str(model_hint).strip()
                try:
                    loc_all = page.get_by_text(re.compile(re.escape(model_text), re.I))
                    n = loc_all.count()
                    if n >= 2:
                        loc_all.nth(1).click(timeout=5000)
                    elif n >= 1:
                        loc_all.first.click(timeout=5000)
                    page.wait_for_timeout(3000)
                except Exception:
                    pass
            price_pattern = re.compile(r"\d{1,3}(?:[.,]\d{3}){2,}")
            text = ""
            for sel in [
                "[class*='product-price']",
                "[class*='price']",
                "div[class*='stardust']",
                "[data-sqe='price']",
                "main",
                "[role='main']",
            ]:
                try:
                    loc = page.locator(sel).first
                    loc.wait_for(state="visible", timeout=3000)
                    t = loc.inner_text(timeout=2000).strip()
                    if t and price_pattern.search(t):
                        if len(t) < 200:
                            text = t
                            break
                        if not text:
                            text = t
                except Exception:
                    continue
            if not text:
                try:
                    text = page.inner_text("body", timeout=8000)
                except Exception:
                    text = ""
            browser.close()
        if not text:
            return None
        for m in re.findall(r'(\d{1,3}(?:[.,]\d{3}){2,})', text):
            digits = re.sub(r'[^\d]', '', m)
            if not digits:
                continue
            num = int(digits)
            if 50000 <= num <= 500000000:
                return num
        for m in re.findall(r'\b(\d{6,})\b', re.sub(r'[.,\s]', '', text)):
            try:
                num = int(m)
                if 50000 <= num <= 500000000:
                    return num
            except Exception:
                continue
        return None
    except Exception:
        return None


def extract_price_fallback(soup):
    """Fallback: find price from elements with price-like class or itemprop/data-price."""
    # 1) itemprop="price"
    el = soup.find(itemprop='price')
    if el:
        text = el.get_text(strip=True) or el.get('content', '')
        price = re.sub(r'[^\d]', '', text)
        if price and len(price) >= 6:
            return int(price)
    # 2) data-price attribute
    el = soup.find(attrs={'data-price': True})
    if el:
        raw = el.get('data-price', '')
        price = re.sub(r'[^\d]', '', str(raw))
        if price and len(price) >= 6:
            return int(price)
    # 3) class contains price/gia/sale and text looks like VND
    vnd_pattern = re.compile(r'\d{1,3}[.,]\d{3}[.,]\d{3}')
    for tag_name in ('span', 'div', 'p', 'strong', 'b'):
        for el in soup.find_all(tag_name, class_=lambda c: c and any(k in ' '.join(c).lower() for k in ('price', 'gia', 'sale', 'cost', 'giá'))):
            text = el.get_text(strip=True)
            m = vnd_pattern.search(text)
            if m and len(text) < 30:
                price = re.sub(r'[^\d]', '', m.group(0))
                if len(price) >= 6:
                    return int(price)
    return None


def extract_price_generic(url, soup, selector_info):
    """Extract price using generic CSS selector. Tries exact class then partial class match."""
    try:
        tag = selector_info.get('tag', 'div')
        class_name = selector_info.get('class', '')
        nested_tag = selector_info.get('nested_tag')
        index = selector_info.get('index', -1)
        
        if class_name:
            elements = soup.find_all(tag, class_=class_name)
            # If no exact match, try partial (e.g. "price" matches "nk-price-final")
            if not elements:
                elements = soup.find_all(tag, class_=lambda c: c and class_name in ' '.join(c))
        else:
            elements = soup.find_all(tag)
        
        if not elements:
            return None
        
        if index >= 0 and index < len(elements):
            element = elements[index]
        else:
            element = elements[0]
        
        if nested_tag:
            element = element.find(nested_tag)
            if not element:
                return None
        
        text = element.get_text(" ", strip=True) if element else ''
        if not text:
            return None

        # Prefer formatted VND patterns first (avoid concatenating old+new prices)
        matches = re.findall(r'(\d{1,3}(?:[.,]\d{3}){2,})', text)
        for m in matches:
            digits = re.sub(r'[^\d]', '', m)
            if not digits:
                continue
            num = int(digits)
            if 50000 <= num <= 500000000:
                return num
        if matches:
            digits = re.sub(r'[^\d]', '', matches[0])
            num = int(digits) if digits else None
            if num and 50000 <= num <= 500000000:
                return num

        # Fallback: long digit sequences (e.g. 4190000)
        for m in re.findall(r'(\d{6,})', text.replace(" ", "")):
            try:
                num = int(m)
                if 50000 <= num <= 500000000:
                    return num
            except Exception:
                continue
        return None
    except Exception as e:
        return None


def extract_price_nguyenkim_headless(url):
    """Extract price from Nguyễn Kim using a headless browser (Playwright).

    This is only used when normal HTML parsing (requests + BeautifulSoup) cannot
    see the price because it is rendered client-side by JavaScript.
    """
    if not HAS_PLAYWRIGHT:
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(20000)
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(5000)

            text = ""
            for sel in ["div.nk2020-pdp-price", "[class*='pdp-price']", "[class*='product-price']"]:
                try:
                    loc = page.locator(sel).first
                    loc.wait_for(state="visible", timeout=8000)
                    text = loc.inner_text(timeout=5000).strip()
                    if text and re.search(r'\d{1,3}[.,]\d{3}[.,]\d{3}', text):
                        break
                except Exception:
                    continue
            if not text or not re.search(r'\d{1,3}[.,]\d{3}[.,]\d{3}', text):
                try:
                    text = page.inner_text("body", timeout=8000)
                except Exception:
                    text = ""
            browser.close()

        if not text:
            return None

        matches = re.findall(r'(\d{1,3}(?:[.,]\d{3}){2,})', text)
        for m in matches:
            digits = re.sub(r'[^\d]', '', m)
            if not digits:
                continue
            num = int(digits)
            if 50000 <= num <= 500000000:
                return num
        if matches:
            digits = re.sub(r'[^\d]', '', matches[0])
            return int(digits) if digits else None
        return None
    except Exception:
        return None


def extract_price_pico_jsonld(url, soup):
    """Extract price from Pico using JSON-LD structured data"""
    try:
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                # Handle both dict and list formats
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and 'offers' in item:
                            offers = item['offers']
                            if isinstance(offers, dict) and 'price' in offers:
                                price = offers['price']
                                if isinstance(price, (int, float)):
                                    return int(price)
                                elif isinstance(price, str):
                                    price = re.sub(r'[^\d]', '', price)
                                    return int(price) if price else None
                elif isinstance(data, dict):
                    # Check if 'offers' is directly in data
                    if 'offers' in data:
                        offers = data['offers']
                        if isinstance(offers, dict) and 'price' in offers:
                            price = offers['price']
                            if isinstance(price, (int, float)):
                                return int(price)
                            elif isinstance(price, str):
                                price = re.sub(r'[^\d]', '', price)
                                return int(price) if price else None
                    # Check if '@graph' contains offers
                    if '@graph' in data and isinstance(data['@graph'], list):
                        for item in data['@graph']:
                            if isinstance(item, dict) and 'offers' in item:
                                offers = item['offers']
                                if isinstance(offers, dict) and 'price' in offers:
                                    price = offers['price']
                                    if isinstance(price, (int, float)):
                                        return int(price)
                                    elif isinstance(price, str):
                                        price = re.sub(r'[^\d]', '', price)
                                        return int(price) if price else None
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
    except Exception:
        pass
    return None


def extract_price_pico_headless(url):
    """Lấy giá sản phẩm chính trên Pico (block right-detail/price-wrapper do JS render)."""
    if not HAS_PLAYWRIGHT:
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(15000)
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            })
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(3500)

            text = ""
            price_pattern = re.compile(r"\d{1,3}[.,]\d{3}[.,]\d{3}")
            # 1) Sản phẩm chính: div.price-wrapper có class "products" (trong right-detail)
            for selector in [
                "div.price-wrapper.products p",
                "div[class*='price-wrapper'][class*='products'] p",
                "div.right-detail div.sale-price p",
                "div.right-detail p",
            ]:
                try:
                    loc = page.locator(selector).first
                    loc.wait_for(timeout=6000)
                    text = loc.inner_text(timeout=2000).strip()
                    if text and price_pattern.search(text):
                        break
                except Exception:
                    text = ""
                    continue

            browser.close()

        if not text or not price_pattern.search(text):
            return None
        digits = re.sub(r"[^\d]", "", price_pattern.search(text).group(0))
        num = int(digits) if digits else None
        if num and 50000 <= num <= 500000000:
            return num
        return None
    except Exception:
        return None


def crawl_price(url, store_name, model=None):
    """Crawl price from a single URL. Returns (price, reason). reason is None on success, else a short string.
    model: optional product model name (e.g. DCP-L2520D), used by Shopee to select the correct variant."""
    if url is None or (isinstance(url, float) and pd.isna(url)):
        return None, None
    url = str(url).strip()
    if not url or url.lower() in ('notfound', 'nan', ''):
        return None, None

    try:
        # HC website has SSL certificate issues, disable verification for it
        store_key = STORE_MAPPING.get(store_name, store_name.lower())
        verify_ssl = store_key != 'hc'

        response = requests.get(url, headers=HEADERS, timeout=10, verify=verify_ssl)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Get selectors
        selectors = load_class_selectors()
        
        if store_key == 'phongvu':
            # Uses JSON-LD, keep existing logic
            price = extract_price_phongvu(url, soup)
        elif store_key == 'dienmayxanh':
            # Điện Máy Xanh: prefer JSON-LD offers.price (stable even when UI price block changes)
            price = extract_price_dienmayxanh(url, soup)
            if price in (None, 0) and HAS_PLAYWRIGHT:
                # Some pages return price=0 in JSON-LD until client-side rendering completes
                price = extract_price_dienmayxanh_headless(url)
            if price is None and store_key in selectors:
                price = extract_price_generic(url, soup, selectors[store_key])
            if price is None:
                price = extract_price_fallback(soup)
        elif store_key == 'nguyenkim':
            # Nguyễn Kim: first try JSON-LD (most reliable), then HTML parsing, then headless
            price = extract_price_nguyenkim_jsonld(url, soup)
            if price is None:
                if store_key in selectors:
                    price = extract_price_generic(url, soup, selectors[store_key])
                if price is None:
                    price = extract_price_fallback(soup)
            if price is None:
                price = extract_price_nguyenkim_headless(url)
        elif store_key == 'pico':
            # Pico: first try JSON-LD (most reliable), then headless, then HTML parsing
            price = extract_price_pico_jsonld(url, soup)
            if price is None:
                price = extract_price_pico_headless(url)
            if price is None and store_key in selectors:
                price = extract_price_generic(url, soup, selectors[store_key])
            if price is None:
                price = extract_price_fallback(soup)
        elif store_key == 'hncomputer':
            # HACOM (hacom.vn): price often in page text/JSON-LD but not in a stable selector
            price = extract_price_hncomputer(url, soup)
            if price is None and store_key in selectors:
                price = extract_price_generic(url, soup, selectors[store_key])
            if price is None:
                price = extract_price_fallback(soup)
        elif store_key == 'phucanh':
            # Phúc Anh (phucanh.vn): main product promo price
            price = extract_price_phucanh(url, soup)
            if price is None and store_key in selectors:
                price = extract_price_generic(url, soup, selectors[store_key])
            if price is None:
                price = extract_price_fallback(soup)
        elif store_key == 'cellphones':
            # CellphoneS (cellphones.com.vn): JSON-LD + full-page VND scan
            price = extract_price_cellphones(url, soup)
            if price is None and store_key in selectors:
                price = extract_price_generic(url, soup, selectors[store_key])
            if price is None:
                price = extract_price_fallback(soup)
        elif store_key == 'shopee':
            # Shopee: API first, then embedded JSON in page, then headless (click variant by model)
            price = extract_price_shopee_api(url, model_hint=model)
            if price is None:
                price = extract_price_shopee_from_page_json(soup, model_hint=model)
            if price is None and HAS_PLAYWRIGHT:
                price = extract_price_shopee_headless(url, model_hint=model)
            if price is None:
                price = extract_price_fallback(soup)
        elif store_key in selectors:
            price = extract_price_generic(url, soup, selectors[store_key])
            if price is None:
                price = extract_price_fallback(soup)
        else:
            price = extract_price_fallback(soup)
            if price is None:
                price_text = soup.get_text()
                price_match = re.search(r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)', price_text)
                if price_match:
                    price = re.sub(r'[^\d]', '', price_match.group(1))
                    price = int(price) if price else None
        
        if price is not None:
            return price, None
        return None, "No price found on page"
    except Exception as e:
        reason = str(e).strip() or "Request failed"
        if len(reason) > 120:
            reason = reason[:117] + "..."
        return None, reason


def crawl_all_prices(df, selected_stores=None):
    """Crawl prices for all products. Returns (scraped_df, failed_by_store, total_links_by_store)."""
    results = []
    failed_by_store = {}  # store_name -> [(model, url, reason), ...]
    total_links_by_store = {}  # store_name -> int

    # Get store columns (exclude Model, Giá tiêu chuẩn, ID)
    store_columns = [col for col in df.columns 
                    if col not in ['Model', 'Giá tiêu chuẩn', 'GIÁ TIÊU CHUẨN', 'ID']]
    
    # Domain-based mall mode:
    domain_to_mall, mall_to_store_key = load_mall_domain_map()
    use_domain_mall_mode = bool(domain_to_mall) and any(col not in STORE_MAPPING for col in store_columns)
    if selected_stores:
        if use_domain_mall_mode:
            selected_set = set(selected_stores)
        else:
            store_columns = [col for col in store_columns if col in selected_stores]
            selected_set = None
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Crawling products"):
        product_data = {'Model': row['Model']}
        
        for store_col in store_columns:
            url = str(row[store_col]).strip() if pd.notna(row[store_col]) else ''
            if not url or url.lower() in ('notfound', 'nan', ''):
                continue
            if use_domain_mall_mode:
                mall = infer_mall_from_url(url, domain_to_mall)
                if not mall:
                    continue
                if selected_stores and mall not in selected_set:
                    continue
                store_key = mall_to_store_key.get(mall) or mall.strip().lower()
                store_name = mall
                price, reason = crawl_price(url, store_key, model=row.get('Model'))
                product_data[mall] = price
            else:
                store_name = store_col
                price, reason = crawl_price(url, store_col, model=row.get('Model'))
                product_data[store_col] = price

            total_links_by_store[store_name] = total_links_by_store.get(store_name, 0) + 1
            if price is None and reason:
                failed_by_store.setdefault(store_name, []).append((row['Model'], url, reason))
            time.sleep(0.1)
        
        results.append(product_data)
    
    return pd.DataFrame(results), failed_by_store, total_links_by_store


def _create_parser():
    """Create argument parser based on available GUI library"""
    default_output = f'output_prices_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
    force_cli = '--cli' in sys.argv
    if HAS_GOOEY and not force_cli:
        parser = GooeyParser(description='Crawl prices from Vietnamese e-commerce websites')
        parser.add_argument(
            '--config',
            widget='FileChooser',
            default=str(DATA_CSV),
            help='Path to DATA.csv file'
        )
        parser.add_argument(
            '--output',
            widget='FileSaver',
            default=default_output,
            help='Output CSV file path'
        )
        parser.add_argument(
            '--stores',
            widget='Listbox',
            choices=list(STORE_MAPPING.keys()),
            nargs='*',
            help='Select stores to crawl (leave empty for all)'
        )
    else:
        parser = argparse.ArgumentParser(description='Crawl prices from Vietnamese e-commerce websites')
        parser.add_argument(
            '--cli',
            action='store_true',
            help='Force command-line mode (disable GUI)'
        )
        parser.add_argument(
            '--config',
            type=str,
            default=str(DATA_CSV),
            help='Path to DATA.csv file'
        )
        parser.add_argument(
            '--output',
            type=str,
            default=default_output,
            help='Output CSV file path'
        )
        parser.add_argument(
            '--stores',
            nargs='*',
            choices=list(STORE_MAPPING.keys()),
            help='Select stores to crawl (leave empty for all)'
        )
    return parser


def main():
    parser = _create_parser()
    args = parser.parse_args()
    session_start = datetime.now()
    print(f"## Crawl session started at {session_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"- Config file: `{args.config}`")
    if args.stores:
        print(f"- Selected stores: {', '.join(args.stores)}")
    else:
        print(f"- Selected stores: all (domain-based where applicable)")

    # Load data
    print("Loading data...")
    if not os.path.exists(args.config):
        print(f"Error: Config file not found: {args.config}")
        return
    
    df = pd.read_csv(args.config, encoding='utf-8')
    print(f"Loaded {len(df)} products")
    
    # Crawl prices
    print("Starting to crawl prices...")
    selected_stores = args.stores if args.stores else None
    scraped_df, failed_by_store, total_links_by_store = crawl_all_prices(df, selected_stores)
    
    # Merge with original data
    print("Merging results...")
    keep_cols = [c for c in df.columns if c in ['Model', 'Giá tiêu chuẩn', 'GIÁ TIÊU CHUẨN', 'ID']]
    base_df = df[keep_cols].copy() if keep_cols else df[['Model']].copy()
    result = safe_merge(base_df, scraped_df, on='Model', how='left')
    
    # Save results
    output_path = args.output
    result.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Results saved to: {output_path}")
    print(f"Total products: {len(result)}")
    
    # Show summary (count and % by links)
    print("\n## Crawl summary (per store)")
    total_links_all = sum(total_links_by_store.values())
    total_prices_found = 0
    for store_col in scraped_df.columns:
        if store_col != 'Model':
            prices_found = result[store_col].notna().sum()
            total_prices_found += int(prices_found)
            total_links = total_links_by_store.get(store_col, 0)
            if total_links > 0:
                pct = round(100 * prices_found / total_links, 1)
                safe_print(f"- **{store_col}**: {prices_found}/{total_links} links with price ({pct}%)")
            else:
                safe_print(f"- **{store_col}**: {prices_found}/{len(result)} products with price")
    
    # Global overview (all links)
    session_end = datetime.now()
    elapsed_sec = (session_end - session_start).total_seconds()
    print("\n## Crawl overview (all stores)")
    print(f"- Start time: {session_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"- End time: {session_end.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"- Duration: **{elapsed_sec:.1f} seconds**")
    print(f"- Total links crawled: **{total_links_all}**")
    if total_links_all > 0:
        pct_all = round(100 * total_prices_found / total_links_all, 1)
        print(f"- Links with price: **{total_prices_found}/{total_links_all} ({pct_all}%)**")
    else:
        print("- Links with price: **0/0**")
    
    # Log failed links (had URL but could not get price)
    if failed_by_store:
        print("\n## Links without price (warnings)")
        for store_name in sorted(failed_by_store.keys()):
            entries = failed_by_store[store_name]
            if not entries:
                continue
            safe_print(f"\n### {store_name}")
            safe_print("")
            for model, url, reason in entries:
                safe_print(f"- `{model}` → {url}")
                safe_print(f"  - Warning: {reason}")
            total_links = total_links_by_store.get(store_name, 0)
            got = total_links - len(entries)
            if total_links > 0:
                pct = round(100 * got / total_links, 1)
                safe_print(f"  - Summary: {got}/{total_links} ({pct}%) links returned a price")
    
    # Open output file automatically
    try:
        output_file = Path(output_path).resolve()
        if output_file.exists():
            print(f"\nOpening output file: {output_file}")
            if platform.system() == 'Windows':
                os.startfile(str(output_file))
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', str(output_file)])
            else:  # Linux
                subprocess.run(['xdg-open', str(output_file)])
    except Exception as e:
        print(f"Note: Could not open file automatically. You can open it manually: {output_path}")


if __name__ == "__main__":
    if HAS_GOOEY and '--cli' not in sys.argv:
        # Wrap main with Gooey decorator
        @Gooey(program_name="Supermarket Price Crawler", 
               default_size=(800, 600),
               navigation='TABBED')
        def gooey_wrapper():
            return main()
        gooey_wrapper()
    else:
        main()

