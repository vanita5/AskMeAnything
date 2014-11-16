DROP TABLE IF EXISTS questions;
CREATE TABLE questions (
    tweet_id INTEGER PRIMARY KEY,
    question TEXT NOT NULL,
    author TEXT DEFAULT 'Anonymous',
    timestamp INTEGER
);
CREATE TABLE answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    q_id INTEGER UNIQUE,
    answer TEXT NOT NULL,
    tweet_id INTEGER,
    timestamp INTEGER
);