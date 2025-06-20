#!/usr/bin/env python3
"""CLI entry point for Flutter MCP Server"""

import sys
import argparse
import os
from typing import Optional
import asyncio

# Add version info
__version__ = "0.1.0"


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog='flutter-mcp',
        description='Flutter MCP Server - Real-time Flutter/Dart documentation for AI assistants',
        epilog='For more information, visit: https://github.com/flutter-mcp/flutter-mcp'
    )
    
    parser.add_argument(
        'command',
        choices=['start', 'serve', 'dev', 'version', 'help'],
        nargs='?',
        default='start',
        help='Command to run (default: start)'
    )
    
    parser.add_argument(
        '--redis-url',
        default=os.environ.get('REDIS_URL', 'redis://localhost:6379'),
        help='Redis URL for caching (default: redis://localhost:6379)'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Run without Redis caching (slower responses)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    args = parser.parse_args()
    
    # Handle commands
    if args.command == 'version':
        print(f"Flutter MCP Server v{__version__}")
        sys.exit(0)
    
    elif args.command == 'help':
        parser.print_help()
        sys.exit(0)
    
    elif args.command == 'dev':
        # Run with MCP Inspector
        print("🚀 Starting Flutter MCP Server with MCP Inspector...")
        print("📝 Opening browser at http://localhost:5173")
        print("⚡ Use Ctrl+C to stop the server\n")
        
        import subprocess
        try:
            # Set environment variables
            env = os.environ.copy()
            if args.redis_url:
                env['REDIS_URL'] = args.redis_url
            if args.no_cache:
                env['NO_CACHE'] = '1'
            if args.debug:
                env['DEBUG'] = '1'
            
            subprocess.run(['mcp', 'dev', 'server.py'], env=env)
        except KeyboardInterrupt:
            print("\n\n✅ Server stopped")
        except FileNotFoundError:
            print("❌ Error: MCP CLI not found. Please install with: pip install 'mcp[cli]'")
            sys.exit(1)
    
    else:  # start or serve
        # Run the server directly
        print(f"🚀 Starting Flutter MCP Server v{__version__}")
        
        if args.no_cache:
            print("⚠️  Running without cache - responses will be slower")
        else:
            print(f"📦 Using Redis at: {args.redis_url}")
        
        print("⚡ Server running - connect your AI assistant")
        print("⚡ Use Ctrl+C to stop the server\n")
        
        # Set environment variables
        if args.redis_url:
            os.environ['REDIS_URL'] = args.redis_url
        if args.no_cache:
            os.environ['NO_CACHE'] = '1'
        if args.debug:
            os.environ['DEBUG'] = '1'
        
        try:
            # Import and run the server
            from server import main as server_main
            server_main()
        except KeyboardInterrupt:
            print("\n\n✅ Server stopped")
        except ImportError as e:
            print(f"❌ Error: Failed to import server: {e}")
            print("Make sure you're in the correct directory and dependencies are installed")
            sys.exit(1)


if __name__ == "__main__":
    main()