#!/usr/bin/env python3
"""
DreamBerd Test Runner
Runs all individual .db test files and reports results
"""

import os
import sys
import glob
import traceback
from pathlib import Path

# Add src directory to path so we can import dreamberd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from dreamberd import run_dreamberd


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.expected_failures = 0  # Tests that are supposed to fail
    
    def add_pass(self):
        self.passed += 1
    
    def add_fail(self, test_name, error):
        self.failed += 1
        self.errors.append((test_name, error))
    
    def add_expected_fail(self):
        self.expected_failures += 1
    
    def summary(self):
        total = self.passed + self.failed + self.expected_failures
        success_rate = (self.passed + self.expected_failures) / total * 100 if total > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"DREAMBER TEST SUITE SUMMARY")
        print(f"{'='*70}")
        print(f"Total tests: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⚠️  Expected failures: {self.expected_failures}")
        print(f"Success rate: {success_rate:.1f}%")
        
        if self.errors:
            print(f"\nFAILED TESTS:")
            for test_name, error in self.errors:
                print(f"❌ {test_name}")
                print(f"   Error: {error}")
                print()


def get_expected_output(file_path):
    """Extract expected output from test file comments"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for // Expected: output comments
        lines = content.split('\n')
        for line in lines:
            if '// Expected:' in line:
                return line.split('// Expected:', 1)[1].strip()
        
        # Default expectations based on filename patterns
        filename = os.path.basename(file_path)
        
        if 'hello_world' in filename or 'exclamation' in filename:
            return "Hello world"
        elif 'const_const_const' in filename:
            return "3.14"
        elif 'arrays_negative_one' in filename:
            return "3"
        elif 'functions' in filename:
            return "5"
        elif 'divide_by_zero' in filename:
            return "undefined"
        elif 'number_names' in filename:
            return "3"
        elif 'equality' in filename:
            return "true"
        elif 'fractions' in filename:
            return "0.5"
        elif 'increment_decrement' in filename:
            return "6"
            
    except Exception:
        pass
    
    return None


def should_fail(file_path):
    """Determine if a test is expected to fail"""
    filename = os.path.basename(file_path)
    
    # Tests that should fail
    fail_tests = [
        'multiple_class_error',
        'delete_primitives', 
        'delete_keywords'
    ]
    
    return any(fail_test in filename for fail_test in fail_tests)


def run_test_file(file_path, result):
    """Run a single .db test file"""
    filename = os.path.basename(file_path)
    test_name = filename.replace('.db', '').replace('_', ' ').title()
    
    print(f"\n{'='*60}")
    print(f"Running: {test_name}")
    print(f"File: {filename}")
    print(f"{'='*60}")
    
    try:
        # Read the test file
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        print(f"Code:")
        print(code)
        print("-" * 40)
        
        expected_output = get_expected_output(file_path)
        should_fail_test = should_fail(file_path)
        
        if should_fail_test:
            print("⚠️  This test is expected to fail")
        
        # Run the DreamBerd code
        output = run_dreamberd(code)
        
        if should_fail_test:
            print("❌ Test should have failed but passed")
            if output:
                print("Output:", '\n'.join(output))
            result.add_fail(test_name, "Expected failure but test passed")
            return
        
        # Check output
        if output:
            output_str = '\n'.join(output)
            print("Output:", output_str)
            
            if expected_output and expected_output in output_str:
                print("✅ PASSED")
                result.add_pass()
            elif expected_output:
                print(f"❌ FAILED - Expected '{expected_output}' but got '{output_str}'")
                result.add_fail(test_name, f"Expected '{expected_output}' but got '{output_str}'")
            else:
                print("✅ PASSED (no specific output expected)")
                result.add_pass()
        else:
            print("Output: (no output)")
            if expected_output:
                print(f"❌ FAILED - Expected '{expected_output}' but got no output")
                result.add_fail(test_name, f"Expected '{expected_output}' but got no output")
            else:
                print("✅ PASSED")
                result.add_pass()
                
    except Exception as e:
        if should_fail(file_path):
            print(f"✅ EXPECTED FAILURE: {e}")
            result.add_expected_fail()
        else:
            error_msg = str(e)
            print(f"❌ ERROR: {error_msg}")
            result.add_fail(test_name, error_msg)


def main():
    """Run all DreamBerd test files"""
    print("🚀 DreamBerd Test Suite Runner")
    print("Running all individual .db test files...")
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    features_dir = script_dir / "features"
    
    if not features_dir.exists():
        print(f"❌ Features directory not found: {features_dir}")
        return
    
    # Find all .db files
    test_files = sorted(glob.glob(str(features_dir / "*.db")))
    
    if not test_files:
        print(f"❌ No .db test files found in {features_dir}")
        return
    
    print(f"Found {len(test_files)} test files")
    
    result = TestResult()
    
    # Run each test file
    for test_file in test_files:
        run_test_file(test_file, result)
    
    # Show summary
    result.summary()
    
    # Exit with appropriate code
    if result.failed > 0:
        sys.exit(1)
    else:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()