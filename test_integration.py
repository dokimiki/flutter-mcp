#!/usr/bin/env python3
"""Integration tests for Flutter MCP Server"""

import asyncio
import sys
from typing import List, Tuple

from server import get_flutter_docs, search_flutter_docs, get_pub_package_info, process_flutter_mentions, health_check


class TestResult:
    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message


async def test_flutter_docs_core_widgets() -> TestResult:
    """Test fetching documentation for core Flutter widgets"""
    test_cases = [
        ("Container", "widgets"),
        ("Scaffold", "material"),
        ("Text", "widgets"),
        ("Column", "widgets"),
        ("Row", "widgets"),
    ]
    
    for class_name, library in test_cases:
        try:
            result = await get_flutter_docs(class_name, library)
            if "error" in result:
                return TestResult(
                    "Flutter Docs - Core Widgets",
                    False,
                    f"Failed to fetch {library}.{class_name}: {result['error']}"
                )
            
            # Verify content
            content = result.get("content", "")
            if len(content) < 100:
                return TestResult(
                    "Flutter Docs - Core Widgets",
                    False,
                    f"Content too short for {library}.{class_name}: {len(content)} chars"
                )
        except Exception as e:
            return TestResult(
                "Flutter Docs - Core Widgets",
                False,
                f"Exception fetching {library}.{class_name}: {str(e)}"
            )
    
    return TestResult("Flutter Docs - Core Widgets", True, f"Tested {len(test_cases)} core widgets")


async def test_pub_packages_popular() -> TestResult:
    """Test fetching information for popular pub.dev packages"""
    test_packages = [
        "provider",
        "bloc",
        "dio",
        "get",
        "riverpod",
    ]
    
    for package in test_packages:
        try:
            result = await get_pub_package_info(package)
            if "error" in result:
                return TestResult(
                    "Pub.dev Packages - Popular",
                    False,
                    f"Failed to fetch {package}: {result['error']}"
                )
            
            # Verify required fields
            if not result.get("version"):
                return TestResult(
                    "Pub.dev Packages - Popular",
                    False,
                    f"No version for {package}"
                )
            
            if "readme" not in result or len(result["readme"]) < 100:
                return TestResult(
                    "Pub.dev Packages - Popular",
                    False,
                    f"README missing or too short for {package}"
                )
        except Exception as e:
            return TestResult(
                "Pub.dev Packages - Popular",
                False,
                f"Exception fetching {package}: {str(e)}"
            )
    
    return TestResult("Pub.dev Packages - Popular", True, f"Tested {len(test_packages)} popular packages")


async def test_search_functionality() -> TestResult:
    """Test search functionality with various patterns"""
    test_queries = [
        "Container",
        "material.AppBar",
        "cupertino.CupertinoButton",
        "dart:core.List",
    ]
    
    for query in test_queries:
        try:
            result = await search_flutter_docs(query)
            if result.get("total", 0) == 0:
                return TestResult(
                    "Search Functionality",
                    False,
                    f"No results for query: {query}"
                )
        except Exception as e:
            return TestResult(
                "Search Functionality",
                False,
                f"Exception searching for {query}: {str(e)}"
            )
    
    return TestResult("Search Functionality", True, f"Tested {len(test_queries)} search patterns")


async def test_flutter_mentions() -> TestResult:
    """Test @flutter_mcp mention processing"""
    test_text = """
    I need help with @flutter_mcp provider for state management.
    Also, how do I use @flutter_mcp material.Scaffold properly?
    What about @flutter_mcp dart:async.Future?
    """
    
    try:
        result = await process_flutter_mentions(test_text)
        
        if result.get("mentions_found", 0) != 3:
            return TestResult(
                "Flutter Mentions",
                False,
                f"Expected 3 mentions, found {result.get('mentions_found', 0)}"
            )
        
        # Check each mention was processed
        results = result.get("results", [])
        if len(results) != 3:
            return TestResult(
                "Flutter Mentions",
                False,
                f"Expected 3 results, got {len(results)}"
            )
        
        # Verify mention types
        expected_types = ["pub_package", "flutter_class", "dart_api"]
        actual_types = [r.get("type") for r in results]
        
        for expected in expected_types:
            if expected not in actual_types:
                return TestResult(
                    "Flutter Mentions",
                    False,
                    f"Missing expected type: {expected}. Got: {actual_types}"
                )
        
    except Exception as e:
        return TestResult(
            "Flutter Mentions",
            False,
            f"Exception processing mentions: {str(e)}"
        )
    
    return TestResult("Flutter Mentions", True, "All mention types processed correctly")


async def test_health_check_functionality() -> TestResult:
    """Test health check returns expected format"""
    try:
        result = await health_check()
        
        # Verify structure
        required_fields = ["status", "timestamp", "checks", "message"]
        for field in required_fields:
            if field not in result:
                return TestResult(
                    "Health Check",
                    False,
                    f"Missing required field: {field}"
                )
        
        # Verify checks
        required_checks = ["flutter_docs", "pub_dev", "redis"]
        for check in required_checks:
            if check not in result["checks"]:
                return TestResult(
                    "Health Check",
                    False,
                    f"Missing required check: {check}"
                )
        
        # Verify status is valid
        valid_statuses = ["ok", "degraded", "failed"]
        if result["status"] not in valid_statuses:
            return TestResult(
                "Health Check",
                False,
                f"Invalid status: {result['status']}"
            )
        
    except Exception as e:
        return TestResult(
            "Health Check",
            False,
            f"Exception running health check: {str(e)}"
        )
    
    return TestResult("Health Check", True, "Health check structure valid")


async def run_all_tests():
    """Run all integration tests"""
    print("🧪 Flutter MCP Server Integration Tests")
    print("=" * 50)
    
    tests = [
        test_flutter_docs_core_widgets(),
        test_pub_packages_popular(),
        test_search_functionality(),
        test_flutter_mentions(),
        test_health_check_functionality(),
    ]
    
    # Run tests with progress indicator
    results = []
    for i, test in enumerate(tests, 1):
        print(f"\n[{i}/{len(tests)}] Running {test.__name__}...", end="", flush=True)
        result = await test
        results.append(result)
        
        if result.passed:
            print(f" ✅ PASSED")
        else:
            print(f" ❌ FAILED")
            print(f"     {result.message}")
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("=" * 50)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"{status} | {result.name}")
        if result.message and result.passed:
            print(f"      {result.message}")
    
    print(f"\nTotal: {passed}/{total} passed ({passed/total*100:.0f}%)")
    
    # Return exit code
    return 0 if passed == total else 1


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    # Set up event loop
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)