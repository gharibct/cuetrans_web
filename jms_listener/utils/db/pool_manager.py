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

                            # CRITICAL: Set global defaults BEFORE creating the pool
                oracledb.defaults.arraysize = 100000
                oracledb.defaults.prefetchrows = 10000

                # For Oracle - using oracledb (new async driver)
                self._oracle_pool = oracledb.create_pool_async(
                    user=user,
                    password=password,
                    dsn=dsn,
                    min=min,
                    max=max,
                    session_callback=self._warm_up_connection,  # Add this!
                )
                # Validate the connection
                async with self._oracle_pool.acquire() as connection:
                    with connection.cursor() as cursor:
                        cursor.arraysize = 100000  # Set on validation too
                        cursor.prefetchrows = 10000
                        await cursor.execute("SELECT 1 FROM DUAL")
                        await cursor.fetchall()  # Complete the warm-up


                logger.info("Successfully connected and validated Oracle database pool.")
            except Exception as e:
                logger.error(f"Failed to create or validate Oracle pool: {e}")
                raise
        return self._oracle_pool

    async def _warm_up_connection(self, connection, requested_tag, **kwargs):
        """Warm up each new connection when it's created"""
        try:
            async with connection.cursor() as cursor:
                # Set fetch parameters
                cursor.arraysize = 10000
                cursor.prefetchrows = 1000
                
                # Execute and fetch to initialize internal buffers
                await cursor.execute("SELECT 1 FROM DUAL")
                await cursor.fetchall()
                
                # Optional: Set session preferences for better performance
                await cursor.execute("ALTER SESSION SET NLS_SORT = BINARY_CI")
                await cursor.execute("ALTER SESSION SET NLS_COMP = LINGUISTIC")
                
                logger.debug("Connection warmed up successfully")
        except Exception as e:
            logger.warning(f"Error warming up connection: {e}")
            # Don't raise - connection might still work

    async def close_pools(self):
        if self._oracle_pool:
            await self._oracle_pool.close()
