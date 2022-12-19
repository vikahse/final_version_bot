import random
from modules import *
from service import *
from main import bot, manager, session
from take_photo import *
from sqlalchemy.exc import PendingRollbackError, IntegrityError
from models import *
from datetime import datetime


@bot.message_handler(commands=['start'])
async def hello_message(message):
    await bot.send_message(message.chat.id, f'Привет! Ты зашел в игру Верю не Верю.\n'
                                            f'Напиши /join, и мы начнем искать'
                                            f' для тебя свободную игру, чтобы ты мог '
                                            f'анонимно играть с другими участниками. \n'
                                            f'Если перед игрой ты хочешь почитать правила игры,'
                                            f'то напиши /rules 🃏')


@bot.message_handler(commands=['end_game'])
async def end_game(message: [types.Message]):
    user_id = message.from_user.id
    if manager.user_game.get(user_id) is not None and manager.user_game.get(user_id).is_game_open:
        game = manager.user_game[message.from_user.id]
        game.is_game_open = False
        markup_reply = types.ReplyKeyboardRemove()
        player = None
        for pl in game.players_in_game:
            if pl.id == message.from_user.id:
                player = pl
        clear_data(game, None)
        for pl in game.players_in_game:
            if pl.id == message.from_user.id:
                pl.finding_game = False
                const = await bot.send_message(user_id, 'Вы вышли из игры! Игра закончилась!',
                                               reply_markup=markup_reply)

                if game.message_sent.message_id is not None and game.message_sent.chat.id == const.chat.id:
                    await bot.delete_message(const.chat.id, game.message_sent.message_id)

            else:
                pl.finding_game = False
                const2 = await bot.send_message(pl.id,
                                                f'Игра закончилась, так как игрок №{player.number} вышел из нее!',
                                                reply_markup=markup_reply)

                if game.message_sent.message_id is not None and game.message_sent.chat.id == const2.chat.id:
                    await bot.delete_message(const2.chat.id, game.message_sent.message_id)

            pl.cards.clear()
        return
    else:
        await bot.send_message(user_id, 'Вы еще не играете!')


