# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['documentation.py'],
             pathex=['C:\\Users\\elkaaba\\Desktop\\dokumentation'],
             binaries=[],
             datas=[('logo.png', '.'),
                    ('folder.png', '.'),
                    ('files/arabic_reshaper', 'arabic_reshaper')],
             hiddenimports=['reportlab.graphics.barcode.code128',
                            'reportlab.graphics.barcode.code39',
                            'reportlab.graphics.barcode.code93',
                            'reportlab.graphics.barcode.ecc200datamatrix',
                            'reportlab.graphics.barcode.usps',
                            'reportlab.graphics.barcode.usps4s'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='documentation',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False, icon='folder.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='documentation')
