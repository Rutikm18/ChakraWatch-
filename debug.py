#!/usr/bin/env python3
"""
ChakraWatch Debug Script
Helps diagnose and fix common issues
"""

import os
import sys
import requests
import subprocess
from pathlib import Path
import time

def check_current_directory():
    """Check what files are in current directory"""
    print("📁 Current Directory Contents:")
    print(f"   Location: {os.getcwd()}")
    
    files = list(Path('.').iterdir())
    for file in sorted(files):
        if file.is_file():
            size = file.stat().st_size
            print(f"   📄 {file.name} ({size:,} bytes)")
        elif file.is_dir():
            file_count = len(list(file.iterdir())) if file.exists() else 0
            print(f"   📁 {file.name}/ ({file_count} files)")

def check_required_files():
    """Check if ChakraWatch files exist"""
    print("\n🔍 Checking ChakraWatch Files:")
    
    required_files = {
        'app.py': 'Backend FastAPI application',
        'frontend/index.html': 'Frontend HTML file',
        'frontend/style.css': 'Frontend CSS styling',
        'frontend/script.js': 'Frontend JavaScript'
    }
    
    missing = []
    for file_path, description in required_files.items():
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"   ✅ {file_path} ({size:,} bytes)")
        else:
            print(f"   ❌ {file_path} - {description}")
            missing.append(file_path)
    
    return missing

def check_running_servers():
    """Check what's running on port 8000"""
    print("\n🌐 Checking Port 8000:")
    
    try:
        response = requests.get('http://localhost:8000', timeout=5)
        print(f"   Status: {response.status_code}")
        
        try:
            data = response.json()
            print(f"   Response: {data}")
            
            # Check if it's ChakraWatch
            if 'ChakraWatch' in str(data):
                print("   ✅ ChakraWatch is running")
                return 'chakrawatch'
            else:
                print("   ⚠️  Different application is running")
                return 'other'
                
        except:
            print("   📄 HTML response (good - frontend serving)")
            return 'frontend'
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Nothing running on port 8000")
        return 'none'
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return 'error'

def kill_port_8000():
    """Kill anything running on port 8000"""
    print("\n🛑 Killing processes on port 8000...")
    
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for line in lines:
                if ':8000' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) > 4:
                        pid = parts[-1]
                        subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                        print(f"   ✅ Killed process {pid}")
        else:  # Unix/Linux/Mac
            subprocess.run(['pkill', '-f', 'uvicorn.*8000'], capture_output=True)
            subprocess.run(['pkill', '-f', 'python.*app'], capture_output=True)
            print("   ✅ Killed Python processes on port 8000")
            
    except Exception as e:
        print(f"   ⚠️  Could not kill processes: {e}")

def create_missing_files():
    """Create missing ChakraWatch files"""
    print("\n📁 Creating missing files...")
    
    # Create frontend directory
    Path('frontend').mkdir(exist_ok=True)
    
    # Minimal index.html if missing
    if not Path('frontend/index.html').exists():
        html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChakraWatch - Cybersecurity Threat Intelligence</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🛡️ ChakraWatch</h1>
            <p>Professional Cybersecurity Threat Intelligence Platform</p>
            <button onclick="location.reload()">🔄 Refresh</button>
        </header>
        
        <main class="main">
            <div id="status">Loading ChakraWatch...</div>
            <div id="articles">No articles loaded yet.</div>
        </main>
    </div>
    <script src="/static/script.js"></script>
</body>
</html>'''
        
        with open('frontend/index.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("   ✅ Created frontend/index.html")
    
    # Minimal style.css if missing
    if not Path('frontend/style.css').exists():
        css_content = '''/* ChakraWatch Basic Styles */
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    min-height: 100vh;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
}

.header {
    text-align: center;
    padding: 2rem;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 15px;
    margin-bottom: 2rem;
    backdrop-filter: blur(10px);
}

.header h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}

.header p {
    font-size: 1.2rem;
    opacity: 0.9;
}

.header button {
    padding: 10px 20px;
    background: #4169E1;
    color: white;
    border: none;
    border-radius: 25px;
    cursor: pointer;
    font-size: 16px;
    margin-top: 1rem;
}

.header button:hover {
    background: #2E4BC6;
    transform: translateY(-2px);
}

.main {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 15px;
    padding: 2rem;
    backdrop-filter: blur(10px);
}

#status, #articles {
    margin: 1rem 0;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
}'''
        
        with open('frontend/style.css', 'w', encoding='utf-8') as f:
            f.write(css_content)
        print("   ✅ Created frontend/style.css")
    
    # Minimal script.js if missing
    if not Path('frontend/script.js').exists():
        js_content = '''// ChakraWatch Basic JavaScript
console.log('🛡️ ChakraWatch Frontend Loading...');

// Check API health
async function checkHealth() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        document.getElementById('status').innerHTML = `
            <h3>✅ ChakraWatch Status: ${data.status}</h3>
            <p>Total Articles: ${data.total_articles || 0}</p>
            <p>Last Updated: ${new Date().toLocaleString()}</p>
        `;
    } catch (error) {
        document.getElementById('status').innerHTML = `
            <h3>❌ Connection Error</h3>
            <p>Could not connect to ChakraWatch API</p>
            <p>Error: ${error.message}</p>
        `;
    }
}

