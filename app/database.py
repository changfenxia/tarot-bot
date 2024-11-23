import aiosqlite
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "tarot.db"):
        self.db_path = db_path
        self._init_db_path()

    def _init_db_path(self):
        """Ensure the database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    async def init(self):
        """Initialize the database with required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_cooldowns (
                    user_id INTEGER PRIMARY KEY,
                    last_request TIMESTAMP NOT NULL
                )
            ''')
            await db.commit()
        logger.info("Database initialized successfully")

    async def is_on_cooldown(self, user_id: int, cooldown_seconds: int = 30) -> bool:
        """Check if user is on cooldown"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    'SELECT last_request FROM user_cooldowns WHERE user_id = ?',
                    (user_id,)
                )
                row = await cursor.fetchone()
                
                if not row:
                    return False
                
                last_request = datetime.fromisoformat(row['last_request'])
                time_diff = (datetime.now() - last_request).total_seconds()
                
                return time_diff < cooldown_seconds
                
        except Exception as e:
            logger.error(f"Error checking cooldown: {e}")
            return False

    async def update_last_request(self, user_id: int):
        """Update user's last request timestamp"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO user_cooldowns (user_id, last_request)
                    VALUES (?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                    last_request = excluded.last_request
                ''', (user_id, datetime.now().isoformat()))
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error updating last request: {e}")

    async def cleanup_old_records(self, hours: int = 24):
        """Remove records older than specified hours"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
                await db.execute(
                    'DELETE FROM user_cooldowns WHERE last_request < ?',
                    (cutoff_time,)
                )
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error cleaning up old records: {e}")
