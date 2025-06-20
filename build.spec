# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build specification for Flutter MCP Server"""

from PyInstaller.utils.hooks import collect_all

# Collect all data files and binaries from packages
datas = []
binaries = []
hiddenimports = []

# Collect MCP package completely
mcp_datas, mcp_binaries, mcp_hiddenimports = collect_all('mcp')
datas += mcp_datas
binaries += mcp_binaries
hiddenimports += mcp_hiddenimports

# Add specific hidden imports that PyInstaller might miss
hiddenimports += [
    'mcp.server.fastmcp',
    'platformdirs',
    'sqlite3',
    'beautifulsoup4',
    'bs4',
    'httpx',
    'structlog',
    'aiofiles',
]

a = Analysis(
    ['src/flutter_mcp/__main__.py'],
    pathex=['src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='flutter-mcp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)