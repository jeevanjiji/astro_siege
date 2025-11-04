"""
Build script for creating Windows executable using PyInstaller
Run: python build_exe.py
"""
import PyInstaller.__main__
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    'main.py',
    '--name=AstroSiege',
    '--onefile',
    '--windowed',
    '--icon=assets/g1.png',  # If you have an icon
    '--add-data=assets;assets',
    '--noconsole',
    '--clean',
])

print("\n✅ Build complete! Check the 'dist' folder for AstroSiege.exe")
