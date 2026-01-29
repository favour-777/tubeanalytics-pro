# Report Generator - Beautiful, professional outputs
# PDF + CSV exports

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from io import BytesIO
import csv
from typing import Dict, List


class ReportGenerator:
    """Generate professional PDF and CSV reports"""
    
    def generate_pdf(self, intelligence_report: Dict, channel_data: Dict) -> bytes:
        """Generate beautiful PDF report"""
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=30
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#FF0000'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#282828'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        )
        
        subheading_style = ParagraphStyle(
            'SubHeading',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#606060'),
            spaceAfter=8,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )
        
        # Title
        story.append(Paragraph(f"YouTube Channel Intelligence Report", title_style))
        story.append(Paragraph(f"{self._escape(channel_data['channel_name'])}", heading_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Executive Summary Box
        summary_data = [
            ['Metric', 'Value'],
            ['Average Views', f"{intelligence_report['avg_views']:,}"],
            ['Engagement Rate', f"{intelligence_report['avg_engagement_rate']:.2f}%"],
            ['Best Posting Day', intelligence_report['best_posting_day']],
            ['Growth Trend', intelligence_report['engagement_insights']['growth_trend']]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF0000')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')])
        ]))
        
        story.append(Paragraph("Executive Summary", heading_style))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Top Performing Topics
        if intelligence_report.get('top_performing_topics'):
            story.append(Paragraph("Top Performing Content Topics", heading_style))
            
            for i, topic in enumerate(intelligence_report['top_performing_topics'][:5], 1):
                story.append(Paragraph(f"<b>{i}. {self._escape(topic['topic'])}</b>", subheading_style))
                story.append(Paragraph(
                    f"Average Views: <b>{topic.get('avgViews', 0):,}</b> | "
                    f"Opportunity: <b>{topic.get('opportunity', 'N/A').upper()}</b>",
                    styles['Normal']
                ))
                story.append(Paragraph(
                    f"<i>{self._escape(topic.get('insight', 'High-performing content category'))}</i>",
                    styles['Normal']
                ))
                story.append(Spacer(1, 0.1*inch))
            
            story.append(Spacer(1, 0.2*inch))
        
        # Content Gaps
        if intelligence_report.get('content_gaps'):
            story.append(Paragraph("Content Gap Opportunities", heading_style))
            story.append(Paragraph(
                "These are topics your competitors are succeeding with that you haven't covered:",
                styles['Normal']
            ))
            story.append(Spacer(1, 0.1*inch))
            
            for i, gap in enumerate(intelligence_report['content_gaps'][:5], 1):
                story.append(Paragraph(f"<b>{i}. {self._escape(gap['gap'])}</b>", subheading_style))
                story.append(Paragraph(
                    f"Competitor Avg Views: <b>{gap.get('competitorAvgViews', 0):,}</b>",
                    styles['Normal']
                ))
                story.append(Paragraph(
                    f"<i>{self._escape(gap.get('opportunity', 'Untapped opportunity'))}</i>",
                    styles['Normal']
                ))
                story.append(Spacer(1, 0.1*inch))
            
            story.append(Spacer(1, 0.2*inch))
        
        # Keyword Opportunities
        if intelligence_report.get('keyword_opportunities'):
            story.append(PageBreak())
            story.append(Paragraph("SEO Keyword Opportunities", heading_style))
            
            kw_data = [['Keyword', 'Search Intent', 'Competition']]
            for kw in intelligence_report['keyword_opportunities'][:10]:
                kw_data.append([
                    self._escape(kw.get('keyword', '')),
                    self._escape(kw.get('searchIntent', '')[:40]),
                    kw.get('competition', 'N/A').upper()
                ])
            
            kw_table = Table(kw_data, colWidths=[2*inch, 3*inch, 1.5*inch])
            kw_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF0000')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')])
            ]))
            
            story.append(kw_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Actionable Recommendations
        if intelligence_report.get('actionable_recommendations'):
            story.append(Paragraph("Actionable Recommendations", heading_style))
            story.append(Paragraph(
                "Specific actions to grow your channel:",
                styles['Normal']
            ))
            story.append(Spacer(1, 0.1*inch))
            
            for i, rec in enumerate(intelligence_report['actionable_recommendations'], 1):
                story.append(Paragraph(
                    f"<b>{i}.</b> {self._escape(rec)}",
                    styles['Normal']
                ))
                story.append(Spacer(1, 0.08*inch))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#888888'),
            alignment=TA_CENTER
        )
        story.append(Paragraph(
            "Generated by YouTube Channel Intelligence Pro | Powered by AI",
            footer_style
        ))
        
        # Build PDF
        doc.build(story)
        return buffer.getvalue()
    
    def generate_csv(self, intelligence_report: Dict) -> str:
        """Generate CSV export of all data"""
        
        output = BytesIO()
        output.write(b'\xef\xbb\xbf')  # UTF-8 BOM
        
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        
        # Header
        writer.writerow(['YouTube Channel Intelligence Report'])
        writer.writerow([])
        
        # Summary Metrics
        writer.writerow(['SUMMARY METRICS'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Average Views', intelligence_report['avg_views']])
        writer.writerow(['Engagement Rate', f"{intelligence_report['avg_engagement_rate']}%"])
        writer.writerow(['Best Posting Day', intelligence_report['best_posting_day']])
        writer.writerow(['Growth Trend', intelligence_report['engagement_insights']['growth_trend']])
        writer.writerow([])
        
        # Top Topics
        writer.writerow(['TOP PERFORMING TOPICS'])
        writer.writerow(['Topic', 'Avg Views', 'Video Count', 'Opportunity', 'Insight'])
        for topic in intelligence_report.get('top_performing_topics', []):
            writer.writerow([
                topic.get('topic', ''),
                topic.get('avgViews', 0),
                topic.get('videoCount', 0),
                topic.get('opportunity', ''),
                topic.get('insight', '')
            ])
        writer.writerow([])
        
        # Content Gaps
        if intelligence_report.get('content_gaps'):
            writer.writerow(['CONTENT GAP OPPORTUNITIES'])
            writer.writerow(['Gap', 'Competitor Avg Views', 'Opportunity', 'Recommended Approach'])
            for gap in intelligence_report['content_gaps']:
                writer.writerow([
                    gap.get('gap', ''),
                    gap.get('competitorAvgViews', 0),
                    gap.get('opportunity', ''),
                    gap.get('recommended_approach', '')
                ])
            writer.writerow([])
        
        # Keywords
        if intelligence_report.get('keyword_opportunities'):
            writer.writerow(['KEYWORD OPPORTUNITIES'])
            writer.writerow(['Keyword', 'Search Intent', 'Competition', 'Opportunity'])
            for kw in intelligence_report['keyword_opportunities']:
                writer.writerow([
                    kw.get('keyword', ''),
                    kw.get('searchIntent', ''),
                    kw.get('competition', ''),
                    kw.get('opportunity', '')
                ])
            writer.writerow([])
        
        # Recommendations
        if intelligence_report.get('actionable_recommendations'):
            writer.writerow(['ACTIONABLE RECOMMENDATIONS'])
            for i, rec in enumerate(intelligence_report['actionable_recommendations'], 1):
                writer.writerow([f"{i}. {rec}"])
        
        return output.getvalue().decode('utf-8')
    
    def _escape(self, text: str) -> str:
        """Escape special characters for PDF"""
        if not text:
            return ""
        text = str(text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text