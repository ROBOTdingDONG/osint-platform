"""
Twitter Data Collector for OSINT Platform
Collects tweets based on configured keywords and hashtags
"""

import os
import tweepy
from datetime import datetime, timedelta
from typing import List, Dict, Any
from ...core.database import get_collection
from ...core.logging_config import get_logger

logger = get_logger('twitter_collector')


class TwitterCollector:
    """Twitter data collector using Tweepy"""
    
    def __init__(self):
        """Initialize Twitter API client"""
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            raise ValueError("Twitter API credentials not found in environment variables")
        
        # Initialize Tweepy client
        auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
        auth.set_access_token(self.access_token, self.access_token_secret)
        self.api = tweepy.API(auth, wait_on_rate_limit=True)
        
        # Verify credentials
        try:
            self.api.verify_credentials()
            logger.info("Twitter API authentication successful")
        except Exception as e:
            logger.error(f"Twitter API authentication failed: {e}")
            raise
    
    async def collect_data(self, keywords: List[str] = None, count: int = 100) -> List[Dict[str, Any]]:
        """Collect tweets based on keywords"""
        if keywords is None:
            keywords = self._get_default_keywords()
        
        collected_tweets = []
        
        try:
            for keyword in keywords:
                logger.info(f"Collecting tweets for keyword: {keyword}")
                
                # Search for tweets
                tweets = tweepy.Cursor(
                    self.api.search_tweets,
                    q=keyword,
                    lang='en',
                    result_type='recent',
                    tweet_mode='extended'
                ).items(count)
                
                for tweet in tweets:
                    tweet_data = self._process_tweet(tweet, keyword)
                    collected_tweets.append(tweet_data)
                    
                    # Store in database
                    await self._store_tweet(tweet_data)
                
                logger.info(f"Collected {len(collected_tweets)} tweets for {keyword}")
            
            logger.info(f"Total tweets collected: {len(collected_tweets)}")
            return collected_tweets
            
        except Exception as e:
            logger.error(f"Error collecting Twitter data: {e}")
            raise
    
    def _process_tweet(self, tweet, keyword: str) -> Dict[str, Any]:
        """Process raw tweet data into standardized format"""
        return {
            'id': str(tweet.id),
            'text': tweet.full_text,
            'author': {
                'id': str(tweet.user.id),
                'username': tweet.user.screen_name,
                'name': tweet.user.name,
                'followers_count': tweet.user.followers_count,
                'verified': tweet.user.verified
            },
            'created_at': tweet.created_at.isoformat(),
            'metrics': {
                'retweet_count': tweet.retweet_count,
                'favorite_count': tweet.favorite_count,
                'reply_count': getattr(tweet, 'reply_count', 0)
            },
            'metadata': {
                'source': 'twitter',
                'keyword': keyword,
                'language': tweet.lang,
                'is_retweet': hasattr(tweet, 'retweeted_status'),
                'hashtags': [hashtag['text'] for hashtag in tweet.entities.get('hashtags', [])],
                'mentions': [mention['screen_name'] for mention in tweet.entities.get('user_mentions', [])],
                'urls': [url['expanded_url'] for url in tweet.entities.get('urls', [])]
            },
            'collection_timestamp': datetime.utcnow().isoformat(),
            'content_hash': self._generate_content_hash(tweet.full_text)
        }
    
    async def _store_tweet(self, tweet_data: Dict[str, Any]) -> None:
        """Store tweet in database"""
        try:
            collection = await get_collection('collected_data')
            
            # Check if tweet already exists
            existing = await collection.find_one({
                'content_hash': tweet_data['content_hash']
            })
            
            if not existing:
                await collection.insert_one(tweet_data)
                logger.debug(f"Stored tweet {tweet_data['id']}")
            else:
                logger.debug(f"Tweet {tweet_data['id']} already exists")
                
        except Exception as e:
            logger.error(f"Error storing tweet: {e}")
    
    def _get_default_keywords(self) -> List[str]:
        """Get default keywords from configuration"""
        # In production, this would come from database configuration
        return [
            'artificial intelligence',
            'machine learning',
            'cybersecurity',
            'data privacy',
            'technology trends'
        ]
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate hash for content deduplication"""
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get_trending_topics(self, woeid: int = 1) -> List[Dict[str, Any]]:
        """Get trending topics for specified location"""
        try:
            trends = self.api.get_place_trends(woeid)[0]['trends']
            
            processed_trends = []
            for trend in trends:
                processed_trends.append({
                    'name': trend['name'],
                    'url': trend['url'],
                    'volume': trend.get('tweet_volume'),
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return processed_trends
            
        except Exception as e:
            logger.error(f"Error getting trending topics: {e}")
            return []
    
    async def collect_user_timeline(self, username: str, count: int = 50) -> List[Dict[str, Any]]:
        """Collect tweets from specific user timeline"""
        try:
            tweets = self.api.user_timeline(
                screen_name=username,
                count=count,
                tweet_mode='extended',
                exclude_replies=True,
                include_rts=False
            )
            
            collected_tweets = []
            for tweet in tweets:
                tweet_data = self._process_tweet(tweet, f'user:{username}')
                collected_tweets.append(tweet_data)
                await self._store_tweet(tweet_data)
            
            logger.info(f"Collected {len(collected_tweets)} tweets from @{username}")
            return collected_tweets
            
        except Exception as e:
            logger.error(f"Error collecting user timeline for @{username}: {e}")
            return []
