#!/usr/bin/env python3
"""Test HC directly with crawl_price"""
import sys
import importlib.util
import warnings

# Suppress SSL warnings for HC
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

spec = importlib.util.spec_from_file_location("crawler", "Supermarket Price Crawler.py")
crawler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crawler)

HC_URL = "https://hc.com.vn/ords/product/may-in-laser-brother-hl-l2321d-in-duplex"

print(f"Testing HC URL: {HC_URL}\n")
price = crawler.crawl_price(HC_URL, 'HC')
print(f"Result: {price}")


