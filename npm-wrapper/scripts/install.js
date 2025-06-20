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
   npx @flutter-mcp/server

📚 Documentation:
   https://github.com/yourusername/flutter-mcp-server

💡 Usage with Claude Desktop:
   Add this to your claude_desktop_config.json:
   
   {
     "mcpServers": {
       "flutter-mcp": {
         "command": "npx",
         "args": ["@flutter-mcp/server", "--stdio"]
       }
     }
   }

🐛 Issues or questions?
   https://github.com/yourusername/flutter-mcp-server/issues

Happy coding! 🎉
`);