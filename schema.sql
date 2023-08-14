BEGIN;

CREATE TABLE IF NOT EXISTS blacklist(
    user_id BIGINT PRIMARY KEY,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS guilds(
    id BIGINT PRIMARY KEY,
    all_counter BIGINT, --whether a channel is a counter or not
    bot_counter BIGINT,
    member_counter BIGINT,
    category_counter BIGINT,
    welcome_channel BIGINT,
    leave_channel BIGINT,
    twitch_channel BIGINT,
    welcome_text TEXT,
    leave_text TEXT,
    twitch_text TEXT
);

-- modconfig part of customisation table or separate?
CREATE TABLE IF NOT EXISTS guild_config( --contains booleans only
    guild_id BIGINT PRIMARY KEY REFERENCES guilds(id),
    counter_category_denied BOOLEAN DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS ideas(
    id SERIAL PRIMARY KEY,
    author_id BIGINT NOT NULL,
    created_at TIMESTAMP,
    content TEXT,
    title TEXT
);

CREATE TABLE IF NOT EXISTS idea_voters(
    id BIGINT,
    voter_id BIGINT,
    PRIMARY KEY (id, voter_id)
);

-- add to guild orm, but first figure the economy out
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

CREATE TABLE IF NOT EXISTS prefixes(
    guild_id BIGINT,
    prefix VARCHAR(10),
    PRIMARY KEY (prefix, guild_id)
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

CREATE TABLE IF NOT EXISTS twitch_users(
    username TEXT,
    user_id BIGINT,
    guild_id BIGINT REFERENCES guilds(id),
    PRIMARY KEY (username, user_id, guild_id)
);

CREATE TABLE IF NOT EXISTS users(
    id BIGINT PRIMARY KEY,
    xp BIGINT DEFAULT 0,
    level BIGINT DEFAULT 1,
    messages BIGINT DEFAULT 0,
    total_xp BIGINT DEFAULT 0,
    money BIGINT DEFAULT 0,
    worked BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS warnings(
    user_id BIGINT,
    guild_id BIGINT,
    id SERIAL PRIMARY KEY,
    reason TEXT,
    created_at TIMESTAMP,
    warned_by BIGINT
);

ALTER SEQUENCE jobs_id_seq START 10000000 INCREMENT BY 1;
ALTER SEQUENCE warnings_id_seq START 10000000 INCREMENT BY 1;

ALTER TABLE jobs ALTER COLUMN id SET DEFAULT NEXTVAL('jobs_id_seq');
ALTER TABLE warnings ALTER COLUMN id SET DEFAULT NEXTVAL('warnings_id_seq');

-- SINGLE-LINE COMMENT 

COMMIT;