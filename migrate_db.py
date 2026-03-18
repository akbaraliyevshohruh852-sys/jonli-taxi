import asyncio
from core.database import init_db, db

async def main():
    await init_db()
    
    expected_tables = ["drivers", "passengers", "orders", "payments", "blacklist"]
    for table in expected_tables:
        cols = await db._execute(f"PRAGMA table_info({table})", fetch_all=True)
        print(f"Table {table}: {[c['name'] for c in cols]}")

if __name__ == "__main__":
    asyncio.run(main())
