from telebot import types


def make_markup_bid():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    btn1 = types.KeyboardButton('Туз')
    btn2 = types.KeyboardButton('Король')
    btn3 = types.KeyboardButton('Дама')
    btn4 = types.KeyboardButton('Валет')
    btn5 = types.KeyboardButton('10')
    btn6 = types.KeyboardButton('9')
    btn7 = types.KeyboardButton('8')
    btn8 = types.KeyboardButton('7')
    btn9 = types.KeyboardButton('6')
    btn10 = types.KeyboardButton('5')
    btn11 = types.KeyboardButton('4')
    btn12 = types.KeyboardButton('3')
    btn13 = types.KeyboardButton('2')
    keyboard.row(btn1, btn2, btn3, btn4)
    keyboard.row(btn5, btn6, btn7, btn8)
    keyboard.row(btn9, btn10, btn11, btn12, btn13)
    return keyboard


def refactor(number, suit):
    if suit == 'Дама':
        if number % 10 == 1:
            return f'{number} даму'
        else:
            return f'{number} дамы'
    elif suit == 'Король':
        return f'{number} короля'
    elif suit == 'Валет':
        return f'{number} вальта'
    elif suit == 'Туз':
        if number % 10 == 1:
            return f'{number} туз'
        else:
            return f'{number} туза'
    elif suit == '10':
        if number % 10 == 1:
            return f'{number} десятку'
        else:
            return f'{number} десятки'
    elif suit == '9':
        if number % 10 == 1:
            return f'{number} девятку'
        else:
            return f'{number} девятки'
    elif suit == '8':
        if number % 10 == 1:
            return f'{number} восьмерку'
        else:
            return f'{number} восьмерки'
    elif suit == '7':
        if number % 10 == 1:
            return f'{number} семерку'
        else:
            return f'{number} семерки'
    elif suit == '6':
        if number % 10 == 1:
            return f'{number} шестерку'
        else:
            return f'{number} шестерки'
    elif suit == '5':
        if number % 10 == 1:
            return f'{number} пятерку'
        else:
            return f'{number} пятерки'
    elif suit == '4':
        if number % 10 == 1:
            return f'{number} четверку'
        else:
            return f'{number} четверки'
    elif suit == '3':
        if number % 10 == 1:
            return f'{number} тройку'
        else:
            return f'{number} тройки'
    elif suit == '2':
        if number % 10 == 1:
            return f'{number} двойку'
        else:
            return f'{number} двойки'
    elif suit == 'карта':
        if number % 10 == 1 and number // 10 != 1:
            return f'{number} карта'
        elif 2 <= number % 10 <= 4 and number // 10 != 1:
            return f'{number} карты'
        else:
            return f'{number} карт'


def More_value(suit):
    if suit == 'Дама':
        return "дам"
    elif suit == 'Король':
        return 'королей'
    elif suit == 'Валет':
        return 'вальтов'
    elif suit == 'Туз':
        return 'тузов'
    elif suit == '10':
        return 'десяток'
    elif suit == '9':
        return 'девяток'
    elif suit == '8':
        return 'восьмерок'
    elif suit == '7':
        return 'семерок'
    elif suit == '6':
        return 'шестерок'
    elif suit == '5':
        return 'пятерок'
    elif suit == '4':
        return 'четверок'
    elif suit == '3':
        return 'троек'
    elif suit == '2':
        return 'двоек'