import certifi
# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['hyperzip_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        (certifi.where(), 'certifi'),
        ('oxipng.exe', '.'),  # Include oxipng.exe in the root of the packaged app
        ('assets/oxipng-9.1.4-i686-pc-windows-msvc', 'oxipng-9.1.4-i686-pc-windows-msvc'),  # Include the oxipng directory
        # Include the tinify certificate bundle
        ('C:\\Users\\05\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\tinify\\data\\cacert.pem', 'tinify\\data'),
    ],
        hiddenimports=['PIL._tkinter_finder', 'PIL.Image', 'PIL.JpegImagePlugin', 'customtkinter', 'tinify', 'htmlmin', 'jsmin', 'csscompressor', 'tkinter', 'tkinter.filedialog', 'tkinter.messagebox', 'certifi'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HyperZip',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # Reverted back to False
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
