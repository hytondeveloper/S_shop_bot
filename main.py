import asyncio
import logging
import os
import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from DataBase import Data_base_users, Data_base_models, Newsletter
from DataBase.private import Token, Admins, Abs_path
from Functions import Check_dir


bot_token = Token.BOT_TOKEN # Создаем экземпляры бота и диспетчера
bot = Bot(token=bot_token)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

abs_path = Abs_path.abs_path # Путь к папкам, где лежат фото
abs_path_database_data = Abs_path.abs_path_database_data # Путь к базе данных пользователей и моделей кроссовок

logging.basicConfig(level=logging.INFO) # Настраиваем логгирование

########################################################################################################################
# Обработчик временных сообщений:
class YourStateMachine(StatesGroup):
    waiting_for_message = State() # Форма заказа для отправки админу
    awaiting_promo_code = State() # Промокод для отправки админу
    waiting_for_manager_message = State() # Сообщение для отправки админу
    waiting_for_message_newsletter = State() # Сообщение для рассылки по БД

########################################################################################################################
# # Функция для сброса состояния
# async def reset_state(state: FSMContext):
#     await state.finish()


########################################################################################################################
# Клавиатура создаваемая при вызове /start или 'Главное меню'
async def create_keyboard():
    keyboard = types.InlineKeyboardMarkup()

    buttons_one = [
        types.InlineKeyboardButton(text='🏷️промокод🏷️', callback_data='promo'),
        types.InlineKeyboardButton(text='🧑‍💻МЕНЕДЖЕР🧑‍💻', callback_data='manager')
    ]
    buttons_two = [
        types.InlineKeyboardButton(text='📝отзывы📝', callback_data='reviews'),
        types.InlineKeyboardButton(text='📢Информация📢', callback_data='info')
    ]

    button_catalog = types.InlineKeyboardButton(text='🛒 🛒 KATAЛOГ 🛒 🛒', callback_data='catalog')

    keyboard.add(*buttons_one)
    keyboard.add(*buttons_two)
    keyboard.add(button_catalog)
    return keyboard

########################################################################################################################
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    print(message.from_user.id)
    user_name = message.from_user.username
    current_date = datetime.date.today()

    #
    status = await Data_base_users.DB_add_user(abs_path_database_data, message.from_user.id, current_date, user_name)
    if status == True:
        keyboard = await create_keyboard()
        if message.from_user.id == Admins.admin_id:
            # Создать и отправить кнопку для админа
            admin_keyboard = types.InlineKeyboardMarkup()
            refresh_button = types.InlineKeyboardButton(text='Обновить 🔧 БД', callback_data='admin_panel')
            newsletter_button = types.InlineKeyboardButton(text='Рассылка по БД', callback_data='newsletter')
            admin_keyboard.add(refresh_button, newsletter_button)
            keyboard.add(refresh_button, newsletter_button)  # Добавляем кнопку админ-панели к основной клавиатуре

        await message.answer(f'*{message.from_user.first_name}*  🤝  🏪'
                             f'\n🧔🏽‍♂️💬'
                             f'\nРады приветствовать Bас в нашем виртуальном мире моды и стиля, где Вы сможете'
                             f' обновить свою обувную коллекцию и подчеркнуть свою уникальность.'
                             f'\n             👉 *Для* 👈'
                             f'\n*просмотра ассортимента*'
                             f'\n   👇      *нажмите на*     👇'
                             f'\n   🛒 🛒 *KATAЛOГ* 🛒 🛒'
                             f'\n'
                             f'\nДля обращения в службу поддержки магазина, воспользуйтесь кнопкой↩️'
                             f'\n🧑‍💻*МЕНЕДЖЕР*🧑‍💻', reply_markup=keyboard, parse_mode='Markdown')
    # print(message.from_user.id)
    else:
        await message.answer(f'👻')


