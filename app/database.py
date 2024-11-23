import aiosqlite
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "tarot.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self._ensure_db_dir()
        asyncio.run(self.init())  # Initialize tables when creating database object

    def _ensure_db_dir(self):
        """Ensure the database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    async def init(self):
        """Initialize database tables"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS bot_settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                ''')
                
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS user_cooldowns (
                        user_id INTEGER PRIMARY KEY,
                        last_request TEXT NOT NULL
                    )
                ''')
                
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS request_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        username TEXT,
                        question TEXT NOT NULL,
                        cards TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        success BOOLEAN NOT NULL
                    )
                ''')
                
                # Set default cooldown if not exists
                await db.execute(
                    'INSERT OR IGNORE INTO bot_settings (key, value) VALUES (?, ?)',
                    ('cooldown_minutes', '1440')  # 24 hours in minutes
                )
                
                # Set default test mode if not exists
                await db.execute(
                    'INSERT OR IGNORE INTO bot_settings (key, value) VALUES (?, ?)',
                    ('test_mode', 'false')
                )
                
                await db.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    async def get_cooldown_minutes(self) -> int:
        """Get current cooldown setting in minutes"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    'SELECT value FROM bot_settings WHERE key = ?',
                    ('cooldown_minutes',)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return int(row[0])
                    return 1440  # Default: 24 hours = 1440 minutes
        except Exception as e:
            logger.error(f"Error getting cooldown setting: {e}")
            return 1440  # Default on error

    async def set_cooldown_minutes(self, minutes: int, updated_by: int) -> bool:
        """Set cooldown in minutes"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    '''INSERT OR REPLACE INTO bot_settings 
                       (key, value, updated_at, updated_by) 
                       VALUES (?, ?, CURRENT_TIMESTAMP, ?)''',
                    ('cooldown_minutes', str(minutes), updated_by)
                )
                await db.commit()
                logger.info(f"Cooldown set to {minutes} minutes by user {updated_by}")
                return True
        except Exception as e:
            logger.error(f"Error setting cooldown: {e}")
            return False

    async def get_remaining_cooldown_minutes(self, user_id: int) -> int:
        """Get remaining cooldown time in minutes"""
        try:
            cooldown_minutes = await self.get_cooldown_minutes()
            cooldown_seconds = cooldown_minutes * 60
            
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    'SELECT last_request FROM user_cooldowns WHERE user_id = ?',
                    (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        return 0

                    last_request = datetime.fromisoformat(row[0])
                    time_diff = (datetime.now() - last_request).total_seconds()
                    remaining_seconds = cooldown_seconds - time_diff
                    
                    if remaining_seconds <= 0:
                        return 0
                    
                    # Round up to the nearest minute if less than a minute remains
                    remaining_minutes = max(1, int((remaining_seconds + 59) // 60))
                    return remaining_minutes

        except Exception as e:
            logger.error(f"Error checking remaining cooldown: {e}")
            return 0

    async def is_on_cooldown(self, user_id: int) -> tuple[bool, int]:
        """Check if user is on cooldown and return remaining minutes"""
        try:
            remaining_minutes = await self.get_remaining_cooldown_minutes(user_id)
            return remaining_minutes > 0, remaining_minutes

        except Exception as e:
            logger.error(f"Error checking cooldown: {e}")
            return False, 0

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

    async def log_request(self, user_id: int, username: str, question: str, cards: list, success: bool):
        """Log a tarot request"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO request_log (user_id, username, question, cards, timestamp, success)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, username, question, ','.join(cards), datetime.now().isoformat(), success))
                await db.commit()
        except Exception as e:
            logger.error(f"Error logging request: {e}")

    async def get_user_stats(self, days: int = 7) -> dict:
        """Get statistics for the last N days"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Total requests
                cursor = await db.execute('''
                    SELECT COUNT(*) as total,
                           COUNT(DISTINCT user_id) as unique_users,
                           SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
                           SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed
                    FROM request_log
                    WHERE timestamp > ?
                ''', (cutoff_time,))
                stats = await cursor.fetchone()
                
                # Most active users
                cursor = await db.execute('''
                    SELECT username, COUNT(*) as request_count
                    FROM request_log
                    WHERE timestamp > ? AND username IS NOT NULL
                    GROUP BY username
                    ORDER BY request_count DESC
                    LIMIT 5
                ''', (cutoff_time,))
                top_users = await cursor.fetchall()
                
                # Most common questions (keywords)
                cursor = await db.execute('''
                    SELECT question, COUNT(*) as count
                    FROM request_log
                    WHERE timestamp > ?
                    GROUP BY question
                    ORDER BY count DESC
                    LIMIT 5
                ''', (cutoff_time,))
                top_questions = await cursor.fetchall()
                
                return {
                    "period_days": days,
                    "total_requests": stats['total'],
                    "unique_users": stats['unique_users'],
                    "successful_requests": stats['successful'],
                    "failed_requests": stats['failed'],
                    "top_users": [(row['username'], row['request_count']) for row in top_users],
                    "top_questions": [(row['question'], row['count']) for row in top_questions]
                }
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

    async def cleanup_old_records(self, hours: int = 24):
        """Remove records older than specified hours"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
                await db.execute(
                    'DELETE FROM user_cooldowns WHERE last_request < ?',
                    (cutoff_time,)
                )
                await db.execute(
                    'DELETE FROM request_log WHERE timestamp < ?',
                    (cutoff_time,)
                )
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error cleaning up old records: {e}")

    async def is_test_mode(self) -> bool:
        """Check if bot is in test mode"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    'SELECT value FROM bot_settings WHERE key = ?',
                    ('test_mode',)
                ) as cursor:
                    row = await cursor.fetchone()
                    return row[0].lower() == 'true' if row else False
        except Exception as e:
            logger.error(f"Error checking test mode: {e}")
            return False

    async def toggle_test_mode(self) -> bool:
        """Toggle test mode and return new state"""
        try:
            current_mode = await self.is_test_mode()
            new_mode = 'false' if current_mode else 'true'
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    'UPDATE bot_settings SET value = ? WHERE key = ?',
                    (new_mode, 'test_mode')
                )
                await db.commit()
                
            return not current_mode
        except Exception as e:
            logger.error(f"Error toggling test mode: {e}")
            return False

    def close(self):
        """Close database connection (placeholder for cleanup)"""
        logger.info("Database cleanup called")
        pass  # aiosqlite handles connection cleanup automatically through context managers
