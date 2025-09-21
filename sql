CREATE DATABASE library_db;
USE library_db;

CREATE TABLE students (
    roll_no VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200),
    author VARCHAR(100)
);

CREATE TABLE issues (
    id INT AUTO_INCREMENT PRIMARY KEY,
    roll_no VARCHAR(20),
    book_title VARCHAR(200)
);
