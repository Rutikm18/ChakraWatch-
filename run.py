#!/usr/bin/env python3
"""
ChakraWatch Development Runner
Simple script to start the development server with proper setup
"""

import os
import sys
import subprocess
import webbrowser
import time
import signal
from pathlib import Path
import importlib.util

def check_python_version():
    """Check if Python version is 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def check_requirements():
    """Check if required packages are installed"""
    required_packages = {
        'fastapi': 'FastAPI web framework',
        'uvicorn': 'ASGI server',
        'requests': 'HTTP library',
        'sqlalchemy': 'Database ORM',
        'pydantic': 'Data validation',
        'feedparser': 'RSS/Atom parser',
        'beautifulsoup4': 'HTML parser'
    }
    
    missing = []
    for package, description in required_packages.items():
        try:
            if package == 'beautifulsoup4':
                import bs4
            else:
                importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} - {description}")
    
    if missing:
        print(f"\n📦 Missing packages detected!")
        print(f"Install with: pip install {' '.join(missing)}")
        
        # Offer to install automatically
        response = input("\nWould you like to install missing packages now? (y/n): ")
        if response.lower() in ['y', 'yes']:
            try:
                print("Installing packages...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
                print("✅ Packages installed successfully!")
                return True
            except subprocess.CalledProcessError:
                print("❌ Failed to install packages")
                return False
        return False
    
    print("✅ All required packages are installed")
    return True

def create_directories():
    """Create necessary directories"""
    dirs = ['data', 'logs', 'frontend']
    created = []
    
    for dir_name in dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            created.append(dir_name)
        print(f"✅ Directory: {dir_name}")
    
    if created:
        print(f"📁 Created directories: {', '.join(created)}")
    
    return True

def create_frontend_files():
    """Create frontend files if they don't exist"""
    frontend_dir = Path('frontend')
    
    # Check if frontend files exist
    files_exist = {
        'index.html': (frontend_dir / 'index.html').exists(),
        'style.css': (frontend_dir / 'style.css').exists(),
        'script.js': (frontend_dir / 'script.js').exists()
    }
    
    missing_files = [name for name, exists in files_exist.items() if not exists]
    
    if missing_files:
        print(f"⚠️  Missing frontend files: {', '.join(missing_files)}")
        print("   Please ensure you have the frontend files in the 'frontend' directory:")
        print("   - frontend/index.html")
        print("   - frontend/style.css") 
        print("   - frontend/script.js")
        
        response = input("\nContinue anyway? The API will still work. (y/n): ")
        if response.lower() not in ['y', 'yes']:
            return False
    else:
        print("✅ All frontend files found")
    
    return True

def check_port_availability(port=8000):
    """Check if port is available"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            print(f"✅ Port {port} is available")
            return True
    except OSError:
        print(f"❌ Port {port} is already in use")
        return False

def test_basic_imports():
    """Test if we can import the main modules"""
    try:
        # Test if app.py can be imported
        spec = importlib.util.spec_from_file_location("app", "app.py")
        if spec is None:
            print("❌ Cannot find app.py")
            return False
        
        print("✅ app.py found and looks valid")
        return True
    except Exception as e:
        print(f"❌ Error with app.py: {e}")
        return False

def start_server(port=8000, reload=True):
    """Start the FastAPI server"""
    print(f"\n🚀 Starting ChakraWatch server...")
    print(f"   Backend API: http://localhost:{port}")
    print(f"   Frontend: http://localhost:{port}")
    print(f"   API Docs: http://localhost:{port}/docs")
    print(f"   Health Check: http://localhost:{port}/health")
    print("\n📝 Logs will appear below...")
    print("   Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Start uvicorn server
        cmd = [
            sys.executable, '-m', 'uvicorn',
            'app:app',
            '--host', '0.0.0.0',
            '--port', str(port),
            '--log-level', 'info'
        ]
        
        if reload:
            cmd.append('--reload')
        
        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            print("\n\n🛑 Stopping server...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Start the server
        process = subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except FileNotFoundError:
        print("❌ uvicorn not found. Make sure it's installed:")
        print("   pip install uvicorn")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def open_browser(url="http://localhost:8000", delay=3):
    """Open browser after a delay"""
    def delayed_open():
        time.sleep(delay)
        try:
            webbrowser.open(url)
            print(f"🌐 Opened browser to {url}")
        except Exception as e:
            print(f"Could not open browser: {e}")
    
    import threading
    thread = threading.Thread(target=delayed_open)
    thread.daemon = True
    thread.start()

def show_status():
    """Show current status"""
    print("📊 ChakraWatch Status Check")
    print("=" * 50)
    
    # Check files
    files_to_check = [
        'app.py',
        'frontend/index.html',
        'frontend/style.css', 
        'frontend/script.js'
    ]
    
    for file_path in files_to_check:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"✅ {file_path} ({size:,} bytes)")
        else:
            print(f"❌ {file_path} (missing)")
    
    # Check directories
    for dir_name in ['data', 'logs', 'frontend']:
        if Path(dir_name).exists():
            file_count = len(list(Path(dir_name).iterdir()))
            print(f"✅ {dir_name}/ ({file_count} files)")
        else:
            print(f"❌ {dir_name}/ (missing)")

def main():
    """Main runner function"""
    print("🛡️  ChakraWatch Development Runner")
    print("=" * 50)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'status':
            show_status()
            return
        elif sys.argv[1] == 'install':
            check_requirements()
            return
        elif sys.argv[1] == 'help':
            print("Usage:")
            print("  python run.py        - Start the server")
            print("  python run.py status - Check file status")
            print("  python run.py install - Install dependencies")
            print("  python run.py help   - Show this help")
            return
    
    # Run checks
    checks = [
        ("Python Version", check_python_version),
        ("Required Packages", check_requirements),
        ("Directories", create_directories),
        ("Frontend Files", create_frontend_files),
        ("App Module", test_basic_imports),
        ("Port Availability", check_port_availability)
    ]
    
    print("🔍 Running pre-flight checks...")
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        if not check_func():
            print(f"\n❌ {check_name} check failed!")
            print("Please fix the issues above and try again.")
            sys.exit(1)
    
    print("\n✅ All checks passed!")
    print("\n" + "=" * 50)
    
    # Ask if user wants to open browser
    response = input("\nOpen browser automatically? (y/n): ")
    if response.lower() in ['y', 'yes']:
        open_browser()
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()