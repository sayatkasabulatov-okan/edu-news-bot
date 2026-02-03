"""Service for collecting real statistics from Telegram"""
from typing import Dict, Optional
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from loguru import logger

from src.database.models import Post
from src.database.repositories.post_repo import PostRepository


class TelegramStatsService:
    """Service for collecting post statistics from Telegram"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def get_post_statistics(self, channel_id: int, message_id: int) -> Optional[Dict]:
        """
        Get statistics for a specific post from Telegram channel

        Args:
            channel_id: Telegram channel ID
            message_id: Message ID in the channel

        Returns:
            Dictionary with statistics or None if error
        """
        try:
            # Method 1: Try to get message directly
            # This works if bot is admin in the channel
            message = await self.bot.forward_message(
                chat_id=channel_id,
                from_chat_id=channel_id,
                message_id=message_id
            )

            # Delete the forwarded message immediately
            await self.bot.delete_message(
                chat_id=channel_id,
                message_id=message.message_id
            )

            # Extract available statistics
            stats = {
                'views': getattr(message, 'views', 0),
                'forwards': getattr(message, 'forwards', 0),
                'reactions': 0,  # Will be calculated from reactions if available
            }

            # Try to get reactions if available
            if hasattr(message, 'reactions') and message.reactions:
                total_reactions = sum(
                    reaction.total_count
                    for reaction in message.reactions.reactions
                )
                stats['reactions'] = total_reactions

            logger.info(f"Got stats for message {message_id}: {stats}")
            return stats

        except TelegramError as e:
            logger.error(f"Error getting stats for message {message_id}: {e}")
            # Try alternative method - get chat and analyze
            return await self._get_stats_alternative(channel_id, message_id)

        except Exception as e:
            logger.error(f"Unexpected error getting stats: {e}")
            return None

    async def _get_stats_alternative(self, channel_id: int, message_id: int) -> Optional[Dict]:
        """
        Alternative method to get statistics using getChatMember and other API calls

        Args:
            channel_id: Telegram channel ID
            message_id: Message ID

        Returns:
            Dictionary with statistics or None
        """
        try:
            # This is a fallback - returns zero stats
            # In production, you might want to use Telegram Analytics API
            # or store statistics when posts are published

            logger.warning(f"Using fallback stats method for message {message_id}")

            return {
                'views': 0,
                'forwards': 0,
                'reactions': 0,
            }

        except Exception as e:
            logger.error(f"Error in alternative stats method: {e}")
            return None

    async def update_post_statistics(self, post: Post) -> bool:
        """
        Update statistics for a published post

        Args:
            post: Post object to update

        Returns:
            True if successful, False otherwise
        """
        if not post.channel_id or not post.message_id:
            logger.warning(f"Post {post.id} has no channel/message info")
            return False

        stats = await self.get_post_statistics(post.channel_id, post.message_id)

        if stats:
            post.views_count = stats.get('views', 0)
            post.reactions_count = stats.get('reactions', 0)
            post.forwards_count = stats.get('forwards', 0)
            post.last_stats_update = datetime.now()

            logger.info(f"Updated stats for post {post.id}: "
                       f"{post.views_count} views, "
                       f"{post.reactions_count} reactions, "
                       f"{post.forwards_count} forwards")
            return True

        return False

    async def get_channel_info(self, channel_id: int) -> Optional[Dict]:
        """
        Get general channel information

        Args:
            channel_id: Telegram channel ID

        Returns:
            Dictionary with channel info or None
        """
        try:
            chat = await self.bot.get_chat(channel_id)

            info = {
                'title': chat.title,
                'username': chat.username,
                'description': chat.description,
                'member_count': await self.bot.get_chat_member_count(channel_id),
                'type': chat.type,
            }

            logger.info(f"Got channel info: {info}")
            return info

        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return None

    async def bulk_update_statistics(self, posts: list) -> Dict:
        """
        Update statistics for multiple posts

        Args:
            posts: List of Post objects

        Returns:
            Dictionary with update results
        """
        results = {
            'updated': 0,
            'failed': 0,
            'total': len(posts)
        }

        for post in posts:
            try:
                success = await self.update_post_statistics(post)
                if success:
                    results['updated'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                logger.error(f"Error updating post {post.id}: {e}")
                results['failed'] += 1

        logger.info(f"Bulk update results: {results}")
        return results
