# ChakraWatch 🛡️

**Professional Cybersecurity Threat Intelligence Platform**

ChakraWatch monitors cybersecurity threats in real-time from multiple sources, providing AI-powered analysis and a clean, professional interface.

## 🎥 Demo Video

<!-- Add your UI demo video here -->
[![ChakraWatch Demo](https://img.youtube.com/vi/YOUR_VIDEO_ID/0.jpg)](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)

*Click to watch ChakraWatch in action*

## ✨ Features

- 🔍 **Real-time threat monitoring** from 4+ security sources
- 🧠 **AI-powered threat analysis** with confidence scoring
- 🎯 **Automatic IOC extraction** (IPs, domains, hashes, CVEs)
- 📊 **Professional dashboard** with live statistics
- 🔍 **Advanced search & filtering** by threat level, source, keywords
- 📱 **Mobile responsive** with dark/light themes

## 🚀 Quick Start

```bash
# Install dependencies
pip install fastapi uvicorn requests sqlalchemy pydantic feedparser beautifulsoup4

# Clone or download the files
# - app.py (backend)
# - frontend/index.html (UI)
# - frontend/style.css (styling)
# - frontend/script.js (functionality)

# Start the server
python app.py

# Open browser
# http://localhost:8000
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

## 📄 License

MIT License - Free to use and modify.

---

**Made for cybersecurity professionals** 🛡️

⭐ Star this repo if it helps secure your organization!