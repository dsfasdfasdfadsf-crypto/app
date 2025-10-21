#!/usr/bin/env python3
"""
Windows-compatible installer for Polymarket Arbitrage Bot
Handles encoding issues and provides clear feedback
"""
import sys
import subprocess
import os
from pathlib import Path

def print_safe(message):
    """Print message safely on Windows console"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback to ASCII-only output
        ascii_message = message.encode('ascii', 'replace').decode('ascii')
        print(ascii_message)

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_safe("[ERROR] Python 3.8 or higher is required")
        print_safe(f"[INFO] Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print_safe(f"[OK] Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print_safe("[INFO] Installing dependencies...")
    
    requirements = [
        "PyQt6>=6.6.0",
        "aiohttp>=3.9.0", 
        "pyyaml>=6.0.0",
        "python-dotenv>=1.0.0"
    ]
    
    for req in requirements:
        try:
            print_safe(f"[INSTALL] Installing {req}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", req
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print_safe(f"[OK] Installed {req}")
            else:
                print_safe(f"[ERROR] Failed to install {req}")
                print_safe(f"[ERROR] {result.stderr}")
                return False
                
        except Exception as e:
            print_safe(f"[ERROR] Exception installing {req}: {e}")
            return False
    
    return True

def verify_installation():
    """Verify that all dependencies are properly installed"""
    print_safe("[INFO] Verifying installation...")
    
    modules_to_check = [
        ("PyQt6", "PyQt6"),
        ("aiohttp", "aiohttp"),
        ("yaml", "pyyaml"),
        ("dotenv", "python-dotenv")
    ]
    
    all_good = True
    
    for module_name, package_name in modules_to_check:
        try:
            __import__(module_name)
            print_safe(f"[OK] {package_name} is available")
        except ImportError:
            print_safe(f"[ERROR] {package_name} is not available")
            all_good = False
    
    return all_good

def check_config_file():
    """Check if config file exists"""
    config_path = Path("config.yaml")
    if config_path.exists():
        print_safe("[OK] Configuration file found")
        return True
    else:
        print_safe("[ERROR] Configuration file 'config.yaml' not found!")
        print_safe("[INFO] Make sure you're running this from the app directory")
        return False

def main():
    """Main installer function"""
    print_safe("=" * 60)
    print_safe("[*] POLYMARKET ARBITRAGE BOT - WINDOWS INSTALLER")
    print_safe("=" * 60)
    
    # Check Python version
    if not check_python_version():
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print_safe("[ERROR] Failed to install dependencies")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Verify installation
    if not verify_installation():
        print_safe("[ERROR] Installation verification failed")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Check config
    if not check_config_file():
        print_safe("[WARN] Config file missing, but installation completed")
    
    print_safe("\n" + "=" * 60)
    print_safe("[SUCCESS] INSTALLATION COMPLETED")
    print_safe("=" * 60)
    print_safe("[INFO] All dependencies have been installed successfully")
    print_safe("[INFO] You can now run the application with:")
    print_safe("[INFO]   python main.py")
    print_safe("=" * 60)
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()