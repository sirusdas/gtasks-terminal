#!/usr/bin/env python3
"""
gtasks-automation Post-Installation Setup Script

This script helps users configure the Google Tasks CLI application
after installing it via pip. It handles configuration setup and 
authentication preparation.
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import yaml


def get_os_type() -> str:
    """Get the current operating system type."""
    system = platform.system().lower()
    if system == "linux":
        return "linux"
    elif system == "darwin":
        return "mac"
    elif system == "windows":
        return "windows"
    else:
        return "unknown"


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"{text:^60}")
    print(f"{'='*60}")


def print_step(text: str):
    """Print a step in the setup process."""
    print(f"\n>>> {text}")


def check_gtasks_installed():
    """Check if gtasks-cli is installed."""
    print_step("Checking if gtasks-cli is installed...")
    
    try:
        result = subprocess.run(["gtasks", "--help"], 
                              capture_output=True, 
                              text=True, 
                              timeout=10)
        
        if result.returncode == 0:
            print("✅ gtasks-cli is installed and available")
            return True
        else:
            print("❌ gtasks-cli is not available in current PATH")
            print("💡 Please install with: pip install gtasks-cli")
            return False
    except FileNotFoundError:
        print("❌ gtasks-cli is not installed")
        print("💡 Please install with: pip install gtasks-cli")
        return False
    except subprocess.TimeoutExpired:
        print("❌ gtasks-cli command timed out")
        return False
    except Exception as e:
        print(f"❌ Error checking gtasks-cli: {e}")
        return False


def create_config_directory():
    """Create the configuration directory."""
    print_step("Creating configuration directory...")
    
    config_dir = Path.home() / ".gtasks"
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Configuration directory created: {config_dir}")
        return True
    except Exception as e:
        print(f"❌ Failed to create configuration directory: {e}")
        return False


def setup_default_config():
    """Set up the default configuration."""
    print_step("Setting up default configuration...")
    
    config_dir = Path.home() / ".gtasks"
    config_path = config_dir / "config.yaml"
    
    default_config = {
        'default_tasklist': 'My Tasks',
        'date_format': '%Y-%m-%d',
        'time_format': '%H:%M',
        'sync_on_action': True,
        'offline_mode': False,
        'display': {
            'colors': True,
            'table_style': 'simple',
            'max_width': 100
        },
        'sync': {
            'pull_range_days': 10,
            'auto_save': True
        },
        'accounts': {},
        'aliases': {
            'ls': 'list',
            'rm': 'delete',
            'complete': 'done'
        },
        'custom_reports': {
            'urgent': {
                'filter': 'priority:high status:pending',
                'sort': 'due',
                'columns': ['id', 'title', 'due', 'project']
            }
        }
    }
    
    if not config_path.exists():
        try:
            with open(config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            print(f"✅ Default configuration created: {config_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to create default configuration: {e}")
            return False
    else:
        print(f"⚠️  Configuration already exists: {config_path}")
        return True


def setup_google_auth():
    """Guide user through Google authentication setup."""
    print_step("Setting up Google authentication...")
    
    print("\nTo use Google Tasks CLI, you need to set up Google authentication:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a new project or select an existing one")
    print("3. Enable the Google Tasks API")
    print("4. Create credentials for an OAuth 2.0 client ID")
    print("5. Download the credentials JSON file")
    print("6. Save it as 'credentials.json' in your ~/.gtasks directory")
    
    config_dir = Path.home() / ".gtasks"
    credentials_path = config_dir / "credentials.json"
    
    if credentials_path.exists():
        print(f"\n✅ Found existing credentials at: {credentials_path}")
    else:
        print(f"\n💡 Place your credentials file at: {credentials_path}")
        print("   After placing the file, run: gtasks auth")
    
    return True


def test_basic_functionality():
    """Test basic functionality of the installed CLI."""
    print_step("Testing basic functionality...")
    
    try:
        # Test basic command
        result = subprocess.run(["gtasks", "--help"], 
                              capture_output=True, 
                              text=True, 
                              timeout=10)
        
        if result.returncode == 0:
            print("✅ Basic functionality test passed")
            return True
        else:
            print("❌ Basic functionality test failed")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Basic functionality test failed with error: {e}")
        return False


def print_final_instructions():
    """Print final instructions for the user."""
    print_header("Setup Complete!")
    
    print("\n🎉 Congratulations! Google Tasks CLI is ready to use.")
    print("\n📋 Next Steps:")
    print("   1. If you haven't already, set up Google authentication:")
    print("      gtasks auth")
    print("   2. You can now use gtasks commands:")
    print("      gtasks list          - List your tasks")
    print("      gtasks add \"Buy milk\" - Add a new task")
    print("      gtasks interactive   - Enter interactive mode")
    print("      gtasks --help        - Show all available commands")
    print("\n🔧 Configuration is stored in: ~/.gtasks/config.yaml")
    print("🔒 Credentials are stored in: ~/.gtasks/credentials.json")
    print("\n💡 Pro Tips:")
    print("   - Use 'gtasks interactive' for a rich terminal UI")
    print("   - Use 'gtasks advanced-sync' for enhanced synchronization")
    print("   - Use 'gtasks generate-report' to create analytical reports")
    print("   - Check 'gtasks account --help' for multi-account support")
    print("\n🌐 For more information, visit: https://github.com/sirusdas/gtasks-terminal")


def main():
    """Main setup function."""
    print_header("Google Tasks CLI - Post-Installation Setup")
    
    print(f"Detected OS: {get_os_type().title()}")
    
    # Check if gtasks-cli is installed
    if not check_gtasks_installed():
        print("\n❌ Please install gtasks-cli first using:")
        print("   pip install gtasks-cli")
        print("   Then run this setup script again.")
        return False
    
    # Perform setup steps
    steps = [
        ("Create config directory", create_config_directory),
        ("Setup default config", setup_default_config),
        ("Setup Google auth", setup_google_auth),
        ("Test basic functionality", test_basic_functionality),
    ]
    
    results = []
    for step_name, step_func in steps:
        print(f"\n[{len(results)+1}/{len(steps)}] {step_name}")
        result = step_func()
        results.append((step_name, result))
        
        if not result:
            print(f"❌ Step '{step_name}' failed")
            continue
    
    # Print summary
    print_header("Setup Summary")
    all_passed = True
    for step_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {step_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print_final_instructions()
        print(f"\n✅ Overall Setup Status: SUCCESS")
        return True
    else:
        print(f"\n⚠️  Overall Setup Status: PARTIAL (some steps failed)")
        print("   Please check the errors above and try to resolve them manually.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)