BEGIN;
CREATE TABLE IF NOT EXISTS users(

    user_id BIGINT,
    guild_id BIGINT,

    xp BIGINT DEFAULT 0,
    level BIGINT DEFAULT 1,
    messages BIGINT DEFAULT 0,
    total_xp BIGINT DEFAULT 0,

    money TEXT DEFAULT 0,
    worked BIGINT DEFAULT 0,

    event_type TEXT,
    job_id BIGINT,

    PRIMARY KEY (user_id, guild_id, event_type)
    );

CREATE TABLE IF NOT EXISTS warnings(

    user_id BIGINT,
    guild_id BIGINT,

    warn_id INTEGER PRIMARY KEY AUTOINCREMENT,
    warn_text TEXT,
    created_at TIMESTAMP,

    warned_by BIGINT
    );

CREATE TABLE IF NOT EXISTS server_data(

    guild_id BIGINT,

    message_text TEXT,          
    channel_id BIGINT,

    event_type TEXT,
    deny_clicked INTEGER,

    PRIMARY KEY (guild_id, event_type)
    );

CREATE TABLE IF NOT EXISTS jobs(

    guild_id BIGINT,

    name TEXT,
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    salary BIGINT,
    description TEXT
    );

UPDATE SQLITE_SEQUENCE SET seq = 1000000 WHERE name = 'jobs' OR name = 'warnings';
COMMIT;
