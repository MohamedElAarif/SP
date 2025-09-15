#!/usr/bin/env python3
"""
Test runner for the Web Scraping Web Application
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True, capture_output=True, text=True)
        print(f"✓ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {command}")
        print(f"Error: {e.stderr}")
        return False

def run_backend_tests():
    """Run backend tests"""
    print("Running backend tests...")
    backend_dir = Path("backend")
    
    if not backend_dir.exists():
        print("✗ Backend directory not found")
        return False
    
    # Run pytest
    pip_cmd = "venv/bin/pip" if os.name != 'nt' else "venv\\Scripts\\pip"
    python_cmd = "venv/bin/python" if os.name != 'nt' else "venv\\Scripts\\python"
    
    # Install test dependencies
    if not run_command(f"{pip_cmd} install pytest pytest-asyncio httpx", cwd=backend_dir):
        return False
    
    # Run tests
    if not run_command(f"{python_cmd} -m pytest tests/ -v", cwd=backend_dir):
        return False
    
    print("✓ Backend tests passed")
    return True

def run_frontend_tests():
    """Run frontend tests"""
    print("Running frontend tests...")
    frontend_dir = Path("frontend")
    
    if not frontend_dir.exists():
        print("✗ Frontend directory not found")
        return False
    
    # Run npm test
    if not run_command("npm test -- --coverage --watchAll=false", cwd=frontend_dir):
        return False
    
    print("✓ Frontend tests passed")
    return True

def main():
    """Main test runner"""
    print("Web Scraping Web Application Test Runner")
    print("=" * 45)
    
    success = True
    
    # Run backend tests
    if not run_backend_tests():
        success = False
    
    # Run frontend tests
    if not run_frontend_tests():
        success = False
    
    if success:
        print("\n" + "=" * 45)
        print("✓ All tests passed!")
    else:
        print("\n✗ Some tests failed. Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