########################################################################################################################
# # # # # # # # # # # # # # # # # # # # # # # # # # АДМИН ПАНЕЛЬ # # # # # # # # # # # # # # # # # # # # # # # # # # # #
########################################################################################################################
# Кнопка 'Обновить 🔧 БД'
@dp.callback_query_handler(lambda query: query.data == 'admin_panel')
async def admin_panel_button(query: types.CallbackQuery):
    # Отправляем сообщение "Обновление базы данных..."
    await query.answer('Обновление базы данных...')

    global abs_path_database_data # Путь к БД обуви
    all_models_in_bd = await Data_base_models.get_all_models(abs_path_database_data)  # Все модели находящиеся в БД
    # print(f'было (находящиеся в БД)={all_models_in_bd}')

    global abs_path # Путь к папкам с фото
    all_models_in_dir = await Check_dir.get_folders_with_photos(abs_path) # Всё модели в фотографиях

    # Удалите элементы из all_models_in_bd(базаданных), которых нет в all_models_in_dir(фотографии)
    all_models_in_bd = [item for item in all_models_in_bd if item in all_models_in_dir]
    # Добавьте элементы из all_models_in_dir(фотографии), которых нет в all_models_in_bd(база данных)
    all_models_in_bd.extend(item for item in all_models_in_dir if item not in all_models_in_bd)
    # Добавление в БД
    text_for_unswer = await Data_base_models.add_models_to_db(abs_path_database_data, all_models_in_bd)

    # # Удаление предыдущей клавиатуры (reply_markup=None)
    # await query.message.edit_reply_markup(reply_markup=None)
    # Удаляем предыдущее сообщение
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)

    keyboard = await create_keyboard()

    # Отправляем сообщение о завершении операции
    await query.message.answer(text_for_unswer, reply_markup=keyboard)


########################################################################################################################
# Кнопка 'Рассылка по БД'
@dp.callback_query_handler(lambda query: query.data == 'newsletter')
async def newsletter_button(query: types.CallbackQuery, state: FSMContext):
    # Создаю кнопку 'отменить'
    cancel_keyboard = types.InlineKeyboardMarkup()
    cancel_button = types.InlineKeyboardButton("Отменить", callback_data="cancel")
    cancel_keyboard.add(cancel_button)

    await bot.send_message(query.from_user.id, f"Напишите текст для рассылки:"
                                               "\n\nВы можете отменить текущий запрос, нажав на кнопку 'Отменить'.",
                           parse_mode='Markdown',
                           reply_markup=cancel_keyboard)
    # messege_id_for_delete = query.message.message_id
    # chat_id_for_delete = query.message.chat.id
    # print(query.message.message_id)
    # print(cancel_button.callback_data)

    # Сохраняем данные в state
    await state.update_data(
        message_id_for_delete=query.message.message_id,
        chat_id_for_delete=query.message.chat.id
    )
    await YourStateMachine.waiting_for_message_newsletter.set()


