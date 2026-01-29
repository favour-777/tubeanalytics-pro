# YouTube Data Fetcher - Uses proven Apify actors
# Zero loose ends, production-grade

from apify import Actor
from typing import List, Dict, Optional
import re


class YouTubeFetcher:
    """Fetches YouTube data using proven Apify actors"""
    
    def __init__(self):
        self.youtube_scraper_id = 'streamers/youtube-scraper'  # 193K users - most trusted
        self.transcript_scraper_id = 'bernardo/youtube-captions-scraper'  # Proven transcript actor
    
    async def fetch_channel_data(self, channel_url: str, video_count: int = 20) -> Optional[Dict]:
        """Fetch channel videos using proven YouTube scraper"""
        
        try:
            Actor.log.info(f"Calling YouTube scraper for: {channel_url}")
            
            # Call the proven YouTube scraper
            run = await Actor.call(
                actor_id=self.youtube_scraper_id,
                run_input={
                    'startUrls': [{'url': channel_url}],
                    'maxResults': video_count,
                    'searchKeywords': '',
                }
            )
            
            # Get results
            dataset_id = run.get('defaultDatasetId')
            if not dataset_id:
                raise Exception("No dataset returned from YouTube scraper")
            
            Actor.log.info(f"Fetching results from dataset: {dataset_id}")
            dataset_items = await Actor.apify_client.dataset(dataset_id).list_items()
            
            if not dataset_items or not dataset_items.items:
                Actor.log.warning(f"No videos found for {channel_url}")
                return None
            
            videos = dataset_items.items
            Actor.log.info(f"Successfully fetched {len(videos)} videos")
            
            # Extract channel info from first video
            first_video = videos[0] if videos else {}
            
            return {
                'channel_name': first_video.get('channelName', 'Unknown'),
                'channel_id': first_video.get('channelId', self._extract_channel_id(channel_url)),
                'channel_url': channel_url,
                'videos': self._normalize_videos(videos),
                'video_ids': [v.get('id') for v in videos if v.get('id')]
            }
            
        except Exception as e:
            Actor.log.error(f"Error fetching channel data: {str(e)}")
            raise
    
    async def fetch_transcripts(self, video_ids: List[str]) -> List[Dict]:
        """Fetch transcripts for given video IDs"""
        
        if not video_ids:
            return []
        
        transcripts = []
        
        try:
            Actor.log.info(f"Fetching transcripts for {len(video_ids)} videos")
            
            # Process in batches to avoid timeouts
            batch_size = 10
            for i in range(0, len(video_ids), batch_size):
                batch = video_ids[i:i+batch_size]
                video_urls = [f"https://www.youtube.com/watch?v={vid}" for vid in batch]
                
                Actor.log.info(f"Processing batch {i//batch_size + 1}")
                
                run = await Actor.call(
                    actor_id=self.transcript_scraper_id,
                    run_input={
                        'startUrls': [{'url': url} for url in video_urls],
                        'language': 'en'
                    }
                )
                
                dataset_id = run.get('defaultDatasetId')
                if dataset_id:
                    dataset_items = await Actor.apify_client.dataset(dataset_id).list_items()
                    if dataset_items and dataset_items.items:
                        for item in dataset_items.items:
                            if item.get('transcript'):
                                transcripts.append({
                                    'video_id': item.get('videoId'),
                                    'transcript': item.get('transcript')
                                })
            
            Actor.log.info(f"Successfully fetched {len(transcripts)} transcripts")
            return transcripts
            
        except Exception as e:
            Actor.log.warning(f"Transcript fetching failed (non-critical): {str(e)}")
            return []  # Transcripts are optional - don't fail the whole run
    
    def _normalize_videos(self, videos: List[Dict]) -> List[Dict]:
        """Normalize video data from scraper"""
        normalized = []
        
        for video in videos:
            normalized.append({
                'id': video.get('id'),
                'title': video.get('title', ''),
                'views': self._parse_number(video.get('views', 0)),
                'likes': self._parse_number(video.get('likes', 0)),
                'comments': self._parse_number(video.get('comments', 0)),
                'duration': video.get('duration', ''),
                'published': video.get('date', ''),
                'url': f"https://www.youtube.com/watch?v={video.get('id')}"
            })
        
        return normalized
    
    def _parse_number(self, value) -> int:
        """Parse number from various formats (1.2M, 50K, etc.)"""
        if isinstance(value, int):
            return value
        
        if isinstance(value, str):
            value = value.replace(',', '').strip()
            
            multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
            
            for suffix, multiplier in multipliers.items():
                if suffix in value.upper():
                    try:
                        number = float(value.upper().replace(suffix, ''))
                        return int(number * multiplier)
                    except:
                        pass
            
            try:
                return int(float(value))
            except:
                return 0
        
        return 0
    
    def _extract_channel_id(self, url: str) -> str:
        """Extract channel ID from URL"""
        patterns = [
            r'youtube\.com/@([^/]+)',
            r'youtube\.com/c/([^/]+)',
            r'youtube\.com/channel/([^/]+)',
            r'youtube\.com/user/([^/]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return url.split('/')[-1] or 'unknown'