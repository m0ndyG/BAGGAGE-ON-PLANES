import pymysql
import bcrypt
import datetime

# Настройки подключения к БД (измените на свои)
db_config = {
    "host": "localhost",
    "user": "admin",
    "password": "admin",
    "database": "new_baggage_accounting",
    "port": 3307
}


def clear_database():
    """Удаляет все записи из всех таблиц в базе данных."""
    connection = None # Инициализация переменной для соединения
    try:
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()

        # Отключаем проверку внешних ключей, чтобы очистить все таблицы в любом порядке
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

        # Удаляем все записи из таблиц
        cursor.execute("DELETE FROM baggage;")
        cursor.execute("DELETE FROM aircraft;")
        cursor.execute("DELETE FROM reports;")
        cursor.execute("DELETE FROM users;")

        # Включаем проверку внешних ключей обратно
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        connection.commit()
        print("База данных очищена.")

    except pymysql.Error as e:
        print(f"Ошибка при очистке базы данных: {e}")
    finally:
        if connection:
            connection.close()


def populate_database():
    """Добавляет несколько тестовых записей в таблицы."""
    connection = None # Инициализация переменной для соединения
    try:
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()

        # --- Добавление пользователей ---
        users_data = [
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4")
        ]
        
        for username, password in users_data:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed_password))

        connection.commit() # Сохbotраняем изменения после добавления всех пользователей

        # Получаем ID пользователей для использования в других таблицах
        cursor.execute("SELECT id, username FROM users")
        users_map = {row[1]: row[0] for row in cursor.fetchall()} # Исправлено здесь

        # --- Добавление самолетов ---
        aircrafts_data = [
            ("AA123", "Боинг 747", "30000", "50000", users_map["1"]),
            ("BB456", "Аэробус A320", "10000", "20000", users_map["1"]),
            ("CC789", "Embraer 190", "5000", "10000", users_map["2"]),
            ("DD001", "Airbus A380", "50000", "80000", users_map["2"]),
            ("EE222", "Bombardier CRJ900", "4000", "9000", users_map["3"])
        ]
        for number, name, capacity, max_volume, user_id in aircrafts_data:
              cursor.execute("INSERT INTO aircraft (number, name, capacity, max_volume, user_id) VALUES (%s, %s, %s, %s, %s)", (number, name, capacity, max_volume, user_id))
        
        connection.commit()

        # --- Добавление записей о багаже ---
        baggage_data = [
            ("Иванов И.И.", "BG1001", "Обычный", "0.1", "Средний", "5", "AA123", "Москва", "Лондон", datetime.datetime(2024, 1, 1, 10, 0, 0), datetime.datetime(2024, 1, 1, 14, 0, 0), "Прибыл", "Книга", users_map["1"]),
            ("Петров П.П.", "BG1002", "Ценный", "0.05", "Маленький", "2", "BB456", "Лондон", "Париж", datetime.datetime(2024, 1, 2, 12, 0, 0), datetime.datetime(2024, 1, 2, 16, 0, 0), "В пути", "Кольцо", users_map["2"]),
            ("Сидоров С.С.", "BG1003", "Хрупкий", "0.2", "Большой", "10", "CC789", "Париж", "Рим", datetime.datetime(2024, 1, 3, 8, 0, 0), datetime.datetime(2024, 1, 3, 10, 0, 0), "Зарегистрирован", "Ваза", users_map["1"]),
            ("Смирнов С.С.", "BG1004", "Обычный", "0.3", "Средний", "7", "DD001", "Рим", "Берлин", datetime.datetime(2024, 1, 4, 11, 0, 0), datetime.datetime(2024, 1, 4, 17, 0, 0), "Прибыл", "Одежда", users_map["2"]),
            ("Кузнецова К.К.", "BG1005", "Ценный", "0.1", "Маленький", "3", "EE222", "Берлин", "Москва", datetime.datetime(2024, 1, 5, 15, 0, 0), datetime.datetime(2024, 1, 5, 20, 0, 0), "В пути", "Ноутбук", users_map["3"]),
            ("Леонов Л.Л.", "BG1006", "Хрупкий", "0.25", "Средний", "9", "AA123", "Москва", "Лондон", datetime.datetime(2024, 1, 6, 14, 0, 0), datetime.datetime(2024, 1, 6, 18, 0, 0), "Прибыл", "Фарфор", users_map["1"]),
            ("Иванова И.И.", "BG1007", "Обычный", "0.15", "Средний", "6", "BB456", "Лондон", "Париж", datetime.datetime(2024, 1, 7, 9, 0, 0), datetime.datetime(2024, 1, 7, 13, 0, 0), "Зарегистрирован", "Сувениры", users_map["3"]),
            ("Федоров Ф.Ф.", "BG1008", "Хрупкий", "0.2", "Большой", "11", "CC789", "Париж", "Рим", datetime.datetime(2024, 1, 8, 16, 0, 0), datetime.datetime(2024, 1, 8, 20, 0, 0), "В пути", "Зеркало", users_map["4"]),
            ("Андреева А.А.", "BG1009", "Обычный", "0.12", "Маленький", "4", "AA123", "Москва", "Нью-Йорк", datetime.datetime(2024, 1, 9, 7, 0, 0), datetime.datetime(2024, 1, 9, 19, 0, 0), "В пути", "Книга", users_map["1"]),
            ("Волков В.В.", "BG1010", "Ценный", "0.08", "Средний", "3", "BB456", "Нью-Йорк", "Токио", datetime.datetime(2024, 1, 10, 13, 0, 0), datetime.datetime(2024, 1, 10, 22, 0, 0), "Прибыл", "Электроника", users_map["2"]),
            ("Григорьев Г.Г.", "BG1011", "Хрупкий", "0.35", "Большой", "12", "CC789", "Токио", "Сидней", datetime.datetime(2024, 1, 11, 9, 0, 0), datetime.datetime(2024, 1, 11, 23, 0, 0), "Зарегистрирован", "Стекло", users_map["3"]),
            ("Дмитриева Д.Д.", "BG1012", "Обычный", "0.2", "Средний", "8", "DD001", "Сидней", "Москва", datetime.datetime(2024, 1, 12, 10, 0, 0), datetime.datetime(2024, 1, 12, 17, 0, 0), "В пути", "Подарки", users_map["4"]),
            ("Егоров Е.Е.", "BG1013", "Ценный", "0.07", "Маленький", "1", "EE222", "Москва", "Париж", datetime.datetime(2024, 1, 13, 14, 0, 0), datetime.datetime(2024, 1, 13, 19, 0, 0), "Прибыл", "Деньги", users_map["1"]),
            ("Жукова Ж.Ж.", "BG1014", "Хрупкий", "0.28", "Средний", "10", "AA123", "Париж", "Лондон", datetime.datetime(2024, 1, 14, 12, 0, 0), datetime.datetime(2024, 1, 14, 15, 0, 0), "Зарегистрирован", "Посуда", users_map["2"]),
            ("Зайцев З.З.", "BG1015", "Обычный", "0.18", "Большой", "7", "BB456", "Лондон", "Берлин", datetime.datetime(2024, 1, 15, 11, 0, 0), datetime.datetime(2024, 1, 15, 18, 0, 0), "В пути", "Постельное", users_map["3"]),
            ("Комаров К.К.", "BG1016", "Ценный", "0.06", "Средний", "2", "CC789", "Берлин", "Рим", datetime.datetime(2024, 1, 16, 8, 0, 0), datetime.datetime(2024, 1, 16, 15, 0, 0), "Прибыл", "Ювелирка", users_map["4"]),
            ("Николаев Н.Н.", "BG1017", "Обычный", "0.3", "Большой", "11", "DD001", "Рим", "Москва", datetime.datetime(2024, 1, 17, 10, 0, 0), datetime.datetime(2024, 1, 17, 14, 0, 0), "Прибыл", "Продукты", users_map["1"]),
            ("Орлова О.О.", "BG1018", "Хрупкий", "0.1", "Средний", "4", "EE222", "Москва", "Нью-Йорк", datetime.datetime(2024, 1, 18, 17, 0, 0), datetime.datetime(2024, 1, 18, 23, 0, 0), "В пути", "Ваза", users_map["2"]),
            ("Павлов П.П.", "BG1019", "Ценный", "0.09", "Маленький", "1", "AA123", "Нью-Йорк", "Токио", datetime.datetime(2024, 1, 19, 13, 0, 0), datetime.datetime(2024, 1, 19, 18, 0, 0), "Зарегистрирован", "Кольцо", users_map["3"]),
            ("Романов Р.Р.", "BG1020", "Обычный", "0.2", "Большой", "10", "BB456", "Токио", "Сидней", datetime.datetime(2024, 1, 20, 9, 0, 0), datetime.datetime(2024, 1, 20, 22, 0, 0), "Прибыл", "Книга", users_map["4"]),
             ("Соколова С.С.", "BG1021", "Хрупкий", "0.15", "Средний", "6", "CC789", "Сидней", "Берлин", datetime.datetime(2024, 1, 21, 11, 0, 0), datetime.datetime(2024, 1, 21, 16, 0, 0), "В пути", "Фарфор", users_map["1"]),
            ("Тимофеев Т.Т.", "BG1022", "Ценный", "0.22", "Средний", "8", "DD001", "Берлин", "Лондон", datetime.datetime(2024, 1, 22, 15, 0, 0), datetime.datetime(2024, 1, 22, 22, 0, 0), "Прибыл", "Картина", users_map["2"]),
            ("Ульянов У.У.", "BG1023", "Обычный", "0.16", "Маленький", "3", "EE222", "Лондон", "Москва", datetime.datetime(2024, 1, 23, 10, 0, 0), datetime.datetime(2024, 1, 23, 14, 0, 0), "Зарегистрирован", "Документы", users_map["3"]),
             ("Фомина Ф.Ф.", "BG1024", "Хрупкий", "0.3", "Большой", "11", "AA123", "Москва", "Рим", datetime.datetime(2024, 1, 24, 17, 0, 0), datetime.datetime(2024, 1, 24, 20, 0, 0), "Прибыл", "Скульптура", users_map["1"]),
             ("Харитонов Х.Х.", "BG1025", "Ценный", "0.11", "Средний", "5", "BB456", "Рим", "Нью-Йорк", datetime.datetime(2024, 1, 25, 9, 0, 0), datetime.datetime(2024, 1, 25, 18, 0, 0), "В пути", "Золото", users_map["4"])
        ]
        for owner, number, type, volume, size, weight, aircraft, dep_route, arr_route, dep_date, arr_date, status, desc, user_id in baggage_data:
            cursor.execute(
                "INSERT INTO baggage (owner, number, type, volume, size, weight, aircraft, dep_route, arr_route, dep_date, arr_date, status, `desc`, user_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (owner, number, type, volume, size, weight, aircraft, dep_route, arr_route, dep_date, arr_date, status, desc, user_id)
            )

        connection.commit()
        print("Тестовые записи успешно добавлены.")

    except pymysql.Error as e:
        print(f"Ошибка при добавлении тестовых записей: {e}")

    finally:
        if connection:
             connection.close()


if __name__ == '__main__':
    action = input("Выберите действие (clear/populate/both): ").lower()

    if action == "clear":
       clear_database()
    elif action == "populate":
         populate_database()
    elif action == "both":
          clear_database()
          populate_database()
    else:
        print("Неверное действие. Выберите 'clear', 'populate' или 'both'.")