@bot.message_handler(commands=['whole_statistics'])
async def whole_statistics(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    current_player = manager.players_ids.get(user_id)
    if current_player is None:
        await bot.send_message(chat_id, 'Ты пока не сыграл ни одной игры! Подключайся!\n')
        return
    game = manager.user_game[user_id]
    # для таймаутов
    if game.is_game_open:
        game.message_check = True
    # для таймаутов
    num_games = current_player.num_of_games
    num_wins = current_player.num_of_wins
    await bot.send_message(chat_id, f'Вот твоя статистика по всем играм!\n'
                                    f'Общее количество сыгранных партий - {num_games}\n'
                                    f'Число побед - {num_wins}')


@bot.message_handler(commands=['rules'])
async def rules(message):
    chat_id = message.chat.id
    with open('rules.txt') as f:
        await bot.send_message(chat_id, f.read())


@bot.message_handler(commands=['join'])
async def join_game(message: [types.Message]):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if manager.chat_ids.get(chat_id) is None:
        manager.chat_ids[chat_id] = user_id
        player = Player(message.from_user, chat_id)
        manager.players_ids[user_id] = player

    player = manager.players_ids[user_id]

    if player.finding_game and manager.user_game[user_id].is_game_open == False:
        await bot.send_message(user_id, 'Мы все еще ищем игру')
        return

    if manager.user_game.get(user_id) is not None and manager.user_game[user_id].is_game_open:
        await bot.send_message(user_id, 'Вы уже играете!')
        return

    await bot.send_message(message.from_user.id,
                           'Мы начали искать подходящую игру, по прошествии 3 минут игра будет '
                           'отменена по причине нехватки игроков')

    player.finding_game = True
    game = await manager.find_players(player)
    if game is not None:
        game.game_time = datetime.now()
        game.is_game_open = True
        game.cur_player = 1
        await bot.send_message(message.from_user.id, 'приятной игры!')
        await send_info_about_game(game, chat_id, player)
        await hand_out_cards(game, player)
        if message.from_user.id == game.players_in_game[game.cur_player - 1].id:
            markup = types.InlineKeyboardMarkup(row_width=1)
            make_choice_btn = types.InlineKeyboardButton(text='⬇️ Выбрать карты ⬇️', callback_data="cards")
            markup.add(make_choice_btn)

            const = await bot.send_message(message.from_user.id, text=f'Игрок {game.cur_player} сделай ход',
                                           reply_markup=markup)
            game.message_sent = const
            await game.check()


    else:
        player.finding_game = False
        await bot.send_message(message.from_user.id, 'Не удалось найти доступные игры')


@bot.message_handler(commands=['statistics'])
async def statistics(message: [types.Message]):
    user_id = message.from_user.id
    game = manager.user_game.get(user_id)
    if game is not None and game.is_game_open:
        # для таймаутов
        if game.is_game_open:
            game.message_check = True
        # для таймаутов
        text = ""
        text += f'Кол-во карт на столе: 🃏x{refactor(len(game.cards_in_game), "карта")} \n'
        text += f'Кол-во карт у каждого игрока: \n'
        for pl in game.players_in_game:
            if pl.id == user_id:
                text += f'№{pl.number}(Вы): 🃏x{refactor(len(pl.cards), "карта")} \n'
            else:
                text += f'№{pl.number}: 🃏x{refactor(len(pl.cards), "карта")} \n'
        text += f'Кол-во карт в сдаче: 🃏x{refactor(len(game.used_cards), "карта")} \n'
        if user_id == game.players_in_game[game.cur_player - 1].id:
            text += f'Сейчас ход игрока №{game.cur_player}(Вы) \n'
        else:
            text += f'Сейчас ход игрока №{game.cur_player} \n'
        await bot.send_message(user_id, text)
    else:
        await bot.send_message(user_id, 'Вы еще не играете!')


@bot.message_handler(commands=['view_cards'])
async def view_cards_command(message: [types.Message]):
    user_id = message.from_user.id
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)

    if manager.players_ids.get(user_id) is not None and manager.user_game.get(user_id) is not None and \
            manager.user_game[user_id].is_game_open:

        # для таймаутов
        manager.user_game[user_id].message_check = True
        # для таймаутов

        current = manager.players_ids[user_id]
        ost = len(current.cards) % 3
        current.cards.sort()
        btn = types.KeyboardButton(f'Закончить просмотр')
        keyboard.add(btn)

        current.view_cards = True
        for i in range(0, len(current.cards) - ost, 3):
            btn1 = types.KeyboardButton(f'{STIKERS[current.cards[i]]}')
            btn2 = types.KeyboardButton(f'{STIKERS[current.cards[i + 1]]}')
            btn3 = types.KeyboardButton(f'{STIKERS[current.cards[i + 2]]}')
            keyboard.row(btn1, btn2, btn3)
        if ost == 1:
            keyboard.add(types.KeyboardButton(f'{STIKERS[current.cards[-1]]}'))
        elif ost == 2:
            btn1 = types.KeyboardButton(f'{STIKERS[current.cards[-1]]}')
            btn2 = types.KeyboardButton(f'{STIKERS[current.cards[-2]]}')
            keyboard.row(btn1, btn2)

        await bot.send_message(message.chat.id, text='Посмотрите на карты', reply_markup=keyboard)
    else:
        await bot.send_message(message.chat.id, text='Вы еще не в игре, напишите /join, чтобы присоединиться')


@bot.callback_query_handler(func=lambda call: call.data == "view_cards")
async def view_cards(call):
    game = manager.user_game[call.from_user.id]
    if game.is_game_open:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        current = manager.players_ids[call.from_user.id]
        ost = len(current.cards) % 3
        current.cards.sort()
        btn = types.KeyboardButton(f'Закончить просмотр')
        keyboard.add(btn)

        current.view_cards = True
        for i in range(0, len(current.cards) - ost, 3):
            btn1 = types.KeyboardButton(f'{STIKERS[current.cards[i]]}')
            btn2 = types.KeyboardButton(f'{STIKERS[current.cards[i + 1]]}')
            btn3 = types.KeyboardButton(f'{STIKERS[current.cards[i + 2]]}')
            keyboard.row(btn1, btn2, btn3)
        if ost == 1:
            keyboard.add(types.KeyboardButton(f'{STIKERS[current.cards[-1]]}'))
        elif ost == 2:
            btn1 = types.KeyboardButton(f'{STIKERS[current.cards[-1]]}')
            btn2 = types.KeyboardButton(f'{STIKERS[current.cards[-2]]}')
            keyboard.row(btn1, btn2)

        await bot.send_message(call.message.chat.id, text='Посмотрите на карты', reply_markup=keyboard)

        game.message_sent = call.message


