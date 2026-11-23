-- Makes the Lost and Found database in MySQL and the account the website uses to reach it.
-- Run it once as root in MySQL Workbench: File > Open SQL Script > this file, then the lightning button.
-- Change the password here and in the .env file to the same new value.

-- 1. The database. utf8mb4 stores every character, including emoji typed in posts.
CREATE DATABASE IF NOT EXISTS lostandfound CHARACTER SET utf8mb4;

-- 2. The account the website logs in with (one line for each way of saying "this computer").
CREATE USER IF NOT EXISTS 'lostandfound_app'@'localhost' IDENTIFIED BY 'Change-This-Password-1';
CREATE USER IF NOT EXISTS 'lostandfound_app'@'127.0.0.1' IDENTIFIED BY 'Change-This-Password-1';

-- 3. The account may create and change the tables in this database only.
GRANT ALL PRIVILEGES ON lostandfound.* TO 'lostandfound_app'@'localhost';
GRANT ALL PRIVILEGES ON lostandfound.* TO 'lostandfound_app'@'127.0.0.1';

-- 4. "python manage.py test" makes and deletes its own database called test_lostandfound.
GRANT ALL PRIVILEGES ON test_lostandfound.* TO 'lostandfound_app'@'localhost';
GRANT ALL PRIVILEGES ON test_lostandfound.* TO 'lostandfound_app'@'127.0.0.1';

FLUSH PRIVILEGES;

-- The tables themselves are made by Django:  python manage.py migrate
