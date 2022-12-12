from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from constants import *
from main import bot
from modules import Game, Player

with Image.open("./cards/cell.png") as im_cell:
    x, y = im_cell.size
dx = x // 10
dy = y // 3


def field_sides():
    return (x + dx) * 4 + 4 * y, 6 * dy + 4 * y


def card_position_at_field(i, len):
    if (len > 24):
        j = i % 8
        i = i // 8
        return j * (x + dx) + x // 2 + dx, i * dy + 6 * dy + 4 * y - y - 3 * dy
    elif (16 < len <= 24):
        j = i % 6
        i = i // 6
        return j * (x + dx) + x // 2 + x + dx, i * dy + 6 * dy + 4 * y - y - 3 * dy
    else:
        j = i % 4
        i = i // 4
        return j * (x + dx) + 2 * y, i * dy + 6 * dy + 4 * y - y - 3 * dy


def card_position_of_bid(i, flag):
    return i * (x + dx) + 2 * y + flag * (x + dx), 2 * dy + y + y // 2


def get_ind(count_pl, index, flag=0):
    if count_pl == 2:
        return ((x + dx) * 4 + 4 * y - x) // 2 + flag * (x + dx) - 2 * dx, 0
    if count_pl == 3:
        if index == 1:
            return dx + flag * (x + dx), (6 * dy + 4 * y - y) // 2
        else:
            return (x + dx) * 4 + 4 * y - x - dx - flag * (x + dx), (6 * dy + 4 * y - y) // 2
    if count_pl == 4:
        if index == 1:
            return dx + flag * (x + dx), (6 * dy + 4 * y - y) // 2
        elif index == 2:
            return ((x + dx) * 4 + 4 * y - x) // 2 - x // 2 + flag * (x + dx), 0
        else:
            return (x + dx) * 4 + 4 * y - x - dx - flag * (x + dx), (6 * dy + 4 * y - y) // 2

    if count_pl == 5:
        if index == 1:
            return dx + flag * (x + dx), (6 * dy + 4 * y - y) // 2
        elif index == 2:
            return ((x + dx) * 4 + 4 * y - 2 * (x + dx)) // 3 - x // 2 + flag * (x + dx), 0
        elif index == 3:
            return 2 * ((x + dx) * 4 + 4 * y - 2 * (x + dx)) // 3 - x // 2 + (x + dx) + flag * (x + dx), 0
        else:
            return (x + dx) * 4 + 4 * y - x - dx - flag * (x + dx), (6 * dy + 4 * y - y) // 2
    if count_pl == 6:
        if index == 1:
            return dx + flag * (x + dx), (6 * dy + 4 * y - y) // 2
        elif index == 2:
            return ((x + dx) * 4 + 4 * y - 3 * x) // 4 - x // 2 + flag * (x + dx), 0
        elif index == 3:
            return 2 * ((x + dx) * 4 + 4 * y - 3 * x) // 4 + (x + dx) - x // 2 + flag * (x + dx), 0
        elif index == 4:
            return 3 * ((x + dx) * 4 + 4 * y - 3 * x) // 4 + 2 * (x + dx) - x // 2 + flag * (x + dx), 0
        else:
            return (x + dx) * 4 + 4 * y - x - dx - flag * (x + dx), (6 * dy + 4 * y - y) // 2


async def take_photo_of_the_field(game: Game, player: Player, cur, prev, believe, new_step):
    with Image.new('RGB', field_sides(),
                   (22, 132, 66)) as new_im:
        index = 1
        for i in range(player.number + 1, len(game.players_in_game) + 1):
            with Image.open("./cards/user_{}.png".format(i)) as im:
                new_im.paste(im, get_ind(len(game.players_in_game), index, 0))
            with Image.open("./cards/cell_{}.png".format(len(game.players_in_game[i - 1].cards))) as im:
                new_im.paste(im, get_ind(len(game.players_in_game), index, 1))
            index += 1
        for i in range(1, player.number):
            with Image.open("./cards/user_{}.png".format(i)) as im:
                new_im.paste(im, get_ind(len(game.players_in_game), index, 0))
            with Image.open("./cards/cell_{}.png".format(len(game.players_in_game[i - 1].cards))) as im:
                new_im.paste(im, get_ind(len(game.players_in_game), index, 1))
            index += 1
        # отрисовка твоих карт
        player.cards.sort()
        if (len(player.cards) <= 32):
            for i in range(len(player.cards)):
                current_card = player.cards[i]
                with Image.open("./cards/{}.png".format(
                        SUITS_STR[current_card])) as im:
                    new_im.paste(im, card_position_at_field(i, len(player.cards)))
        else:
            with Image.open("./cards/cell_{}.png".format(len(player.cards))) as im:
                new_im.paste(im, (((x + dx) * 4 + 4 * y) // 2 - x // 2, 5 * dy + 3 * y))
        with Image.open("./cards/your_cards.png") as im:
            new_im.paste(im, (x + dx + 2 * y, 6 * dy + 4 * y - y - 4 * dy))
        if new_step:
            if game.is_game_open:
                with Image.open(f"./cards/step_user_{game.cur_player}.png") as im:
                    new_im.paste(im, (2 * y + x, (6 * dy + 4 * y - y) // 2 - y))
                # тут про ход текущего игрока
            if game.current_card_value != "" and len(game.cards_in_game) > 0:
                with Image.open("./cards/{}.png".format(
                        ITEMS[game.current_card_value])) as im:
                    new_im.paste(im, card_position_of_bid(0, 1))
                with Image.open("./cards/cell_{}.png".format(len(game.cards_in_game))) as im:
                    new_im.paste(im, card_position_of_bid(1, 1))
        else:
            if believe:
                with Image.new('RGB', (350, 35), (22, 132, 66)) as img:
                    draw = ImageDraw.Draw(img)
                    font = ImageFont.truetype("./cards/arial.ttf", 25)
                    draw.text((0, 0), f"Игрок {cur} поверил игроку {prev}", (0, 0, 0), font=font)
                    new_im.paste(img, (2 * y, (6 * dy + 4 * y - y) // 2 - y))
            else:
                with Image.new('RGB', (350, 35), (22, 132, 66)) as img:
                    draw = ImageDraw.Draw(img)
                    font = ImageFont.truetype("./cards/arial.ttf", 25)
                    draw.text((0, 0), f"Игрок {cur} не поверил игроку {prev}", (0, 0, 0), font=font)
                    new_im.paste(img, (2 * y, (6 * dy + 4 * y - y) // 2 - y))

            for i in range(len(game.previous_cards)):
                current_card = game.previous_cards[i]
                with Image.open("./cards/{}.png".format(
                        SUITS_STR[current_card])) as im:
                    new_im.paste(im, card_position_of_bid(i, 0))
    await bot.send_photo(player.id, photo=new_im)
