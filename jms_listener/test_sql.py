import asyncio
import oracledb
from datetime import datetime

pool = None

async def create_pool():
    global pool
    print(f"create_pool: {datetime.now()}")
    pool = oracledb.create_pool_async(
        user="PDO_STAGE_COE_TMS_APP",
        password="PDO_STAGE_COE_TMS_APP",
        dsn="cuetranspdoprod.cdmgnqqkccnr.eu-central-1.rds.amazonaws.com:1521/orcl",
        min=5,
        max=20,
        increment=2
    )

async def get_locations():

    async with pool.acquire() as conn:
        print(f"get_locations 1 : {datetime.now()}")
        conn.autocommit = False 
        async with conn.cursor() as cursor:
            print(f"get_locations 2 : {datetime.now()}")
            await cursor.execute("""
select loc_code as "id",loc_name as "value",1 as "seqno"
from jms_location_mst where status  in ('AC')
union
select 'ALL' as "id",'ALL' as "value",0 as "seqno"
from dual
order by "seqno","value"
            """)
            print(f"get_locations 3 : {datetime.now()}")
            rows = await fetch_rows_as_dicts(cursor)

    return rows


def get_column_name(column) -> str:
    return getattr(column, "name", column[0])

async def fetch_rows_as_dicts(cursor) -> list[dict]:

    cursor.arraysize = 500
    cursor.prefetchrows = 500

    columns = [get_column_name(column) for column in cursor.description]

    result = []

    while True:

        batch = await cursor.fetchmany(500)

        if not batch:
            break

        for row in batch:
            result.append({
                columns[i]: (
                    row[i] if row[i] is not None else ""
                )
                for i in range(len(columns))
            })

    return result

async def main():
    print(f"main 1 : {datetime.now()}")
    await create_pool()
    print(f"main 2 : {datetime.now()}")
    rows = await get_locations()
    print(f"main 3 : {datetime.now()}")
    print(f"Total rows fetched: {len(rows)}")
    # for row in rows:
    #     print(row)

asyncio.run(main())