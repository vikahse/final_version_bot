from main import *


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    num_of_games = Column(String)
    num_of_wins = Column(String)


class Game(Base):
    __tablename__ = 'games'

    # id = Column(Integer, primary_key=True)
    num_of_players = Column(Integer)
    winner_id = Column(Integer, primary_key=True)
    duration_of_game = Column(Integer)


Base.metadata.create_all(bind=engine)