// Load articles
async function loadArticles() {
    try {
        const response = await fetch('/articles');
        const data = await response.json();
        
        if (data.items && data.items.length > 0) {
            const articlesHtml = data.items.map(article => `
                <div style="margin: 1rem 0; padding: 1rem; background: rgba(255,255,255,0.1); border-radius: 8px;">
                    <h4>${article.title}</h4>
                    <p>${article.summary || 'No summary available'}</p>
                    <small>Source: ${article.source_name} | Level: ${article.threat_level}</small>
                </div>
            `).join('');
            
            document.getElementById('articles').innerHTML = `
                <h3>📰 Latest Articles (${data.total})</h3>
                ${articlesHtml}
            `;
        } else {
            document.getElementById('articles').innerHTML = `
                <h3>📰 No Articles Found</h3>
                <p>Try clicking the refresh button or check if scraping is working.</p>
            `;
        }
    } catch (error) {
        document.getElementById('articles').innerHTML = `
            <h3>❌ Could not load articles</h3>
            <p>Error: ${error.message}</p>
        `;
    }
}

// Initialize when page loads
window.addEventListener('DOMContentLoaded', function() {
    checkHealth();
    loadArticles();
    
    // Auto-refresh every 30 seconds
    setInterval(() => {
        checkHealth();
        loadArticles();
    }, 30000);
});'''
        
        with open('frontend/script.js', 'w', encoding='utf-8') as f:
            f.write(js_content)
        print("   ✅ Created frontend/script.js")

def create_minimal_app():
    """Create minimal app.py if missing"""
    if not Path('app.py').exists():
        print("\n📄 Creating minimal app.py...")
        
        app_content = '''#!/usr/bin/env python3
"""
ChakraWatch - Minimal Working Version
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime

# Create directories
os.makedirs("frontend", exist_ok=True)

# Initialize FastAPI app
app = FastAPI(title="ChakraWatch API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
    print("✅ Static files mounted")
except Exception as e:
    print(f"⚠️ Could not mount static files: {e}")

@app.get("/")
async def root():
    """Serve frontend or API info"""
    if os.path.exists("frontend/index.html"):
        return FileResponse('frontend/index.html')
    else:
        return {
            "name": "ChakraWatch API",
            "status": "running", 
            "message": "Frontend files not found. Please create frontend/index.html",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "total_articles": 0,
        "frontend_files": {
            "html": os.path.exists("frontend/index.html"),
            "css": os.path.exists("frontend/style.css"), 
            "js": os.path.exists("frontend/script.js")
        }
    }

@app.get("/articles")
async def get_articles():
    """Get articles (dummy data for now)"""
    return {
        "items": [
            {
                "id": 1,
                "title": "Sample Security Alert",
                "summary": "This is a sample security article for testing purposes.",
                "source_name": "Test Source",
                "threat_level": "medium",
                "published_date": datetime.now().isoformat()
            }
        ],
        "total": 1,
        "page": 1,
        "pages": 1
    }

if __name__ == "__main__":
    import uvicorn
    print("🛡️ Starting ChakraWatch...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
'''
        
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(app_content)
        print("   ✅ Created app.py")

def start_chakrawatch():
    """Start ChakraWatch server"""
    print("\n🚀 Starting ChakraWatch...")
    
    try:
        # Try to import uvicorn
        import uvicorn
        
        # Start the server
        print("   Starting on http://localhost:8000")
        print("   Press Ctrl+C to stop")
        
        # Use subprocess to avoid blocking
        process = subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 
            'app:app', 
            '--host', '0.0.0.0', 
            '--port', '8000', 
            '--reload'
        ])
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if it's working
        try:
            response = requests.get('http://localhost:8000', timeout=5)
            if response.status_code == 200:
                print("   ✅ ChakraWatch started successfully!")
                print("   🌐 Open: http://localhost:8000")
                return True
            else:
                print(f"   ⚠️ Server responding with status {response.status_code}")
                return False
        except:
            print("   ⚠️ Server may still be starting...")
            return False
            
    except ImportError:
        print("   ❌ uvicorn not installed")
        print("   Install with: pip install uvicorn")
        return False
    except Exception as e:
        print(f"   ❌ Error starting server: {e}")
        return False

def main():
    """Main debug function"""
    print("🛡️ ChakraWatch Debug & Fix Tool")
    print("=" * 50)
    
    # Step 1: Check current state
    check_current_directory()
    missing_files = check_required_files()
    server_status = check_running_servers()
    
    # Step 2: Kill wrong server if needed
    if server_status in ['other', 'error']:
        print("\n⚠️ Wrong application is running!")
        kill_port_8000()
        time.sleep(2)
    
    # Step 3: Create missing files
    if missing_files:
        print(f"\n⚠️ Missing files: {', '.join(missing_files)}")
        create_missing_files()
        
        if 'app.py' in missing_files:
            create_minimal_app()
    
    # Step 4: Start ChakraWatch
    print("\n" + "=" * 50)
    print("🚀 Ready to start ChakraWatch!")
    
    response = input("\nStart ChakraWatch now? (y/n): ")
    if response.lower() in ['y', 'yes']:
        start_chakrawatch()
    else:
        print("\n📋 Manual start command:")
        print("   python app.py")
        print("   # OR")
        print("   uvicorn app:app --host 0.0.0.0 --port 8000 --reload")

if __name__ == "__main__":
    main()