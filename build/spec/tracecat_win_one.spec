# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['..\\..\\tracecat.py'],
             pathex=['..\\..\\'],
             binaries=[],
             datas=[
              ('../../venv/lib/site-packages/perfetto/trace_processor', './perfetto/trace_processor'),
              ('../../libs/', './libs'),
              ('../../demon/obj/local/arm64-v8a/tracecatd', './demon/obj/local/arm64-v8a/'),
              ('../../configs', './configs')
             ],
             hiddenimports=[],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='tracecat',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
