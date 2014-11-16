CREATE TABLE IF NOT EXISTS questions (
    tweet_id INTEGER PRIMARY KEY,
    question TEXT NOT NULL,
    author TEXT DEFAULT 'Anonymous',
    timestamp INTEGER
);
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    q_id INTEGER UNIQUE,
    answer TEXT NOT NULL,
    tweet_id INTEGER,
    timestamp INTEGER
);