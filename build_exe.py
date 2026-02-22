"""
Build script for creating PARE executable
"""
import os
import subprocess
import sys

def build_exe():
    """Build PARE.exe using PyInstaller"""
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--name=PARE",
        "--onefile",
        "--windowed",
        "--icon=assets/logo_solid.png" if os.path.exists("assets/logo_solid.png") else "",
        "--add-data=assets;assets",
        "--hidden-import=PIL._tkinter_finder",
        "pare.py"
    ]
    
    # Remove empty icon argument if no icon exists
    cmd = [arg for arg in cmd if arg]
    
    print("Building PARE.exe...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print("\n✅ Build successful!")
        print("📦 Executable location: dist/PARE.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    build_exe()
