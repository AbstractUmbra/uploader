CREATE TABLE IF NOT EXISTS images (
    filename TEXT PRIMARY KEY,
    author INT NOT NULL,
    deletion_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
);
CREATE TABLE IF NOT EXISTS audio (
    filename TEXT PRIMARY KEY,
    soundgasm_author INT NOT NULL,
    title TEXT NOT NULL,
    deletion_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
    UNIQUE (title, soundgasm_author)
);
