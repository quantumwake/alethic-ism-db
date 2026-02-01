-- Migration: Add edge_function column to processor_state table
-- Date: 2026-01-31
-- Description: Adds JSONB column for edge function configuration on processor state transitions

-- Add edge_function column to processor_state
ALTER TABLE PROCESSOR_STATE ADD COLUMN IF NOT EXISTS EDGE_FUNCTION JSONB NULL;

-- Comment for documentation
COMMENT ON COLUMN PROCESSOR_STATE.EDGE_FUNCTION IS 'Edge function configuration for processor state transitions. Contains function_type, enabled, template_id, max_attempts, and config fields.';

COMMIT;