@dp.message_handler(state=YourStateMachine.waiting_for_message_newsletter)
async def process_manager_message(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = message.text

    global abs_path_database_data
    await Newsletter.send_newsletter_to_all_users(abs_path_database_data, message.text)

    # Получаем данные из state
    state_data = await state.get_data()
    # message_id_for_delete = state_data.get('message_id_for_delete')
    # chat_id_for_delete = state_data.get('chat_id_for_delete')
    # print(message_id_for_delete, chat_id_for_delete)
    # # Удаляем все предыдущие сообщения и кнопки администратора
    # await bot.delete_message(chat_id=chat_id_for_delete, message_id=message_id_for_delete)

    await message.answer("Рассылка выполнена успешно")
    await state.finish()


########################################################################################################################
########################################################################################################################

# Обработчик для кнопки 'Заказать'
@dp.callback_query_handler(lambda query: query.data == 'order')
async def handle_order_button(query: types.CallbackQuery, state: FSMContext):
    # print(query.from_user)
    # user_id = query.from_user.id
    # user_name = query.from_user.username

    # Удаление предыдущей клавиатуры (reply_markup=None)
    await query.message.edit_reply_markup(reply_markup=None)

    user_choice_model = query.message.caption
    await state.update_data(user_choice_model=user_choice_model)
    # Создаю кнопку 'отменить'
    cancel_keyboard = types.InlineKeyboardMarkup()
    cancel_button = types.InlineKeyboardButton("Отменить", callback_data="cancel")
    cancel_keyboard.add(cancel_button)

    # print('user_id =', user_id, '\nuser_name = ', user_name, '\nподпись фотки =', user_choice_model)

    await bot.send_message(query.from_user.id, f"{query.from_user.first_name} ➡️ напишите текстом:"
                                               f"\n\n*1)*🦶Kакой размер вам нужен*?*"
                                               f"\n\n*2)*🚚Какой тип доставики*?*"
                                               f"\n📦Европочта:"
                                               "\n   📌Номер отделения европочты↙️"
                                               "\n                  _ИЛИ_"
                                               "\n📯Белпочта:"
                                               "\n   📌Полный адрес доставки c почтовым индексом↙️"
                                               "\n                  _ИЛИ_"
                                               "\n🚶🏼Самовывоз"
                                               "\n\n*3)* 👤 ФИО"
                                               "\n\n*4)* 📞 Контактный номер телефона"
                                               "\n\nВы можете отменить текущий запрос, нажав на кнопку 'Отменить'.",
                           parse_mode='Markdown',
                           reply_markup=cancel_keyboard)

    await YourStateMachine.waiting_for_message.set()


@dp.message_handler(state=YourStateMachine.waiting_for_message)
async def process_order_message(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = message.text
        user_choice_model = data['user_choice_model']

    admin_id = Admins.admin_id
    admin_message = f"Пользователь ➡️ `{message.from_user.username}` \nID:(*{message.from_user.id}*)\n*{message.from_user.first_name} {message.from_user.last_name}*\n" \
                    f"Хочет заказать :\n{user_choice_model}\n\n{message.text}\n\n🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩"

    await bot.send_message(admin_id, admin_message, parse_mode='Markdown')
    await state.finish()

    keyboard = await create_keyboard()
    await message.answer("Ваш заказ был принят🛒\nЖдите ответа, Вам ответит наш менеджер📲", reply_markup=keyboard,
                         parse_mode='Markdown')




########################################################################################################################
# Обработчик для кнопки 'Менеджер' (отправка сообщения adminy)
@dp.callback_query_handler(lambda query: query.data == 'manager')
async def contact_manager_handler(query: types.CallbackQuery):
    # Удаление предыдущей клавиатуры (reply_markup=None)
    await query.message.edit_reply_markup(reply_markup=None)



    # Создаю кнопку 'отменить'
    cancel_keyboard = types.InlineKeyboardMarkup()
    cancel_button = types.InlineKeyboardButton("Отменить", callback_data="cancel")
    cancel_keyboard.add(cancel_button)

    await bot.send_message(query.from_user.id, "🖊Напишите сообщение для отправки администратору:",
                           reply_markup=cancel_keyboard)
    await YourStateMachine.waiting_for_manager_message.set()
    # Удаляем предыдущее сообщение
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)


@dp.message_handler(state=YourStateMachine.waiting_for_manager_message)
async def process_manager_message(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = message.text

    admin_id = Admins.admin_id
    admin_message = (f"Username➡️`{message.from_user.username}`\n(ID:*{message.from_user.id}*)\n"
                     f"*{message.from_user.first_name} {message.from_user.last_name}*:\n\n{message.text}")

    await bot.send_message(admin_id, f'{admin_message}\n\n🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥', parse_mode='Markdown')
    keyboard = await create_keyboard()
    await message.answer("Сообщение отправлено администратору📨\n⏳Ожидайте ответа⏳", reply_markup=keyboard)
    await state.finish()



########################################################################################################################
# Обработчик для кнопки 'Есть промокод?'
@dp.callback_query_handler(lambda query: query.data == 'promo')
async def handle_promo_button(query: types.CallbackQuery):
    # Удаляем предыдущее сообщение
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
    await asyncio.sleep(2) # Замедляю программу, что бы не баловались с этой кнопкой
    user_id = query.from_user.id
    keyboard = await create_keyboard() # Кнопки главного меню
    await bot.send_message(chat_id=user_id,
                           text=f'Мы промо-коды ещё не выпускали! Что ты балуешься? 🤪\n\n🔙 *Возвращаемся...* 🔙'
                                f'\n🏠*В ГЛАВНОЕ МЕНЮ*🏠\n*Для просмотра ассортимента*'
                                f'\n👇 *нажмите на* 👇\n🛒 🛒 *KATAЛOГ* 🛒 🛒',
                           reply_markup=keyboard, parse_mode='Markdown')



########################################################################################################################
# Обработчик для кнопки 'отменить'
# @dp.callback_query_handler(lambda query: query.data == 'cancel', state=YourStateMachine.waiting_for_message)
@dp.callback_query_handler(lambda query: query.data == 'cancel', state=YourStateMachine.waiting_for_message)
@dp.callback_query_handler(lambda query: query.data == 'cancel', state=YourStateMachine.awaiting_promo_code)
@dp.callback_query_handler(lambda query: query.data == 'cancel', state=YourStateMachine.waiting_for_manager_message)
async def cancel_order(query: types.CallbackQuery, state: FSMContext):


    await bot.send_message(query.from_user.id, "Запрос отменен.")
    await state.finish()  # Сброс состояния
    # Главное меню
    await handle_main_menu_button(query)
########################################################################################################################

# @dp.callback_query_handler(lambda query: query.data == 'promo')
# async def handle_promo_button(query: types.CallbackQuery):
#     # Удаление предыдущей клавиатуры (reply_markup=None)
#     await query.message.edit_reply_markup(reply_markup=None)
#
#     text = '*Введите ваш промо код:*'
#     await bot.send_message(chat_id=query.from_user.id, text=text, parse_mode='Markdown')
#     # Установка состояния активной кнопки для пользователя
#     # await dp.bot.send_message(chat_id=query.from_user.id, text='Кнопка promo активна')
#     # Устанавливаем состояние пользователя для ожидания промо кода
#     await YourStateMachine.awaiting_promo_code.set()
#
#
# #############
# # Обработчик текстовых сообщений
# @dp.message_handler(state=YourStateMachine.awaiting_promo_code)
# async def handle_text(message: types.Message, state: FSMContext):
#     user_text = message.text
#     user_id = message.from_user.id
#     keyboard = await create_keyboard() # Кнопки главного меню
#
#     # !! ЗДЕСЬ НАПИСАТЬ ДЕЙСТВИЯ ПО ПРОМО-КОДУ
#     # * ПРОВЕРКА В БД НА НАЛИЧИЕ ПРОМОКОДА
#     # * ОТВЕТ ПОЛЬЗОВАТЕЛЮ НА ПРОМО-КОД
#     # * ПЕРЕСЧЁТ ВСЕХ ЦЕН ОТТАЛКИВАЯСЬ ОТ ПРОМО КОДА
#
#     # Ваш код обработки промо кода
#     await bot.send_message(chat_id=user_id,
#                            text=f'*ВАШ ПРОМО-КОД➡️*  _{user_text}_\n\n🔙 *Возвращаемся...* 🔙\n🏠*В ГЛАВНОЕ МЕНЮ*🏠\n*Для просмотра ассортимента*\n'
#                                 f'👇 *нажими на* 👇\n🛒 🛒 KATAЛOГ 🛒 🛒',
#                            reply_markup=keyboard, parse_mode='Markdown')
#
#     # Сбрасываем состояние пользователя
#     await state.finish()


########################################################################################################################
# Обработчик других текстовых сообщений
@dp.message_handler()
async def handle_other_text(message: types.Message):
    user_id = message.from_user.id
    # Ваш код обработки других текстовых сообщений
    await bot.send_message(chat_id=user_id, text='Пишите только тогда, когда я Вас этого попрошу 🙅🏽'
                                                 '\nТорможу бота на 3 сек 🐢'
                                                 '\nВ следующий раз-поставлю в угол 🙇')
    await asyncio.sleep(3) # Замедляю программу, что бы не баловались с этой кнопкой



########################################################################################################################
# Кнопка 'Отзывы'
@dp.callback_query_handler(lambda query: query.data == 'reviews')
async def handle_reviews_button(query: types.CallbackQuery):
    # Удаление предыдущей клавиатуры (reply_markup=None)
    await query.message.edit_reply_markup(reply_markup=None)
    keyboard = await create_keyboard()
    text = f'https://t.me/+8dayy7BPUZ4xYjVi'
    await query.message.answer(text, parse_mode='Markdown', reply_markup=keyboard)



########################################################################################################################
# Кнопка 'Информация'
@dp.callback_query_handler(lambda query: query.data == 'info')
async def handle_info_button(query: types.CallbackQuery):
    # Удаление предыдущей клавиатуры (reply_markup=None)
    await query.message.edit_reply_markup(reply_markup=None)
    keyboard = await create_keyboard()
    text = 'https://t.me/+SBzb11TDgnNlMjRi'
    await query.message.answer(text, reply_markup=keyboard, parse_mode='Markdown')



########################################################################################################################
# Кнопка 'Каталог'
@dp.callback_query_handler(lambda query: query.data == 'catalog')
async def handle_catalog_button(query: types.CallbackQuery):

    global abs_path
    folders = os.listdir(abs_path)  # Получаем список подпапок

    # Удаление предыдущей клавиатуры (reply_markup=None)
    await query.message.edit_reply_markup(reply_markup=None)

    # Удаляем предыдущее сообщение
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)

    keyboard = types.InlineKeyboardMarkup()
    for folder in folders:
        callback_data = f'gender_{folder}'
        keyboard.row(types.InlineKeyboardButton(text=folder, callback_data=callback_data))
    keyboard.add(types.InlineKeyboardButton(text='↩️Главное меню↩️', callback_data='main_menu'))
    await query.message.answer('Выберите категорию:👇', reply_markup=keyboard)



########################################################################################################################
# Кнопки папок (уже нажал): Муж. Жен. Дет.
@dp.callback_query_handler(lambda query: query.data.startswith('gender_'))
async def handle_folder_selection(query: types.CallbackQuery):

    global abs_path
    user_data = query.data # gender_ИпяПапки

    path = user_data.split('_') # разделяю данные по _ , что бы получить имя выбранной папки (Муж. Жен. Дет.)
    # Получение списка папок в заданной директории
    # folders = Check_dir.get_folders(f'/home/user/Pictures/123/{path[1]}')
    folders = os.listdir(f'{abs_path}/{path[1]}') # Полный путь с выбранной папкой (М,Ж,Д)

    # Удаляем предыдущее сообщение
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
    # # Удаление предыдущей клавиатуры (reply_markup=None)
    # await query.message.edit_reply_markup(reply_markup=None)

    # Создание кнопок
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = []

    # Для каждой папки в списке папок
    for folder in folders:
        # Получение полного пути к папке
        folder_path = os.path.join(f'{abs_path}{path[1]}/', folder)
        #
        # Получение количества файлов в папке
        file_count = len(os.listdir(folder_path))
        if file_count != 0:
            # Создание текста для кнопки, содержащего: имя папки и (количество файлов)
            button_text = f"{folder} ({file_count})"
            data_text = f'{path[1]}/{folder}'
            # print(data_text)
            # Создание объекта кнопки с текстом и указанием обратного вызова (callback_data) как имя папки
            buttons.append(types.InlineKeyboardButton(text=button_text, callback_data=data_text))

    back_to_catalog_menu = types.InlineKeyboardButton(text='⤵️Kаталог⤵️', callback_data='catalog')
    back_to_main_menu = types.InlineKeyboardButton(text='↩️Главное меню↩️', callback_data='main_menu')
    # Добавление кнопок на клавиатуру
    keyboard.add(*buttons)
    keyboard.add(back_to_catalog_menu)
    keyboard.add(back_to_main_menu)
    # Отправка сообщения с текстом "Выберите бренд:👇" и встроенной клавиатурой
    await query.message.answer('Выберите бренд:👇', reply_markup=keyboard)


###
########################################################################################################################
# Кнопка 'Главное меню'
@dp.callback_query_handler(lambda query: query.data == 'main_menu')
async def handle_main_menu_button(query: types.CallbackQuery):
    # Удаление предыдущей клавиатуры (reply_markup=None)
    await query.message.edit_reply_markup(reply_markup=None)
    # Удаляем предыдущее сообщение
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)

    keyboard = await create_keyboard()
    await query.message.answer('🏠*ВЫ В ГЛАВНОМ МЕНЮ*🏠\n\nДля просмотра ассортимента\n👇    *нажмите на*    👇\n'
                               '🛒 🛒 *KATAЛOГ* 🛒 🛒', reply_markup=keyboard, parse_mode='Markdown')



