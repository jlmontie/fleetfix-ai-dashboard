#!/usr/bin/env python3
"""
FleetFix AI Dashboard Test Runner
Simple script to run pytest with proper Python path configuration
"""

import os
import sys
import subprocess

def main():
    """Run the test suite"""
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Set PYTHONPATH environment variable
    env = os.environ.copy()
    env['PYTHONPATH'] = current_dir
    
    # Run pytest with proper configuration
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '-v',
        '--tb=short',
        '--color=yes'
    ]
    
    # Add any command line arguments
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    
    print("Running FleetFix AI Dashboard Tests...")
    print("=" * 50)
    
    try:
        result = subprocess.run(cmd, env=env, cwd=current_dir)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
