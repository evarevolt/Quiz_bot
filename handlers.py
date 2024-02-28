from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import or_f
from aiogram.filters.callback_data import CallbackData
from aiogram.filters.command import Command
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F
import json

from db_connection import get_quiz_index, get_player_statistics, get_last_user_score, update_quiz_info

router = Router()
class QuizCallback(CallbackData, prefix="quiz_answer"):
    index: int
    is_correct: bool

quiz_data = []
with open('questions.json', encoding='utf-8') as file:
    quiz_data = json.load(file)

# Хэндлер на команду /start
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    # Добавляем в сборщик одну кнопку
    builder.add(types.KeyboardButton(text="Начать игру"))
    builder.add(types.KeyboardButton(text="Статистика игроков"))
    # Прикрепляем кнопки к сообщению
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))

# Хэндлер на команду /quiz
@router.message(F.text=="Начать игру")
@router.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    # Отправляем новое сообщение без кнопок
    await message.answer(f"Давайте начнем квиз!")
    # Запускаем новый квиз
    await new_quiz(message)


@router.message(F.text == "Статистика игроков")
@router.message(Command("stats"))
async def send_statistics(message: types.Message):
    statistics = await get_player_statistics()
    stats_message = "Статистика игроков:\n\n" + "\n".join([f"ID пользователя: {user_id}, Последний результат: {score}" for user_id, score in statistics])
    await message.answer(stats_message)


async def new_quiz(message):
    # получаем id пользователя, отправившего сообщение
    user_id = message.from_user.id
    # сбрасываем значение текущего индекса вопроса квиза в 0
    current_question_index = 0
    user_score = 0
    await update_quiz_info(user_id, current_question_index, user_score)
    # запрашиваем новый вопрос для квиза
    await get_question(message, user_id)

async def get_question(message, user_id):

    # Запрашиваем из базы текущий индекс для вопроса
    current_question_index = await get_quiz_index(user_id)
    # Получаем индекс правильного ответа для текущего вопроса
    correct_index = quiz_data[current_question_index]['correct_option']
    # Получаем список вариантов ответа для текущего вопроса
    opts = quiz_data[current_question_index]['options']

    # Функция генерации кнопок для текущего вопроса квиза
    # В качестве аргументов передаем варианты ответов и значение правильного ответа (не индекс!)
    kb = generate_options_keyboard(opts, opts[correct_index])
    # Отправляем в чат сообщение с вопросом, прикрепляем сгенерированные кнопки
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)

def generate_options_keyboard(answer_options, right_answer):
  # Создаем сборщика клавиатур типа Inline
    builder = InlineKeyboardBuilder()

    # В цикле создаем 4 Inline кнопки, а точнее Callback-кнопки
    for index, option in enumerate(answer_options):
        # Используем фабрику для создания callback_data для каждой кнопки

        callback_data = QuizCallback(index=index, is_correct=(option == right_answer)).pack()
        # Текст на кнопках соответствует вариантам ответов
        builder.add(types.InlineKeyboardButton(text=option, callback_data=callback_data))

    # Выводим по одной кнопке в столбик
    builder.adjust(1)
    return builder.as_markup()


@router.callback_query(QuizCallback.filter())
async def answer_callback(callback: types.CallbackQuery, callback_data: QuizCallback):

    # Извлекаем данные из callback_data
    current_question_index = await get_quiz_index(callback.from_user.id)
    selected_option = quiz_data[current_question_index]['options'][callback_data.index]
    correct_option = quiz_data[current_question_index]['correct_option']
    text_answer = f"_Неправильно._ Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}"
    final_score = await get_last_user_score(callback.from_user.id)
    SCORE_BY_CORRECT_ANSWER = 25

    # Проверка правильности ответа и выполнение соответствующей логики
    if callback_data.is_correct:
        text_answer = "_Верно!_"
        final_score += SCORE_BY_CORRECT_ANSWER

    # редактируем текущее сообщение с целью убрать кнопки (reply_markup=None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    # Отправляем в чат сообщение об ошибке с указанием верного ответа
    await callback.message.answer(f"Ваш выбор: *{selected_option}*\n{text_answer}", parse_mode="Markdown")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await update_quiz_info(callback.from_user.id, current_question_index, final_score)

    # Проверяем достигнут ли конец квиза
    if current_question_index < len(quiz_data):
        # Следующий вопрос
        await get_question(callback.message, callback.from_user.id)
    else:
        final_score = await get_last_user_score(callback.from_user.id)
        corrent_answers_count = int(final_score / SCORE_BY_CORRECT_ANSWER)
        corrent_percent = corrent_answers_count / len(quiz_data)
        incorrent_percent = 1.0 - corrent_percent

        result_text = f"\nФинальный счет: *{final_score}*\n*{corrent_percent:.2%}* правильных ответов, " \
                      f"*{incorrent_percent:.2%}* неправильных ответов"

        # Уведомление об окончании квиза
        await callback.message.answer("Это был последний вопрос. Квиз завершен!" + result_text,
                                      parse_mode="Markdown")
