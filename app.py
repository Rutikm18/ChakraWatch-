# app.py - ChakraWatch Complete Backend (FIXED VERSION)
import os
import re
import json
import asyncio
import logging
import sys
import requests
import feedparser
import time
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from urllib.parse import urljoin

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Database imports
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, create_engine, and_, or_, func, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func as sql_func

# Pydantic imports
from pydantic import BaseModel, Field
from enum import Enum

# BeautifulSoup for web scraping
from bs4 import BeautifulSoup

# Create directories first
os.makedirs("data", exist_ok=True)
os.makedirs("logs", exist_ok=True)
os.makedirs("frontend", exist_ok=True)

# Safe logging configuration
class SafeFormatter(logging.Formatter):
    def format(self, record):
        # Replace problematic Unicode characters
        msg = super().format(record)
        return msg.encode('ascii', errors='replace').decode('ascii')

# Configure logging with safe handling
log_handlers = []

# File handler
try:
    file_handler = logging.FileHandler('logs/app.log', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    log_handlers.append(file_handler)
except Exception as e:
    print(f"Could not create file handler: {e}")

# Console handler with safe encoding
try:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(SafeFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    log_handlers.append(console_handler)
except Exception as e:
    print(f"Could not create console handler: {e}")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    handlers=log_handlers
)

logger = logging.getLogger(__name__)

# Safe logging function
def safe_log(level, message):
    """Safe logging function that handles Unicode characters"""
    safe_message = message.replace('✅', '[OK]').replace('❌', '[ERROR]').replace('⚠️', '[WARNING]')
    getattr(logger, level)(safe_message)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

class Settings:
    DATABASE_URL = "sqlite:///./data/chakrawatch.db"
    DEBUG = True
    MAX_ARTICLES_PER_SOURCE = 20
    REQUEST_TIMEOUT = 30
    
    # Updated Threat Sources with more reliable options
    THREAT_SOURCES = {
        "security_affairs": {
            "name": "Security Affairs",
            "url": "https://securityaffairs.com/feed",
            "enabled": True,
            "type": "rss"
        },
        "bleeping_computer": {
            "name": "BleepingComputer",
            "url": "https://www.bleepingcomputer.com/feed/",
            "enabled": True,
            "type": "rss"
        },
        "hacker_news_rss": {
            "name": "The Hacker News",
            "url": "https://feeds.feedburner.com/TheHackersNews",
            "enabled": True,
            "type": "rss"
        },
        "cyware": {
            "name": "Cyware",
            "url": "https://cyware.com/allnews.rss",
            "enabled": True,
            "type": "rss"
        }
    }
    
    # Enhanced threat keywords
    THREAT_KEYWORDS = {
        "critical": [
            "zero-day", "0day", "critical vulnerability", "ransomware", 
            "data breach", "supply chain attack", "rce", "remote code execution",
            "critical security flaw", "emergency patch", "actively exploited"
        ],
        "high": [
            "vulnerability", "exploit", "malware", "phishing", "apt", 
            "backdoor", "trojan", "sql injection", "privilege escalation",
            "security flaw", "code execution", "buffer overflow"
        ],
        "medium": [
            "security update", "patch", "warning", "alert", "mitigation", 
            "workaround", "security advisory", "authentication bypass",
            "information disclosure", "denial of service"
        ],
        "low": [
            "security news", "announcement", "report", "advisory", 
            "awareness", "security tip", "best practices"
        ]
    }

settings = Settings()

# ==============================================================================
# DATABASE MODELS
# ==============================================================================

Base = declarative_base()

class ThreatLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ThreatArticle(Base):
    __tablename__ = "threat_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    summary = Column(Text)
    content = Column(Text)
    url = Column(String(1000), unique=True, nullable=False, index=True)
    image_url = Column(String(1000))
    source_name = Column(String(100), index=True)
    author = Column(String(200))
    published_date = Column(DateTime, index=True)
    scraped_date = Column(DateTime, default=sql_func.now())
    threat_level = Column(String(20), default=ThreatLevel.MEDIUM, index=True)
    confidence_score = Column(Float, default=0.5)
    tags = Column(JSON)
    iocs = Column(JSON)
    views = Column(Integer, default=0)
    bookmarked = Column(Boolean, default=False)

# ==============================================================================
# PYDANTIC MODELS
# ==============================================================================

class SearchFilters(BaseModel):
    keywords: Optional[List[str]] = None
    threat_levels: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    has_iocs: Optional[bool] = None

class ThreatArticleResponse(BaseModel):
    id: int
    title: str
    summary: str
    content: str
    url: str
    image_url: Optional[str]
    source_name: str
    author: Optional[str]
    published_date: Optional[datetime]
    scraped_date: datetime
    threat_level: str
    confidence_score: float
    tags: List[str]
    iocs: List[str]
    views: int
    bookmarked: bool
    
    class Config:
        from_attributes = True

class PaginatedResponse(BaseModel):
    items: List[ThreatArticleResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool

# ==============================================================================
# AI THREAT ANALYZER
# ==============================================================================

class ThreatAnalyzer:
    def __init__(self):
        self.threat_keywords = settings.THREAT_KEYWORDS
        
        # IOC patterns
        self.ioc_patterns = {
            'ip': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'domain': r'\b[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}\b',
            'hash_md5': r'\b[a-fA-F0-9]{32}\b',
            'hash_sha256': r'\b[a-fA-F0-9]{64}\b',
            'cve': r'CVE-\d{4}-\d{4,}',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        }
        
        # Tag patterns
        self.tag_patterns = {
            'malware': r'\b(malware|virus|trojan|spyware|rootkit|worm)\b',
            'ransomware': r'\b(ransomware|crypto|encryption)\b',
            'phishing': r'\b(phishing|social engineering|scam)\b',
            'vulnerability': r'\b(vulnerability|cve|exploit|zero-day)\b',
            'data-breach': r'\b(data breach|leak|stolen data)\b',
            'apt': r'\b(apt|advanced persistent threat)\b',
            'mobile': r'\b(android|ios|mobile|smartphone)\b',
            'cloud': r'\b(cloud|aws|azure|google cloud)\b',
            'iot': r'\b(iot|internet of things)\b',
            'cryptocurrency': r'\b(bitcoin|cryptocurrency|crypto|blockchain)\b'
        }
    
    def analyze_threat_level(self, title: str, content: str) -> Tuple[ThreatLevel, float]:
        """Analyze threat level using AI keyword matching"""
        text = f"{title} {content}".lower()
        scores = {}
        
        for level, keywords in self.threat_keywords.items():
            score = 0
            for keyword in keywords:
                matches = len(re.findall(r'\b' + re.escape(keyword.lower()) + r'\b', text))
                score += matches
            scores[level] = score
        
        # Determine threat level
        if scores["critical"] > 0:
            return ThreatLevel.CRITICAL, min(scores["critical"] / 3.0, 1.0)
        elif scores["high"] > 0:
            return ThreatLevel.HIGH, min(scores["high"] / 2.0, 1.0)
        elif scores["medium"] > 0:
            return ThreatLevel.MEDIUM, min(scores["medium"] / 1.5, 1.0)
        else:
            return ThreatLevel.LOW, 0.3
    
    def extract_iocs(self, text: str) -> List[str]:
        """Extract IOCs using regex patterns"""
        iocs = []
        for ioc_type, pattern in self.ioc_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if self._validate_ioc(ioc_type, match):
                    iocs.append(f"{ioc_type}:{match}")
        return list(set(iocs))  # Remove duplicates
    
    def _validate_ioc(self, ioc_type: str, value: str) -> bool:
        """Basic IOC validation"""
        if ioc_type == 'ip':
            parts = value.split('.')
            return all(0 <= int(part) <= 255 for part in parts if part.isdigit())
        elif ioc_type == 'domain':
            return len(value) > 4 and '.' in value
        return True
    
    def extract_tags(self, title: str, content: str) -> List[str]:
        """Extract security tags"""
        text = f"{title} {content}".lower()
        tags = []
        
        for tag, pattern in self.tag_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                tags.append(tag)
        
        return tags

# ==============================================================================
# WEB SCRAPERS
# ==============================================================================

class ScraperManager:
    def __init__(self):
        self.analyzer = ThreatAnalyzer()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        self.session = requests.Session()
    
    def get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def scrape_all_sources(self) -> List[Dict]:
        """Scrape all configured sources with improved error handling"""
        all_articles = []
        
        for source_name, config in settings.THREAT_SOURCES.items():
            if not config.get("enabled", True):
                continue
            
            try:
                safe_log('info', f"Starting scrape for {source_name}...")
                
                if config.get("type") == "rss":
                    articles = await self.scrape_rss_feed(source_name, config)
                else:
                    articles = await self.scrape_html_source(source_name, config)
                
                all_articles.extend(articles)
                safe_log('info', f"Completed scrape for {source_name}: {len(articles)} articles")
                
                # Add delay between sources
                time.sleep(2)
                
            except Exception as e:
                safe_log('error', f"Failed to scrape {source_name}: {str(e)}")
                continue
        
        safe_log('info', f"Total articles scraped: {len(all_articles)}")
        return all_articles
    
    async def scrape_rss_feed(self, source_name: str, config: Dict) -> List[Dict]:
        """Scrape RSS feed with improved error handling"""
        try:
            safe_log('info', f"Fetching RSS feed from {config['url']}")
            
            # Add delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(
                config["url"], 
                headers=self.get_headers(), 
                timeout=settings.REQUEST_TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()
            
            safe_log('info', f"RSS response status: {response.status_code}")
            
            feed = feedparser.parse(response.content)
            articles = []
            
            if not feed.entries:
                safe_log('warning', f"No entries found in RSS feed for {source_name}")
                return []
            
            safe_log('info', f"Found {len(feed.entries)} entries in RSS feed")
            
            for entry in feed.entries[:settings.MAX_ARTICLES_PER_SOURCE]:
                try:
                    title = entry.get('title', '').strip()
                    summary = entry.get('summary', '').strip()
                    url = entry.get('link', '').strip()
                    
                    if not title or not url:
                        continue
                    
                    # Parse date
                    published_date = datetime.now()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            published_date = datetime(*entry.published_parsed[:6])
                        except:
                            pass
                    
                    # Clean HTML from summary
                    if summary:
                        soup = BeautifulSoup(summary, 'html.parser')
                        summary = soup.get_text(strip=True)
                    
                    # Analyze content
                    content = summary
                    threat_level, confidence = self.analyzer.analyze_threat_level(title, content)
                    iocs = self.analyzer.extract_iocs(f"{title} {content}")
                    tags = self.analyzer.extract_tags(title, content)
                    
                    articles.append({
                        'title': title,
                        'summary': summary,
                        'content': content,
                        'url': url,
                        'source_name': source_name,
                        'published_date': published_date,
                        'threat_level': threat_level.value,
                        'confidence_score': confidence,
                        'tags': tags,
                        'iocs': iocs
                    })
                    
                except Exception as e:
                    safe_log('error', f"Error parsing RSS entry: {str(e)}")
                    continue
            
            safe_log('info', f"Successfully parsed {len(articles)} articles from {source_name}")
            return articles
            
        except requests.exceptions.RequestException as e:
            safe_log('error', f"Request error for RSS feed {source_name}: {str(e)}")
            return []
        except Exception as e:
            safe_log('error', f"Error scraping RSS feed {source_name}: {str(e)}")
            return []
    
    async def scrape_html_source(self, source_name: str, config: Dict) -> List[Dict]:
        """Scrape HTML source with improved error handling"""
        try:
            safe_log('info', f"Scraping HTML from {config['url']}")
            
            # Add delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(
                config["url"], 
                headers=self.get_headers(), 
                timeout=settings.REQUEST_TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Generic selectors for finding articles
            article_containers = soup.find_all('article') or soup.find_all('div', class_=lambda x: x and any(
                keyword in x.lower() for keyword in ['post', 'article', 'news', 'item']
            ))
            
            for container in article_containers[:settings.MAX_ARTICLES_PER_SOURCE]:
                try:
                    # Extract title and URL
                    title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
                    if not title_elem:
                        continue
                    
                    link_elem = title_elem.find('a') or container.find('a')
                    if not link_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    url = urljoin(config["url"], link_elem.get('href', ''))
                    
                    # Extract summary
                    summary_elem = container.find('p') or container.find('div', class_=lambda x: x and 'desc' in x.lower())
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""
                    
                    # Extract image
                    img_elem = container.find('img')
                    image_url = urljoin(config["url"], img_elem.get('src', '')) if img_elem else None
                    
                    content = summary
                    
                    # Analyze content
                    threat_level, confidence = self.analyzer.analyze_threat_level(title, content)
                    iocs = self.analyzer.extract_iocs(f"{title} {content}")
                    tags = self.analyzer.extract_tags(title, content)
                    
                    articles.append({
                        'title': title,
                        'summary': summary,
                        'content': content,
                        'url': url,
                        'image_url': image_url,
                        'source_name': source_name,
                        'published_date': datetime.now(),
                        'threat_level': threat_level.value,
                        'confidence_score': confidence,
                        'tags': tags,
                        'iocs': iocs
                    })
                    
                except Exception as e:
                    safe_log('error', f"Error parsing HTML article: {str(e)}")
                    continue
            
            return articles
            
        except requests.exceptions.RequestException as e:
            safe_log('error', f"Request error for HTML source {source_name}: {str(e)}")
            return []
        except Exception as e:
            safe_log('error', f"Error scraping HTML source {source_name}: {str(e)}")
            return []

# ==============================================================================
# DATABASE MANAGER
# ==============================================================================

class DatabaseManager:
    def __init__(self):
        self.engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create database tables"""
        Base.metadata.create_all(bind=self.engine)
        safe_log('info', "Database tables created/verified")
    
    def get_session(self) -> Session:
        return self.SessionLocal()
    
    async def save_articles(self, articles_data: List[Dict]) -> int:
        """Save articles to database"""
        session = self.get_session()
        saved_count = 0
        
        try:
            for article_data in articles_data:
                # Check if exists
                existing = session.query(ThreatArticle).filter(
                    ThreatArticle.url == article_data['url']
                ).first()
                
                if existing:
                    continue
                
                # Create new article
                article = ThreatArticle()
                article.title = article_data.get('title', '')
                article.summary = article_data.get('summary', '')
                article.content = article_data.get('content', '')
                article.url = article_data.get('url', '')
                article.image_url = article_data.get('image_url')
                article.source_name = article_data.get('source_name', '')
                article.author = article_data.get('author')
                article.published_date = article_data.get('published_date', datetime.now())
                article.threat_level = article_data.get('threat_level', 'medium')
                article.confidence_score = article_data.get('confidence_score', 0.5)
                article.tags = json.dumps(article_data.get('tags', []))
                article.iocs = json.dumps(article_data.get('iocs', []))
                
                session.add(article)
                saved_count += 1
            
            session.commit()
            safe_log('info', f"Saved {saved_count} new articles to database")
            return saved_count
            
        except Exception as e:
            session.rollback()
            safe_log('error', f"Error saving articles: {str(e)}")
            raise
        finally:
            session.close()
    
    async def search_articles(self, filters: SearchFilters, page: int = 1, per_page: int = 20) -> PaginatedResponse:
        """Search articles with filters"""
        session = self.get_session()
        
        try:
            query = session.query(ThreatArticle)
            
            # Apply filters
            conditions = []
            
            if filters.keywords:
                keyword_conditions = []
                for keyword in filters.keywords:
                    keyword_like = f"%{keyword}%"
                    keyword_conditions.append(
                        or_(
                            ThreatArticle.title.ilike(keyword_like),
                            ThreatArticle.summary.ilike(keyword_like),
                            ThreatArticle.content.ilike(keyword_like)
                        )
                    )
                conditions.append(or_(*keyword_conditions))
            
            if filters.threat_levels:
                conditions.append(ThreatArticle.threat_level.in_(filters.threat_levels))
            
            if filters.sources:
                conditions.append(ThreatArticle.source_name.in_(filters.sources))
            
            if filters.date_from:
                conditions.append(ThreatArticle.published_date >= filters.date_from)
            
            if filters.date_to:
                conditions.append(ThreatArticle.published_date <= filters.date_to)
            
            if filters.has_iocs is not None:
                if filters.has_iocs:
                    conditions.append(ThreatArticle.iocs != '[]')
                else:
                    conditions.append(ThreatArticle.iocs == '[]')
            
            if conditions:
                query = query.filter(and_(*conditions))
            
            total = query.count()
            
            # Pagination
            query = query.order_by(desc(ThreatArticle.published_date))
            offset = (page - 1) * per_page
            articles = query.offset(offset).limit(per_page).all()
            
            pages = (total + per_page - 1) // per_page
            
            # Convert to response models
            items = []
            for article in articles:
                items.append(ThreatArticleResponse(
                    id=article.id,
                    title=article.title,
                    summary=article.summary or '',
                    content=article.content or '',
                    url=article.url,
                    image_url=article.image_url,
                    source_name=article.source_name,
                    author=article.author,
                    published_date=article.published_date,
                    scraped_date=article.scraped_date,
                    threat_level=article.threat_level,
                    confidence_score=article.confidence_score,
                    tags=json.loads(article.tags) if article.tags else [],
                    iocs=json.loads(article.iocs) if article.iocs else [],
                    views=article.views,
                    bookmarked=article.bookmarked
                ))
            
            return PaginatedResponse(
                items=items,
                total=total,
                page=page,
                per_page=per_page,
                pages=pages,
                has_next=page < pages,
                has_prev=page > 1
            )
            
        finally:
            session.close()
    
    async def get_statistics(self) -> Dict:
        """Get statistics"""
        session = self.get_session()
        
        try:
            total_articles = session.query(ThreatArticle).count()
            
            # Threat distribution
            threat_dist = session.query(
                ThreatArticle.threat_level,
                func.count(ThreatArticle.id)
            ).group_by(ThreatArticle.threat_level).all()
            
            threat_distribution = {level: count for level, count in threat_dist}
            
            # Source distribution
            source_dist = session.query(
                ThreatArticle.source_name,
                func.count(ThreatArticle.id)
            ).group_by(ThreatArticle.source_name).all()
            
            source_distribution = {source: count for source, count in source_dist}
            
            # Articles with IOCs
            articles_with_iocs = session.query(ThreatArticle).filter(
                and_(
                    ThreatArticle.iocs.isnot(None),
                    ThreatArticle.iocs != '[]'
                )
            ).count()
            
            return {
                "total_articles": total_articles,
                "threat_distribution": threat_distribution,
                "source_distribution": source_distribution,
                "articles_with_iocs": articles_with_iocs,
                "last_updated": datetime.now().isoformat()
            }
            
        finally:
            session.close()

# ==============================================================================
# FASTAPI APPLICATION WITH IMPROVED ERROR HANDLING
# ==============================================================================

# Initialize FastAPI app
app = FastAPI(
    title="ChakraWatch API",
    description="Cybersecurity Threat Intelligence Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure frontend directory exists
try:
    if not os.path.exists("frontend"):
        os.makedirs("frontend", exist_ok=True)
        safe_log('warning', "Frontend directory created. Please add your HTML, CSS, and JS files!")
    
    # Mount static files with better error handling
    if os.path.exists("frontend") and os.path.isdir("frontend"):
        app.mount("/static", StaticFiles(directory="frontend"), name="static")
        safe_log('info', "[OK] Static files mounted successfully")
    else:
        safe_log('warning', "Frontend directory not found, static files not mounted")
        
except Exception as e:
    safe_log('error', f"Could not mount static files: {str(e)}")

# Initialize components with error handling
try:
    db_manager = DatabaseManager()
    safe_log('info', "[OK] Database manager initialized")
except Exception as e:
    safe_log('error', f"Failed to initialize database manager: {str(e)}")
    raise

try:
    scraper_manager = ScraperManager()
    safe_log('info', "[OK] Scraper manager initialized")
except Exception as e:
    safe_log('error', f"Failed to initialize scraper manager: {str(e)}")
    raise

@app.on_event("startup")
async def startup_event():
    """Initialize on startup with better error handling"""
    try:
        safe_log('info', "Starting ChakraWatch server...")
        
        # Create database tables
        db_manager.create_tables()
        
        # Test database connection
        session = db_manager.get_session()
        count = session.query(ThreatArticle).count()
        session.close()
        safe_log('info', f"[OK] Database connection verified. Current articles: {count}")
        
        safe_log('info', "[OK] ChakraWatch server startup completed")
        
    except Exception as e:
        safe_log('error', f"Error during startup: {str(e)}")
        raise

from fastapi.responses import JSONResponse

@app.exception_handler(404)
async def custom_404_handler(request, exc):
    """Custom 404 handler for debugging"""
    safe_log('warning', f"404 Error: {request.method} {request.url}")
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The endpoint {request.method} {request.url.path} was not found",
            "available_endpoints": [
                "GET /",
                "GET /health", 
                "GET /articles",
                "POST /search",
                "GET /stats",
                "POST /scrape",
                "POST /analyze",
                "GET /debug/files"
            ]
        }
    )

@app.exception_handler(500)
async def custom_500_handler(request, exc):
    """Custom 500 handler for debugging"""
    safe_log('error', f"500 Error: {request.method} {request.url} - {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An internal server error occurred",
            "detail": str(exc) if settings.DEBUG else "Contact administrator"
        }
    )

# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@app.get("/")
async def root():
    """Serve frontend or API info"""
    if os.path.exists("frontend/index.html"):
        return FileResponse('frontend/index.html')
    else:
        return {
            "name": "ChakraWatch API",
            "status": "running",
            "version": "1.0.0",
            "message": "Frontend files not found. Please ensure frontend/index.html exists.",
            "api_docs": "http://localhost:8000/docs",
            "endpoints": {
                "health": "/health",
                "articles": "/articles", 
                "search": "/search",
                "stats": "/stats",
                "scrape": "/scrape"
            }
        }

@app.get("/health")
async def health_check():
    """Health check"""
    try:
        session = db_manager.get_session()
        total_articles = session.query(ThreatArticle).count()
        session.close()
        
        return {
            "status": "healthy",
            "total_articles": total_articles,
            "timestamp": datetime.now().isoformat(),
            "frontend_files": {
                "html": os.path.exists("frontend/index.html"),
                "css": os.path.exists("frontend/style.css"),
                "js": os.path.exists("frontend/script.js")
            }
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/articles", response_model=PaginatedResponse)
async def get_articles(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    threat_level: Optional[str] = None,
    source: Optional[str] = None
):
    """Get articles"""
    filters = SearchFilters()
    if threat_level:
        filters.threat_levels = [threat_level]
    if source:
        filters.sources = [source]
    
    return await db_manager.search_articles(filters, page, per_page)

@app.post("/search", response_model=PaginatedResponse)
async def search_articles(
    filters: SearchFilters,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Search articles"""
    return await db_manager.search_articles(filters, page, per_page)

@app.get("/stats")
async def get_stats():
    """Get statistics"""
    return await db_manager.get_statistics()

@app.post("/scrape")
async def trigger_scrape(background_tasks: BackgroundTasks):
    """Trigger manual scraping"""
    background_tasks.add_task(scrape_all_sources)
    return {"message": "Scraping initiated", "status": "success"}

@app.post("/analyze")
async def analyze_text(request: dict):
    """Analyze custom text"""
    text = request.get("text", "")
    analyzer = ThreatAnalyzer()
    
    threat_level, confidence = analyzer.analyze_threat_level("", text)
    iocs = analyzer.extract_iocs(text)
    tags = analyzer.extract_tags("", text)
    
    return {
        "threat_level": threat_level.value,
        "confidence_score": confidence,
        "iocs": iocs,
        "tags": tags
    }

# Additional file serving endpoints
@app.get("/style.css")
async def serve_css():
    """Serve CSS file directly"""
    if os.path.exists("frontend/style.css"):
        return FileResponse('frontend/style.css', media_type='text/css')
    else:
        raise HTTPException(status_code=404, detail="CSS file not found")

@app.get("/script.js") 
async def serve_js():
    """Serve JavaScript file directly"""
    if os.path.exists("frontend/script.js"):
        return FileResponse('frontend/script.js', media_type='application/javascript')
    else:
        raise HTTPException(status_code=404, detail="JavaScript file not found")

# Debug endpoint
@app.get("/debug/files")
async def debug_files():
    """Debug endpoint to check file status"""
    files_status = {}
    
    frontend_files = ["index.html", "style.css", "script.js"]
    
    for file in frontend_files:
        file_path = f"frontend/{file}"
        files_status[file] = {
            "exists": os.path.exists(file_path),
            "path": file_path,
            "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
        }
    
    return {
        "frontend_directory_exists": os.path.exists("frontend"),
        "files": files_status,
        "working_directory": os.getcwd()
    }

# ==============================================================================
# BACKGROUND TASKS
# ==============================================================================

async def scrape_all_sources():
    """Background scraping task"""
    try:
        safe_log('info', "Starting background scraping...")
        articles = await scraper_manager.scrape_all_sources()
        
        if articles:
            saved_count = await db_manager.save_articles(articles)
            safe_log('info', f"Background scraping completed: {len(articles)} found, {saved_count} saved")
        else:
            safe_log('warning', "No articles found during scraping")
            
    except Exception as e:
        safe_log('error', f"Error in background scraping: {str(e)}")

# ==============================================================================
# MAIN RUNNER
# ==============================================================================

if __name__ == "__main__":
    try:
        import uvicorn
        safe_log('info', "Starting uvicorn server...")
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000, 
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        safe_log('info', "Server shutdown by user")
    except Exception as e:
        safe_log('error', f"Failed to start server: {str(e)}")
        raise