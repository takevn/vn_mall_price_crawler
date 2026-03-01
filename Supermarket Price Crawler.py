"""
Supermarket Price Crawler
Crawls prices from multiple Vietnamese e-commerce websites
"""

import sys
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import re
import os
from pathlib import Path
from tqdm import tqdm
import time
import warnings
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
    # Fallback for command line
    import argparse

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

# Store name mapping
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
        
        text = element.get_text(strip=True) if element else ''
        price = re.sub(r'[^\d]', '', text)
        return int(price) if price else None
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


def crawl_price(url, store_name):
    """Crawl price from a single URL"""
    if not url or pd.isna(url) or url.strip() == '':
        return None
    
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
        
        return price
    except Exception as e:
        return None


def crawl_all_prices(df, selected_stores=None):
    """Crawl prices for all products"""
    results = []
    
    # Get store columns (exclude Model, Giá tiêu chuẩn, ID)
    store_columns = [col for col in df.columns 
                    if col not in ['Model', 'Giá tiêu chuẩn', 'ID']]
    
    if selected_stores:
        store_columns = [col for col in store_columns if col in selected_stores]
    
    # Create progress bar for products
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Crawling products"):
        product_data = {'Model': row['Model']}
        
        # Crawl each store
        for store_col in store_columns:
            url = row[store_col]
            price = crawl_price(url, store_col)
            product_data[store_col] = price
            time.sleep(0.1)  # Small delay to avoid overwhelming servers
        
        results.append(product_data)
    
    return pd.DataFrame(results)


def _create_parser():
    """Create argument parser based on available GUI library"""
    # Generate default output filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    default_output = f'output_prices_{timestamp}.csv'
    
    if HAS_GOOEY:
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
    scraped_df = crawl_all_prices(df, selected_stores)
    
    # Merge with original data
    print("Merging results...")
    # Use suffixes so store columns from scraped_df (prices) win
    result = safe_merge(df, scraped_df, on='Model', how='left', suffixes=('_url', ''))
    # Drop URL columns so each store has a single column with the scraped price
    store_columns = [c for c in df.columns if c not in ['Model', 'Giá tiêu chuẩn', 'ID']]
    for col in store_columns:
        url_col = col + '_url'
        if url_col in result.columns:
            result.drop(columns=[url_col], inplace=True)
    
    # Save results
    output_path = args.output
    result.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Results saved to: {output_path}")
    print(f"Total products: {len(result)}")
    
    # Show summary
    print("\n=== Summary ===")
    for store_col in scraped_df.columns:
        if store_col != 'Model':
            prices_found = scraped_df[store_col].notna().sum()
            safe_print(f"{store_col}: {prices_found}/{len(scraped_df)} prices found")
    
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
    if HAS_GOOEY:
        # Wrap main with Gooey decorator
        @Gooey(program_name="Supermarket Price Crawler", 
               default_size=(800, 600),
               navigation='TABBED')
        def gooey_wrapper():
            return main()
        gooey_wrapper()
    else:
        main()

