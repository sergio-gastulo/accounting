CREATE TABLE cuentas (
    id INTEGER PRIMARY KEY,
    date CHAR(10) NOT NULL, -- ISO convention https://en.wikipedia.org/wiki/ISO_8601
    amount REAL NOT NULL,
    currency CHAR(3) DEFAULT 'PEN', -- ISO convention https://en.wikipedia.org/wiki/ISO_4217
    description TEXT,
    category TEXT NOT NULL
);