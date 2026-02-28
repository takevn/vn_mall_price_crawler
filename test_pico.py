"""Quick test for Pico headless price extraction."""
import sys
import re
import importlib.util

# Optional: debug selectors (set to True to see what page returns)
DEBUG = len(sys.argv) > 1 and sys.argv[1] == "debug"

url = "https://pico.vn/may-in-laser-brother-hll2321d-a42-mat30-trangphuttn-2385-2600-trang-HLL2321D"

if DEBUG:
    from playwright.sync_api import sync_playwright
    print("Debug: opening page and trying selectors...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(15000)
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(5000)
        for sel in [
            "div.price-wrapper.products p",
            "div[class*='price-wrapper'][class*='products'] p",
            "div.right-detail div.sale-price p",
            "div.right-detail p",
        ]:
            try:
                n = page.locator(sel).count()
                t = page.locator(sel).first.inner_text(timeout=3000).strip() if n else ""
                print(f"  {sel!r} -> count={n}, first_text={t[:60]!r}...")
            except Exception as e:
                print(f"  {sel!r} -> error: {e}")
        browser.close()
    print("Done.")
else:
    spec = importlib.util.spec_from_file_location(
        "crawler",
        "Supermarket Price Crawler.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    price = mod.extract_price_pico_headless(url)
    print("Pico price:", price, "(expected 2950000)")
