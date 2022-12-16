CREATE TABLE "voices"
(
    id         TEXT,
    voice_name TEXT
)
CREATE TABLE music
(
    intro_music TEXT,
    mid_music   TEXT,
    end_music   TEXT
)
CREATE TABLE "defaults"
(
    title     TEXT,
    slug      TEXT,
    cold_open TEXT,
    intro     TEXT,
    body      TEXT,
    ending    TEXT,
    voice     TEXT
)
CREATE TABLE "post"
(
    id          INTEGER
        primary key autoincrement,
    created     TIMESTAMP default CURRENT_TIMESTAMP not null,
    title       TEXT not null,
    slug        TEXT not null,
    cold_open   TEXT not null,
    intro_music TEXT not null,
    intro       TEXT not null,
    body        TEXT not null,
    mid_music   TEXT not null,
    ending      TEXT not null,
    end_music   TEXT not null,
    audio       TEXT,
    voice       TEXT,
    audio_size  INTEGER,
)