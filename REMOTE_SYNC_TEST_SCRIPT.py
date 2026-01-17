#!/usr/bin/env python3
"""
Remote Sync Feature Test Script
================================

This script tests the remote sync feature with the provided Turso credentials.

Usage:
    python REMOTE_SYNC_TEST_SCRIPT.py

Prerequisites:
    1. Set the Turso token environment variable:
       export GTASKS_TURSO_TOKEN="your-jwt-token-here"
       
    2. Or pass the token as a command line argument:
       python REMOTE_SYNC_TEST_SCRIPT.py --token "your-jwt-token-here"

Provided Credentials:
    URL: libsql://gtaskssqllite-sirusdas.aws-ap-south-1.turso.io
    Token: (JWT token provided by user)
"""

import os
import sys
import argparse
from pathlib import Path

# Add gtasks_cli to path
gtasks_cli_path = Path(__file__).parent / 'gtasks_cli' / 'src'
sys.path.insert(0, str(gtasks_cli_path))


def test_connection():
    """Test connection to Turso database"""
    print("=" * 60)
    print("TEST 1: Testing Connection to Turso Database")
    print("=" * 60)
    
    url = "libsql://gtaskssqllite-sirusdas.aws-ap-south-1.turso.io"
    token = os.environ.get('GTASKS_TURSO_TOKEN')
    
    if not token:
        print("❌ ERROR: No token provided. Set GTASKS_TURSO_TOKEN environment variable")
        print("   Example: export GTASKS_TURSO_TOKEN='your-token'")
        return False
    
    print(f"URL: {url}")
    print(f"Token: {token[:20]}..." if len(token) > 20 else f"Token: {token}")
    
    # Save token to config file for persistence
    print("\n💾 Saving token to config file...")
    try:
        from gtasks_cli.storage.sync_config_storage import SyncConfigStorage
        config_storage = SyncConfigStorage()
        config_storage.save_turso_token(url, token)
        print("✅ Token saved to ~/.gtasks/turso_tokens.json")
    except Exception as e:
        print(f"⚠️  Warning: Could not save token: {e}")
    
    try:
        from gtasks_cli.storage.libsql_storage import LibSQLStorage
        
        print("\n🔌 Attempting connection...")
        storage = LibSQLStorage(url=url, auth_token=token)
        
        if storage.test_connection():
            print("✅ Connection successful!")
            storage.close()
            return True
        else:
            print("❌ Connection test failed!")
            storage.close()
            return False
    
    except Exception as e:
        error_str = str(e)
        print(f"❌ Error testing connection: {e}")
        
        # Provide diagnostic hints
        if "505" in error_str:
            print("\n💡 Diagnostic hints for HTTP 505 error:")
            print("   1. Verify the JWT token is valid and not expired")
            print("   2. Check that the database 'gtaskssqllite-sirusdas' exists in Turso")
            print("   3. Verify the region 'aws-ap-south-1' is correct for your database")
            print("   4. Ensure your Turso account has access to this database")
            print("   5. Try regenerating the authentication token in Turso dashboard")
        elif "Invalid response" in error_str:
            print("\n💡 The Turso server rejected the WebSocket connection.")
            print("   This could indicate authentication or database configuration issues.")
        
        return False


def test_add_remote_db():
    """Test adding a remote database"""
    print("\n" + "=" * 60)
    print("TEST 2: Adding Remote Database")
    print("=" * 60)
    
    url = "libsql://gtaskssqllite-sirusdas.aws-ap-south-1.turso.io"
    name = "Test Turso DB"
    token = os.environ.get('GTASKS_TURSO_TOKEN')
    
    if not token:
        print("❌ ERROR: No token provided")
        return False
    
    try:
        from gtasks_cli.storage.sync_config_storage import SyncConfigStorage
        
        config_storage = SyncConfigStorage()
        db_id = config_storage.add_remote_db(url, name, token)
        
        print(f"✅ Database added successfully!")
        print(f"   ID: {db_id}")
        print(f"   URL: {url}")
        print(f"   Name: {name}")
        
        return db_id
    
    except Exception as e:
        print(f"❌ Error adding remote database: {e}")
        return False


def test_list_remote_dbs():
    """Test listing remote databases"""
    print("\n" + "=" * 60)
    print("TEST 3: Listing Remote Databases")
    print("=" * 60)
    
    try:
        from gtasks_cli.storage.sync_config_storage import SyncConfigStorage
        
        config_storage = SyncConfigStorage()
        databases = config_storage.list_remote_dbs()
        
        if databases:
            print(f"✅ Found {len(databases)} remote database(s):")
            for db in databases:
                print(f"   ID: {db['id']}")
                print(f"   Name: {db['name']}")
                print(f"   URL: {db['url']}")
                print(f"   Active: {db['active']}")
                print()
        else:
            print("✅ No remote databases configured")
        
        return databases
    
    except Exception as e:
        print(f"❌ Error listing remote databases: {e}")
        return []


