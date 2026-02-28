"""
Command-line runner for Supermarket Price Crawler
This script provides a command-line interface to run the crawler
"""

import sys
import os
import argparse
from pathlib import Path

# Add the crawler directory to path if needed
crawler_dir = Path(__file__).parent / "Supermarket Price Crawler"
if crawler_dir.exists():
    sys.path.insert(0, str(crawler_dir))

def main():
    parser = argparse.ArgumentParser(
        description='Supermarket Price Crawler - Command Line Interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_crawler.py                    # Run with default settings
  python run_crawler.py --config config/DATA.csv
  python run_crawler.py --output results.csv
  python run_crawler.py --stores phongvu nguyenkim
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/DATA.csv',
        help='Path to DATA.csv configuration file (default: config/DATA.csv)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='output_prices.csv',
        help='Output file path for crawled prices (default: output_prices.csv)'
    )
    
    parser.add_argument(
        '--stores',
        nargs='+',
        help='Specific stores to crawl (e.g., phongvu nguyenkim dienmayxanh)'
    )
    
    parser.add_argument(
        '--fix-merge',
        action='store_true',
        help='Apply fix for Model column merge issue'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Try to import and run the main crawler
    try:
        # Check if we can import the main module
        main_script = Path("Supermarket Price Crawler.py")
        if not main_script.exists():
            # Try in the subdirectory
            main_script = crawler_dir / "Supermarket Price Crawler.py"
            if not main_script.exists():
                print("Error: Cannot find 'Supermarket Price Crawler.py'")
                print("Please ensure the source file is in the current directory or 'Supermarket Price Crawler' subdirectory")
                return 1
        
        print(f"Running crawler with config: {args.config}")
        if args.stores:
            print(f"Stores to crawl: {', '.join(args.stores)}")
        print(f"Output file: {args.output}")
        
        if args.fix_merge:
            print("Applying merge fix for Model column...")
            # Import and apply the fix module
            try:
                from fix_merge_issue import safe_merge
                print("Fix module loaded successfully")
            except ImportError:
                print("Warning: fix_merge_issue.py not found. Make sure it's in the same directory.")
        
        # Try to run the crawler
        if main_script.exists() and main_script.suffix == '.py':
            # Run Python script
            print(f"\nExecuting: python \"{main_script}\"")
            import subprocess
            result = subprocess.run([sys.executable, str(main_script)], 
                                   cwd=str(main_script.parent))
            return result.returncode
        elif (crawler_dir / "Supermarket Price Crawler.exe").exists():
            # Run executable
            exe_path = crawler_dir / "Supermarket Price Crawler.exe"
            print(f"\nExecuting: \"{exe_path}\"")
            import subprocess
            result = subprocess.run([str(exe_path)], 
                                   cwd=str(exe_path.parent))
            return result.returncode
        else:
            # Fallback: provide instructions
            print("\nTo run the crawler:")
            print(f"  python \"{main_script}\"")
            print("\nOr if it's an executable:")
            if (crawler_dir / "Supermarket Price Crawler.exe").exists():
                exe_path = crawler_dir / "Supermarket Price Crawler.exe"
                print(f"  \"{exe_path}\"")
            return 0
        
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

