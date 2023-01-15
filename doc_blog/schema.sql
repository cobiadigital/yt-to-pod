DROP TABLE IF EXISTS voices;
DROP TABLE IF EXISTS post;

CREATE TABLE "voices"
(
    id         TEXT,
    voice_name TEXT
);

CREATE TABLE "post"
(
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    slug        TEXT not null,
    response    TEXT,
    audio       TEXT,
    voice       TEXT,
    audio_size  INTEGER
);