@bot.callback_query_handler(func=lambda call: call.data == "not_believe")
async def not_believe(call):
    game = manager.user_game[call.from_user.id]
    # для таймаутов
    if game.is_game_open:
        game.message_check = True
    # для таймаутов
    if game.is_game_open:
        flag = True
        for card in game.previous_cards:
            if ITEMS[game.current_card_value] + '_' not in card:
                flag = False
        game.current_card_value = ""
        if not flag:  # не поверил и оказался прав
            if len(game.players_in_game[game.cur_player - 1].cards) == 0:
                winner = game.players_in_game[game.cur_player - 1]
                for pl in game.players_in_game:
                    await take_photo_of_the_field(game, pl, game.cur_player, game.prev_player, False, False)
                for card in game.cards_in_game:
                    game.players_in_game[game.prev_player - 1].cards.append(card)
                game.cards_in_game.clear()
                game.previous_cards.clear()
                game.is_game_open = False
                for pl in game.players_in_game:
                    await take_photo_of_the_field(game, pl, game.cur_player, game.prev_player, False, True)
                    # pl.num_of_games += 1
                    if pl.id != winner.id:
                        conts = await bot.send_message(pl.id, text=f'Игрок {winner.number} победил! Игра окончена')

                        if game.message_sent.message_id is not None and game.message_sent.chat.id == conts.chat.id:
                            await bot.delete_message(call.message.chat.id, game.message_sent.message_id)

                    # else:
                    #     pl.num_of_wins += 1
                const = await bot.send_message(winner.id, text=f'Поздравляем! Вы победили! Игра окончена')

                if game.message_sent.message_id is not None and game.message_sent.chat.id == const.chat.id:
                    await bot.delete_message(call.message.chat.id, game.message_sent.message_id)

                clear_data(game, winner)

            else:
                markup = types.InlineKeyboardMarkup(row_width=1)
                make_choice_btn = types.InlineKeyboardButton(text='⬇️ Выбрать карты ⬇️', callback_data="cards")
                markup.add(make_choice_btn)

                for other_pl in game.players_in_game:
                    await take_photo_of_the_field(game, other_pl, game.cur_player, game.prev_player, False, False)
                    if other_pl.number != game.prev_player:
                        await bot.send_message(other_pl.chat_id,
                                               text=f'Игрок {game.prev_player} взял 🃏x{refactor(len(game.cards_in_game), "карта")}')

                    else:
                        await bot.send_message(game.players_in_game[game.prev_player - 1].chat_id,
                                               text=f'Вы взяли 🃏x{refactor(len(game.cards_in_game), "карта")}')

                for card in game.cards_in_game:
                    game.players_in_game[game.prev_player - 1].cards.append(card)
                number_of_cards = len(game.cards_in_game)
                game.cards_in_game.clear()
                game.previous_cards.clear()
                for pl in game.players_in_game:
                    await take_photo_of_the_field(game, pl, game.cur_player, game.prev_player, False, True)

                await bot.delete_message(call.message.chat.id, game.message_sent.message_id)

                const = await bot.send_message(call.message.chat.id,
                                       f'Игрок {game.cur_player}, сделай ставку:',
                                       reply_markup=markup)

                game.message_sent = const
        else:  # не поверил и не прав
            for other_pl in game.players_in_game:
                await take_photo_of_the_field(game, other_pl, game.cur_player, game.prev_player, False, False)
                if other_pl.number != game.cur_player:
                    await bot.send_message(other_pl.chat_id,
                                           text=f'Игрок {game.cur_player} взял 🃏x{refactor(len(game.cards_in_game), "карта")}')
                else:
                    await bot.send_message(game.players_in_game[game.cur_player - 1].chat_id,
                                           text=f'Вы взяли 🃏x{refactor(len(game.cards_in_game), "карта")}')

            await bot.delete_message(call.message.chat.id, game.message_sent.message_id)

            for card in game.cards_in_game:
                game.players_in_game[game.cur_player - 1].cards.append(card)
            game.cards_in_game.clear()
            game.previous_cards.clear()
            await update_current_player(game)
            await new_step(game)


