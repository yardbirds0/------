-- ========================================
-- Chat Database Schema
-- For Cherry Studio UI Chat Persistence
-- ========================================

-- ----------------------------------------
-- Sessions Table
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    settings_json TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at DESC);

-- ----------------------------------------
-- Session Prompts Table
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS session_prompts (
    session_id TEXT PRIMARY KEY,
    group_name TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- ----------------------------------------
-- Session Prompt History Table
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS session_prompt_history (
    session_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    group_name TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, version),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_session_prompt_history
    ON session_prompt_history(session_id, version DESC);

-- ----------------------------------------
-- Messages Table
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT DEFAULT '{}',
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp);

-- ----------------------------------------
-- Full-Text Search Virtual Table (FTS5)
-- ----------------------------------------
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    content,
    content='messages',
    content_rowid='rowid'
);

-- ----------------------------------------
-- Triggers to Keep FTS in Sync
-- ----------------------------------------

-- Trigger: After INSERT on messages
CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (new.rowid, new.content);
END;

-- Trigger: After DELETE on messages
CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
    DELETE FROM messages_fts WHERE rowid = old.rowid;
END;

-- Trigger: After UPDATE on messages
CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
    UPDATE messages_fts SET content = new.content WHERE rowid = new.rowid;
END;

-- ========================================
-- End of Schema
-- ========================================
