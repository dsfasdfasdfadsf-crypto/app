#!/bin/bash
# ============================================
# Polymarket Arbitrage Bot - Unix Installer
# Works on Linux and macOS
# ============================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo "============================================"
    echo "⚡ POLYMARKET ARBITRAGE BOT"
    echo "   Unix/Linux Installer"
    echo "============================================"
    echo
}

print_step() {
    echo -e "${BLUE}[$1] $2${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

check_python() {
    print_step "1/4" "Checking Python..."
    
    # Find Python command
    PYTHON_CMD=""
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 8 ]; then
            PYTHON_CMD="python3"
            print_success "Python3 $PYTHON_VERSION found"
        fi
    fi
    
    if [ -z "$PYTHON_CMD" ] && command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
        MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 8 ]; then
            PYTHON_CMD="python"
            print_success "Python $PYTHON_VERSION found"
        fi
    fi
    
    if [ -z "$PYTHON_CMD" ]; then
        print_error "Python 3.8+ is required!"
        echo
        echo "Please install Python 3.8+ using your system package manager:"
        echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip"
        echo "  CentOS/RHEL:   sudo yum install python3 python3-pip"
        echo "  macOS:         brew install python3"
        echo
        echo "Or download from: https://www.python.org/downloads/"
        exit 1
    fi
    
    export PYTHON_CMD
}

install_dependencies() {
    print_step "2/4" "Installing dependencies..."
    
    APP_DIR="polymarket-arbitrage-bot/app"
    
    if [ ! -d "$APP_DIR" ]; then
        print_error "Application directory not found: $APP_DIR"
        exit 1
    fi
    
    if [ ! -f "$APP_DIR/requirements.txt" ]; then
        print_error "Requirements file not found: $APP_DIR/requirements.txt"
        exit 1
    fi
    
    # Upgrade pip
    echo "  Upgrading pip..."
    $PYTHON_CMD -m pip install --upgrade pip --user --quiet
    
    # Install requirements
    echo "  Installing packages..."
    if $PYTHON_CMD -m pip install -r "$APP_DIR/requirements.txt" --user --quiet; then
        print_success "Dependencies installed successfully"
    else
        print_warning "Some packages failed, trying individual installation..."
        
        # Try individual packages
        for package in "PyQt6>=6.6.0" "aiohttp>=3.9.0" "pyyaml>=6.0.0" "python-dotenv>=1.0.0"; do
            echo "  Installing $package..."
            $PYTHON_CMD -m pip install "$package" --user --quiet || print_warning "Failed to install $package"
        done
        
        print_success "Package installation completed (some may have failed)"
    fi
}

create_launcher() {
    print_step "3/4" "Creating launcher..."
    
    APP_DIR="$(pwd)/polymarket-arbitrage-bot/app"
    LAUNCHER_PATH="run_bot.sh"
    
    cat > "$LAUNCHER_PATH" << EOF
#!/bin/bash
# Polymarket Arbitrage Bot Launcher
cd "$APP_DIR"
$PYTHON_CMD main.py
EOF
    
    chmod +x "$LAUNCHER_PATH"
    print_success "Launcher created: $LAUNCHER_PATH"
}

test_installation() {
    print_step "4/4" "Testing installation..."
    
    APP_DIR="polymarket-arbitrage-bot/app"
    
    cd "$APP_DIR"
    
    TEST_SCRIPT='
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
'
    
    if $PYTHON_CMD -c "$TEST_SCRIPT"; then
        print_success "Installation test passed"
        cd - > /dev/null
        return 0
    else
        print_error "Installation test failed"
        cd - > /dev/null
        return 1
    fi
}

main() {
    print_banner
    
    # Check Python
    check_python
    
    # Install dependencies
    install_dependencies
    
    # Create launcher
    create_launcher
    
    # Test installation
    if test_installation; then
        echo
        echo "============================================"
        echo "🎉 INSTALLATION COMPLETE!"
        echo "============================================"
        echo
        echo "🚀 To run the bot:"
        echo "   ./run_bot.sh"
        echo
        echo "📁 Or navigate to:"
        echo "   cd polymarket-arbitrage-bot/app"
        echo "   $PYTHON_CMD main.py"
        echo
        echo "📖 Documentation:"
        echo "   polymarket-arbitrage-bot/app/docs/"
        echo
    else
        echo
        print_error "Installation completed with errors."
        echo "Please check the error messages above."
        exit 1
    fi
    
    echo "============================================"
}

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root is not recommended."
    echo "Consider running as a regular user."
    echo
fi

main "$@"