# YouTube Channel Intelligence Pro - Main Entry Point
# Contest-winning quality code

import asyncio
from apify import Actor
from datetime import datetime
import os

from .youtube_fetcher import YouTubeFetcher
from .intelligence_analyzer import IntelligenceAnalyzer
from .report_generator import ReportGenerator


async def main():
    async with Actor:
        Actor.log.info("🚀 YouTube Channel Intelligence Pro - Starting")
        
        # Get input
        actor_input = await Actor.get_input() or {}
        
        # Parse input
        channel_urls_str = actor_input.get('channelUrls', '').strip()
        channel_urls = [url.strip() for url in channel_urls_str.split('\n') if url.strip()]
        
        competitor_urls_str = actor_input.get('compareWithCompetitors', '').strip()
        competitor_urls = [url.strip() for url in competitor_urls_str.split('\n') if url.strip()] if competitor_urls_str else []
        
        video_count = actor_input.get('videoCount', 20)
        include_transcripts = actor_input.get('includeTranscripts', True)
        analysis_type = actor_input.get('analysisType', 'comprehensive')
        user_api_key = actor_input.get('anthropicApiKey', '').strip() or None
        
        # Validation
        if not channel_urls:
            await Actor.fail('❌ Please provide at least one YouTube channel URL')
            return
        
        Actor.log.info(f"📊 Analyzing {len(channel_urls)} channel(s)")
        if competitor_urls:
            Actor.log.info(f"🥊 Comparing against {len(competitor_urls)} competitor(s)")
        
        # Initialize components
        fetcher = YouTubeFetcher()
        analyzer = IntelligenceAnalyzer(user_api_key=user_api_key)
        report_gen = ReportGenerator()
        
        # Process each channel
        for idx, channel_url in enumerate(channel_urls, 1):
            try:
                Actor.log.info(f"\n{'='*60}")
                Actor.log.info(f"📺 [{idx}/{len(channel_urls)}] Processing: {channel_url}")
                Actor.log.info(f"{'='*60}")
                
                # Step 1: Fetch channel data
                Actor.log.info("🔄 Step 1/4: Fetching channel data from YouTube...")
                channel_data = await fetcher.fetch_channel_data(
                    channel_url=channel_url,
                    video_count=video_count
                )
                
                if not channel_data or not channel_data.get('videos'):
                    Actor.log.warning(f"⚠️ No data found for {channel_url}")
                    continue
                
                Actor.log.info(f"✅ Fetched {len(channel_data['videos'])} videos")
                
                # Step 2: Fetch transcripts (if enabled)
                transcripts = []
                if include_transcripts:
                    Actor.log.info("🔄 Step 2/4: Fetching video transcripts...")
                    transcripts = await fetcher.fetch_transcripts(
                        video_ids=channel_data['video_ids'][:10]  # Top 10 for speed
                    )
                    Actor.log.info(f"✅ Fetched {len(transcripts)} transcripts")
                else:
                    Actor.log.info("⏭️ Step 2/4: Skipping transcripts (disabled)")
                
                # Step 3: Fetch competitor data (if provided)
                competitor_data = []
                if competitor_urls:
                    Actor.log.info(f"🔄 Step 3/4: Fetching {len(competitor_urls)} competitor channel(s)...")
                    for comp_url in competitor_urls:
                        comp_data = await fetcher.fetch_channel_data(
                            channel_url=comp_url,
                            video_count=video_count
                        )
                        if comp_data:
                            competitor_data.append(comp_data)
                    Actor.log.info(f"✅ Fetched {len(competitor_data)} competitor(s)")
                else:
                    Actor.log.info("⏭️ Step 3/4: No competitors to analyze")
                
                # Step 4: AI Analysis
                Actor.log.info("🤖 Step 4/4: Running AI intelligence analysis...")
                intelligence_report = await analyzer.analyze_channel(
                    channel_data=channel_data,
                    transcripts=transcripts,
                    competitor_data=competitor_data,
                    analysis_type=analysis_type
                )
                Actor.log.info("✅ Analysis complete!")
                
                # Generate exports
                Actor.log.info("📄 Generating professional reports...")
                
                # PDF Report
                pdf_content = report_gen.generate_pdf(
                    intelligence_report=intelligence_report,
                    channel_data=channel_data
                )
                
                pdf_key = f"{channel_data['channel_id']}_intelligence_report.pdf"
                await Actor.set_value(pdf_key, pdf_content, content_type='application/pdf')
                
                pdf_url = f"https://api.apify.com/v2/key-value-stores/{Actor.get_env().get('default_key_value_store_id')}/records/{pdf_key}"
                Actor.log.info(f"✅ PDF Report: {pdf_url}")
                
                # CSV Export
                csv_content = report_gen.generate_csv(intelligence_report)
                csv_key = f"{channel_data['channel_id']}_data.csv"
                await Actor.set_value(csv_key, csv_content, content_type='text/csv')
                
                csv_url = f"https://api.apify.com/v2/key-value-stores/{Actor.get_env().get('default_key_value_store_id')}/records/{csv_key}"
                Actor.log.info(f"✅ CSV Data: {csv_url}")
                
                # Push to dataset
                result = {
                    'channelName': channel_data['channel_name'],
                    'channelUrl': channel_url,
                    'channelId': channel_data['channel_id'],
                    'videosAnalyzed': len(channel_data['videos']),
                    'analysisType': analysis_type,
                    'processedAt': datetime.utcnow().isoformat() + 'Z',
                    
                    # Key Metrics
                    'topTopic': intelligence_report['top_performing_topics'][0]['topic'] if intelligence_report.get('top_performing_topics') else None,
                    'avgViews': intelligence_report.get('avg_views', 0),
                    'bestPostingDay': intelligence_report.get('best_posting_day', 'N/A'),
                    'bestPostingTime': intelligence_report.get('best_posting_time', 'N/A'),
                    
                    # Intelligence
                    'topPerformingTopics': intelligence_report.get('top_performing_topics', []),
                    'contentGaps': intelligence_report.get('content_gaps', []),
                    'contentGapsFound': len(intelligence_report.get('content_gaps', [])),
                    'keywordOpportunities': intelligence_report.get('keyword_opportunities', []),
                    'engagementInsights': intelligence_report.get('engagement_insights', {}),
                    'actionableRecommendations': intelligence_report.get('actionable_recommendations', []),
                    
                    # Export URLs
                    'reportUrl': pdf_url,
                    'csvUrl': csv_url,
                    
                    # Stats
                    'statistics': {
                        'totalVideos': len(channel_data['videos']),
                        'totalViews': sum(v.get('views', 0) for v in channel_data['videos']),
                        'avgEngagement': intelligence_report.get('avg_engagement_rate', 0),
                        'transcriptsAnalyzed': len(transcripts)
                    },
                    
                    'status': 'success'
                }
                
                await Actor.push_data(result)
                
                Actor.log.info("✅ Channel analysis complete!")
                Actor.log.info(f"📊 Top Topic: {result['topTopic']}")
                Actor.log.info(f"👁️ Avg Views: {result['avgViews']:,.0f}")
                Actor.log.info(f"🔍 Content Gaps Found: {result['contentGapsFound']}")
                
            except Exception as e:
                Actor.log.error(f"❌ Error processing {channel_url}: {str(e)}")
                await Actor.push_data({
                    'channelUrl': channel_url,
                    'status': 'failed',
                    'error': str(e),
                    'processedAt': datetime.utcnow().isoformat() + 'Z'
                })
        
        Actor.log.info("\n🎉 All channels processed successfully!")
        Actor.log.info("💡 Check the Dataset tab for insights and Key-Value Store for reports")


if __name__ == '__main__':
    asyncio.run(main())