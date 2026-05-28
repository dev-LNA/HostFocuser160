block_cipher = None

a = Analysis(
    ['main4.py'],
    pathex=[],
    binaries=[],
    datas=[
        # (Origem no PC, Destino dentro do EXE)
        ('assets/*', 'assets'),
        ('assets/ui/*', 'assets/ui'),
        ('assets/ui/icons/*', 'assets/ui/icons'),
        ('misc/psw.cfg', 'misc'),     # Senha embutida (protegida dentro do EXE)
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
    name='main4',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, 
    icon='assets/icon.png'
)


import shutil
import os


# --- SCRIPT DE AUTOMATIZAÇÃO (Cópia Externa) ---
import shutil
import os

#Caminho de destino para as configurações (AO LADO do .exe)
dist_exe_path = os.path.join('dist') 
config_dest = os.path.join(dist_exe_path, 'src', 'config')
config_src = os.path.join('src', 'config')

print(f">>> Criando pasta de configurações externa em: {config_dest}")
if not os.path.exists(config_dest):
    os.makedirs(config_dest)

for file in os.listdir(config_src):
    if file.endswith(".toml"):
        shutil.copy2(os.path.join(config_src, file), config_dest)
        print(f"  + Config externa: {file}")