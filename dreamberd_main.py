#!/usr/bin/env python3
"""
DreamBerd Interpreter Entry Point
Usage: python dreamberd_main.py <filename.db>
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from dreamberd import run_dreamberd

def main():
    """Main entry point for DreamBerd interpreter"""
    if len(sys.argv) != 2:
        print("Usage: python dreamberd_main.py <filename.db>")
        sys.exit(1)
    
    filename = sys.argv[1]
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    
    try:
        # Read the file content
        with open(filename, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Run the DreamBerd code
        output = run_dreamberd(code)
        
        # Print the output
        if output:
            for line in output:
                print(line)
    except Exception as e:
        print(f"Error executing {filename}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()