########################################################################################################################
########################################################################################################################
########################################################################################################################
# Функция для автоматического сброса состояния после таймаута
# async def auto_reset_state():
#     while True:
#         await asyncio.sleep(30)  # Подождать 5 минут (300 секунд)
#         await reset_state(state)

########################################################################################################################
########################################################################################################################
########################################################################################################################
# Кнопки '◀️ предыдущая', '▶️ следующая'
@dp.callback_query_handler(lambda query: query.data.startswith(('next_', 'prev_')))
async def handle_next_previous_photo(query: types.CallbackQuery):
    # Извлекаем выбранную папку, индекс фотографии и максимальный индекс из данных callback'а
    data_parts = query.data.split('_')
    selected_folder = data_parts[1] # Выбранный гендер (М,Ж,Д) / Название папки с фотками
    # print(selected_folder)
    photo_index = int(data_parts[2]) # Индекс выбранной фотографии
    # print(photo_index)
    max_index = int(data_parts[3]) # Максимальный индекс
    # print(max_index)
    # Определяем направление (следующее или предыдущее) на основе префикса данных callback'а
    is_next = query.data.startswith('next_')

    # Вычисляем индекс следующей или предыдущей фотографии
    next_photo_index = photo_index + 1 if is_next else photo_index - 1

    global abs_path
    # Формируем путь к выбранной папке
    folder_path = os.path.join(abs_path, selected_folder)

    # Получаем список файлов в выбранной папке
    files = os.listdir(folder_path)

    # Фильтруем список файлов, оставляя только изображения
    photo_files = [f for f in files if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith(
        ('.jpg', '.jpeg', '.png', '.gif'))]

    if photo_files and 0 <= next_photo_index <= max_index:
        # Получаем имя следующей фотографии на основе индекса
        next_photo = photo_files[next_photo_index]
        print('next_photo', next_photo)
        # Удаление предыдущей клавиатуры (reply_markup=None)
        await query.message.edit_reply_markup(reply_markup=None)

        # Формируем кнопки для клавиатуры
        buttons = []
        buttons.append(types.InlineKeyboardButton(text='⬅️',
                                                  callback_data=f'prev_{selected_folder}_{next_photo_index}_{max_index}'))
        buttons.append(
            types.InlineKeyboardButton(text='➡️',
                                       callback_data=f'next_{selected_folder}_{next_photo_index}_{max_index}'))
        button_order = (types.InlineKeyboardButton(text='🛒Заказать🛒', callback_data='order'))
        button_catalog = (types.InlineKeyboardButton(text='⤵️Каталог⤵️', callback_data='catalog'))
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(*buttons)
        keyboard.add(button_order)
        keyboard.add(button_catalog)

        # Формируем путь к следующей фотографии
        path = os.path.join(folder_path, next_photo)

        # Удаляем предыдущее сообщение
        await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)

        # Открываем следующую фотографию в режиме чтения
        with open(path, 'rb') as next_photo_file:

            parts = path.split('/')
            filename = parts[-1]  # Получаем последний элемент после разделения по '/'
            name_of_model = filename.split('.')[0].lower()  # Имя файла без расширения
            global abs_path_database_data
            print(name_of_model)
            text = await Data_base_models.data_base_models(abs_path_database_data, name_of_model) # Получаю модель, размеры, цену

            # Отправляем следующую фотографию с подписью и клавиатурой в ответ на сообщение
            await query.message.answer_photo(photo=next_photo_file, caption=text, reply_markup=keyboard)
    else:
        if is_next:
            await query.message.answer('Это была последняя модель данного бренда\nСмотрите ◀️*предыдущие* модели',
                                       parse_mode='Markdown')

        else:
            await query.message.answer('Это была первая модель данного бренда\nСмотрите *следующие*▶️ модели',
                                       parse_mode='Markdown')