@bot.callback_query_handler(func=lambda call: call.data == "believe")
async def believe(call):
    game = manager.user_game[call.from_user.id]
    # для таймаутов
    if game.is_game_open:
        game.message_check = True
    # для таймаутов
    if game.is_game_open:
        check = ITEMS[str(game.current_card_value)]
        count = len(game.previous_cards)
        count_cur = 0
        game.current_card_value = ""
        for card in game.previous_cards:
            if card[0] == check:
                count_cur += 1
            elif card[:2] == check:
                count_cur += 1

        if count_cur == count:  # повериил и прав карты сбрасываются он снова ходит
            if len(game.players_in_game[game.cur_player - 1].cards) == 0:
                winner = game.players_in_game[game.cur_player - 1]
                for pl in game.players_in_game:
                    await take_photo_of_the_field(game, pl, game.cur_player, game.prev_player, True, False)
                game.used_cards.append(game.cards_in_game)
                game.cards_in_game.clear()
                game.previous_cards.clear()
                game.is_game_open = False
                for pl in game.players_in_game:
                    await take_photo_of_the_field(game, pl, game.cur_player, game.prev_player, False, True)
                    if pl.id != winner.id:
                        conts = await bot.send_message(pl.id, text=f'Игрок {winner.number} победил! Игра окончена')

                        if game.message_sent.message_id is not None and game.message_sent.chat.id == conts.chat.id:
                            await bot.delete_message(call.message.chat.id, game.message_sent.message_id)

                const = await bot.send_message(winner.id, text=f'Поздравляем! Вы победили! Игра окончена')

                if game.message_sent.message_id is not None and game.message_sent.chat.id == const.chat.id:
                    await bot.delete_message(call.message.chat.id, game.message_sent.message_id)

                clear_data(game, winner)
            else:
                markup = types.InlineKeyboardMarkup(row_width=1)
                make_choice_btn = types.InlineKeyboardButton(text='⬇️ Выбрать карты ⬇️', callback_data="cards")
                markup.add(make_choice_btn)
                for card in game.cards_in_game:
                    game.used_cards.append(card)
                for other_pl in game.players_in_game:
                    await take_photo_of_the_field(game, other_pl, game.cur_player, game.prev_player, True, False)
                    await bot.send_message(other_pl.id,
                                           f'Карты сбросились.\n'
                                           f'Сейчас на столе 🃏x0 карт.')

                await bot.delete_message(call.message.chat.id, game.message_sent.message_id)

                number_of_cards = len(game.cards_in_game)
                game.cards_in_game.clear()
                game.previous_cards.clear()
                for pl in game.players_in_game:
                    await take_photo_of_the_field(game, pl, game.cur_player, game.prev_player, False, True)
                const = await bot.send_message(call.message.chat.id, f'Игрок {game.cur_player}, сделай ставку:',
                                       reply_markup=markup)
                game.message_sent = const
        else:  # поверил и не прав
            for other_pl in game.players_in_game:
                await take_photo_of_the_field(game, other_pl, game.cur_player, game.prev_player, True, False)
                if other_pl.number != game.cur_player:
                    await bot.send_message(other_pl.chat_id,
                                           text=f'Игрок {game.cur_player} взял 🃏x{refactor(len(game.cards_in_game), "карта")}')
                else:
                    await bot.delete_message(call.message.chat.id, game.message_sent.message_id)

                    await bot.send_message(game.players_in_game[game.cur_player - 1].chat_id,
                                           text=f'Вы взяли 🃏x{refactor(len(game.cards_in_game), "карта")}')

            for card in game.cards_in_game:
                game.players_in_game[game.cur_player - 1].cards.append(card)
            game.cards_in_game.clear()
            game.previous_cards.clear()
            await update_current_player(game)
            await new_step(game)


