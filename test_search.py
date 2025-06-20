#!/usr/bin/env python3
"""Test script for the search_flutter_docs tool"""

import asyncio
import json
from src.flutter_mcp.server import search_flutter_docs

async def test_search():
    """Test various search queries"""
    test_queries = [
        "state management",
        "Container",
        "navigation",
        "http requests",
        "animation",
        "TextField",
        "provider",
        "future",
        "scaffold"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing query: '{query}'")
        print('='*60)
        
        try:
            result = await search_flutter_docs(query)
            
            print(f"Total results: {result['total']}")
            print(f"\nTop results:")
            
            for i, item in enumerate(result['results'][:5], 1):
                print(f"\n{i}. {item['title']}")
                print(f"   Type: {item['type']}")
                print(f"   Relevance: {item['relevance']:.2f}")
                print(f"   Description: {item['description'][:100]}...")
                if 'url' in item:
                    print(f"   URL: {item['url']}")
            
            if result.get('suggestions'):
                print(f"\nSuggestions:")
                for suggestion in result['suggestions']:
                    print(f"  - {suggestion}")
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_search())