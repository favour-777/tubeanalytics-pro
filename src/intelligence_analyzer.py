# AI Intelligence Analyzer - The secret sauce
# This is what makes the actor VALUABLE

import os
import json
import re
from typing import Dict, List, Any
from collections import Counter
from datetime import datetime
import anthropic


class IntelligenceAnalyzer:
    """Analyzes YouTube data to extract actionable business intelligence"""
    
    def __init__(self, user_api_key: str = None):
        api_key = user_api_key or os.environ.get('ANTHROPIC_API_KEY')
        
        if not api_key:
            raise ValueError("Claude API key required")
        
        self.client = anthropic.Anthropic(api_key=api_key)
    
    async def analyze_channel(
        self,
        channel_data: Dict,
        transcripts: List[Dict],
        competitor_data: List[Dict],
        analysis_type: str
    ) -> Dict:
        """Run comprehensive channel intelligence analysis"""
        
        # Step 1: Statistical Analysis (fast, no AI)
        stats = self._compute_statistics(channel_data)
        
        # Step 2: Topic Extraction (AI-powered)
        topics = await self._extract_topics(channel_data, transcripts)
        
        # Step 3: Competitive Analysis (if competitors provided)
        gaps = []
        if competitor_data:
            gaps = await self._find_content_gaps(channel_data, competitor_data, topics)
        
        # Step 4: Keyword Opportunities (from transcripts)
        keywords = []
        if transcripts:
            keywords = await self._extract_keyword_opportunities(transcripts)
        
        # Step 5: Actionable Recommendations (AI synthesis)
        recommendations = await self._generate_recommendations(
            channel_data=channel_data,
            stats=stats,
            topics=topics,
            gaps=gaps,
            keywords=keywords,
            analysis_type=analysis_type
        )
        
        return {
            # Core Metrics
            'avg_views': stats['avg_views'],
            'avg_engagement_rate': stats['avg_engagement_rate'],
            'best_posting_day': stats['best_posting_day'],
            'best_posting_time': stats['best_posting_time'],
            
            # Intelligence
            'top_performing_topics': topics[:10],
            'content_gaps': gaps[:10],
            'keyword_opportunities': keywords[:15],
            
            # Insights
            'engagement_insights': {
                'peak_performance_range': stats['peak_performance_range'],
                'consistency_score': stats['consistency_score'],
                'growth_trend': stats['growth_trend']
            },
            
            # Actionable
            'actionable_recommendations': recommendations
        }
    
    def _compute_statistics(self, channel_data: Dict) -> Dict:
        """Compute statistical insights from video data"""
        
        videos = channel_data['videos']
        
        if not videos:
            return self._empty_stats()
        
        # Basic metrics
        views = [v['views'] for v in videos if v.get('views')]
        likes = [v['likes'] for v in videos if v.get('likes')]
        comments = [v['comments'] for v in videos if v.get('comments')]
        
        avg_views = sum(views) / len(views) if views else 0
        avg_likes = sum(likes) / len(likes) if likes else 0
        avg_comments = sum(comments) / len(comments) if comments else 0
        
        # Engagement rate
        engagement_rates = []
        for v in videos:
            if v.get('views', 0) > 0:
                engagement = ((v.get('likes', 0) + v.get('comments', 0)) / v['views']) * 100
                engagement_rates.append(engagement)
        
        avg_engagement = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0
        
        # Posting patterns
        publishing_days = []
        for v in videos:
            if v.get('published'):
                try:
                    # Parse date and get day of week
                    # Format varies, try different approaches
                    day = self._extract_day_of_week(v['published'])
                    if day:
                        publishing_days.append(day)
                except:
                    pass
        
        best_day = Counter(publishing_days).most_common(1)[0][0] if publishing_days else 'Tuesday'
        
        # Performance consistency
        if len(views) > 5:
            import numpy as np
            std_dev = np.std(views)
            consistency = 100 - min((std_dev / avg_views) * 100, 100) if avg_views > 0 else 0
        else:
            consistency = 50
        
        # Growth trend
        if len(views) >= 10:
            first_half = sum(views[:len(views)//2]) / (len(views)//2)
            second_half = sum(views[len(views)//2:]) / (len(views) - len(views)//2)
            growth = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
            
            if growth > 20:
                trend = "Strong Growth"
            elif growth > 0:
                trend = "Steady Growth"
            elif growth > -20:
                trend = "Stable"
            else:
                trend = "Declining"
        else:
            trend = "Insufficient Data"
        
        return {
            'avg_views': int(avg_views),
            'avg_likes': int(avg_likes),
            'avg_comments': int(avg_comments),
            'avg_engagement_rate': round(avg_engagement, 2),
            'best_posting_day': best_day,
            'best_posting_time': '10:00 AM EST',  # Most common optimal time
            'peak_performance_range': f"{int(avg_views * 0.8):,} - {int(avg_views * 1.5):,} views",
            'consistency_score': round(consistency, 1),
            'growth_trend': trend
        }
    
    async def _extract_topics(self, channel_data: Dict, transcripts: List[Dict]) -> List[Dict]:
        """Extract and rank topics using AI"""
        
        videos = channel_data['videos'][:20]  # Top 20 for analysis
        
        # Prepare data for Claude
        video_titles = [v['title'] for v in videos if v.get('title')]
        video_performance = {v['title']: v['views'] for v in videos if v.get('title') and v.get('views')}
        
        system = "You are an expert YouTube content strategist who identifies trending topics and content patterns."
        
        prompt = f"""Analyze these YouTube video titles and their view counts to identify top-performing content topics.

Video Titles and Performance:
{json.dumps([{'title': t, 'views': video_performance[t]} for t in video_titles[:15]], indent=2)}

TASK:
1. Identify the 8-10 main content topics/themes
2. Calculate average views for each topic
3. Assess the opportunity level (high/medium/low)
4. Provide specific examples

Return ONLY valid JSON:
{{
  "topics": [
    {{
      "topic": "Specific topic name",
      "avgViews": 1500000,
      "videoCount": 5,
      "opportunity": "high|medium|low",
      "examples": ["Example video title 1", "Example 2"],
      "insight": "Why this topic performs well (1 sentence)"
    }}
  ]
}}

Focus on ACTIONABLE topic categories that a creator can replicate."""
        
        try:
            response = self._call_claude(system, prompt, max_tokens=3000)
            data = self._parse_json(response)
            return sorted(data.get('topics', []), key=lambda x: x.get('avgViews', 0), reverse=True)
        except Exception as e:
            print(f"Topic extraction error: {e}")
            return self._fallback_topics(videos)
    
    async def _find_content_gaps(
        self,
        channel_data: Dict,
        competitor_data: List[Dict],
        channel_topics: List[Dict]
    ) -> List[Dict]:
        """Find content gaps vs competitors using AI"""
        
        channel_topics_str = ", ".join([t['topic'] for t in channel_topics[:10]])
        
        competitor_summaries = []
        for comp in competitor_data[:3]:  # Top 3 competitors
            comp_titles = [v['title'] for v in comp['videos'][:15] if v.get('title')]
            comp_avg_views = sum(v['views'] for v in comp['videos'] if v.get('views')) / len(comp['videos'])
            
            competitor_summaries.append({
                'name': comp['channel_name'],
                'avgViews': int(comp_avg_views),
                'titles': comp_titles[:10]
            })
        
        system = "You are an expert at competitive YouTube content analysis."
        
        prompt = f"""Identify content gaps - topics competitors cover successfully that the main channel doesn't.

Main Channel Topics: {channel_topics_str}

Competitor Channels:
{json.dumps(competitor_summaries, indent=2)}

TASK:
Find 5-8 content gaps where competitors are succeeding but the main channel has no coverage.

Return ONLY valid JSON:
{{
  "gaps": [
    {{
      "gap": "Specific content type/topic",
      "competitorAvgViews": 1200000,
      "competitorExample": "Example video title",
      "opportunity": "Why this is a good opportunity (1 sentence)",
      "recommended_approach": "How to tackle this topic (1 sentence)"
    }}
  ]
}}"""
        
        try:
            response = self._call_claude(system, prompt, max_tokens=2500)
            data = self._parse_json(response)
            return data.get('gaps', [])
        except Exception as e:
            print(f"Gap analysis error: {e}")
            return []
    
    async def _extract_keyword_opportunities(self, transcripts: List[Dict]) -> List[Dict]:
        """Extract SEO keyword opportunities from transcripts"""
        
        if not transcripts:
            return []
        
        # Combine transcripts (sample to stay within limits)
        combined_text = " ".join([t['transcript'][:3000] for t in transcripts[:5]])
        
        system = "You are an expert YouTube SEO strategist."
        
        prompt = f"""Analyze these video transcripts and identify high-value keyword opportunities for YouTube SEO.

Transcript Sample:
{combined_text[:8000]}

TASK:
Find 10-15 keyword opportunities that:
1. Appear naturally in successful content
2. Have search potential
3. Are specific and actionable

Return ONLY valid JSON:
{{
  "keywords": [
    {{
      "keyword": "specific phrase",
      "searchIntent": "What viewers want",
      "competition": "low|medium|high",
      "opportunity": "Why use this keyword (1 sentence)"
    }}
  ]
}}"""
        
        try:
            response = self._call_claude(system, prompt, max_tokens=2000)
            data = self._parse_json(response)
            return data.get('keywords', [])
        except Exception as e:
            print(f"Keyword extraction error: {e}")
            return []
    
    async def _generate_recommendations(
        self,
        channel_data: Dict,
        stats: Dict,
        topics: List[Dict],
        gaps: List[Dict],
        keywords: List[Dict],
        analysis_type: str
    ) -> List[str]:
        """Generate actionable recommendations"""
        
        context = {
            'channelName': channel_data['channel_name'],
            'avgViews': stats['avg_views'],
            'topTopic': topics[0]['topic'] if topics else 'Unknown',
            'bestDay': stats['best_posting_day'],
            'growthTrend': stats['growth_trend'],
            'topGap': gaps[0] if gaps else None,
            'topKeyword': keywords[0] if keywords else None
        }
        
        system = "You are a YouTube growth consultant providing specific, actionable advice."
        
        prompt = f"""Based on this channel analysis, provide 5-7 specific, actionable recommendations.

Channel: {context['channelName']}
Current Performance: {context['avgViews']:,} avg views
Top Topic: {context['topTopic']}
Growth Trend: {context['growthTrend']}
Best Posting Day: {context['bestDay']}

{f"Biggest Content Gap: {context['topGap']['gap']}" if context['topGap'] else ""}
{f"Top Keyword Opportunity: {context['topKeyword']['keyword']}" if context['topKeyword'] else ""}

Analysis Focus: {analysis_type}

Provide SPECIFIC recommendations like:
- "Post '{context['topTopic']}' content on {context['bestDay']}s at 10 AM for 40% higher engagement"
- NOT vague advice like "post consistently"

Return ONLY valid JSON:
{{
  "recommendations": [
    "Specific actionable recommendation 1",
    "Specific actionable recommendation 2"
  ]
}}"""
        
        try:
            response = self._call_claude(system, prompt, max_tokens=1500)
            data = self._parse_json(response)
            return data.get('recommendations', [])[:7]
        except Exception as e:
            print(f"Recommendations error: {e}")
            return self._fallback_recommendations(context)
    
    def _call_claude(self, system: str, prompt: str, max_tokens: int = 2000) -> str:
        """Call Claude API"""
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    
    def _parse_json(self, text: str) -> Dict:
        """Parse JSON from Claude response"""
        text = text.strip()
        text = re.sub(r'^```json\n?', '', text)
        text = re.sub(r'^```\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
        
        try:
            return json.loads(text)
        except:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {}
    
    def _extract_day_of_week(self, date_str: str) -> str:
        """Extract day of week from various date formats"""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day in days:
            if day.lower() in date_str.lower():
                return day
        
        return 'Tuesday'  # Default fallback
    
    def _empty_stats(self) -> Dict:
        """Return empty stats structure"""
        return {
            'avg_views': 0,
            'avg_likes': 0,
            'avg_comments': 0,
            'avg_engagement_rate': 0,
            'best_posting_day': 'Tuesday',
            'best_posting_time': '10:00 AM EST',
            'peak_performance_range': 'N/A',
            'consistency_score': 0,
            'growth_trend': 'Insufficient Data'
        }
    
    def _fallback_topics(self, videos: List[Dict]) -> List[Dict]:
        """Simple topic extraction fallback"""
        word_counts = Counter()
        
        for v in videos:
            title = v.get('title', '').lower()
            words = title.split()
            for word in words:
                if len(word) > 4:
                    word_counts[word] += 1
        
        topics = []
        for word, count in word_counts.most_common(5):
            topics.append({
                'topic': word.title(),
                'avgViews': sum(v['views'] for v in videos) // len(videos),
                'videoCount': count,
                'opportunity': 'medium',
                'insight': f"Appears in {count} video titles"
            })
        
        return topics
    
    def _fallback_recommendations(self, context: Dict) -> List[str]:
        """Generate basic recommendations as fallback"""
        return [
            f"Focus on your top-performing topic: {context['topTopic']}",
            f"Post consistently on {context['bestDay']}s for best engagement",
            f"Target {int(context['avgViews'] * 1.2):,} views per video (20% growth)",
            "Optimize thumbnails for your top-performing content style",
            "Analyze competitor content in your niche for new ideas"
        ]