#!/usr/bin/env python3
"""
Setup script for the Web Scraping Web Application
"""

import os
import sys
import subprocess
import shutil
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

def check_requirements():
    """Check if required tools are installed"""
    print("Checking requirements...")
    
    requirements = {
        "python": "python --version",
        "node": "node --version",
        "npm": "npm --version",
        "docker": "docker --version",
        "docker-compose": "docker-compose --version"
    }
    
    missing = []
    for tool, command in requirements.items():
        if not run_command(command):
            missing.append(tool)
    
    if missing:
        print(f"\nMissing requirements: {', '.join(missing)}")
        print("Please install the missing tools and run this script again.")
        return False
    
    print("✓ All requirements satisfied")
    return True

def setup_backend():
    """Setup Python backend"""
    print("\nSetting up backend...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("✗ Backend directory not found")
        return False
    
    # Create virtual environment
    if not run_command("python -m venv venv", cwd=backend_dir):
        return False
    
    # Install dependencies
    pip_cmd = "venv/bin/pip" if os.name != 'nt' else "venv\\Scripts\\pip"
    if not run_command(f"{pip_cmd} install -r requirements.txt", cwd=backend_dir):
        return False
    
    # Copy environment file
    env_example = backend_dir / "env.example"
    env_file = backend_dir / ".env"
    if env_example.exists() and not env_file.exists():
        shutil.copy(env_example, env_file)
        print("✓ Created .env file from template")
    
    print("✓ Backend setup complete")
    return True

def setup_frontend():
    """Setup React frontend"""
    print("\nSetting up frontend...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("✗ Frontend directory not found")
        return False
    
    # Install dependencies
    if not run_command("npm install", cwd=frontend_dir):
        return False
    
    print("✓ Frontend setup complete")
    return True

def setup_docker():
    """Setup Docker environment"""
    print("\nSetting up Docker...")
    
    if not Path("docker-compose.yml").exists():
        print("✗ docker-compose.yml not found")
        return False
    
    print("✓ Docker configuration ready")
    return True

def main():
    """Main setup function"""
    print("Web Scraping Web Application Setup")
    print("=" * 40)
    
    if not check_requirements():
        sys.exit(1)
    
    success = True
    
    # Setup components
    if not setup_backend():
        success = False
    
    if not setup_frontend():
        success = False
    
    if not setup_docker():
        success = False
    
    if success:
        print("\n" + "=" * 40)
        print("✓ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Start the application with: docker-compose up")
        print("2. Or run components separately:")
        print("   - Backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
        print("   - Frontend: cd frontend && npm start")
        print("\nAccess the application at http://localhost:3000")
    else:
        print("\n✗ Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
