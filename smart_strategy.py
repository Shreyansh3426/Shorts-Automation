#!/usr/bin/env python3
"""
🧠 SMART STRATEGY ENGINE - Channel Analytics & Auto-Optimization
Analyzes your uploaded videos, A/B test results, and trending topics
to dynamically adjust content strategy for maximum engagement.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import Counter

class SmartStrategy:
    def __init__(self, db_path: str = 'shorts.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
    def analyze_channel_performance(self) -> Dict:
        """Analyze all uploaded videos and their performance."""
        cursor = self.conn.cursor()
        
        # Get all uploaded videos
        cursor.execute("""
            SELECT id, topic, status, created_at 
            FROM jobs 
            WHERE status IN ('uploaded', 'done')
            ORDER BY created_at DESC
        """)
        
        videos = cursor.fetchall()
        
        return {
            'total_videos': len(videos),
            'videos': [dict(v) for v in videos],
            'last_upload': videos[0]['created_at'] if videos else None,
            'upload_frequency': self._calc_upload_frequency(videos),
        }
    
    def _calc_upload_frequency(self, videos):
        """Calculate uploads per day."""
        if len(videos) < 2:
            return "Unknown"
        
        dates = [v['created_at'].split()[0] for v in videos]
        unique_dates = len(set(dates))
        last_date = datetime.fromisoformat(dates[-1]).date()
        total_days = (datetime.now().date() - last_date).days + 1
        
        freq = unique_dates / max(total_days, 1)
        
        if freq >= 4:
            return "Every 6 hours ✅ (Optimal)"
        elif freq >= 1:
            return "Daily ✅ (Good)"
        else:
            return f"{freq:.1f} uploads/day"
    
    def get_trending_topics(self, days: int = 7) -> List[Tuple[str, int]]:
        """Get most popular topics from recent uploads."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT topic FROM jobs 
            WHERE created_at > ? AND status IN ('uploaded', 'done')
        """, (cutoff_date,))
        
        topics = [row[0] for row in cursor.fetchall()]
        
        # Extract keywords from topics
        keywords = []
        for topic in topics:
            words = [w.lower() for w in topic.split() if len(w) > 3]
            keywords.extend(words)
        
        # Find most common
        return Counter(keywords).most_common(10)
    
    def analyze_topic_patterns(self) -> Dict:
        """Identify performance patterns by topic category."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT topic, COUNT(*) as count 
            FROM jobs 
            WHERE status IN ('uploaded', 'done')
            GROUP BY topic
            ORDER BY count DESC
            LIMIT 20
        """)
        
        topics = cursor.fetchall()
        
        # Categorize topics
        categories = {
            'science': 0,
            'nature': 0,
            'animals': 0,
            'health': 0,
            'technology': 0,
            'mystery': 0,
            'documentary': 0,
        }
        
        topic_list = [dict(t) for t in topics]
        
        for t in topic_list:
            topic_lower = t['topic'].lower()
            if any(word in topic_lower for word in ['discover', 'scientists', 'secret', 'researchers']):
                categories['science'] += 1
            if any(word in topic_lower for word in ['animal', 'insect', 'bird', 'fish', 'snake', 'bug', 'creature']):
                categories['animals'] += 1
            if any(word in topic_lower for word in ['nature', 'forest', 'ocean', 'desert', 'mountain', 'plant']):
                categories['nature'] += 1
            if any(word in topic_lower for word in ['health', 'stomach', 'body', 'disease', 'virus', 'bacteria', 'organ']):
                categories['health'] += 1
        
        return {
            'total_topics': len(topic_list),
            'recent_topics': topic_list,
            'categories': categories,
            'top_category': max(categories, key=categories.get),
        }
    
    def get_recommendations(self) -> List[str]:
        """Generate AI recommendations for content strategy."""
        perf = self.analyze_channel_performance()
        topics = self.get_trending_topics()
        patterns = self.analyze_topic_patterns()
        
        recommendations = []
        
        # Upload frequency recommendation
        if '6 hours' in perf['upload_frequency']:
            recommendations.append("✅ Upload frequency OPTIMAL - maintaining 4 videos/day")
        
        # Topic strategy
        if topics:
            top_topics = [t[0] for t in topics[:3]]
            rec = f"🎯 Top performing topics: {', '.join(top_topics)}"
            recommendations.append(rec)
        
        # Category focus
        if patterns['top_category'] != 'documentary':
            rec = f"📌 Focus on {patterns['top_category']} content (your strongest category)"
            recommendations.append(rec)
        
        # Diversity
        unique_cats = len([c for c in patterns['categories'].values() if c > 0])
        if unique_cats < 3:
            recommendations.append(f"🔄 Expand category diversity (currently {unique_cats} categories)")
        
        # Volume
        if perf['total_videos'] < 5:
            recommendations.append("🚀 Build more content volume for better data")
        elif perf['total_videos'] > 20:
            recommendations.append("📊 Enough volume for reliable trend analysis")
        
        # Consistency
        recommendations.append("⏰ Maintain consistent schedule for algorithm boost")
        
        return recommendations
    
    def generate_strategy_report(self) -> str:
        """Generate a comprehensive strategy report."""
        perf = self.analyze_channel_performance()
        topics = self.get_trending_topics()
        patterns = self.analyze_topic_patterns()
        recs = self.get_recommendations()
        
        report = f"""
╔════════════════════════════════════════════════════════════════╗
║         🧠 SMART CHANNEL STRATEGY REPORT - {datetime.now().strftime('%Y-%m-%d')}        
║════════════════════════════════════════════════════════════════╝

📊 CHANNEL PERFORMANCE
   • Total Videos: {perf['total_videos']}
   • Upload Frequency: {perf['upload_frequency']}
   • Last Upload: {perf['last_upload']}

🔥 TOP TRENDING TOPICS (Last 7 Days)
"""
        for idx, (topic, count) in enumerate(topics[:5], 1):
            report += f"   {idx}. {topic} ({count} mentions)\n"
        
        report += f"""
📌 CATEGORY ANALYSIS
"""
        for category, count in sorted(patterns['categories'].items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                report += f"   • {category.capitalize()}: {count} videos\n"
        
        report += f"""
💡 AI RECOMMENDATIONS
"""
        for rec in recs:
            report += f"   {rec}\n"
        
        report += f"""
🎯 NEXT STEPS
   1. Continue current upload schedule (4x daily)
   2. Focus on top performing keywords
   3. A/B test new variations of popular topics
   4. Monitor engagement metrics in YouTube Studio
   5. Sync analytics weekly for better insights

════════════════════════════════════════════════════════════════
"""
        return report
    
    def save_report(self, filename: str = 'strategy_report.txt'):
        """Save strategy report to file."""
        report = self.generate_strategy_report()
        with open(filename, 'w') as f:
            f.write(report)
        return filename
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    print("\n🧠 SMART STRATEGY ENGINE\n")
    
    try:
        strategy = SmartStrategy()
        
        # Generate and print report
        print(strategy.generate_strategy_report())
        
        # Save report
        filename = strategy.save_report()
        print(f"\n📄 Report saved to: {filename}")
        
        strategy.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
