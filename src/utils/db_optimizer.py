"""Database query optimization utilities"""
from typing import List, Optional, Any
from sqlalchemy import Index, text
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger


class DatabaseOptimizer:
    """Utilities for database query optimization"""

    @staticmethod
    async def create_indexes(session: AsyncSession):
        """
        Create database indexes for frequently queried columns

        This should be called during database initialization
        """
        indexes = [
            # Articles indexes
            "CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url)",
            "CREATE INDEX IF NOT EXISTS idx_articles_source_id ON articles(source_id)",
            "CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_articles_is_processed ON articles(is_processed)",
            "CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at DESC)",

            # Digests indexes
            "CREATE INDEX IF NOT EXISTS idx_digests_status ON digests(status)",
            "CREATE INDEX IF NOT EXISTS idx_digests_created_at ON digests(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_digests_scheduled_for ON digests(scheduled_for)",

            # Posts indexes
            "CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status)",
            "CREATE INDEX IF NOT EXISTS idx_posts_digest_id ON posts(digest_id)",
            "CREATE INDEX IF NOT EXISTS idx_posts_scheduled_for ON posts(scheduled_for)",
            "CREATE INDEX IF NOT EXISTS idx_posts_published_at ON posts(published_at DESC)",

            # Sources indexes
            "CREATE INDEX IF NOT EXISTS idx_sources_is_active ON sources(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_sources_last_checked_at ON sources(last_checked_at DESC)",

            # Composite indexes for common queries
            "CREATE INDEX IF NOT EXISTS idx_articles_source_processed ON articles(source_id, is_processed)",
            "CREATE INDEX IF NOT EXISTS idx_digests_status_created ON digests(status, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_posts_status_scheduled ON posts(status, scheduled_for)",
        ]

        logger.info("Creating database indexes for optimization...")

        for index_sql in indexes:
            try:
                await session.execute(text(index_sql))
                index_name = index_sql.split("idx_")[1].split(" ")[0]
                logger.debug(f"✅ Created index: idx_{index_name}")
            except Exception as e:
                logger.warning(f"Could not create index: {e}")

        await session.commit()
        logger.info(f"✅ Database indexes created ({len(indexes)} total)")

    @staticmethod
    async def analyze_tables(session: AsyncSession):
        """
        Run ANALYZE on all tables to update statistics

        This helps the query planner make better decisions
        """
        tables = ['articles', 'digests', 'posts', 'sources', 'settings']

        logger.info("Analyzing database tables...")

        for table in tables:
            try:
                await session.execute(text(f"ANALYZE {table}"))
                logger.debug(f"✅ Analyzed table: {table}")
            except Exception as e:
                logger.warning(f"Could not analyze table {table}: {e}")

        await session.commit()
        logger.info("✅ Database analysis completed")

    @staticmethod
    async def vacuum_database(session: AsyncSession):
        """
        Run VACUUM to reclaim space and update statistics

        Note: This should be run periodically (e.g., weekly) outside transactions
        """
        try:
            # Close transaction before VACUUM
            await session.commit()

            logger.info("Running VACUUM on database...")
            await session.execute(text("VACUUM ANALYZE"))

            logger.info("✅ Database VACUUM completed")
        except Exception as e:
            logger.error(f"Could not VACUUM database: {e}")

    @staticmethod
    def get_optimization_tips() -> List[str]:
        """
        Get optimization tips for the bot

        Returns:
            List of optimization recommendations
        """
        return [
            "Use SELECT only needed columns instead of SELECT *",
            "Add WHERE clauses to filter data early",
            "Use indexes on frequently queried columns",
            "Batch INSERT/UPDATE operations when possible",
            "Use async session context managers to auto-close connections",
            "Limit result sets with LIMIT clause",
            "Use joins efficiently instead of multiple queries",
            "Cache frequently accessed data (e.g., settings)",
            "Run ANALYZE periodically to update query statistics",
            "Monitor slow queries and add indexes as needed"
        ]


class QueryOptimizer:
    """Helper methods for optimized queries"""

    @staticmethod
    def paginate(query, page: int = 1, per_page: int = 20):
        """
        Add pagination to a query

        Args:
            query: SQLAlchemy query object
            page: Page number (1-indexed)
            per_page: Items per page

        Returns:
            Paginated query
        """
        offset = (page - 1) * per_page
        return query.limit(per_page).offset(offset)

    @staticmethod
    def batch_operation(items: List[Any], batch_size: int = 100):
        """
        Split items into batches for bulk operations

        Args:
            items: List of items to process
            batch_size: Size of each batch

        Yields:
            Batches of items
        """
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]


# Global optimizer instance
db_optimizer = DatabaseOptimizer()
