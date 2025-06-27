#!/usr/bin/env node
/**
 * Post-install script for Flutter MCP Server
 * Provides helpful information after npm installation
 */

const os = require('os');

console.log(`
╔════════════════════════════════════════════════════════════════╗
║              Flutter MCP Server Installed!                     ║
╚════════════════════════════════════════════════════════════════╝

Thank you for installing Flutter MCP Server!

🚀 Quick Start:
   flutter-mcp                    # If installed globally
   npx flutter-mcp                # One-time usage

📚 Documentation:
   https://github.com/flutter-mcp/flutter-mcp

💡 Usage with Claude Desktop:
   Add this to your claude_desktop_config.json:
   
   {
     "mcpServers": {
       "flutter-docs": {
         "command": "npx",
         "args": ["flutter-mcp"]
       }
     }
   }

   Or if installed globally:
   
   {
     "mcpServers": {
       "flutter-docs": {
         "command": "flutter-mcp"
       }
     }
   }

🐛 Issues or questions?
   https://github.com/flutter-mcp/flutter-mcp/issues

Happy coding! 🎉
`);