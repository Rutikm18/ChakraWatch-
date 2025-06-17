# ChakraWatch 🛡️

**Cybersecurity Threat Intelligence Platform**

ChakraWatch monitors cybersecurity threats in real-time from multiple sources, providing AI-powered analysis and a professional interface.

## 🎥 Demo Video

[![ChakraWatch Demo](https://img.youtube.com/vi/wvji5hDXLNY/0.jpg)](https://youtu.be/wvji5hDXLNY)

*Click to watch ChakraWatch in action*

## Features

- Real-time threat monitoring
- AI-powered threat analysis
- Automatic IOC extraction (IPs, domains, hashes)
- Professional dashboard with live statistics
- Advanced search & filtering by threat level, source, keywords
- Mobile responsive with dark/light themes

## Quick Start

1. Install dependencies:
    ```bash
    pip install fastapi uvicorn requests sqlalchemy pydantic feedparser beautifulsoup4
    ```

2. Clone or download the necessary files:
    - `app.py` (backend)
    - `frontend/index.html`, `frontend/style.css`, `frontend/script.js` (UI)

3. Start the server:
    ```bash
    python app.py
    ```

4. Open in your browser at [http://localhost:8000](http://localhost:8000)

## Usage

- **View Dashboard**: Monitor real-time threat statistics.
- **Browse Threats**: Review the latest security articles.
- **Search & Filter**: Find specific threats by keywords, level, and source.
- **Manual Refresh**: Click the "Scrape" button to refresh data.

## API Endpoints

- `GET /` - Frontend dashboard
- `GET /health` - System status
- `POST /search` - Search with filters
- `POST /scrape` - Trigger data refresh

## License

MIT License - Free to use and modify.
