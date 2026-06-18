-- TSH SQLite Schema v1.0.0
-- High-volume searchable data: commands, caveats, field notices, platforms
-- Each .db file gets its own subset of these tables.
-- Run: sqlite3 commands.db < schema.sql (etc.) or use tools/migrate/ scripts.

----------------------------------------------------------------------
-- commands.db
----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS commands (
  id INTEGER PRIMARY KEY,
  os TEXT NOT NULL,
  version TEXT NOT NULL,
  version_min TEXT,
  version_max TEXT,
  platform TEXT,
  syntax TEXT NOT NULL,
  description TEXT,
  defaults TEXT,
  mode TEXT,
  context TEXT,
  UNIQUE(os, version, platform, syntax)
);

CREATE INDEX IF NOT EXISTS idx_cmd_os_ver ON commands(os, version);
CREATE INDEX IF NOT EXISTS idx_cmd_os_plat ON commands(os, platform);
CREATE INDEX IF NOT EXISTS idx_cmd_syntax ON commands(syntax);

CREATE VIRTUAL TABLE IF NOT EXISTS commands_fts USING fts5(
  syntax, description,
  content='commands',
  content_rowid='id'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS commands_ai AFTER INSERT ON commands BEGIN
  INSERT INTO commands_fts(rowid, syntax, description) VALUES (new.id, new.syntax, new.description);
END;
CREATE TRIGGER IF NOT EXISTS commands_ad AFTER DELETE ON commands BEGIN
  INSERT INTO commands_fts(commands_fts, rowid, syntax, description) VALUES('delete', old.id, old.syntax, old.description);
END;
CREATE TRIGGER IF NOT EXISTS commands_au AFTER UPDATE ON commands BEGIN
  INSERT INTO commands_fts(commands_fts, rowid, syntax, description) VALUES('delete', old.id, old.syntax, old.description);
  INSERT INTO commands_fts(rowid, syntax, description) VALUES (new.id, new.syntax, new.description);
END;

----------------------------------------------------------------------
-- caveats.db
----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS caveats (
  id INTEGER PRIMARY KEY,
  os TEXT NOT NULL,
  csc_id TEXT,
  headline TEXT NOT NULL,
  description TEXT,
  severity TEXT,
  affected_versions TEXT,
  affected_platforms TEXT,
  affected_pids TEXT,
  fixed_in TEXT,
  keywords TEXT,
  UNIQUE(os, csc_id)
);

CREATE INDEX IF NOT EXISTS idx_cav_csc ON caveats(csc_id);
CREATE INDEX IF NOT EXISTS idx_cav_os ON caveats(os);
CREATE INDEX IF NOT EXISTS idx_cav_severity ON caveats(severity);

CREATE VIRTUAL TABLE IF NOT EXISTS caveats_fts USING fts5(
  headline, description, keywords,
  content='caveats',
  content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS caveats_ai AFTER INSERT ON caveats BEGIN
  INSERT INTO caveats_fts(rowid, headline, description, keywords) VALUES (new.id, new.headline, new.description, new.keywords);
END;
CREATE TRIGGER IF NOT EXISTS caveats_ad AFTER DELETE ON caveats BEGIN
  INSERT INTO caveats_fts(caveats_fts, rowid, headline, description, keywords) VALUES('delete', old.id, old.headline, old.description, old.keywords);
END;
CREATE TRIGGER IF NOT EXISTS caveats_au AFTER UPDATE ON caveats BEGIN
  INSERT INTO caveats_fts(caveats_fts, rowid, headline, description, keywords) VALUES('delete', old.id, old.headline, old.description, old.keywords);
  INSERT INTO caveats_fts(rowid, headline, description, keywords) VALUES (new.id, new.headline, new.description, new.keywords);
END;

----------------------------------------------------------------------
-- field_notices.db
----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS field_notices (
  id INTEGER PRIMARY KEY,
  os TEXT,
  fn_id TEXT,
  csc_id TEXT,
  severity TEXT,
  headline TEXT NOT NULL,
  description TEXT,
  symptoms TEXT,
  solution TEXT,
  affected_pids TEXT,
  affected_platforms TEXT,
  affected_versions TEXT,
  UNIQUE(fn_id)
);

CREATE INDEX IF NOT EXISTS idx_fn_os ON field_notices(os);
CREATE INDEX IF NOT EXISTS idx_fn_csc ON field_notices(csc_id);

CREATE VIRTUAL TABLE IF NOT EXISTS field_notices_fts USING fts5(
  headline, description, symptoms,
  content='field_notices',
  content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS fn_ai AFTER INSERT ON field_notices BEGIN
  INSERT INTO field_notices_fts(rowid, headline, description, symptoms) VALUES (new.id, new.headline, new.description, new.symptoms);
END;
CREATE TRIGGER IF NOT EXISTS fn_ad AFTER DELETE ON field_notices BEGIN
  INSERT INTO field_notices_fts(field_notices_fts, rowid, headline, description, symptoms) VALUES('delete', old.id, old.headline, old.description, old.symptoms);
END;
CREATE TRIGGER IF NOT EXISTS fn_au AFTER UPDATE ON field_notices BEGIN
  INSERT INTO field_notices_fts(field_notices_fts, rowid, headline, description, symptoms) VALUES('delete', old.id, old.headline, old.description, old.symptoms);
  INSERT INTO field_notices_fts(rowid, headline, description, symptoms) VALUES (new.id, new.headline, new.description, new.symptoms);
END;

----------------------------------------------------------------------
-- platforms.db
----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS platforms (
  id INTEGER PRIMARY KEY,
  platform_id TEXT NOT NULL,
  platform_family TEXT NOT NULL,
  os TEXT NOT NULL,
  chassis_type TEXT,
  asic_family TEXT,
  asic_model TEXT,
  total_ports INTEGER,
  total_bandwidth_tbps REAL,
  UNIQUE(platform_id)
);

CREATE INDEX IF NOT EXISTS idx_plat_os ON platforms(os);
CREATE INDEX IF NOT EXISTS idx_plat_asic ON platforms(asic_family);
CREATE INDEX IF NOT EXISTS idx_plat_family ON platforms(platform_family);

CREATE TABLE IF NOT EXISTS platform_ports (
  id INTEGER PRIMARY KEY,
  platform_id TEXT NOT NULL REFERENCES platforms(platform_id),
  asic_id INTEGER,
  slice_id INTEGER,
  port_label TEXT,
  native_speed TEXT,
  breakout_options TEXT,
  UNIQUE(platform_id, port_label)
);

CREATE INDEX IF NOT EXISTS idx_pp_platform ON platform_ports(platform_id);
CREATE INDEX IF NOT EXISTS idx_pp_asic ON platform_ports(asic_id);

----------------------------------------------------------------------
-- metadata table (shared across all .db files)
----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS _metadata (
  key TEXT PRIMARY KEY,
  value TEXT
);

INSERT OR REPLACE INTO _metadata (key, value) VALUES
  ('schema_version', '1.0.0'),
  ('created_at', datetime('now')),
  ('description', 'TSH datastore — high-volume searchable records');
