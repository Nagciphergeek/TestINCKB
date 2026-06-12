#!/usr/bin/env python
"""
run_tests.py
Run all unit tests without requiring pytest.
Usage: python run_tests.py
"""
import sys
import os
import importlib
import traceback

TEST_MODULES = [
    "tests.test_anonymizer",
    "tests.test_kb_db",
    "tests.test_pdf_generator",
]

sys.path.insert(0, os.path.dirname(__file__))

total_passed = 0
total_failed = 0

print("=" * 65)
print("  Incident2KB — Test Suite")
print("=" * 65)

for module_name in TEST_MODULES:
    print(f"\n📦 {module_name}")
    print("-" * 50)
    try:
        mod = importlib.import_module(module_name)
    except Exception as e:
        print(f"  ❌ Failed to import module: {e}")
        traceback.print_exc()
        total_failed += 1
        continue

    test_fns = [
        (name, fn) for name, fn in vars(mod).items()
        if name.startswith("test_") and callable(fn)
    ]

    for name, fn in test_fns:
        try:
            fn()
            print(f"  ✅ PASS  {name}")
            total_passed += 1
        except Exception as e:
            print(f"  ❌ FAIL  {name}: {e}")
            total_failed += 1

print("\n" + "=" * 65)
print(f"  Results: {total_passed} passed, {total_failed} failed")
print("=" * 65)

sys.exit(0 if total_failed == 0 else 1)
