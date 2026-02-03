"""Analytics service for post statistics"""
import io
from typing import List, Dict
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
from telegram import Bot
from loguru import logger

from src.database.models import Post


class AnalyticsService:
    """Service for generating post analytics and visualizations"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def get_post_statistics(self, posts: List[Post], use_real_data: bool = True) -> List[Dict]:
        """
        Get statistics for published posts

        Args:
            posts: List of published posts
            use_real_data: If True, use stored stats from DB; if False, fetch from Telegram

        Returns:
            List of dictionaries with post statistics
        """
        statistics = []

        if use_real_data:
            # Use data stored in database
            for post in posts:
                stats = {
                    'post_id': post.id,
                    'message_id': post.message_id,
                    'published_at': post.published_at,
                    'content_preview': post.content[:50] + '...' if len(post.content) > 50 else post.content,
                    'views': post.views_count or 0,
                    'reactions': post.reactions_count or 0,
                    'forwards': post.forwards_count or 0,
                }
                statistics.append(stats)
        else:
            # Fetch fresh data from Telegram
            from src.services.telegram_stats_service import TelegramStatsService
            stats_service = TelegramStatsService(self.bot)

            for post in posts:
                if not post.channel_id or not post.message_id:
                    continue

                try:
                    telegram_stats = await stats_service.get_post_statistics(
                        post.channel_id,
                        post.message_id
                    )

                    stats = {
                        'post_id': post.id,
                        'message_id': post.message_id,
                        'published_at': post.published_at,
                        'content_preview': post.content[:50] + '...' if len(post.content) > 50 else post.content,
                        'views': telegram_stats.get('views', 0) if telegram_stats else 0,
                        'reactions': telegram_stats.get('reactions', 0) if telegram_stats else 0,
                        'forwards': telegram_stats.get('forwards', 0) if telegram_stats else 0,
                    }

                    statistics.append(stats)

                except Exception as e:
                    logger.error(f"Error getting stats for post {post.id}: {e}")
                    # Add post with zero stats if error
                    statistics.append({
                        'post_id': post.id,
                        'message_id': post.message_id,
                        'published_at': post.published_at,
                        'content_preview': post.content[:50] + '...' if len(post.content) > 50 else post.content,
                        'views': 0,
                        'reactions': 0,
                        'forwards': 0,
                    })

        return statistics

    async def get_mock_statistics(self, posts: List[Post]) -> List[Dict]:
        """
        Generate mock statistics for demonstration
        This simulates real analytics data

        Args:
            posts: List of published posts

        Returns:
            List of dictionaries with mock post statistics
        """
        import random

        statistics = []

        for i, post in enumerate(posts):
            # Generate realistic mock data
            base_views = 1000 - (i * 150)  # Newer posts have more views

            stats = {
                'post_id': post.id,
                'message_id': post.message_id,
                'published_at': post.published_at,
                'content_preview': post.content[:50] + '...' if len(post.content) > 50 else post.content,
                'views': max(100, base_views + random.randint(-200, 200)),
                'reactions': max(10, (base_views // 50) + random.randint(-10, 20)),
                'forwards': max(5, (base_views // 100) + random.randint(-3, 10)),
            }

            statistics.append(stats)

        return statistics

    def generate_analytics_chart(self, statistics: List[Dict]) -> io.BytesIO:
        """
        Generate a beautiful chart from post statistics

        Args:
            statistics: List of post statistics

        Returns:
            BytesIO object containing the chart image
        """
        if not statistics:
            # Create empty chart
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'Нет данных для отображения',
                   ha='center', va='center', fontsize=16)
            ax.axis('off')
        else:
            # Set up figure with Russian font support
            plt.rcParams['font.family'] = 'DejaVu Sans'

            # Create figure with subplots
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            fig.suptitle('📊 Аналитика последних 5 постов', fontsize=18, fontweight='bold')

            # Prepare data
            post_labels = [f"#{i+1}" for i in range(len(statistics))]
            views = [s['views'] for s in statistics]
            reactions = [s['reactions'] for s in statistics]
            forwards = [s['forwards'] for s in statistics]

            # 1. Bar chart - Views
            ax1 = axes[0, 0]
            bars1 = ax1.bar(post_labels, views, color='#3498db', alpha=0.8, edgecolor='black')
            ax1.set_title('👁️ Просмотры', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Количество', fontsize=11)
            ax1.set_xlabel('Посты', fontsize=11)
            ax1.grid(axis='y', alpha=0.3, linestyle='--')

            # Add value labels on bars
            for bar in bars1:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom', fontsize=10)

            # 2. Bar chart - Reactions
            ax2 = axes[0, 1]
            bars2 = ax2.bar(post_labels, reactions, color='#e74c3c', alpha=0.8, edgecolor='black')
            ax2.set_title('❤️ Реакции', fontsize=14, fontweight='bold')
            ax2.set_ylabel('Количество', fontsize=11)
            ax2.set_xlabel('Посты', fontsize=11)
            ax2.grid(axis='y', alpha=0.3, linestyle='--')

            for bar in bars2:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom', fontsize=10)

            # 3. Bar chart - Forwards
            ax3 = axes[1, 0]
            bars3 = ax3.bar(post_labels, forwards, color='#2ecc71', alpha=0.8, edgecolor='black')
            ax3.set_title('🔄 Пересылки', fontsize=14, fontweight='bold')
            ax3.set_ylabel('Количество', fontsize=11)
            ax3.set_xlabel('Посты', fontsize=11)
            ax3.grid(axis='y', alpha=0.3, linestyle='--')

            for bar in bars3:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom', fontsize=10)

            # 4. Summary table
            ax4 = axes[1, 1]
            ax4.axis('tight')
            ax4.axis('off')

            # Create table data
            table_data = [
                ['Метрика', 'Всего', 'Среднее'],
                ['👁️ Просмотры', f'{sum(views):,}', f'{sum(views)//len(views):,}'],
                ['❤️ Реакции', f'{sum(reactions):,}', f'{sum(reactions)//len(reactions):,}'],
                ['🔄 Пересылки', f'{sum(forwards):,}', f'{sum(forwards)//len(forwards):,}'],
            ]

            table = ax4.table(cellText=table_data, cellLoc='center', loc='center',
                            colWidths=[0.4, 0.3, 0.3])
            table.auto_set_font_size(False)
            table.set_fontsize(11)
            table.scale(1, 2)

            # Style header row
            for i in range(3):
                table[(0, i)].set_facecolor('#34495e')
                table[(0, i)].set_text_props(weight='bold', color='white')

            # Style data rows
            for i in range(1, 4):
                for j in range(3):
                    table[(i, j)].set_facecolor('#ecf0f1' if i % 2 == 0 else 'white')

            ax4.set_title('📈 Общая статистика', fontsize=14, fontweight='bold', pad=20)

            plt.tight_layout()

        # Save to BytesIO
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        buf.seek(0)
        plt.close(fig)

        return buf

    def generate_text_analytics(self, statistics: List[Dict]) -> str:
        """
        Generate text summary of analytics

        Args:
            statistics: List of post statistics

        Returns:
            Formatted text summary
        """
        if not statistics:
            return "📊 **Аналитика постов**\n\n❌ Нет данных для отображения."

        total_views = sum(s['views'] for s in statistics)
        total_reactions = sum(s['reactions'] for s in statistics)
        total_forwards = sum(s['forwards'] for s in statistics)

        avg_views = total_views // len(statistics)
        avg_reactions = total_reactions // len(statistics)
        avg_forwards = total_forwards // len(statistics)

        # Find best performing post
        best_post = max(statistics, key=lambda x: x['views'])

        text = f"""📊 **Аналитика за последние {len(statistics)} постов**

📈 **Общая статистика:**
• Всего просмотров: {total_views:,}
• Всего реакций: {total_reactions:,}
• Всего пересылок: {total_forwards:,}

📊 **Средние показатели:**
• Просмотры: {avg_views:,} на пост
• Реакции: {avg_reactions:,} на пост
• Пересылки: {avg_forwards:,} на пост

🏆 **Лучший пост:**
• ID: #{best_post['post_id']}
• Просмотры: {best_post['views']:,}
• Реакции: {best_post['reactions']:,}
• Дата: {best_post['published_at'].strftime('%d.%m.%Y')}

💡 **Engagement Rate:** {(total_reactions / total_views * 100):.1f}%
"""

        return text
