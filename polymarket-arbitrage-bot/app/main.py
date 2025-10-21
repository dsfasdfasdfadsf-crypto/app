"""
⚡ Polymarket Arbitrage Bot
Real-time arbitrage detection and execution
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def check_dependencies():
    """Check if required dependencies are installed"""
    missing = []
    
    try:
        import PyQt6
    except ImportError:
        missing.append("PyQt6")
    
    try:
        import aiohttp
    except ImportError:
        missing.append("aiohttp")
    
    try:
        import yaml
    except ImportError:
        missing.append("pyyaml")
    
    if missing:
        print("\n" + "=" * 60)
        print("❌ MISSING DEPENDENCIES")
        print("=" * 60)
        print("\nThe following required packages are not installed:")
        for pkg in missing:
            print(f"  • {pkg}")
        print("\n📦 To install all dependencies, run:")
        print("\n  pip install -r requirements.txt")
        print("\nOr install individually:")
        print("\n  pip install PyQt6 aiohttp pyyaml python-dotenv")
        print("\n" + "=" * 60)
        print("\n💡 See INSTALL.md for detailed installation guide")
        print("=" * 60 + "\n")
        sys.exit(1)


def main():
    """Main entry point"""
    try:
        # Check dependencies first
        check_dependencies()
        
        # Import after checking dependencies
        from src.gui.main_window import run_gui
        from src.utils.logger import setup_logger
        
        logger = setup_logger("arbitrage")
        
        logger.info("=" * 60)
        logger.info("⚡ POLYMARKET ARBITRAGE BOT")
        logger.info("=" * 60)
        logger.info("Mode: DEMO (real prices, fake money)")
        logger.info("Fetching real-time data from Polymarket...")
        logger.info("=" * 60)
        
        # Verify config file exists
        from pathlib import Path
        config_path = Path("config.yaml")
        if not config_path.exists():
            logger.error("Configuration file 'config.yaml' not found!")
            print("\n❌ ERROR: Configuration file missing!")
            print("Please ensure 'config.yaml' exists in the application directory.")
            input("Press Enter to exit...")
            sys.exit(1)
        
        try:
            run_gui()
        except ImportError as e:
            logger.error(f"Import error: {e}")
            print(f"\n❌ ERROR: Missing dependency - {e}")
            print("Please run the installer to install all required packages.")
            input("Press Enter to exit...")
            sys.exit(1)
        except KeyboardInterrupt:
            logger.info("\n\nShutdown requested by user")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
            print(f"\n❌ ERROR: {e}")
            print("Check the log files for more details.")
            input("Press Enter to exit...")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        print("The application failed to start.")
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
