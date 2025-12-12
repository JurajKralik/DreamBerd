#!/usr/bin/env python3
"""
Quick DreamBerd Test Runner
Runs a subset of basic tests to validate core functionality
"""

import os
import sys
from pathlib import Path

# Add src directory to path so we can import dreamberd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from dreamberd import run_dreamberd


def run_quick_test(filename, expected_output=None):
    """Run a single test file quickly"""
    script_dir = Path(__file__).parent
    file_path = script_dir / "features" / filename
    
    if not file_path.exists():
        print(f"❌ Test file not found: {filename}")
        return False
    
    print(f"\n🧪 Testing: {filename}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        print(f"Code: {code.strip()}")
        
        output = run_dreamberd(code)
        
        if output:
            output_str = '\n'.join(output)
            print(f"Output: {output_str}")
            
            if expected_output and expected_output in output_str:
                print("✅ PASSED")
                return True
            elif expected_output:
                print(f"❌ FAILED - Expected '{expected_output}'")
                return False
            else:
                print("✅ PASSED (no specific expectation)")
                return True
        else:
            print("Output: (none)")
            if expected_output:
                print(f"❌ FAILED - Expected '{expected_output}'")
                return False
            else:
                print("✅ PASSED")
                return True
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    """Run basic tests to validate core functionality"""
    print("🚀 DreamBerd Quick Test Suite")
    print("Testing basic implemented features...")
    
    tests = [
        ("01_exclamation_marks.db", "Hello world"),
        ("03_const_const.db", "Luke"),
        ("07_const_const_const.db", "3.14"),
        ("10_arrays_negative_one.db", "3"),
        ("17_fractions.db", "0.5"),
        ("18_number_names.db", "3"),
        ("22_divide_by_zero.db", "undefined"),
        ("56_increment_decrement.db", "6"),
    ]
    
    passed = 0
    total = len(tests)
    
    for filename, expected in tests:
        if run_quick_test(filename, expected):
            passed += 1
    
    print(f"\n{'='*50}")
    print(f"QUICK TEST RESULTS")
    print(f"{'='*50}")
    print(f"Passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 All basic tests passed!")
    else:
        print(f"❌ {total - passed} tests failed")


if __name__ == "__main__":
    main()