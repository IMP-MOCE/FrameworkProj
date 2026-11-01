-- ==========================================
-- сервис записи на творческие занятия: структура базы данных
-- ==========================================

-- мастера, в JSON имя мастера хранится внутри занятия
CREATE TABLE IF NOT EXISTS masters (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- занятия, дата в формате ГГГГ-ММ-ДД
CREATE TABLE IF NOT EXISTS workshops (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    master_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    price REAL NOT NULL,
    capacity INTEGER NOT NULL,
    minimum_age INTEGER NOT NULL DEFAULT 0,
    description TEXT,
    FOREIGN KEY (master_id) REFERENCES masters(id)
);

-- участники, в JSON имя и возраст хранятся внутри записи
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    UNIQUE (name, age)
);

-- записи на занятия, отменённая запись остаётся в истории
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY,
    workshop_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'cancelled')),
    FOREIGN KEY (workshop_id) REFERENCES workshops(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
