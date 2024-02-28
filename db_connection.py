import aiosqlite

async def create_table():
    # Создаем соединение с базой данных (если она не существует, то она будет создана)
    async with aiosqlite.connect('quiz_bot.db') as db:
        # Выполняем SQL-запрос к базе данных
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (
        user_id INTEGER PRIMARY KEY,
        question_index INTEGER,
        last_score INTEGER DEFAULT 0
        )''')
        # Сохраняем изменения
        await db.commit()

async def update_quiz_info(user_id: int, index: int, last_score: int):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect('quiz_bot.db') as db:
        sql_query = "INSERT OR REPLACE INTO quiz_state(user_id, question_index, last_score) VALUES(?, ?, ?)"
        await db.execute(sql_query, (user_id, index, last_score))
        # Сохраняем изменения
        await db.commit()

async def get_last_user_score(user_id: int):
    async with aiosqlite.connect('quiz_bot.db') as db:
        async with db.execute('SELECT last_score FROM quiz_state WHERE user_id = ?', (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                return result[0]
            return 0


async def get_player_statistics():
    async with aiosqlite.connect('quiz_bot.db') as db:
        async with db.execute('SELECT user_id, last_score FROM quiz_state') as cursor:
            return await cursor.fetchall()

async def get_quiz_index(user_id):
     # Подключаемся к базе данных
     async with aiosqlite.connect('quiz_bot.db') as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0