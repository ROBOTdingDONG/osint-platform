"""
News API Data Collector for OSINT Platform
Collects news articles from various news sources
"""

import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import quote

from ...core.database import get_collection
from ...core.logging_config import get_logger

logger = get_logger('news_collector')


class NewsAPICollector:
    """News API collector for gathering news articles"""
    
    def __init__(self):
        """Initialize News API client"""
        self.api_key = os.getenv('NEWS_API_KEY')
        
        if not self.api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
        
        self.base_url = "https://newsapi.org/v2"
        self.headers = {
            'X-API-Key': self.api_key,
            'User-Agent': 'OSINT-Platform/1.0'
        }
    
    async def collect_data(self, keywords: List[str] = None, sources: List[str] = None, language: str = 'en', page_size: int = 100) -> List[Dict[str, Any]]:
        """Collect news articles based on keywords and sources"""
        if keywords is None:
            keywords = self._get_default_keywords()
        
        collected_articles = []
        
        try:
            for keyword in keywords:
                logger.info(f"Collecting news articles for keyword: {keyword}")
                
                # Get articles from News API
                articles = await self._search_articles(
                    keyword=keyword,
                    sources=sources,
                    language=language,
                    page_size=page_size
                )
                
                for article in articles:
                    article_data = self._process_article(article, keyword)
                    collected_articles.append(article_data)
                    
                    # Store in database
                    await self._store_article(article_data)
                
                logger.info(f"Collected {len(articles)} articles for {keyword}")
            
            logger.info(f"Total articles collected: {len(collected_articles)}")
            return collected_articles
            
        except Exception as e:
            logger.error(f"Error collecting news data: {e}")
            raise
    
    async def _search_articles(self, keyword: str, sources: List[str] = None, language: str = 'en', page_size: int = 100) -> List[Dict[str, Any]]:
        """Search for articles using News API"""
        try:
            # Calculate date range (last 7 days)
            to_date = datetime.utcnow()
            from_date = to_date - timedelta(days=7)
            
            # Build query parameters
            params = {
                'q': quote(keyword),
                'language': language,
                'sortBy': 'publishedAt',
                'pageSize': min(page_size, 100),  # API limit
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d')
            }
            
            if sources:
                params['sources'] = ','.join(sources)
            
            # Make API request
            response = requests.get(
                f"{self.base_url}/everything",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'ok':
                return data['articles']
            else:
                logger.error(f"News API error: {data.get('message', 'Unknown error')}")
                return []
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling News API: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in news search: {e}")
            return []
    
    def _process_article(self, article: Dict[str, Any], keyword: str) -> Dict[str, Any]:
        """Process raw article data into standardized format"""
        # Generate unique ID
        article_id = self._generate_article_id(article)
        
        return {
            'id': article_id,
            'title': article.get('title', ''),
            'content': article.get('content', ''),
            'description': article.get('description', ''),
            'url': article.get('url', ''),
            'author': article.get('author', ''),
            'published_at': article.get('publishedAt', ''),
            'source': {
                'name': article.get('source', {}).get('name', ''),
                'id': article.get('source', {}).get('id', '')
            },
            'metadata': {
                'source': 'news_api',
                'keyword': keyword,
                'language': 'en',
                'url_to_image': article.get('urlToImage', ''),
                'category': self._categorize_article(article)
            },
            'collection_timestamp': datetime.utcnow().isoformat(),
            'content_hash': self._generate_content_hash(article.get('title', '') + article.get('description', ''))
        }
    
    async def _store_article(self, article_data: Dict[str, Any]) -> None:
        """Store article in database"""
        try:
            collection = await get_collection('collected_data')
            
            # Check if article already exists
            existing = await collection.find_one({
                'content_hash': article_data['content_hash']
            })
            
            if not existing:
                await collection.insert_one(article_data)
                logger.debug(f"Stored article {article_data['id']}")
            else:
                logger.debug(f"Article {article_data['id']} already exists")
                
        except Exception as e:
            logger.error(f"Error storing article: {e}")
    
    def _get_default_keywords(self) -> List[str]:
        """Get default keywords from configuration"""
        return [
            'artificial intelligence',
            'cybersecurity',
            'data breach',
            'technology trends',
            'startup funding',
            'digital transformation',
            'cloud computing',
            'machine learning'
        ]
    
    def _generate_article_id(self, article: Dict[str, Any]) -> str:
        """Generate unique ID for article"""
        import hashlib
        
        # Use URL as primary identifier
        url = article.get('url', '')
        title = article.get('title', '')
        published = article.get('publishedAt', '')
        
        unique_string = f"{url}_{title}_{published}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate hash for content deduplication"""
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()
    
    def _categorize_article(self, article: Dict[str, Any]) -> str:
        """Categorize article based on content"""
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        content = f"{title} {description}"
        
        # Simple keyword-based categorization
        if any(word in content for word in ['security', 'breach', 'hack', 'cyber']):
            return 'cybersecurity'
        elif any(word in content for word in ['ai', 'artificial intelligence', 'machine learning']):
            return 'artificial_intelligence'
        elif any(word in content for word in ['startup', 'funding', 'investment', 'venture']):
            return 'business'
        elif any(word in content for word in ['cloud', 'aws', 'azure', 'infrastructure']):
            return 'cloud_computing'
        else:
            return 'general_tech'
    
    async def get_top_headlines(self, country: str = 'us', category: str = 'technology', page_size: int = 50) -> List[Dict[str, Any]]:
        """Get top headlines from News API"""
        try:
            params = {
                'country': country,
                'category': category,
                'pageSize': min(page_size, 100)
            }
            
            response = requests.get(
                f"{self.base_url}/top-headlines",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'ok':
                processed_articles = []
                for article in data['articles']:
                    article_data = self._process_article(article, 'top_headlines')
                    processed_articles.append(article_data)
                    await self._store_article(article_data)
                
                logger.info(f"Collected {len(processed_articles)} top headlines")
                return processed_articles
            else:
                logger.error(f"News API error: {data.get('message', 'Unknown error')}")
                return []
            
        except Exception as e:
            logger.error(f"Error getting top headlines: {e}")
            return []
    
    async def get_sources(self, category: str = None, language: str = 'en', country: str = 'us') -> List[Dict[str, Any]]:
        """Get available news sources"""
        try:
            params = {
                'language': language,
                'country': country
            }
            
            if category:
                params['category'] = category
            
            response = requests.get(
                f"{self.base_url}/sources",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'ok':
                return data['sources']
            else:
                logger.error(f"News API error: {data.get('message', 'Unknown error')}")
                return []
            
        except Exception as e:
            logger.error(f"Error getting news sources: {e}")
            return []