########################################################################################################################
@dp.callback_query_handler()
async def handle_callback_query(query: types.CallbackQuery):
    selected_folder = query.data # То, что выбрал пользователь (кнопка)
    # Сообщение появляется в черном квадрате (в телефоне - сверху, в компе - по середине) экрана и исчезает
    # await query.answer(f"БРЕНД: {selected_folder}") # Черная табличка вверху, когда юзер выбирает действие

    # Отправляем сообщение пользователю
    await query.message.answer(f"Вы выбрали бренд: {selected_folder}")
    # Удаление предыдущей клавиатуры (reply_markup=None)
    await query.message.edit_reply_markup(reply_markup=None)
    global abs_path
    folder_path = os.path.join(abs_path, selected_folder) # Полный путь до папки с фото
    files = os.listdir(folder_path) # Открытие выбранной папки (бренда) с фотками внутри
    photo_files = [f for f in files if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
    photo_index = len(photo_files)    # Сколько файлов в папке (фоток)
    max_index = photo_index - 1     # Максимальный индекс (за который выходить нельзя) в папке с файлами (фотками)

    first_photo_index = 0
    #print(photo_index)
    if photo_files:
        photo = photo_files[first_photo_index]  # Получаем полное название выбранной фотографии. В данном случае: размер и описание обуви. (str)

        path = os.path.join(folder_path, photo) # Это полный путь до фото
        with open(path, 'rb') as photo_file: # Мы открываем фотографию с помощью функции open(), указывая режим чтения байтов ('rb'),
            # и сохраняем ее объект в переменную photo_file. Это позволяет нам прочитать содержимое фотографии.

            parts = path.split('/')
            filename = parts[-1]  # Получаем последний элемент после разделения по '/'
            name_of_model = filename.split('.')[0].lower()  # Имя файла без расширения
            global abs_path_database_data
            print(name_of_model)
            text = await Data_base_models.data_base_models(abs_path_database_data, name_of_model)

            buttons = []
            if photo_index == 0:
                button_order = (types.InlineKeyboardButton(text='🛒Заказать🛒', callback_data='order'))
                button_catalog = (types.InlineKeyboardButton(text='⤵️Каталог⤵️', callback_data='catalog'))
            else:
                #_{index}_{max_index}
                buttons.append(types.InlineKeyboardButton(text='⬅️', callback_data=f'prev_{selected_folder}_{first_photo_index}_{max_index}'))
                buttons.append(types.InlineKeyboardButton(text='➡️', callback_data=f'next_{selected_folder}_{first_photo_index}_{max_index}'))
                button_order = (types.InlineKeyboardButton(text='🛒Заказать🛒', callback_data='order'))
                button_catalog = (types.InlineKeyboardButton(text='⤵️Каталог⤵️', callback_data='catalog'))
            if buttons:
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                keyboard.add(*buttons)
            keyboard.add(button_order)
            keyboard.add(button_catalog)

            await query.message.answer_photo(photo=photo_file, caption=text, reply_markup=keyboard)

###
########################################################################################################################
########################################################################################################################
########################################################################################################################

if __name__ == '__main__':
    while True:

        loop = asyncio.get_event_loop()
        try:
            loop.create_task(dp.start_polling())
            loop.run_forever()

        except Exception as e:
            current_datetime = datetime.datetime.now().strftime('%d.%m.%Y/%H:%M')
            error_message = f'({current_datetime}) Error: {str(e)}'
            with open('errors.log', 'a+') as error_log:
                error_log.write(error_message + '\n')

        finally:
            loop.close()


