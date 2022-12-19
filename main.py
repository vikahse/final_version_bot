from telebot.async_telebot import AsyncTeleBot

TOKEN = ''
bot = AsyncTeleBot(TOKEN)

from handlers import *
from modules import GameManager

import os
from sqlalchemy import create_engine, Column, Integer, Boolean, String
from dotenv import load_dotenv
from sqlalchemy.orm import scoped_session, declarative_base, sessionmaker

load_dotenv()

host = str(os.getenv("HOST"))
password = str(os.getenv("PASSWORD"))
database = str(os.getenv("DATABASE"))

engine = create_engine(f"postgresql+psycopg2://postgres:{password}@{host}/{database}")

session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()
Base.query = session.query_property()

manager = GameManager()

if __name__ == '__main__':
    asyncio.run(bot.polling(non_stop=True))

