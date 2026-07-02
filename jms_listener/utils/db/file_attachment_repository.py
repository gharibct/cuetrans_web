from typing import Any

from utils.db.pool_manager import PoolManager


pool_mgr = PoolManager()


GET_NEXT_SEQ_ID_QUERY = """
SELECT NVL(MAX(SEQ_ID), 0) + 1 AS NEXT_SEQ_ID
FROM CT_USERS_FILE_ATTACHMENT
"""

INSERT_FILE_ATTACHMENT_QUERY = """
INSERT INTO CT_USERS_FILE_ATTACHMENT (
    SEQ_ID,
    CREATED_DATE,
    USER_NAME,
    FILE_TYPE,
    FILE_NAME,
    FILE_ATTACHMENT_ID,
    FILE_CONTENT
) VALUES (
    :seq_id,
    SYSTIMESTAMP,
    :user_name,
    :file_type,
    :file_name,
    :file_attachment_id,
    :file_content
)
"""

SELECT_FILE_ATTACHMENT_QUERY = """
SELECT FILE_NAME, FILE_CONTENT
FROM CT_USERS_FILE_ATTACHMENT
WHERE FILE_ATTACHMENT_ID = :file_attachment_id
"""


def _column_name(column: Any) -> str:
    return getattr(column, "name", column[0])


async def insert_file_attachment(
    *,
    user_name: str | None,
    file_type: str | None,
    file_name: str,
    file_attachment_id: str,
    file_content: bytes,
) -> None:
    pool = await pool_mgr.get_oracle_pool()

    async with pool.acquire() as conn:
        conn.autocommit = False
        try:
            async with conn.cursor() as cursor:
                await cursor.execute(GET_NEXT_SEQ_ID_QUERY)
                row = await cursor.fetchone()
                seq_id = row[0]

                await cursor.execute(
                    INSERT_FILE_ATTACHMENT_QUERY,
                    {
                        "seq_id": seq_id,
                        "user_name": user_name,
                        "file_type": file_type,
                        "file_name": file_name,
                        "file_attachment_id": file_attachment_id,
                        "file_content": file_content,
                    },
                )

            await conn.commit()
        except Exception:
            await conn.rollback()
            raise


async def fetch_file_attachment(file_attachment_id: str) -> dict | None:
    pool = await pool_mgr.get_oracle_pool()

    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                SELECT_FILE_ATTACHMENT_QUERY,
                {"file_attachment_id": file_attachment_id},
            )
            row = await cursor.fetchone()

            if not row:
                return None

            columns = [_column_name(column) for column in cursor.description]
            return dict(zip(columns, row))
