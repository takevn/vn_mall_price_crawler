#!/usr/bin/env python3
"""Test crawl price from Pico and HC"""
import sys
import requests
from bs4 import BeautifulSoup
import re
import json

# Import from main script
import importlib.util
spec = importlib.util.spec_from_file_location("crawler", "Supermarket Price Crawler.py")
crawler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crawler)

HEADERS = crawler.HEADERS
load_class_selectors = crawler.load_class_selectors
extract_price_generic = crawler.extract_price_generic
extract_price_fallback = crawler.extract_price_fallback
crawl_price = crawler.crawl_price

PICO_URL = "https://pico.vn/may-in-laser-brother-hll2321d-a42-mat30-trangphuttn-2385-2600-trang-HLL2321D"
HC_URL = "https://hc.com.vn/ords/product/may-in-laser-brother-hl-l2321d-in-duplex"

def analyze_pico():
    print("="*60)
    print("ANALYZING PICO")
    print("="*60)
    print(f"URL: {PICO_URL}\n")
    
    try:
        response = requests.get(PICO_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        print(f"[OK] Got HTML response (length: {len(response.content)} bytes)\n")
        
        # Check JSON-LD
        print("--- Checking JSON-LD ---")
        scripts = soup.find_all('script', type='application/ld+json')
        print(f"Found {len(scripts)} JSON-LD scripts")
        for i, script in enumerate(scripts):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'offers' in data:
                    print(f"Script [{i+1}] has 'offers':")
                    print(json.dumps(data.get('offers'), indent=2))
            except:
                pass
        
        # Check for price elements
        print("\n--- Checking price elements ---")
        price_elements = soup.find_all(class_=lambda c: c and 'price' in ' '.join(c).lower())
        print(f"Found {len(price_elements)} elements with 'price' in class")
        for i, el in enumerate(price_elements[:10]):
            classes = ' '.join(el.get('class', []))
            text = el.get_text(strip=True)
            print(f"  [{i+1}] class='{classes}' text='{text[:80]}'")
        
        # Check selectors
        print("\n--- Testing selectors ---")
        selectors = load_class_selectors()
        if 'pico' in selectors:
            print(f"Selector config: {selectors['pico']}")
            price = extract_price_generic(PICO_URL, soup, selectors['pico'])
            print(f"extract_price_generic result: {price}")
        
        price = extract_price_fallback(soup)
        print(f"extract_price_fallback result: {price}")
        
        # Test full crawl
        print("\n--- Testing full crawl_price ---")
        price = crawl_price(PICO_URL, 'Pico')
        print(f"crawl_price result: {price}")
        
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

def analyze_hc():
    print("\n" + "="*60)
    print("ANALYZING HC")
    print("="*60)
    print(f"URL: {HC_URL}\n")
    
    try:
        # HC needs verify=False for SSL
        response = requests.get(HC_URL, headers=HEADERS, timeout=10, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        print(f"[OK] Got HTML response (length: {len(response.content)} bytes)\n")
        
        # Check JSON-LD
        print("--- Checking JSON-LD ---")
        scripts = soup.find_all('script', type='application/ld+json')
        print(f"Found {len(scripts)} JSON-LD scripts")
        for i, script in enumerate(scripts):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'offers' in data:
                    print(f"Script [{i+1}] has 'offers':")
                    print(json.dumps(data.get('offers'), indent=2))
            except:
                pass
        
        # Check for price elements
        print("\n--- Checking price elements ---")
        # Check hc_sale_price
        hc_elements = soup.find_all(class_=lambda c: c and 'hc' in ' '.join(c).lower())
        print(f"Found {len(hc_elements)} elements with 'hc' in class")
        for i, el in enumerate(hc_elements[:15]):
            classes = ' '.join(el.get('class', []))
            text = el.get_text(strip=True)
            if 'price' in classes.lower() or 'sale' in classes.lower():
                print(f"  [{i+1}] class='{classes}' text='{text[:80]}'")
        
        # Check selectors
        print("\n--- Testing selectors ---")
        selectors = load_class_selectors()
        if 'hc' in selectors:
            print(f"Selector config: {selectors['hc']}")
            price = extract_price_generic(HC_URL, soup, selectors['hc'])
            print(f"extract_price_generic result: {price}")
        
        price = extract_price_fallback(soup)
        print(f"extract_price_fallback result: {price}")
        
        # Test full crawl
        print("\n--- Testing full crawl_price ---")
        price = crawl_price(HC_URL, 'HC')
        print(f"crawl_price result: {price}")
        
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_pico()
    analyze_hc()


