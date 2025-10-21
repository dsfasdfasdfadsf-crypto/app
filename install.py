#!/usr/bin/env python3
"""
⚡ Polymarket Arbitrage Bot - Cross-Platform Installer
Universal installer that works on Windows, macOS, and Linux
"""
import os
import sys
import subprocess
import platform
from pathlib import Path


def print_banner():
    """Print installation banner"""
    print("=" * 60)
    print("⚡ POLYMARKET ARBITRAGE BOT")
    print("   Cross-Platform Installer")
    print("=" * 60)
    print()


def check_python():
    """Check if Python is available and version is compatible"""
    print("[1/4] Checking Python...")
    
    # Check Python version
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required!")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        print("\n📥 Please install Python 3.8+ from:")
        print("   https://www.python.org/downloads/")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} found!")
    return True


def get_python_command():
    """Get the correct Python command for this system"""
    # Try different Python commands
    commands = ['python3', 'python', 'py']
    
    for cmd in commands:
        try:
            result = subprocess.run([cmd, '--version'], 
                                  capture_output=True, text=True, check=True)
            if 'Python 3.' in result.stdout:
                return cmd
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    return 'python3'  # Default fallback


def install_dependencies():
    """Install required dependencies"""
    print("\n[2/4] Installing dependencies...")
    
    python_cmd = get_python_command()
    app_dir = Path(__file__).parent / "polymarket-arbitrage-bot" / "app"
    
    if not app_dir.exists():
        print("❌ Application directory not found!")
        return False
    
    requirements_file = app_dir / "requirements.txt"
    if not requirements_file.exists():
        print("❌ Requirements file not found!")
        return False
    
    try:
        # Upgrade pip first
        print("   Upgrading pip...")
        subprocess.run([python_cmd, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                      check=True, capture_output=True)
        
        # Install requirements
        print("   Installing packages...")
        subprocess.run([python_cmd, '-m', 'pip', 'install', '-r', str(requirements_file)], 
                      check=True, capture_output=True)
        
        print("✅ Dependencies installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ Failed to install dependencies!")
        print("   Trying individual package installation...")
        
        # Try installing packages individually
        packages = ['PyQt6>=6.6.0', 'aiohttp>=3.9.0', 'pyyaml>=6.0.0', 'python-dotenv>=1.0.0']
        
        for package in packages:
            try:
                print(f"   Installing {package}...")
                subprocess.run([python_cmd, '-m', 'pip', 'install', package], 
                              check=True, capture_output=True)
            except subprocess.CalledProcessError:
                print(f"   ⚠️  Failed to install {package}")
        
        return True  # Continue even if some packages fail


def create_launcher():
    """Create platform-specific launcher"""
    print("\n[3/4] Creating launcher...")
    
    python_cmd = get_python_command()
    app_dir = Path(__file__).parent / "polymarket-arbitrage-bot" / "app"
    
    system = platform.system().lower()
    
    if system == "windows":
        # Create Windows batch file
        launcher_path = Path(__file__).parent / "run_bot.bat"
        launcher_content = f"""@echo off
title Polymarket Arbitrage Bot
cd /d "{app_dir}"
{python_cmd} main.py
pause
"""
    else:
        # Create Unix shell script
        launcher_path = Path(__file__).parent / "run_bot.sh"
        launcher_content = f"""#!/bin/bash
cd "{app_dir}"
{python_cmd} main.py
"""
    
    try:
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)
        
        # Make executable on Unix systems
        if system != "windows":
            os.chmod(launcher_path, 0o755)
        
        print(f"✅ Launcher created: {launcher_path.name}")
        return launcher_path
        
    except Exception as e:
        print(f"❌ Failed to create launcher: {e}")
        return None


def test_installation():
    """Test if the installation works"""
    print("\n[4/4] Testing installation...")
    
    python_cmd = get_python_command()
    app_dir = Path(__file__).parent / "polymarket-arbitrage-bot" / "app"
    
    try:
        # Test importing main modules
        test_script = '''
import sys
sys.path.insert(0, ".")
try:
    from src.utils.config import config
    from src.core.market import PolymarketAPI
    from src.core.arbitrage import ArbitrageDetector
    from src.core.demo_mode import DemoMode
    print("✅ All modules loaded successfully!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
'''
        
        result = subprocess.run([python_cmd, '-c', test_script], 
                              cwd=app_dir, capture_output=True, text=True, check=True)
        
        print(result.stdout.strip())
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ Installation test failed!")
        if e.stdout:
            print(f"   Output: {e.stdout}")
        if e.stderr:
            print(f"   Error: {e.stderr}")
        return False


def main():
    """Main installation process"""
    print_banner()
    
    # Check Python
    if not check_python():
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n⚠️  Some dependencies may not have installed correctly.")
        print("   The application may still work in demo mode.")
    
    # Create launcher
    launcher = create_launcher()
    
    # Test installation
    if test_installation():
        print("\n" + "=" * 60)
        print("🎉 INSTALLATION COMPLETE!")
        print("=" * 60)
        
        if launcher:
            print(f"\n🚀 To run the bot:")
            if platform.system().lower() == "windows":
                print(f"   Double-click: {launcher.name}")
            else:
                print(f"   Run: ./{launcher.name}")
        
        print(f"\n📁 Or navigate to:")
        print(f"   {Path(__file__).parent / 'polymarket-arbitrage-bot' / 'app'}")
        print(f"   Run: {get_python_command()} main.py")
        
        print(f"\n📖 Documentation:")
        print(f"   {Path(__file__).parent / 'polymarket-arbitrage-bot' / 'app' / 'docs'}")
        
    else:
        print("\n❌ Installation completed with errors.")
        print("   Please check the error messages above.")
    
    print("\n" + "=" * 60)
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()