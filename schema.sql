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
); -- shouldnt be bound to guild

CREATE TABLE IF NOT EXISTS twitch_users(
    username TEXT,
    user_id BIGINT,
    guild_id BIGINT,
    PRIMARY KEY (username, user_id, guild_id)
);

CREATE TABLE IF NOT EXISTS warnings(
    user_id BIGINT,
    guild_id BIGINT,
    warn_id SERIAL PRIMARY KEY, --rename to id
    warn_text TEXT, -- rename to reason
    created_at TIMESTAMP,
    warned_by BIGINT
);

CREATE TABLE IF NOT EXISTS server_data(
    guild_id BIGINT,
    message_text TEXT,
    channel_id BIGINT,
    event_type TEXT,
    counter_name TEXT,
    deny_clicked INTEGER,
    PRIMARY KEY (guild_id, event_type, counter_name)
);

CREATE TABLE IF NOT EXISTS prefixes(
    guild_id BIGINT,
    prefix VARCHAR(10),
    PRIMARY KEY (prefix, guild_id)
);

CREATE TABLE IF NOT EXISTS jobs(
    guild_id BIGINT,
    name TEXT,
    id SERIAL PRIMARY KEY,
    salary BIGINT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS news(
    title TEXT,
    message_id BIGINT,
    channel_id BIGINT,
    news_id SERIAL PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS blacklist(
    user_id BIGINT PRIMARY KEY,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS todo(
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    channel_id BIGINT,
    message_id BIGINT,
    guild_id BIGINT,
    content TEXT,
    due_at TIMESTAMP,
    completed_at TIMESTAMP,
    cached_content TEXT
);

ALTER SEQUENCE jobs_id_seq START 10000000 INCREMENT BY 1;
ALTER SEQUENCE warnings_warn_id_seq START 10000000 INCREMENT BY 1;

ALTER TABLE jobs ALTER COLUMN id SET DEFAULT NEXTVAL('jobs_id_seq');
ALTER TABLE warnings ALTER COLUMN warn_id SET DEFAULT NEXTVAL('warnings_warn_id_seq');

-- SINGLE-LINE COMMENT 

COMMIT;