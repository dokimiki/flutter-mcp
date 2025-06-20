#!/usr/bin/env python3
"""Test script for Flutter MCP tools"""

import asyncio
import json
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from flutter_mcp.server import get_flutter_docs, search_flutter_docs, get_pub_package_info, process_flutter_mentions

async def test_tools():
    print("🧪 Testing Flutter MCP Tools")
    print("=" * 50)
    
    # Test 1: Get Flutter docs
    print("\n1. Testing get_flutter_docs for Container widget:")
    result = await get_flutter_docs("Container", "widgets")
    print(f"   Source: {result.get('source', 'unknown')}")
    print(f"   Content length: {len(result.get('content', ''))} chars")
    print(f"   Has error: {'error' in result}")
    
    # Test 2: Search Flutter docs
    print("\n2. Testing search_flutter_docs for material.AppBar:")
    result = await search_flutter_docs("material.AppBar")
    print(f"   Total results: {result.get('total', 0)}")
    if result.get('results'):
        print(f"   First result source: {result['results'][0].get('source', 'unknown')}")
    
    # Test 3: Get pub package info with README
    print("\n3. Testing get_pub_package_info for provider package:")
    result = await get_pub_package_info("provider")
    print(f"   Source: {result.get('source', 'unknown')}")
    print(f"   Version: {result.get('version', 'unknown')}")
    print(f"   Has README: {'readme' in result}")
    if 'readme' in result:
        print(f"   README length: {len(result['readme'])} chars")
    
    # Test 4: Process Flutter mentions
    print("\n4. Testing process_flutter_mentions:")
    test_text = """
    I want to use @flutter_mcp provider for state management.
    Also need docs for @flutter_mcp material.Scaffold widget.
    """
    result = await process_flutter_mentions(test_text)
    print(f"   Found mentions: {result.get('mentions_found', 0)}")
    for mention in result.get('results', []):
        print(f"   - {mention.get('mention', '')} -> {mention.get('type', 'unknown')}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_tools())