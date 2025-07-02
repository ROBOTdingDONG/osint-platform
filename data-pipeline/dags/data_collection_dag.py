"""
Main Data Collection DAG for OSINT Platform
Orchestrates data collection from various sources
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

# Default arguments for the DAG
default_args = {
    'owner': 'osint-platform',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    'osint_data_collection',
    default_args=default_args,
    description='OSINT data collection pipeline',
    schedule_interval=timedelta(hours=1),  # Run every hour
    catchup=False,
    max_active_runs=1,
    tags=['osint', 'data-collection'],
)


def collect_social_media_data(**context):
    """
    Collect data from social media sources
    """
    from collectors.social_media.twitter_collector import TwitterCollector
    from collectors.social_media.reddit_collector import RedditCollector
    
    print("Starting social media data collection...")
    
    # Twitter collection
    twitter_collector = TwitterCollector()
    twitter_data = twitter_collector.collect_data()
    print(f"Collected {len(twitter_data)} Twitter posts")
    
    # Reddit collection
    reddit_collector = RedditCollector()
    reddit_data = reddit_collector.collect_data()
    print(f"Collected {len(reddit_data)} Reddit posts")
    
    return {
        'twitter_count': len(twitter_data),
        'reddit_count': len(reddit_data),
        'timestamp': datetime.utcnow().isoformat()
    }


def collect_news_data(**context):
    """
    Collect data from news sources
    """
    from collectors.news.news_api_collector import NewsAPICollector
    from collectors.news.rss_collector import RSSCollector
    
    print("Starting news data collection...")
    
    # News API collection
    news_collector = NewsAPICollector()
    news_data = news_collector.collect_data()
    print(f"Collected {len(news_data)} news articles")
    
    # RSS feed collection
    rss_collector = RSSCollector()
    rss_data = rss_collector.collect_data()
    print(f"Collected {len(rss_data)} RSS articles")
    
    return {
        'news_count': len(news_data),
        'rss_count': len(rss_data),
        'timestamp': datetime.utcnow().isoformat()
    }


def process_collected_data(**context):
    """
    Process and analyze collected data
    """
    from processors.sentiment_processor import SentimentProcessor
    from processors.entity_processor import EntityProcessor
    
    print("Starting data processing...")
    
    # Sentiment analysis
    sentiment_processor = SentimentProcessor()
    sentiment_results = sentiment_processor.process_recent_data()
    print(f"Processed sentiment for {sentiment_results['processed_count']} items")
    
    # Entity extraction
    entity_processor = EntityProcessor()
    entity_results = entity_processor.process_recent_data()
    print(f"Extracted entities from {entity_results['processed_count']} items")
    
    return {
        'sentiment_processed': sentiment_results['processed_count'],
        'entities_extracted': entity_results['processed_count'],
        'timestamp': datetime.utcnow().isoformat()
    }


def generate_alerts(**context):
    """
    Generate alerts based on processed data
    """
    from processors.alert_processor import AlertProcessor
    
    print("Checking for alert conditions...")
    
    alert_processor = AlertProcessor()
    alerts = alert_processor.check_alert_conditions()
    
    print(f"Generated {len(alerts)} new alerts")
    
    return {
        'alerts_generated': len(alerts),
        'timestamp': datetime.utcnow().isoformat()
    }


# Define tasks
social_media_task = PythonOperator(
    task_id='collect_social_media_data',
    python_callable=collect_social_media_data,
    dag=dag,
)

news_task = PythonOperator(
    task_id='collect_news_data',
    python_callable=collect_news_data,
    dag=dag,
)

process_task = PythonOperator(
    task_id='process_collected_data',
    python_callable=process_collected_data,
    dag=dag,
)

alerts_task = PythonOperator(
    task_id='generate_alerts',
    python_callable=generate_alerts,
    dag=dag,
)

cleanup_task = BashOperator(
    task_id='cleanup_old_data',
    bash_command='python /opt/airflow/scripts/cleanup_old_data.py',
    dag=dag,
)

# Define task dependencies
[social_media_task, news_task] >> process_task >> alerts_task >> cleanup_task
