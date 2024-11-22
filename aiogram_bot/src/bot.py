import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, html
from aiogram.filters import Command
from aiogram.types import Message
from asyncpg import create_pool
import redis.asyncio as aioredis
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)

# Bot token from BotFather
TOKEN = os.getenv("BOT_TOKEN")

# Database connection settings
POSTGRES_USER = os.getenv("DB_USER")
POSTGRES_PASSWORD = os.getenv("DB_PASSWORD")
POSTGRES_DB = os.getenv("DB_NAME")
POSTGRES_HOST = os.getenv("DB_HOST")
POSTGRES_PORT = os.getenv("DB_PORT")
REDIS_URL = os.getenv("REDIS_URL")
NEO4J_URI = os.getenv("NEO4j_URL")
NEO4J_USER = os.getenv("NEO4j_USER")
NEO4J_PASSWORD = os.getenv("NEO4j_PASSWORD")

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Initialize database connections
postgres_pool = None
redis_client = None
neo4j_driver = None

async def on_startup():
    global postgres_pool, redis_client, neo4j_driver

    # Connect to PostgreSQL
    postgres_pool = await create_pool(
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    )
    
    # Connect to Redis
    redis_client = aioredis.from_url(REDIS_URL)

    # Connect to Neo4j
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

@dp.message(Command("example"))
async def example_command(message: Message):
    user_id = message.from_user.id

    # Store data in PostgreSQL
    async with postgres_pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO users (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING", user_id)

    # Store data in Redis
    await redis_client.set(f"user:{user_id}", "Example data")

    # Store data in Neo4j
    with neo4j_driver.session() as session:
        session.run("MERGE (u:User {id: $id})", id=user_id)

    await message.answer(f"Data for user {user_id} has been stored in all databases!")

@dp.message()
async def echo_handler(message: Message):
    await message.answer(f"You said: {html.escape(message.text)}")

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
