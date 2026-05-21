-- Chess Signup Database Setup
-- Run this once: mysql -u root -p < database.sql

CREATE DATABASE IF NOT EXISTS chess_signup
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE chess_signup;

CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    email       VARCHAR(255)    NOT NULL UNIQUE,
    username    VARCHAR(20)     NOT NULL UNIQUE,
    password_hash VARCHAR(255)  NOT NULL,
    created_at  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email    (email),
    INDEX idx_username (username)
);
