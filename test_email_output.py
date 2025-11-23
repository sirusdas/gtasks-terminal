#!/usr/bin/env python3
"""
Test script to verify the email output is clean and properly formatted
"""

import subprocess
import sys

def test_email_output():
    """Test that the email output is clean and properly formatted."""
    print("Testing email output for rp9 report...")
    
    # Run the command and capture output
    try:
        result = subprocess.run([
            'gtasks', 'generate-report', 'rp9'
        ], capture_output=True, text=True, timeout=30)
        
        # Check if command was successful
        if result.returncode != 0:
            print(f"Command failed with return code {result.returncode}")
            print(f"Error: {result.stderr}")
            return False
            
        output = result.stdout
    
        # Check that output doesn't contain Rich formatting codes
        if '[bold' in output or '[dim' in output or '[cyan' in output:
            print("❌ Output contains Rich formatting codes - not suitable for email")
            return False
            
        # Check that output contains expected elements
        expected_elements = [
            "ORGANIZED TASKS REPORT",
            "Generated on:",
            "Total tasks:",
            "# Other Tasks",
            "Tasks with \"HOLD\" tag",
            "PM related Tasks ",
            "END OF ORGANIZED TASKS REPORT"
        ]
        
        for element in expected_elements:
            if element not in output:
                print(f"❌ Missing expected element: {element}")
                return False
                
        # Check that output contains clean task formatting
        if '└─' in output or '📓' in output:
            print("✅ Output contains clean formatting suitable for email")
        else:
            print("⚠️  Output may be missing some formatting elements")
            
        print("✅ Email output test passed")
        print(f"Output length: {len(output)} characters")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

if __name__ == "__main__":
    success = test_email_output()
    sys.exit(0 if success else 1)