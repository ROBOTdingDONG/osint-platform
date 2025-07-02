"""
Sentiment Analysis Processor for OSINT Platform
Analyzes sentiment of collected text data using multiple approaches
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from textblob import TextBlob
try:
    import openai
except ImportError:
    openai = None

from ..core.database import get_collection
from ..core.logging_config import get_logger, performance_logger

logger = get_logger('sentiment_processor')


class SentimentProcessor:
    """Processes text data for sentiment analysis"""
    
    def __init__(self):
        """Initialize sentiment processor with available models"""
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if openai and self.openai_api_key:
            openai.api_key = self.openai_api_key
            self.use_openai = True
            logger.info("OpenAI API configured for advanced sentiment analysis")
        else:
            self.use_openai = False
            logger.info("Using TextBlob for sentiment analysis")
    
    async def process_recent_data(self, hours_back: int = 1) -> Dict[str, Any]:
        """Process recently collected data for sentiment"""
        start_time = datetime.utcnow()
        
        try:
            # Get unprocessed data from the last N hours
            collection = await get_collection('collected_data')
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            # Find data that needs sentiment analysis
            cursor = collection.find({
                'collection_timestamp': {'$gte': cutoff_time.isoformat()},
                'sentiment_score': {'$exists': False}
            })
            
            processed_count = 0
            
            async for document in cursor:
                try:
                    # Extract text content
                    text = self._extract_text(document)
                    
                    if text:
                        # Analyze sentiment
                        sentiment_result = await self._analyze_sentiment(text)
                        
                        # Update document with sentiment data
                        await collection.update_one(
                            {'_id': document['_id']},
                            {
                                '$set': {
                                    'sentiment_score': sentiment_result['score'],
                                    'sentiment_label': sentiment_result['label'],
                                    'sentiment_confidence': sentiment_result['confidence'],
                                    'sentiment_processed_at': datetime.utcnow().isoformat()
                                }
                            }
                        )
                        
                        processed_count += 1
                        
                        if processed_count % 10 == 0:
                            logger.info(f"Processed sentiment for {processed_count} items")
                
                except Exception as e:
                    logger.error(f"Error processing sentiment for document {document.get('_id')}: {e}")
                    continue
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            performance_logger.log_data_processing('sentiment_analysis', processed_count, duration)
            
            logger.info(f"Sentiment processing completed: {processed_count} items in {duration:.2f}s")
            
            return {
                'processed_count': processed_count,
                'duration_seconds': duration,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in sentiment processing: {e}")
            raise
    
    def _extract_text(self, document: Dict[str, Any]) -> Optional[str]:
        """Extract text content from document"""
        # Try different text fields based on source
        text_fields = ['text', 'content', 'title', 'description']
        
        for field in text_fields:
            if field in document and document[field]:
                return str(document[field])
        
        return None
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text using available models"""
        if self.use_openai and len(text) > 100:  # Use OpenAI for longer texts
            return await self._analyze_with_openai(text)
        else:
            return self._analyze_with_textblob(text)
    
    def _analyze_with_textblob(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using TextBlob"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Convert to standardized format
            score = (polarity + 1) / 2  # Convert to 0-1 scale
            
            if polarity > 0.1:
                label = 'positive'
            elif polarity < -0.1:
                label = 'negative'
            else:
                label = 'neutral'
            
            confidence = abs(polarity)  # Use absolute polarity as confidence
            
            return {
                'score': score,
                'label': label,
                'confidence': confidence,
                'method': 'textblob',
                'raw_polarity': polarity,
                'subjectivity': subjectivity
            }
            
        except Exception as e:
            logger.error(f"TextBlob sentiment analysis failed: {e}")
            return {
                'score': 0.5,
                'label': 'neutral',
                'confidence': 0.0,
                'method': 'textblob',
                'error': str(e)
            }
    
    async def _analyze_with_openai(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using OpenAI API"""
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sentiment analysis expert. Analyze the sentiment of the given text and respond with a JSON object containing 'score' (0-1 where 0 is very negative, 0.5 is neutral, 1 is very positive), 'label' (positive/negative/neutral), and 'confidence' (0-1)."
                    },
                    {
                        "role": "user",
                        "content": f"Analyze the sentiment of this text: {text[:1000]}"  # Limit text length
                    }
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            # Parse the response
            result_text = response.choices[0].message.content
            
            try:
                import json
                result = json.loads(result_text)
                result['method'] = 'openai'
                return result
            except json.JSONDecodeError:
                # Fallback to TextBlob if OpenAI response is not valid JSON
                logger.warning("OpenAI returned invalid JSON, falling back to TextBlob")
                return self._analyze_with_textblob(text)
            
        except Exception as e:
            logger.error(f"OpenAI sentiment analysis failed: {e}")
            # Fallback to TextBlob
            return self._analyze_with_textblob(text)
    
    async def get_sentiment_summary(self, source: str = None, time_range: int = 24) -> Dict[str, Any]:
        """Get sentiment summary for recent data"""
        try:
            collection = await get_collection('collected_data')
            
            cutoff_time = datetime.utcnow() - timedelta(hours=time_range)
            
            # Build query
            query = {
                'collection_timestamp': {'$gte': cutoff_time.isoformat()},
                'sentiment_score': {'$exists': True}
            }
            
            if source:
                query['metadata.source'] = source
            
            # Aggregate sentiment data
            pipeline = [
                {'$match': query},
                {
                    '$group': {
                        '_id': None,
                        'avg_sentiment': {'$avg': '$sentiment_score'},
                        'total_count': {'$sum': 1},
                        'positive_count': {
                            '$sum': {
                                '$cond': [{'$eq': ['$sentiment_label', 'positive']}, 1, 0]
                            }
                        },
                        'negative_count': {
                            '$sum': {
                                '$cond': [{'$eq': ['$sentiment_label', 'negative']}, 1, 0]
                            }
                        },
                        'neutral_count': {
                            '$sum': {
                                '$cond': [{'$eq': ['$sentiment_label', 'neutral']}, 1, 0]
                            }
                        }
                    }
                }
            ]
            
            result = await collection.aggregate(pipeline).to_list(1)
            
            if result:
                data = result[0]
                return {
                    'average_sentiment': data['avg_sentiment'],
                    'total_items': data['total_count'],
                    'distribution': {
                        'positive': data['positive_count'],
                        'negative': data['negative_count'],
                        'neutral': data['neutral_count']
                    },
                    'source': source,
                    'time_range_hours': time_range,
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'average_sentiment': 0.5,
                    'total_items': 0,
                    'distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
                    'source': source,
                    'time_range_hours': time_range,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting sentiment summary: {e}")
            raise