@bot.callback_query_handler(func=lambda call: call.data == "cards")
async def cards(call):
    game = manager.user_game.get(call.from_user.id)
    # для таймаутов
    if game is not None and game.is_game_open:
        game.message_check = True
    # для таймаутов
    if game is not None and game.is_game_open:

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        current = game.players_in_game[game.cur_player - 1]
        ost = len(current.cards) % 3
        current.cards.sort()
        for i in range(0, len(current.cards) - ost, 3):
            btn1 = types.KeyboardButton(f'{STIKERS[current.cards[i]]}')
            btn2 = types.KeyboardButton(f'{STIKERS[current.cards[i + 1]]}')
            btn3 = types.KeyboardButton(f'{STIKERS[current.cards[i + 2]]}')
            keyboard.row(btn1, btn2, btn3)
        if ost == 1:
            keyboard.add(types.KeyboardButton(f'{STIKERS[current.cards[-1]]}'))
        elif ost == 2:
            btn1 = types.KeyboardButton(f'{STIKERS[current.cards[-1]]}')
            btn2 = types.KeyboardButton(f'{STIKERS[current.cards[-2]]}')
            keyboard.row(btn1, btn2)
        if game.current_card_value != "":
            await bot.send_message(call.message.chat.id,
                                   f'Добавь еще {More_value(game.current_card_value)}. Максимум можно выбрать {min(4, len(current.cards))} карты',
                                   reply_markup=keyboard)
        else:
            await bot.send_message(call.message.chat.id,
                                   f'Выбери карты. Максимум можно выбрать {min(4, len(current.cards))} карты',
                                   reply_markup=keyboard)
        game.message_sent = call.message


@bot.message_handler(content_types=['text'])
async def message_reply(message):
    markup_reply = types.ReplyKeyboardRemove()
    game = manager.user_game[message.from_user.id]
    # для таймаутов
    if game is not None and game.is_game_open:
        game.message_check = True
    # для таймаутов
    if game.is_game_open:
        current = manager.players_ids[message.from_user.id]
        if current.view_cards and message.text == 'Закончить просмотр':
            await bot.send_message(message.chat.id, 'Отлично!', reply_markup=markup_reply)
            current.view_cards = False
        elif current.view_cards and message.text != 'Закончить просмотр':
            await bot.send_message(message.chat.id, 'Здесь вы не можете выбирать карты', reply_markup=markup_reply)
            current.view_cards = False
        elif message.from_user.id == game.players_in_game[
            game.cur_player - 1].id and message.text in INVERSE_STIKERS.keys() and \
                INVERSE_STIKERS[message.text] in game.players_in_game[game.cur_player - 1].cards:
            game.players_in_game[game.cur_player - 1].current_cards.append(INVERSE_STIKERS[message.text])
            game.players_in_game[game.cur_player - 1].cards.remove(INVERSE_STIKERS[message.text])
            if len(game.players_in_game[game.cur_player - 1].current_cards) == 4 or len(
                    game.players_in_game[game.cur_player - 1].cards) == 0:
                if game.current_card_value != "":
                    await bot.send_message(message.chat.id, 'Хорошо! Выбор окончен', reply_markup=markup_reply)
                    game.previous_cards = game.players_in_game[game.cur_player - 1].current_cards.copy()
                    await bot.send_message(message.chat.id,
                                           f'Хорошо! Я скажу остальным игрокам, что вы положили еще {refactor(len(game.previous_cards), game.current_card_value)}',
                                           reply_markup=markup_reply)
                    game.is_add_previous_player = True
                    game.players_in_game[game.cur_player - 1].current_cards.clear()

                    await bot.delete_message(message.chat.id, game.message_sent.message_id)

                    for card in game.previous_cards:
                        game.cards_in_game.append(card)
                    await update_current_player(game)
                    await new_step(game)
                else:
                    await bot.send_message(message.chat.id, 'Хорошо! Выбор окончен', reply_markup=markup_reply)
                    game.previous_cards = game.players_in_game[game.cur_player - 1].current_cards.copy()
                    game.players_in_game[game.cur_player - 1].current_cards.clear()
                    await do_a_bid(game)
                    game.is_add_previous_player = False

                    await bot.delete_message(message.chat.id, game.message_sent.message_id)

            else:
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
                keyboard.add(types.KeyboardButton('Закончить выбор'))
                current = game.players_in_game[game.cur_player - 1]
                ost = len(current.cards) % 3
                current.cards.sort()
                for i in range(0, len(current.cards) - ost, 3):
                    btn1 = types.KeyboardButton(f'{STIKERS[current.cards[i]]}')
                    btn2 = types.KeyboardButton(f'{STIKERS[current.cards[i + 1]]}')
                    btn3 = types.KeyboardButton(f'{STIKERS[current.cards[i + 2]]}')
                    keyboard.row(btn1, btn2, btn3)
                if ost == 1:
                    keyboard.add(types.KeyboardButton(f'{STIKERS[current.cards[-1]]}'))
                elif ost == 2:
                    btn1 = types.KeyboardButton(f'{STIKERS[current.cards[-1]]}')
                    btn2 = types.KeyboardButton(f'{STIKERS[current.cards[-2]]}')
                    keyboard.row(btn1, btn2)
                await bot.send_message(message.chat.id,
                                       f'Еще можно выбрать {min(len(current.cards), 4 - len(game.players_in_game[game.cur_player - 1].current_cards))}x🃏',
                                       reply_markup=keyboard)

        elif message.from_user.id == game.players_in_game[game.cur_player - 1].id and \
                message.text == 'Закончить выбор' and game.current_card_value == "":
            await bot.send_message(message.chat.id, 'Хорошо! Выбор окончен', reply_markup=markup_reply)
            game.previous_cards = game.players_in_game[game.cur_player - 1].current_cards.copy()
            game.players_in_game[game.cur_player - 1].current_cards.clear()

            await bot.delete_message(message.chat.id, game.message_sent.message_id)

            await do_a_bid(game)

        elif message.from_user.id == game.players_in_game[game.cur_player - 1].id and \
                message.text == 'Закончить выбор' and game.current_card_value != "":
            await bot.send_message(message.chat.id, 'Хорошо! Выбор окончен', reply_markup=markup_reply)
            game.previous_cards = game.players_in_game[game.cur_player - 1].current_cards.copy()
            await bot.send_message(message.chat.id,
                                   f'Хорошо! Я скажу остальным игрокам, что вы пололожили еще '
                                   f'{refactor(len(game.previous_cards), game.current_card_value)}',
                                   reply_markup=markup_reply)

            await bot.delete_message(message.chat.id, game.message_sent.message_id)

            game.is_add_previous_player = True
            game.players_in_game[game.cur_player - 1].current_cards.clear()
            for card in game.previous_cards:
                game.cards_in_game.append(card)
            await update_current_player(game)
            await new_step(game)
        elif message.from_user.id == game.players_in_game[game.cur_player - 1].id and message.text in VALUES:
            game.current_card_value = message.text
            await bot.send_message(message.chat.id,
                                   f'Хорошо! Я скажу остальным игрокам, что вы положили '
                                   f'{refactor(len(game.previous_cards), message.text)}',
                                   reply_markup=markup_reply)
            game.is_add_previous_player = False
            for card in game.previous_cards:
                game.cards_in_game.append(card)
            await update_current_player(game)
            await new_step(game)
        else:
            await bot.send_message(message.from_user.id, text=f'Не ваш ход', reply_markup=markup_reply)


