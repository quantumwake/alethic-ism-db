-- Migration: Add properties JSONB column to STATE table
-- Date: 2026-03-09
-- Description: Stores StateProperties model (execution strategy, routing, persistence, inheritance, output enrichments)

ALTER TABLE STATE ADD COLUMN IF NOT EXISTS PROPERTIES JSONB NULL;

COMMENT ON COLUMN STATE.PROPERTIES IS 'StateProperties JSON — execution strategy, routing mode, persistence, inheritance, output enrichments, dedup_enabled, append_to_session';

COMMIT;
