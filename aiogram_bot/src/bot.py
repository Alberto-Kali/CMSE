import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, html
from aiogram.filters import Command
from aiogram.types import Message
import psycopg2

import redis.asyncio as aioredis
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)

# Bot token from BotFather
TOKEN = os.getenv("BOT_TOKEN")

# Database connection settings
POSTGRES_URL = os.getenv("DB_URL")
REDIS_URL = os.getenv("REDIS_URL")
NEO4J_URL = os.getenv("NEO4j_URL")
NEO4J_USER = os.getenv("NEO4j_USER")
NEO4J_PASSWORD = os.getenv("NEO4j_PASSWORD")


# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Initialize database connections
conn = None
redis_client = None
neo4j_driver = None

async def on_startup():
    global conn, redis_client, neo4j_driver

    # Connect to PostgreSQL
    #conn = await asyncpg.connect('postgresql://postgres@localhost/test')
    conn = psycopg2.connect(POSTGRES_URL)
    
    # Connect to Redis
    redis_client = aioredis.from_url(REDIS_URL)

    # Connect to Neo4j
    neo4j_driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD))

@dp.message(Command("example"))
async def example_command(message: Message):
    user_id = message.from_user.id

    # Store data in Redis
    await redis_client.set(f"user:{user_id}", "Example data")

    # Store data in Neo4j
    with neo4j_driver.session() as session:
        session.run("MERGE (u:User {id: $id})", id=user_id)

    await message.answer(f"Data for user {user_id} has been stored in all databases!")

@dp.message()
async def echo_handler(message: Message):
    await message.answer(f"You said: {message.text}")

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
