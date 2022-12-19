import asyncio
from constants import *
from datetime import datetime

class Player:
    def __init__(self, user, chat_id):
        self._id = user.id
        self._number = 0
        self._name = user.first_name + (' ' + user.last_name if user.last_name else '')
        self._nick = user.username
        self._cards = []
        self._current_cards = []
        self._chat_id = chat_id
        self._num_of_games = 0
        self._num_of_wins = 0
        self._view_cards = False
        self._finding_game = False

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, ID):
        self._id = ID

    @property
    def number(self):
        return self._number

    @number.setter
    def number(self, num):
        self._number = num

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def nick(self):
        return self._nick

    @nick.setter
    def nick(self, nick):
        self._nick = nick

    @property
    def chat_id(self):
        return self._chat_id

    @chat_id.setter
    def chat_id(self, chat_id):
        self._chat_id = chat_id

    @property
    def num_of_games(self):
        return self._num_of_games

    @num_of_games.setter
    def num_of_games(self, num_of_games):
        self._num_of_games = num_of_games

    @property
    def num_of_wins(self):
        return self._num_of_wins

    @num_of_wins.setter
    def num_of_wins(self, num_of_wins):
        self._num_of_wins = num_of_wins

    @property
    def cards(self):
        return self._cards

    @cards.setter
    def cards(self, new_cards):
        self._cards = new_cards

    @property
    def current_cards(self):
        return self._current_cards

    @current_cards.setter
    def current_cards(self, new_current_cards):
        self._current_cards = new_current_cards

    @property
    def view_cards(self):
        return self._view_cards

    @view_cards.setter
    def view_cards(self, flag):
        self._view_cards = flag

    @property
    def finding_game(self):
        return self._finding_game

    @finding_game.setter
    def finding_game(self, flag):
        self._finding_game = flag


class GameManager:
    def __init__(self):
        self.games = []
        self.chat_ids = {}  # в join_game когда создается пользователь, его user_id и chat_id добавляются сюда
        self.players_ids = {}  # в join_game когда создается пользователь, его user_id и инстанс добавляются сюда
        self.user_game = {}  # user_id in bot -> their current game
        self.open_game = -1
        self.recent_messages = {}  # game -> last message time

    async def find_players(self, player):  # здесь же добавлять чела в user_game
        if self.open_game == -1:
            new_game = Game()
            self.games.append(new_game)
            self.open_game = len(self.games) - 1

        game = self.games[self.open_game]
        if len(game.players_in_game) < 6 and player not in game.players_in_game:
            game.players_in_game.append(player)
            player.number = game.players_cnt
            player.in_game = True
            game.players_cnt += 1
            if len(game.players_in_game) == 6:
                self.open_game = -1

        await asyncio.sleep(CREATE_GAME_TIME)
        self.open_game = -1  # после прохода времени набора в любом случае игра закрывается
        game.number_of_card_for_each = 52 // len(game.players_in_game)
        if len(game.players_in_game) < 2:
            game.players_in_game.clear()
            game.players_cnt = 1
            return None
        else:
            self.user_game[player.id] = game
            return game


from main import bot


class Game:
    def __init__(self):
        self.players_cnt = 1  # от этого счетчика раздаются номера игрокам
        self.players_in_game = []  # Players
        self.queue = []
        self.previous_cards = set()
        self.cards_in_game = []
        self.current_card_value = ""
        self.time_to_wait = 10
        self.is_add_previous_player = False  # хранит положил человек карты или положил ЕЩЕ
        self.used_cards = []
        self.available = ['a_s', '2_s', '3_s', '4_s', '5_s', '6_s', '7_s', '8_s', '9_s', '10_s', 'j_s', 'q_s', 'k_s',
                          'a_h', '2_h', '3_h', '4_h', '5_h', '6_h', '7_h', '8_h', '9_h', '10_h', 'j_h', 'q_h', 'k_h',
                          'a_c', '2_c', '3_c', '4_c', '5_c', '6_c', '7_c', '8_c', '9_c', '10_c', 'j_c', 'q_c', 'k_c',
                          'a_d', '2_d', '3_d', '4_d', '5_d', '6_d', '7_d', '8_d', '9_d', '10_d', 'j_d', 'q_d', 'k_d']

        self.not_used = 52
        self.number_of_card_for_each = 0
        self.cur_player = 0
        self.prev_player = 0
        self.is_game_open = True
        self.message_check = True
        self.message_sent = None
        self.game_time = datetime.now()

    async def check(self):
        # print(1)
        if not self.message_check:
            # все бездействовали 3 минуты -> выключаем игру
            if self.is_game_open:
                self.is_game_open = False
                for pl in self.players_in_game:
                    pl.cards.clear()
                    pl.num_of_games += 1
                    await bot.send_message(pl.chat_id, "Время вышло - игра окончена:(")
                    return
        self.message_check = False
        await asyncio.sleep(60)
        await self.check()
