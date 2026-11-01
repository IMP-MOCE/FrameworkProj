-- ==========================================
-- сервис записи на творческие занятия: запросы проекта
-- в представлениях вместо конкретных значений стоят параметры ?
-- ==========================================


-- 1. каталог занятий со свободными местами (страница /workshops/)
-- LEFT JOIN оставляет занятия без записей, у них свободны все места
SELECT
    workshops.id,
    workshops.name,
    strftime('%d.%m.%Y', workshops.date) AS date_text,
    workshops.price,
    workshops.capacity - COUNT(bookings.id) AS seats
FROM workshops
LEFT JOIN bookings
    ON bookings.workshop_id = workshops.id
    AND bookings.status = 'active'
GROUP BY workshops.id
ORDER BY workshops.date, workshops.id;


-- 2. мастер по идентификатору (заголовок /workshops/?master=1)
SELECT id, name
FROM masters
WHERE id = 1;


-- 3. занятия одного мастера (страница /workshops/?master=1)
SELECT
    workshops.id,
    workshops.name,
    strftime('%d.%m.%Y', workshops.date) AS date_text,
    workshops.price,
    workshops.capacity - COUNT(bookings.id) AS seats
FROM workshops
LEFT JOIN bookings
    ON bookings.workshop_id = workshops.id
    AND bookings.status = 'active'
WHERE workshops.master_id = 1
GROUP BY workshops.id
ORDER BY workshops.date, workshops.id;


-- 4. занятия со свободными местами на дату для возраста участника
-- (страница /workshops/available/), WHERE отбирает строки до группировки,
-- HAVING отбирает группы, у которых остались места
SELECT
    workshops.id,
    workshops.name,
    strftime('%d.%m.%Y', workshops.date) AS date_text,
    workshops.price,
    workshops.capacity - COUNT(bookings.id) AS seats
FROM workshops
LEFT JOIN bookings
    ON bookings.workshop_id = workshops.id
    AND bookings.status = 'active'
WHERE workshops.date = '2026-10-10'
    AND workshops.minimum_age <= 13
GROUP BY workshops.id
HAVING seats > 0
ORDER BY workshops.name;


-- 5. мастера с количеством занятий и средней ценой (страница /workshops/masters/)
SELECT
    masters.id,
    masters.name,
    COUNT(workshops.id) AS workshops_count,
    AVG(workshops.price) AS average_price
FROM masters
LEFT JOIN workshops ON workshops.master_id = masters.id
GROUP BY masters.id
ORDER BY masters.name;


-- 6. все записи с занятием и участником (страница /bookings/)
-- данные собираются из трёх таблиц
SELECT
    bookings.id,
    bookings.status,
    workshops.name AS workshop_name,
    strftime('%d.%m.%Y', workshops.date) AS workshop_date,
    users.name AS user_name
FROM bookings
JOIN workshops ON bookings.workshop_id = workshops.id
JOIN users ON bookings.user_id = users.id
ORDER BY bookings.id;


-- 7. общие показатели каталога (страница /bookings/statistics/)
SELECT
    COUNT(*) AS workshops_count,
    MIN(price) AS min_price,
    MAX(price) AS max_price,
    AVG(price) AS average_price
FROM workshops;


-- 8. количество записей по статусам (страница /bookings/statistics/)
SELECT status, COUNT(*) AS bookings_count
FROM bookings
GROUP BY status
ORDER BY status;


-- 9. выручка по активным записям (страница /bookings/statistics/)
-- если активных записей нет, SUM вернёт NULL
SELECT SUM(workshops.price) AS total
FROM bookings
JOIN workshops ON bookings.workshop_id = workshops.id
WHERE bookings.status = 'active';


-- 10. участники и число их активных записей (страница /bookings/statistics/)
-- COUNT(bookings.id) не считает NULL, поэтому у участника без записей будет 0
SELECT
    users.name,
    users.age,
    COUNT(bookings.id) AS active_count
FROM users
LEFT JOIN bookings
    ON bookings.user_id = users.id
    AND bookings.status = 'active'
GROUP BY users.id
ORDER BY active_count DESC, users.name;


-- 11. популярные занятия: не меньше двух активных записей
-- (страница /bookings/statistics/)
SELECT
    workshops.name,
    COUNT(bookings.id) AS active_count
FROM workshops
JOIN bookings ON bookings.workshop_id = workshops.id
WHERE bookings.status = 'active'
GROUP BY workshops.id
HAVING COUNT(bookings.id) >= 2
ORDER BY active_count DESC;


-- 12. занятия без описания, проверка NULL (только для консоли SQLite)
SELECT id, name
FROM workshops
WHERE description IS NULL
ORDER BY id;


-- 13. два самых дорогих занятия, пропустив первое (только для консоли SQLite)
-- без ORDER BY порядок строк для LIMIT и OFFSET не гарантирован
SELECT name, price
FROM workshops
ORDER BY price DESC
LIMIT 2 OFFSET 1;
