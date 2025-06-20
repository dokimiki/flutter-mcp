#!/usr/bin/env python3
"""Manual test script for Flutter MCP Server"""

import asyncio
import sys
sys.path.insert(0, 'src')

from flutter_mcp.server import get_flutter_docs, get_pub_package_info, search_flutter_docs

async def test_flutter_docs():
    """Test Flutter documentation fetching"""
    print("\n🧪 Testing Flutter Docs...")
    
    # Test Container widget
    result = await get_flutter_docs("Container", "widgets")
    if "error" not in result:
        print("✅ Container widget documentation fetched successfully")
        print(f"   - Content length: {len(result.get('content', ''))} chars")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test StatefulWidget
    result = await get_flutter_docs("StatefulWidget", "widgets")
    if "error" not in result:
        print("✅ StatefulWidget documentation fetched successfully")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test Dart core List with fixed URL pattern
    result = await get_flutter_docs("List", "dart:core")
    if "error" not in result:
        print("✅ Dart core List documentation fetched successfully")
        print(f"   - Content length: {len(result.get('content', ''))} chars")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test Dart async Future
    result = await get_flutter_docs("Future", "dart:async")
    if "error" not in result:
        print("✅ Dart async Future documentation fetched successfully")
    else:
        print(f"❌ Error: {result['error']}")

async def test_pub_package():
    """Test pub.dev package fetching"""
    print("\n🧪 Testing Pub Package Docs...")
    
    # Test provider package
    result = await get_pub_package_info("provider")
    if "error" not in result:
        print("✅ Provider package documentation fetched successfully")
        print(f"   - Version: {result.get('version', 'N/A')}")
        print(f"   - Likes: {result.get('likes', 0)}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test dio package
    result = await get_pub_package_info("dio")
    if "error" not in result:
        print("✅ Dio package documentation fetched successfully")
    else:
        print(f"❌ Error: {result['error']}")

async def test_search():
    """Test search functionality"""
    print("\n🧪 Testing Search...")
    
    # Search for "state management"
    result = await search_flutter_docs("state management")
    if "error" not in result:
        print("✅ Search for 'state management' completed")
        print(f"   - Found {len(result.get('results', []))} results")
        if result.get('results'):
            print("   - Top result:", result['results'][0]['title'])
    else:
        print(f"❌ Error: {result['error']}")
    
    # Search for "http"
    result = await search_flutter_docs("http")
    if "error" not in result:
        print("✅ Search for 'http' completed")
        print(f"   - Found {len(result.get('results', []))} results")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Search for new concepts - architecture
    result = await search_flutter_docs("bloc pattern")
    if "error" not in result:
        print("✅ Search for 'bloc pattern' completed")
        print(f"   - Found {len(result.get('results', []))} results")
        if result.get('results'):
            print("   - Top result:", result['results'][0]['title'])
    else:
        print(f"❌ Error: {result['error']}")
    
    # Search for testing
    result = await search_flutter_docs("widget testing")
    if "error" not in result:
        print("✅ Search for 'widget testing' completed")
        print(f"   - Found {len(result.get('results', []))} results")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Search for performance
    result = await search_flutter_docs("performance profiling")
    if "error" not in result:
        print("✅ Search for 'performance profiling' completed")
        print(f"   - Found {len(result.get('results', []))} results")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Search for new widgets
    result = await search_flutter_docs("AnimatedContainer")
    if "error" not in result:
        print("✅ Search for 'AnimatedContainer' completed")
        print(f"   - Found {len(result.get('results', []))} results")
    else:
        print(f"❌ Error: {result['error']}")

async def main():
    print("🚀 Flutter MCP Server Manual Test")
    print("=" * 50)
    
    await test_flutter_docs()
    await test_pub_package()
    await test_search()
    
    print("\n✨ Test completed!")

if __name__ == "__main__":
    asyncio.run(main())