"""Create test published posts for analytics demonstration"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import text

from src.database.connection import get_session
from src.database.repositories.post_repo import PostRepository
from src.database.repositories.digest_repo import DigestRepository


async def create_test_posts():
    """Create 5 test published posts"""

    async with get_session() as session:
        digest_repo = DigestRepository(session)
        post_repo = PostRepository(session)

        print("🔄 Создаю тестовые опубликованные посты...\n")

        # Get existing digest
        digests = await session.execute(text("SELECT id FROM digests LIMIT 1"))
        digest_id = digests.scalar()

        if not digest_id:
            print("❌ Нет дайджестов в БД. Создай дайджест сначала.")
            return

        # Create 5 test posts
        for i in range(5):
            content = f"""📚 Тестовый пост #{i+1}

🎓 Грант на обучение в {['США', 'Германии', 'Великобритании', 'Канаде', 'Австралии'][i]}

💰 Покрытие: 100% стоимости обучения
📅 Дедлайн: {(datetime.now() + timedelta(days=30)).strftime('%d.%m.%Y')}

#образование #гранты #стипендии"""

            # Create post
            post = await post_repo.create_post(
                digest_id=digest_id,
                content=content,
                status='published'
            )

            # Mark as published with fake channel data
            published_at = datetime.now() - timedelta(days=i)

            await session.execute(
                text(f"""UPDATE posts
                SET status='published',
                    published_at='{published_at}',
                    channel_id=-1001234567890,
                    message_id={1000 + i}
                WHERE id={post.id}""")
            )

            print(f"✅ Пост #{i+1} создан (ID: {post.id})")

        await session.commit()
        print(f"\n✅ Создано 5 тестовых постов!")


if __name__ == "__main__":
    asyncio.run(create_test_posts())
