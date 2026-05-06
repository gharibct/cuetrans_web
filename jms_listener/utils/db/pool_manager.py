# db/pool_manager.py
from typing import Optional, Any
import oracledb
from core.settings import settings
import os
import logging

logger = logging.getLogger(__name__)

class PoolManager:
    _instance: Optional["PoolManager"] = None
    _oracle_pool: Any = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_oracle_pool(self):
        if self._oracle_pool is None:
            try:
                user=settings.db_config.get("user", "user")
                # Get password from environment variable in
                password=os.getenv("DB_PASSWORD")
                dsn=settings.db_config.get("dsn", "localhost:1521/mydb")
                min=settings.db_config.get("min_connections", 5)
                max=settings.db_config.get("max_connections", 20)             

                # For Oracle - using oracledb (new async driver)
                self._oracle_pool = oracledb.create_pool_async(
                    user=user,
                    password=password,
                    dsn=dsn,
                    min=min,
                    max=max
                )
                # Validate the connection
                async with self._oracle_pool.acquire() as connection:
                    with connection.cursor() as cursor:
                        await cursor.execute("SELECT 1 FROM DUAL")
                logger.info("Successfully connected and validated Oracle database pool.")
            except Exception as e:
                logger.error(f"Failed to create or validate Oracle pool: {e}")
                raise
        return self._oracle_pool
    
    async def close_pools(self):
        if self._oracle_pool:
            await self._oracle_pool.close()
