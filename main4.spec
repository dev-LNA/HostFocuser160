block_cipher = None

a = Analysis(
    ['main4.py'],
    pathex=[],
    binaries=[],
    datas=[
        # (Origem no PC, Destino dentro do EXE)
        ('src/config/*.toml', 'src/config'),
        ('assets/*', 'assets'),
        ('assets/ui/*', 'assets/ui'),
        ('assets/ui/icons/*', 'assets/ui/icons'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SeuPrograma', # Nome do executável
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, # Mude para False se não quiser a janela preta do terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.png' # Ícone do executável
)