async def do_a_bid(game):
    cur_player = game.players_in_game[game.cur_player - 1]
    count_of_bid = len(game.previous_cards)

    await bot.send_message(cur_player.id,
                           f'Вы хотите сказать другим игрокам что ваши 🃏x{refactor(count_of_bid, "карта")} какого номинала?',
                           reply_markup=make_markup_bid())


async def send_info_about_game(game, chat_id, player):
    num_of_players = len(game.players_in_game)
    number_of_player = player.number
    await bot.send_message(chat_id,
                           f"В игре принимает участие {num_of_players} игроков, ваш номер в данной игре {number_of_player}")


async def new_step(game):
    # pl делает ход
    # остальным присылается инфа об предыдущем ходе ходе
    cur = game.players_in_game[game.cur_player - 1]
    if len(cur.cards) == 0 and len(game.cards_in_game) == 0:
        game.is_game_open = False
    markup_other = types.InlineKeyboardMarkup()
    for other_pl in game.players_in_game:
        if other_pl.number != game.prev_player:
            if len(game.cards_in_game) != 0 and game.is_add_previous_player:
                await bot.send_message(other_pl.chat_id,
                                       text=f'Игрок {game.prev_player} положил еще {refactor(len(game.previous_cards), game.current_card_value)}',
                                       reply_markup=markup_other)
            elif len(game.cards_in_game) != 0:
                await bot.send_message(other_pl.chat_id,
                                       text=f'Игрок {game.prev_player} положил {refactor(len(game.previous_cards), game.current_card_value)}',
                                       reply_markup=markup_other)
        await take_photo_of_the_field(game, other_pl, game.cur_player, game.prev_player, False, True)
    if len(cur.cards) == 0 and len(game.cards_in_game) == 0:
        for pl in game.players_in_game:
            if pl.id != cur.id:
                await bot.send_message(pl.id, text=f'Игрок {cur.number} победил! Игра окончена')
        await bot.send_message(cur.id, text=f'Поздравляем! Вы победили! Игра окончена')
        clear_data(game, cur)
    elif len(cur.cards) == 0 and len(game.cards_in_game) != 0:
        await options_if_end(game, cur.id)
    elif len(cur.cards) != 0 and len(game.cards_in_game) == 0:
        markup = types.InlineKeyboardMarkup(row_width=1)
        make_choice_btn = types.InlineKeyboardButton(text='⬇️ Выбрать карты ⬇️', callback_data="cards")
        markup.add(make_choice_btn)
        const = await bot.send_message(cur.id, f'Игрок {cur.number}, сделай ставку:',
                               reply_markup=markup)
        game.message_sent = const
    else:
        await options(game, cur.id)


