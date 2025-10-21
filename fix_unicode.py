#!/usr/bin/env python3
"""
Script to fix Unicode emoji issues for Windows compatibility
"""
import re
from pathlib import Path

def fix_unicode_in_file(file_path):
    """Replace Unicode emojis with ASCII alternatives"""
    
    # Emoji to ASCII mapping
    emoji_replacements = {
        '⚡': '[*]',
        '🎮': '[DEMO]',
        '📊': '[MARKET]',
        '🔍': '[SEARCH]',
        '🔄': '[REFRESH]',
        '💰': '[PRICES]',
        '▶': '[START]',
        '⏹': '[STOP]',
        '📋': '[LOG]',
        '💵': '[BAL]',
        '📈': '[PROFIT]',
        '✓': '[OK]',
        '❌': '[ERROR]',
        '⚠️': '[WARN]',
        '🚨': '[ALERT]',
        '📡': '[FETCH]',
        '🧪': '[TEST]',
        '🔧': '[FIX]',
        '🎯': '[TARGET]',
        '🛡️': '[SHIELD]'
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace emojis
        for emoji, replacement in emoji_replacements.items():
            content = content.replace(emoji, replacement)
        
        # Write back with UTF-8 encoding
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Fixed Unicode in: {file_path}")
        return True
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """Fix Unicode issues in all relevant files"""
    
    base_path = Path("polymarket-arbitrage-bot/app")
    
    files_to_fix = [
        base_path / "src/gui/main_window.py",
        base_path / "src/core/market.py", 
        base_path / "main.py"
    ]
    
    print("Fixing Unicode emoji issues for Windows compatibility...")
    
    fixed_count = 0
    for file_path in files_to_fix:
        if file_path.exists():
            if fix_unicode_in_file(file_path):
                fixed_count += 1
        else:
            print(f"File not found: {file_path}")
    
    print(f"\nFixed {fixed_count} files")
    print("Unicode emojis have been replaced with ASCII alternatives")
    print("The application should now work on Windows systems")

if __name__ == "__main__":
    main()