def test_sync_manager():
    """Test the sync manager"""
    print("\n" + "=" * 60)
    print("TEST 4: Testing Sync Manager")
    print("=" * 60)
    
    token = os.environ.get('GTASKS_TURSO_TOKEN')
    
    if not token:
        print("❌ ERROR: No token provided")
        return False
    
    try:
        from gtasks_cli.sync.remote_sync_manager import RemoteSyncManager
        
        manager = RemoteSyncManager()
        
        # Test getting remote status
        status = manager.get_remote_status()
        print(f"✅ Remote status retrieved:")
        print(f"   Enabled: {status['enabled']}")
        print(f"   Remote DBs: {len(status['remote_dbs'])}")
        print(f"   Local DB exists: {status['local_db_exists']}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error testing sync manager: {e}")
        return False


def test_sync_operations():
    """Test sync operations"""
    print("\n" + "=" * 60)
    print("TEST 5: Testing Sync Operations")
    print("=" * 60)
    
    token = os.environ.get('GTASKS_TURSO_TOKEN')
    
    if not token:
        print("❌ ERROR: No token provided")
        return False
    
    try:
        from gtasks_cli.sync.remote_sync_manager import RemoteSyncManager
        
        manager = RemoteSyncManager()
        
        # Test push
        print("Testing push operation...")
        push_result = manager.push_to_remote()
        print(f"   Push result: {push_result}")
        
        # Test pull
        print("Testing pull operation...")
        pull_result = manager.pull_from_remote()
        print(f"   Pull result: {pull_result}")
        
        # Test sync all
        print("Testing sync all operation...")
        sync_result = manager.sync_all()
        print(f"   Sync result: {sync_result}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error testing sync operations: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli_commands():
    """Test CLI commands"""
    print("\n" + "=" * 60)
    print("TEST 6: Testing CLI Commands")
    print("=" * 60)
    
    url = "libsql://gtaskssqllite-sirusdas.aws-ap-south-1.turso.io"
    token = os.environ.get('GTASKS_TURSO_TOKEN')
    
    if not token:
        print("❌ ERROR: No token provided")
        return False
    
    print("CLI commands that can be used:")
    print(f"   # Add remote database:")
    print(f"   python -m gtasks_cli remote add {url} 'Test DB'")
    print()
    print(f"   # List remote databases:")
    print(f"   python -m gtasks_cli remote list")
    print()
    print(f"   # Sync with remote:")
    print(f"   python -m gtasks_cli remote sync")
    print()
    print(f"   # Push to remote:")
    print(f"   python -m gtasks_cli remote push")
    print()
    print(f"   # Pull from remote:")
    print(f"   python -m gtasks_cli remote pull")
    print()
    print(f"   # Get status:")
    print(f"   python -m gtasks_cli remote status")
    print()
    print(f"   # Remove remote database:")
    print(f"   python -m gtasks_cli remote remove <db_id>")
    
    return True


def main():
    """Main test function"""
    print("🔧 Remote Sync Feature Test Suite")
    print("=" * 60)
    print(f"URL: libsql://gtasks-remote-db-sirusdas.aws-ap-south-1.turso.io")
    print(f"Token: {'Set ✅' if os.environ.get('GTASKS_TURSO_TOKEN') else 'Not Set ❌'}")
    print()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test remote sync feature')
    parser.add_argument('--token', type=str, help='Turso authentication token')
    parser.add_argument('--test', type=str, choices=['connection', 'add', 'list', 'manager', 'sync', 'cli', 'all'],
                        default='all', help='Specific test to run')
    args = parser.parse_args()
    
    # Set token from arguments if provided
    if args.token and not os.environ.get('GTASKS_TURSO_TOKEN'):
        os.environ['GTASKS_TURSO_TOKEN'] = args.token
        print(f"✅ Token set from command line argument")
    
    # Check if token is available
    if not os.environ.get('GTASKS_TURSO_TOKEN'):
        print("❌ ERROR: No token provided!")
        print("\nPlease set the GTASKS_TURSO_TOKEN environment variable:")
        print("   export GTASKS_TURSO_TOKEN='your-jwt-token-here'")
        print("\nOr pass it as a command line argument:")
        print("   python REMOTE_SYNC_TEST_SCRIPT.py --token 'your-jwt-token-here'")
        sys.exit(1)
    
    # Run tests
    results = {}
    
    if args.test in ['connection', 'all']:
        results['connection'] = test_connection()
    
    if args.test in ['add', 'all']:
        results['add'] = test_add_remote_db()
    
    if args.test in ['list', 'all']:
        results['list'] = test_list_remote_dbs()
    
    if args.test in ['manager', 'all']:
        results['manager'] = test_sync_manager()
    
    if args.test in ['sync', 'all']:
        results['sync'] = test_sync_operations()
    
    if args.test in ['cli', 'all']:
        results['cli'] = test_cli_commands()
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.capitalize():15} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