async def options(game, player_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_look_at_the_cards = types.InlineKeyboardButton(text=f"Посмотреть на карты",
                                                       callback_data="view_cards")
    btn_make_choice = types.InlineKeyboardButton(text=f"Добавить еще {More_value(game.current_card_value)}",
                                                 callback_data="cards")

    btn_believe = types.InlineKeyboardButton(text="Верю", callback_data="believe")
    btn_not_believe = types.InlineKeyboardButton(text="Не верю", callback_data="not_believe")
    markup.add(btn_look_at_the_cards, btn_make_choice, btn_believe, btn_not_believe)
    const = await bot.send_message(player_id, f"Игрок {game.cur_player} сделай ход:", reply_markup=markup)

    game.message_sent = const


async def options_if_end(game, player_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_believe = types.InlineKeyboardButton(text="Верю", callback_data="believe")
    btn_not_believe = types.InlineKeyboardButton(text="Не верю", callback_data="not_believe")
    markup.add(btn_believe, btn_not_believe)
    const = await bot.send_message(player_id, f"Игрок {game.cur_player} сделай ход:", reply_markup=markup)

    game.message_sent = const


async def hand_out_cards(game, player):
    if game.number_of_card_for_each < game.not_used < game.number_of_card_for_each * 2:
        k = game.not_used
    else:
        k = game.number_of_card_for_each

    if len(game.available) != 0:
        for i in range(k):
            sz = random.randint(0, len(game.available) - 1)
            player.cards.append(game.available[sz])
            game.available.pop(sz)

        game.not_used -= k


async def update_current_player(game):
    if game.cur_player >= len(game.players_in_game):
        game.cur_player = 1
        game.prev_player = len(game.players_in_game)
    else:
        game.prev_player = game.cur_player
        game.cur_player += 1


def clear_data(game, player):
    now = datetime.now()
    game.game_time = now - game.game_time

    time = game.game_time.seconds

    for pl in game.players_in_game:
        pl.cards.clear()
        pl.num_of_games += 1
        pl.finding_game = False

        user = User.query.filter_by(id=pl.id).first()
        if not user:
            user = User(id=int(pl.id), num_of_games=pl.num_of_games, num_of_wins=pl.num_of_wins)

            session.add(user)
        else:
            user.num_of_wins = pl.num_of_wins
            user.num_of_games = pl.num_of_games

    if player is not None:
        player.num_of_wins += 1

        game = Game(num_of_players=int(game.players_cnt - 1), winner_id=int(player.id), duration_of_game =int(time))

        session.add(game)

        user = User.query.filter_by(id=player.id).first()
        user.num_of_wins = player.num_of_wins
        user.num_of_games = player.num_of_games
    else:
        game = Game(num_of_players=int(game.players_cnt - 1), winner_id=int(0), duration_of_game=int(time))

        session.add(game)

    try:
        session.commit()
        return True
    except IntegrityError:
        session.rollback()  # откатываем session.add(user)
        return False
