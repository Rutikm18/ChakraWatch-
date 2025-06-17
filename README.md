# ChakraWatch 🛡️

**Professional Cybersecurity Threat Intelligence Platform**

ChakraWatch monitors cybersecurity threats in real-time from multiple sources, providing AI-powered analysis and a clean, professional interface.

## 🎥 Demo Video

[![ChakraWatch Demo](https://img.youtube.com/vi/wvji5hDXLNY/0.jpg)](https://youtu.be/wvji5hDXLNY)

*Click to watch ChakraWatch in action*

## ✨ Features

- 🔍 **Real-time threat monitoring** from 4+ security sources
- 🧠 **AI-powered threat analysis** with confidence scoring
- 🎯 **Automatic IOC extraction** (IPs, domains, hashes, CVEs)
- 📊 **Professional dashboard** with live statistics
- 🔍 **Advanced search & filtering** by threat level, source, keywords
- 📱 **Mobile responsive** with dark/light themes

## 🚀 Quick Start

### Option 1: Add Docker to Existing Setup (Recommended)
```bash
# You already have working ChakraWatch files! 
# Just add Docker configuration and push to Git

# 1. Run the Docker setup script
chmod +x complete_setup.sh
./complete_setup.sh

# 2. Deploy with Docker
./deploy.sh

# Access: http://localhost:8000
```

### Option 2: Continue with Local Development
```bash
# Your current setup works perfectly!
# Start the server as usual
python app.py
# OR
python run.py

# Open browser: http://localhost:8000
```

### Option 3: Manual Docker Setup
```bash
# Create Docker files manually, then:
docker-compose up -d

# Access: http://localhost:8000
```

## 📁 Required Files Structure

```
chakrawatch/
├── app.py                 # ✅ Main FastAPI backend application (existing)
├── requirements.txt       # ✅ Python dependencies (existing)
├── deploy.sh             # ✅ Deployment automation script (existing)
├── README.md             # ✅ This documentation (existing)
├── debug.py              # ✅ Debug utilities (existing)
├── run.py                # ✅ Local development runner (existing)
├── test_basic.py         # ✅ Basic tests (existing)
├── Dockerfile            # 🐳 Docker image configuration (will be created)
├── docker-compose.yml    # 🐳 Docker services configuration (will be created)
├── .dockerignore         # 🐳 Files to exclude from Docker build (will be created)
├── .gitignore            # 🐳 Git ignore rules (will be created)
├── .env.example          # 🐳 Environment variables template (will be created)
├── data/                 # ✅ Database directory (existing)
│   └── chakrawatch.db    # ✅ SQLite database (existing)
├── logs/                 # ✅ Application logs directory (existing)
│   └── app.log           # ✅ Application log file (existing)
└── frontend/             # ✅ Frontend files directory (existing)
    ├── index.html        # ✅ Main UI page (existing)
    ├── style.css         # ✅ Royal blue & white styling (existing)
    └── script.js         # ✅ Interactive functionality (existing)
```

### 📄 What Each File Does

| File | Status | Purpose |
|------|--------|---------|
| `app.py` | ✅ **Existing** | FastAPI backend with threat intelligence logic |
| `frontend/index.html` | ✅ **Existing** | Professional UI with dashboard and search |
| `frontend/style.css` | ✅ **Existing** | Royal blue & white professional styling |
| `frontend/script.js` | ✅ **Existing** | Interactive features and API integration |
| `requirements.txt` | ✅ **Existing** | Python package dependencies |
| `deploy.sh` | ✅ **Existing** | Deployment automation script |
| `Dockerfile` | 🐳 **Will Create** | Container image build instructions |
| `docker-compose.yml` | 🐳 **Will Create** | Multi-container deployment config |
| `.dockerignore` | 🐳 **Will Create** | Excludes unnecessary files from build |
| `.gitignore` | 🐳 **Will Create** | Git version control ignore rules |
| `.env.example` | 🐳 **Will Create** | Environment variables template |

## 🐳 Docker Deployment

### Prerequisites
- Docker installed
- Docker Compose installed

### Quick Deploy
```bash
# Make deployment script executable
chmod +x deploy.sh

# Start ChakraWatch
./deploy.sh

# View logs
./deploy.sh logs

# Check status  
./deploy.sh status

# Stop
./deploy.sh stop
```

### Manual Docker Commands
```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f chakrawatch

# Stop services
docker-compose down
```

### Docker Environment Variables
```bash
# Create .env file for custom configuration
DATABASE_URL=sqlite:///./data/chakrawatch.db
DEBUG=false
MAX_ARTICLES_PER_SOURCE=20
REQUEST_TIMEOUT=30
```

## 🔧 Deployment Commands

### Using deploy.sh (Recommended)
```bash
./deploy.sh              # Start ChakraWatch
./deploy.sh build        # Build Docker image
./deploy.sh logs         # View application logs
./deploy.sh status       # Check health and status
./deploy.sh restart      # Restart services
./deploy.sh stop         # Stop services
./deploy.sh down         # Stop and remove containers
./deploy.sh clean        # Remove everything (careful!)
./deploy.sh help         # Show all commands
```

### Direct Docker Commands
```bash
# Build and start
docker-compose build
docker-compose up -d

# Management
docker-compose ps                    # Show running containers
docker-compose logs -f chakrawatch  # Follow logs
docker-compose exec chakrawatch sh  # Shell into container
docker-compose down                  # Stop and remove

# Troubleshooting
docker-compose restart chakrawatch  # Restart app
docker-compose build --no-cache     # Rebuild image
docker system prune                 # Clean up Docker
```

## 📖 Usage

1. **View Dashboard** - Monitor real-time threat statistics
2. **Browse Threats** - Review latest security articles
3. **Search & Filter** - Find specific threats by keywords, level, source
4. **Analyze Details** - View IOCs, tags, and threat classifications
5. **Manual Refresh** - Click "Scrape" for new data

## 🔧 API Endpoints

- `GET /` - Frontend dashboard
- `GET /health` - System status
- `GET /articles` - Get threat articles
- `POST /search` - Search with filters
- `GET /stats` - Statistics
- `POST /scrape` - Manual data refresh

## 🐛 Troubleshooting

### Local Installation Issues
**Wrong app showing?**
```bash
# Kill other processes and restart
python app.py
```

**No frontend?**
```bash
# Create frontend folder with HTML/CSS/JS files
mkdir frontend
# Add index.html, style.css, script.js
```

**No articles?**
```bash
# Trigger manual scraping
curl -X POST http://localhost:8000/scrape
```

**Port 8000 busy?**
```bash
# Use different port
uvicorn app:app --port 8001
```

### Docker Issues
**Container won't start?**
```bash
# Check logs
docker-compose logs chakrawatch

# Rebuild image
docker-compose build --no-cache
```

**Permission denied on deploy.sh?**
```bash
# Make script executable
chmod +x deploy.sh
```

**Port already in use?**
```bash
# Edit docker-compose.yml to use different port
ports:
  - "8001:8000"  # Change 8000 to 8001
```

**Data not persisting?**
```bash
# Check volume mounts in docker-compose.yml
# Ensure ./data and ./logs directories exist
mkdir -p data logs
```

## 🏭 Production Deployment

### Production Docker Setup
```bash
# Use production docker-compose
cp docker-compose.yml docker-compose.prod.yml

# Edit for production (uncomment PostgreSQL, Redis)
# Update environment variables
# Set DEBUG=false

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### Production Checklist
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable Redis for caching
- [ ] Set strong passwords
- [ ] Configure SSL/TLS
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Use production WSGI server

## 📄 License

MIT License - Free to use and modify.

---

**Made for cybersecurity professionals** 🛡️

⭐ Star this repo if it helps secure your organization!