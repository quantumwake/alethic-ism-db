----------------------------------------
------ USAGE TIER ------
----------------------------------------
CREATE TABLE IF NOT EXISTS USAGE_TIER (
  ID VARCHAR(64) PRIMARY KEY,
  -- UNIT CAPS (NULL = UNLIMITED)
  PER_MINUTE BIGINT CHECK (PER_MINUTE IS NULL OR PER_MINUTE >= 0),
  PER_HOUR   BIGINT CHECK (PER_HOUR   IS NULL OR PER_HOUR   >= 0),
  PER_DAY    BIGINT CHECK (PER_DAY    IS NULL OR PER_DAY    >= 0),
  PER_MONTH  BIGINT CHECK (PER_MONTH  IS NULL OR PER_MONTH  >= 0),
  PER_YEAR   BIGINT CHECK (PER_YEAR   IS NULL OR PER_YEAR   >= 0),

  -- COST CAPS (NULL = UNLIMITED). CURRENCY IN YOUR ROLL-UPS (E.G., USD).
  COST_PER_MINUTE   NUMERIC CHECK (COST_PER_MINUTE   IS NULL OR COST_PER_MINUTE   >= 0),
  COST_PER_HOUR     NUMERIC CHECK (COST_PER_HOUR     IS NULL OR COST_PER_HOUR     >= 0),
  COST_PER_DAY      NUMERIC CHECK (COST_PER_DAY      IS NULL OR COST_PER_DAY      >= 0),
  COST_PER_MONTH    NUMERIC CHECK (COST_PER_MONTH    IS NULL OR COST_PER_MONTH    >= 0),
  COST_PER_YEAR     NUMERIC CHECK (COST_PER_YEAR     IS NULL OR COST_PER_YEAR     >= 0)
);

INSERT INTO USAGE_TIER
(ID, PER_MINUTE, PER_HOUR, PER_DAY, PER_MONTH, PER_YEAR,
 COST_PER_MINUTE, COST_PER_HOUR, COST_PER_DAY, COST_PER_MONTH, COST_PER_YEAR)
VALUES
-- TIER 0 – FREE
('TIER0', 1000, 30000, 200000, 6000000, 6000000 * 12,
 0.00, 0.00, 0.00, 0.00, 0.00),

-- TIER 1 – SANDBOX
('TIER1', 5000, 150000, 1000000, 30000000, 30000000 * 12,
 0.02, 0.50, 1.50, 5, 5 * 12),

-- TIER 2 – DEVELOPER
('TIER2', 25000, 750000, 5000000, 150000000, 150000000 * 12,
 0.10, 2.50, 7.50, 25, 25 * 12),

-- TIER 3 – STARTUP
('TIER3', 125000, 3750000, 25000000, 750000000, 750000000 * 2,
 0.50, 12.50, 37.50, 125, 125 * 12),

-- TIER 4 – BUSINESS
('TIER4', 625000, 18750000, 125000000, 3750000000, 3750000000 * 2,
 2.50, 62.50, 187.50, 625, 625 * 12),

-- TIER 5 – ENTERPRISE
('TIER5', 3125000, 93750000, 625000000, 18750000000, 18750000000 * 2,
 12.50, 312.50, 937.50, 3125, 3125 * 12)
ON CONFLICT (ID) DO NOTHING;

COMMIT;

----------------------------------------
------ USER PROFILES AND PROJECTS ------
----------------------------------------
CREATE TABLE USER_PROFILE (
  USER_ID CHARACTER VARYING(36) PRIMARY KEY NOT NULL,
  EMAIL CHARACTER VARYING(255),
  CREATED_DATE TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  NAME CHARACTER VARYING(255),
  TIER_ID VARCHAR(64) NOT NULL DEFAULT 'TIER1' REFERENCES USAGE_TIER (ID)
);

-- CREATE USER PROFILE CREDENTIALS
CREATE TABLE USER_PROFILE_CREDENTIAL (
    USER_ID VARCHAR(36) NOT NULL PRIMARY KEY REFERENCES USER_PROFILE (USER_ID),
    TYPE VARCHAR(255) NOT NULL,
    CREDENTIALS VARCHAR(255) NOT NULL,
    CREATED_DATE TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE USER_PROJECT (
  PROJECT_ID VARCHAR(36) NOT NULL PRIMARY KEY,
  PROJECT_NAME VARCHAR(255) NOT NULL,
  USER_ID VARCHAR(36) NOT NULL REFERENCES USER_PROFILE (USER_ID),
  CREATED_DATE TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (USER_ID, PROJECT_NAME)
);

ALTER TABLE USER_PROJECT ADD COLUMN UPDATED_DATE TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
CREATE INDEX USER_PROJECT_USER_ID_IDX ON USER_PROJECT (USER_ID);

CREATE TABLE WORKFLOW_NODE (
    NODE_ID VARCHAR(36) NOT NULL PRIMARY KEY,
    OBJECT_ID VARCHAR(255) NULL,    -- THE ACTUAL OBJECT ID BASED ON THE IDENTIFIER
    NODE_TYPE VARCHAR(255) NOT NULL,
    NODE_LABEL VARCHAR(255) NULL,
    PROJECT_ID VARCHAR(36) NOT NULL REFERENCES USER_PROJECT (PROJECT_ID),
    POSITION_X INT NULL,
    POSITION_Y INT NULL,
    WIDTH INT NULL,
    HEIGHT INT NULL
);

CREATE TABLE WORKFLOW_EDGE (
    SOURCE_NODE_ID VARCHAR(36) NOT NULL REFERENCES WORKFLOW_NODE (NODE_ID),
    TARGET_NODE_ID VARCHAR(36) NOT NULL REFERENCES  WORKFLOW_NODE (NODE_ID),
    SOURCE_HANDLE VARCHAR(255) NULL,
    TARGET_HANDLE VARCHAR(255) NULL,
    ANIMATED BOOL NOT NULL DEFAULT TRUE,
    EDGE_LABEL VARCHAR(255) NULL,
    TYPE VARCHAR(255) NOT NULL DEFAULT 'DEFAULT',
    PRIMARY KEY (SOURCE_NODE_ID, TARGET_NODE_ID)
);

CREATE TABLE TEMPLATE (
    TEMPLATE_ID VARCHAR(36) NOT NULL PRIMARY KEY,
    TEMPLATE_PATH VARCHAR(255) NOT NULL,
    TEMPLATE_CONTENT TEXT NOT NULL,
    TEMPLATE_TYPE VARCHAR(255) DEFAULT 'USER_TEMPLATE',
    PROJECT_ID VARCHAR(36) NULL REFERENCES USER_PROJECT (PROJECT_ID)
);

CREATE TABLE STATE
(
    ID VARCHAR(36) NOT NULL PRIMARY KEY,
    PROJECT_ID VARCHAR(36) NULL REFERENCES USER_PROJECT (PROJECT_ID),
    COUNT INT NOT NULL DEFAULT 0,
    STATE_TYPE VARCHAR(255) NOT NULL DEFAULT 'STATECONFIG'
);

CREATE TABLE STATE_CONFIG (
    STATE_ID VARCHAR(255) NOT NULL REFERENCES STATE(ID),
    ATTRIBUTE VARCHAR(255) NOT NULL,
    DATA TEXT,
    PRIMARY KEY (STATE_ID, ATTRIBUTE)
);

CREATE TABLE STATE_COLUMN_KEY_DEFINITION(
    ID SERIAL NOT NULL PRIMARY KEY,
    STATE_ID VARCHAR(255) NOT NULL REFERENCES STATE (ID),
    NAME VARCHAR(255) NOT NULL,
    ALIAS VARCHAR(255),
    REQUIRED BOOL DEFAULT FALSE,
    CALLABLE BOOL DEFAULT FALSE,
    DEFINITION_TYPE VARCHAR(255) NOT NULL
);

CREATE TABLE STATE_COLUMN (
    ID SERIAL NOT NULL PRIMARY KEY,
    STATE_ID VARCHAR(36) NOT NULL REFERENCES STATE(ID),
    NAME VARCHAR(255) NOT NULL,
    DATA_TYPE VARCHAR(64) DEFAULT 'STR',
    REQUIRED BOOLEAN DEFAULT TRUE,
    CALLABLE BOOLEAN DEFAULT FALSE,
    MIN_LENGTH INT DEFAULT 0,
    MAX_LENGTH INT DEFAULT 255,
    DIMENSIONS INT DEFAULT 384,
    VALUE VARCHAR(255),
    SOURCE_COLUMN_NAME VARCHAR(255)
);

ALTER TABLE STATE_COLUMN ADD COLUMN DISPLAY_ORDER INT DEFAULT 0;
CREATE UNIQUE INDEX STATE_COLUMN_UNIQUE_KEY ON STATE_COLUMN (ID, STATE_ID);
CREATE UNIQUE INDEX STATE_COLUMN_STATE_NAME_UX ON STATE_COLUMN (STATE_ID, NAME);

CREATE TABLE STATE_COLUMN_DATA
(
    COLUMN_ID BIGINT NOT NULL REFERENCES STATE_COLUMN (ID),
    DATA_INDEX BIGINT NOT NULL,
    DATA_VALUE TEXT,
    DATA_JSON_VALUE JSONB
);

-- GIN index for JSON queries on DATA_JSON_VALUE
CREATE INDEX STATE_COLUMN_DATA_JSON_GIN_IDX
    ON STATE_COLUMN_DATA USING GIN (DATA_JSON_VALUE)
    WHERE DATA_JSON_VALUE IS NOT NULL;

CREATE TABLE STATE_COLUMN_DATA_MAPPING (
    STATE_ID VARCHAR(36) NOT NULL,
    STATE_KEY VARCHAR(255) NOT NULL,
    DATA_INDEX BIGINT NOT NULL,
    PRIMARY KEY (STATE_ID, STATE_KEY, DATA_INDEX)
);

CREATE TABLE PROCESSOR_CLASS (
    CLASS_NAME VARCHAR(32) NOT NULL PRIMARY KEY
);

INSERT INTO PROCESSOR_CLASS VALUES
    ('CodeProcessing'),
    ('NaturalLanguageProcessing'),
    ('ImageProcessing'),
    ('DataProcessing'),
    ('DataConnector'),
    ('TextProcessing'),
    ('VideoProcessing'),
    ('AudioProcessing'),
    ('SignalProcessing'),
    ('MachineLearning'),
    ('DatabaseProcessing'),
    ('Interactive'),
    ('Proprietary')
    ON CONFLICT DO NOTHING;

COMMIT;

CREATE TABLE PROCESSOR_PROVIDER (
    ID VARCHAR(255) PRIMARY KEY,
    NAME VARCHAR(512) NOT NULL,
    VERSION VARCHAR(256) NOT NULL,
    CLASS_NAME VARCHAR(256) NOT NULL REFERENCES PROCESSOR_CLASS (CLASS_NAME),
    USER_ID VARCHAR(36) NULL REFERENCES USER_PROFILE (USER_ID),
    PROJECT_ID VARCHAR(36) NULL REFERENCES USER_PROJECT (PROJECT_ID)
);

ALTER TABLE PROCESSOR_PROVIDER ADD COLUMN ROUTE JSONB NULL;
ALTER TABLE PROCESSOR_PROVIDER ADD COLUMN CREATED_DATE TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE PROCESSOR_PROVIDER ADD COLUMN UPDATED_DATE TIMESTAMP NULL DEFAULT NULL;

INSERT INTO PROCESSOR_PROVIDER (ID, NAME, VERSION, CLASS_NAME) VALUES
 --- GPT 4o
    ('language/models/openai/gpt-4o', 'OpenAI', 'gpt-4o', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4o-mini', 'OpenAI', 'gpt-4o-mini', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4o-2024-05-13', 'OpenAI', 'gpt-4o-2024-05-13', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4o-2024-08-06', 'OpenAI', 'gpt-4o-2024-08-06', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4o-2024-11-20', 'OpenAI', 'gpt-4o-2024-11-20', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4o-latest', 'OpenAI', 'chatgpt-4o-latest', 'NaturalLanguageProcessing'),

 --- GPT 4.1
    ('language/models/openai/gpt-4.1', 'OpenAI', 'gpt-4.1', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4.1-mini', 'OpenAI', 'gpt-4.1-mini', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4.1-nano', 'OpenAI', 'gpt-4.1-nano', 'NaturalLanguageProcessing'),

--- GPT 5
    ('language/models/openai/gpt-5', 'OpenAI', 'gpt-5', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-5-chat-latest', 'OpenAI', 'gpt-5-chat-latest', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-5-mini', 'OpenAI', 'gpt-5-mini', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-5-nano', 'OpenAI', 'gpt-5-nano', 'NaturalLanguageProcessing'),

--- Other OpenAI
    ('language/models/openai/o1-preview', 'OpenAI', 'o1-preview', 'NaturalLanguageProcessing'),
    ('image/models/openai/dall-e-2', 'OpenAI', 'dall-e-2', 'ImageProcessing'),
    ('image/models/openai/dall-e-3', 'OpenAI', 'dall-e-3', 'ImageProcessing'),

-- OpenRouter
    ('language/models/openrouter/openai/gpt-4.1', 'OpenRouter', 'openai/gpt-4.1', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/openai/gpt-4.1-mini', 'OpenRouter', 'openai/gpt-4.1-mini', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/openai/gpt-4.1-nano', 'OpenRouter', 'openai/gpt-4.1-nano', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/openai/gpt-4', 'OpenRouter', 'openai/gpt-4', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/openai/gpt-4o', 'OpenRouter', 'openai/gpt-4o', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/openai/gpt-4-turbo', 'OpenRouter', 'openai/gpt-4-turbo', 'NaturalLanguageProcessing'),

    ('language/models/openrouter/openai/gpt-5', 'OpenRouter', 'openai/gpt-5', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/openai/gpt-5-mini', 'OpenRouter', 'openai/gpt-5-mini', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/openai/gpt-5-codex', 'OpenRouter', 'openai/gpt-5-codex', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/openai/gpt-5-chat', 'OpenRouter', 'openai/gpt-5-chat', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/openai/gpt-5-nano', 'OpenRouter', 'openai/gpt-5-nano', 'NaturalLanguageProcessing'),

    ('language/models/openrouter/google/gemini-2.5-flash', 'OpenRouter', 'google/gemini-2.5-flash', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/google/gemini-2.5-pro', 'OpenRouter', 'google/gemini-2.5-pro', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/google/gemini-2.5-flash-lite', 'OpenRouter', 'google/gemini-2.5-flash-lite', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/google/gemini-pro-1.5', 'OpenRouter', 'google/gemini-pro-1.5', 'NaturalLanguageProcessing'),

    ('language/models/openrouter/x-ai/grok-4', 'OpenRouter', 'x-ai/grok-4', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/x-ai/grok-4-fast', 'OpenRouter', 'x-ai/grok-4-fast', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/x-ai/grok-3', 'OpenRouter', 'x-ai/grok-3', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/x-ai/grok-3-mini', 'OpenRouter', 'x-ai/grok-3-mini', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/x-ai/grok-2', 'OpenRouter', 'x-ai/grok-2', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/x-ai/grok-2-mini', 'OpenRouter', 'x-ai/grok-2-mini', 'NaturalLanguageProcessing'),

    ('language/models/openrouter/moonshotai/kimi-k2', 'OpenRouter', 'moonshotai/kimi-k2', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/anthropic/claude-3-opus', 'OpenRouter', 'anthropic/claude-3-opus', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/anthropic/claude-opus-4', 'OpenRouter', 'anthropic/claude-opus-4', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/anthropic/claude-opus-4.1', 'OpenRouter', 'anthropic/claude-opus-4.1', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/anthropic/claude-sonnet-4.5', 'OpenRouter', 'anthropic/claude-sonnet-4.5', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/anthropic/claude-sonnet-4', 'OpenRouter', 'anthropic/claude-sonnet-4', 'NaturalLanguageProcessing'),

    ('language/models/openrouter/anthropic/claude-3-sonnet', 'OpenRouter', 'anthropic/claude-3-sonnet', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/anthropic/claude-3.5-sonnet', 'OpenRouter', 'anthropic/claude-3.5-sonnet', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/anthropic/claude-3.7-sonnet', 'OpenRouter', 'anthropic/claude-3.7-sonnet', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/anthropic/claude-3.7-sonnet:thinking', 'OpenRouter', 'anthropic/claude-3.7-sonnet:thinking', 'NaturalLanguageProcessing'),

    ('language/models/openrouter/mistralai/mistral-nemo', 'OpenRouter', 'mistralai/mistral-nemo', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/mistralai/mistral-tiny', 'OpenRouter', 'mistralai/mistral-tiny', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/mistralai/mistral-small-3.2-24b-instruct', 'OpenRouter', 'mistralai/mistral-small-3.2-24b-instruct', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/mistralai/mistral-small', 'OpenRouter', 'mistralai/mistral-small', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/mistralai/mistral-medium-3.1', 'OpenRouter', 'mistralai/mistral-medium-3.1', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/mistralai/mistral-large', 'OpenRouter', 'mistralai/mistral-large', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/mistralai/mistral-large-2411', 'OpenRouter', 'mistralai/mistral-large-2411', 'NaturalLanguageProcessing'),

    ('language/models/openrouter/mistralai/magistral-small-2506', 'OpenRouter', 'mistralai/magistral-small-2506', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/mistralai/magistral-medium-2506', 'OpenRouter', 'mistralai/magistral-medium-2506', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/mistralai/magistral-medium-2506:thinking', 'OpenRouter', 'mistralai/magistral-medium-2506:thinking', 'NaturalLanguageProcessing'),

    ('language/models/openrouter/deepseek/deepseek-r1', 'OpenRouter', 'deepseek/deepseek-r1', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/deepseek/deepseek-r1-distill-llama-70b', 'OpenRouter', 'deepseek/deepseek-r1-distill-llama-70b', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/deepseek/deepseek-r1-0528-qwen3-8b', 'OpenRouter', 'deepseek/deepseek-r1-0528-qwen3-8b', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/deepseek/deepseek-r1-distill-qwen-32b', 'OpenRouter', 'deepseek/deepseek-r1-distill-qwen-32b', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/deepseek/deepseek-chat-v3.1', 'OpenRouter', 'deepseek/deepseek-chat-v3.1', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/deepseek/deepseek-v3.1-terminus', 'OpenRouter', 'deepseek/deepseek-v3.1-terminus', 'NaturalLanguageProcessing'),

    ('language/models/openrouter/meta-llama/llama-4-scout', 'OpenRouter', 'meta-llama/llama-4-scout', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/meta-llama/llama-4-maverick', 'OpenRouter', 'meta-llama/llama-4-maverick', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/meta-llama/llama-3.1-405b-instruct', 'OpenRouter', 'meta-llama/llama-3.1-405b-instruct', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/nvidia/llama-3.3-nemotron-super-49b-v1', 'OpenRouter', 'nvidia/llama-3.3-nemotron-super-49b-v1', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/meta-llama/codellama-34b-instruct', 'OpenRouter', 'meta-llama/codellama-34b-instruct', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/meta-llama/llama-guard-4-12b', 'OpenRouter', 'meta-llama/llama-guard-4-12b', 'NaturalLanguageProcessing'),

-- Others
    ('language/models/llama/llama3.1-8b', 'Llama', 'llama3.1-8b', 'NaturalLanguageProcessing'),
    ('language/models/llama/llama3.1-70b', 'Llama', 'llama3.1-70b', 'NaturalLanguageProcessing'),
    ('language/models/llama/llama3.1-405b', 'Llama', 'llama3.1-405b', 'NaturalLanguageProcessing'),
    ('language/models/google/gemini-1.5-flash', 'Google', 'gemini-1.5-flash', 'NaturalLanguageProcessing'),
    ('language/models/google/gemini-1.5-pro-001', 'Google', 'gemini-1.5-pro-001', 'NaturalLanguageProcessing'),

-- Anthropic
    ('language/models/anthropic/claude-2.0', 'Anthropic', 'claude-2', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-2.1', 'Anthropic', 'claude-2.1', 'NaturalLanguageProcessing'),

    ('language/models/anthropic/claude-3-opus-latest', 'Anthropic', 'claude-3-opus-latest', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-3-opus-20240229', 'Anthropic', 'claude-3-opus-20240229', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-4.0-opus-latest', 'Anthropic', 'claude-opus-4-0', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-4.1-opus-latest', 'Anthropic', 'claude-opus-4-1', 'NaturalLanguageProcessing'),

    ('language/models/anthropic/claude-3-5-sonnet-latest', 'Anthropic', 'claude-3-5-sonnet-latest', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-3-5-sonnet-20240620', 'Anthropic', 'claude-3-5-sonnet-20240620', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-3-5-sonnet-20241022', 'Anthropic', 'claude-3-5-sonnet-20241022', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-3-7-sonnet-latest', 'Anthropic', 'claude-3-7-sonnet-latest', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-4.0-sonnet-latest', 'Anthropic', 'claude-sonnet-4-0', 'NaturalLanguageProcessing'),

    ('language/models/anthropic/claude-3-5-haiku-latest', 'Anthropic', 'claude-3-5-haiku-latest', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-3-5-haiku-20241022', 'Anthropic', 'claude-3-5-haiku-20241022', 'NaturalLanguageProcessing'),

    -- Mixers / Data Transformers
    ('data/transformers/mixer/state-online-join-1.0', 'State Online Join', '1.0', 'DataProcessing'),
    ('data/transformers/mixer/state-online-merge-1.0', 'State Online Merge', '1.0', 'DataProcessing'),
    ('data/transformers/mixer/state-online-cross-join-1.0', 'State Online Cross Join', '1.0', 'DataProcessing'),
    ('data/transformers/mixer/state-tables-1.0', 'State Tables', '1.0', 'DataProcessing'),
    ('data/transformers/sampler/state-sample-multiplier-1.0', 'State Sample Multiplier', '1.0', 'DataProcessing'),

    -- Data Source
    ('data/source/sql-1.0', 'SQL Data Source', '1.0', 'DatabaseProcessing'),

    -- File Source Connectors (DataConnector class — renders as connector node on canvas)
    ('data/source/file/tabular-1.0', 'Tabular File Processor', '1.0', 'DataConnector'),
    ('data/source/file/docs-1.0', 'Document File Processor', '1.0', 'DataConnector'),

    -- Code Executors
    ('code/executor/python/python-executor-1.0', 'Python Executor', '1.0', 'CodeProcessing'),
    ('code/executor/mako/mako-executor-1.0', 'Mako Executor', '1.0', 'CodeProcessing'),

    --- User Interactions
    ('interaction/user/user-interaction', 'User Interaction', '1.0', 'Interactive')
ON CONFLICT (ID) DO UPDATE SET
    NAME=EXCLUDED.NAME,
    VERSION=EXCLUDED.VERSION,
    CLASS_NAME=EXCLUDED.CLASS_NAME;

CREATE TYPE PROCESSOR_STATUS AS ENUM (
       'CREATED', 'ROUTE', 'ROUTED',
       'QUEUED', 'RUNNING', 'COMPLETED',
       'TERMINATE', 'STOPPED', 'FAILED'
);

CREATE TABLE PROCESSOR (
    ID VARCHAR(36) NOT NULL PRIMARY KEY,
    PROVIDER_ID VARCHAR(255) NULL REFERENCES PROCESSOR_PROVIDER (ID),
    PROJECT_ID VARCHAR(36) NOT NULL REFERENCES USER_PROJECT (PROJECT_ID),
    STATUS PROCESSOR_STATUS NOT NULL
);

ALTER TABLE PROCESSOR ADD COLUMN PROPERTIES JSONB NULL;
ALTER TABLE PROCESSOR ADD COLUMN NAME VARCHAR(255) NULL;
ALTER TABLE PROCESSOR ADD COLUMN CREATED_DATE TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE PROCESSOR ADD COLUMN UPDATED_DATE TIMESTAMP NULL DEFAULT NULL;

CREATE TYPE PROCESSOR_STATE_DIRECTION AS ENUM (
       'INPUT', 'OUTPUT'
);

CREATE TABLE PROCESSOR_STATE (
    ID VARCHAR(73) NOT NULL,
    INTERNAL_ID SERIAL NOT NULL,
    PROCESSOR_ID VARCHAR(36) NOT NULL,
    STATE_ID VARCHAR(36) NOT NULL REFERENCES STATE (ID),
    DIRECTION PROCESSOR_STATE_DIRECTION NOT NULL,
    STATUS PROCESSOR_STATUS NOT NULL,
    COUNT INT NULL,
    CURRENT_INDEX INT NULL,
    MAXIMUM_INDEX INT NULL,
    EDGE_FUNCTION JSONB NULL,
    PRIMARY KEY (PROCESSOR_ID, STATE_ID, DIRECTION),
    UNIQUE (INTERNAL_ID),
    UNIQUE (ID)
);

ALTER TABLE PROCESSOR_STATE ADD CONSTRAINT PROCESSOR_STATE_STATE_ID_FK FOREIGN KEY (STATE_ID) REFERENCES STATE(ID);
ALTER TABLE PROCESSOR_STATE ADD CONSTRAINT PROCESSOR_STATE_PROCESSOR_ID_FK FOREIGN KEY (PROCESSOR_ID) REFERENCES PROCESSOR(ID);
COMMIT;

-- CREATE TABLE IF NOT EXISTS TRACE
-- (
--     ID SERIAL NOT NULL PRIMARY KEY,
--     PARTITION   VARCHAR(128)                            NOT NULL,
--     REFERENCE   VARCHAR(128)                            NOT NULL,
--     ACTION      VARCHAR(255)                            NOT NULL,
--     ACTION_TIME TIMESTAMP   DEFAULT CURRENT_TIMESTAMP   NOT NULL,
--     LEVEL       TRACE_LEVEL DEFAULT 'INFO'::TRACE_LEVEL NOT NULL,
--     MESSAGE     TEXT
-- );

CREATE TABLE MONITOR_LOG_EVENT (
    LOG_ID SERIAL NOT NULL PRIMARY KEY,
    LOG_TYPE VARCHAR(255) NOT NULL, -- TODO SHOULD BE AN ENUM OF TYPE LOG_TYPE
    LOG_TIME TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INTERNAL_REFERENCE_ID INT NULL, -- AN INTERNAL ID DEPENDING ON WHAT IS BEING MONITORED, E.G. A PROCESSOR_STATE INTERNAL_ID
    USER_ID VARCHAR(36) NULL,       -- THIS IS USEFUL WHEN PROCESSOR_STATE_ID IS NOT DEFINED
    PROJECT_ID VARCHAR(36) NULL,    -- THIS IS USEFUL WHEN PROCESSOR_STATE_ID IS NOT DEFINED
    EXCEPTION TEXT NULL,
    DATA TEXT NULL
);

CREATE OR REPLACE VIEW STATE_COLUMN_DATA_VIEW
AS
SELECT SC.*, SD.* FROM STATE_COLUMN SC
 LEFT OUTER JOIN STATE_COLUMN_DATA SD
   ON SC.ID = SD.COLUMN_ID
ORDER BY STATE_ID, DATA_INDEX, COLUMN_ID;

--- VALIDATION FUNCTION FOR COLUMN ID
CREATE OR REPLACE FUNCTION VALIDATE_COLUMN_ID(NEW_ID BIGINT, NEW_STATE_ID VARCHAR)
RETURNS BIGINT AS $$
DECLARE
    RESULT BIGINT;
BEGIN
    IF NEW_ID IS NOT NULL THEN
        -- CHECK IF THE PROVIDED ID EXISTS WITH THE GIVEN STATE_ID
        IF EXISTS (SELECT 1 FROM STATE_COLUMN WHERE ID = NEW_ID AND STATE_ID = NEW_STATE_ID) THEN
            RESULT := NEW_ID;
        -- CHECK IF THE PROVIDED ID EXISTS WITH A DIFFERENT STATE_ID
        ELSIF EXISTS (SELECT 1 FROM STATE_COLUMN WHERE ID = NEW_ID) THEN
            RAISE EXCEPTION 'ILLEGAL ID: THE PROVIDED ID ALREADY EXISTS WITH A DIFFERENT STATE_ID';
        ELSE
            RESULT := NULL;
        END IF;
    ELSE
        RESULT := NULL;
    END IF;

    RETURN RESULT;
END;
$$ LANGUAGE PLPGSQL;


-- AUTO-GENERATED DEFINITION
CREATE TYPE USAGE_UNIT_TYPE AS ENUM ('TOKEN', 'COMPUTE');
CREATE TYPE USAGE_UNIT_SUBTYPE AS ENUM ('INPUT', 'OUTPUT');

CREATE TABLE IF NOT EXISTS USAGE
(
    ID               SERIAL PRIMARY KEY,
    TRANSACTION_TIME TIMESTAMP,
    PROJECT_ID       VARCHAR(36)        NOT NULL REFERENCES PUBLIC.USER_PROJECT,
    RESOURCE_ID      VARCHAR(255)       NOT NULL,
    RESOURCE_TYPE    VARCHAR(255)       NOT NULL,
    UNIT_TYPE        USAGE_UNIT_TYPE    NOT NULL,
    UNIT_SUBTYPE     USAGE_UNIT_SUBTYPE NOT NULL,
    UNIT_COUNT       INTEGER DEFAULT 0  NOT NULL,
    METADATA         TEXT
);

CREATE INDEX USAGE_PROJECT_IDX ON USAGE (PROJECT_ID);
CREATE INDEX USAGE_PROJECT_TIME_IDX ON USAGE (PROJECT_ID, TRANSACTION_TIME);

------------------------------------------------------------------
-- SESSION AND SESSION MESSAGES FOR TRACKING USER INTERACTIONS
------------------------------------------------------------------
CREATE TABLE SESSION (
    SESSION_ID VARCHAR(36) NOT NULL PRIMARY KEY,
    CREATED_DATE    TIMESTAMP NOT NULL,
    OWNER_USER_ID   VARCHAR(36) NOT NULL REFERENCES USER_PROFILE (USER_ID)
);

CREATE TABLE SESSION_MESSAGE (
    MESSAGE_ID SERIAL NOT NULL PRIMARY KEY,
    SESSION_ID VARCHAR(36) NOT NULL REFERENCES SESSION (SESSION_ID),
    USER_ID VARCHAR(36) NOT NULL REFERENCES USER_PROFILE (USER_ID),
    ORIGINAL_CONTENT TEXT NULL,
    EXECUTED_CONTENT TEXT NULL,
    MESSAGE_DATE TIMESTAMP NOT NULL
);

CREATE TYPE USER_SESSION_ACCESS_LEVEL AS ENUM ('DEFAULT', 'ADMIN');

CREATE TABLE USER_SESSION_ACCESS (
    USER_ID VARCHAR(36) NOT NULL REFERENCES USER_PROFILE (USER_ID),
    SESSION_ID VARCHAR(36) NOT NULL REFERENCES SESSION (SESSION_ID),
    ACCESS_LEVEL USER_SESSION_ACCESS_LEVEL NOT NULL DEFAULT 'DEFAULT',
    ACCESS_DATE TIMESTAMP NOT NULL
);

drop table if exists vault cascade;
drop type if exists config_type cascade;
drop table if exists config_map cascade;

--------------------------
---- VAULT START
--------------------------
-- DEFINE ENUM FOR CONFIGURATION TYPES
CREATE TYPE CONFIG_TYPE AS ENUM ('secret', 'config_map');

create table config_map
(
    id           varchar(36)  not null primary key,
    name         varchar(255) not null,
    type         config_type  not null,
    data         jsonb        not null,
    vault_key_id varchar(255),
    vault_id     varchar(36),
    owner_id     varchar(36),
    created_at   timestamp default now(),
    updated_at   timestamp default now(),
    deleted_at   timestamp
);

create index idx_configuration_data on config_map using gin (data jsonb_path_ops);
create index idx_configuration_type on config_map (type);

create table vault(
    id         varchar(36) default gen_random_uuid() not null primary key,
    name       varchar(255)                          not null,
    owner_id   varchar(36)                           not null,
    type       varchar(50)                           not null,
    metadata   jsonb,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);

create index idx_vault_type on vault (owner_id);

--------------------------
---- VAULT END
--------------------------

-- TABLE FOR FILTERS
CREATE TABLE FILTER (
    ID VARCHAR(255) PRIMARY KEY, -- UNIQUE IDENTIFIER FOR THE FILTER
    NAME VARCHAR(255), -- FILTER NAME
    USER_ID VARCHAR(36) NOT NULL REFERENCES USER_PROFILE(USER_ID), -- OWNER OF THE FILTER
    FILTER_ITEMS JSONB NOT NULL DEFAULT '{}', -- FILTER ITEMS STORED AS JSON
    CREATED_DATE TIMESTAMP DEFAULT NOW(),
    UPDATED_DATE TIMESTAMP DEFAULT NOW()
);

-- INDEX FOR USER_ID TO OPTIMIZE QUERIES BY USER
CREATE INDEX IDX_FILTER_USER_ID ON FILTER(USER_ID);

-- INDEX FOR JSONB FILTER_ITEMS TO OPTIMIZE QUERIES
CREATE INDEX IDX_FILTER_ITEMS ON FILTER USING GIN(FILTER_ITEMS JSONB_PATH_OPS);

CREATE INDEX PROCESSOR_STATE_PROCESSOR_DIRECTION_IDX ON PROCESSOR_STATE (PROCESSOR_ID, DIRECTION);
CREATE INDEX PROCESSOR_STATE_STATE_DIRECTION_IDX ON PROCESSOR_STATE (STATE_ID, DIRECTION);
CREATE INDEX PROCESSOR_STATE_PROCESSOR ON PROCESSOR_STATE (PROCESSOR_ID);
CREATE INDEX PROCESSOR_STATE_STATE ON PROCESSOR_STATE (STATE_ID);

CREATE INDEX STATE_PROJECT_IDX ON STATE (PROJECT_ID);
CREATE INDEX PROCESSOR_PROJECT_IDX ON PROCESSOR (PROJECT_ID);
CREATE INDEX STATE_COLUMN_STATE_IDX ON STATE_COLUMN (STATE_ID);

CREATE INDEX STATE_CONFIG_STATE_IDX ON STATE_CONFIG (STATE_ID);
CREATE INDEX TEMPLATE_PROJECT_IDX ON TEMPLATE (PROJECT_ID);
CREATE INDEX WORKFLOW_NODE_PROJECT_IDX ON WORKFLOW_NODE (PROJECT_ID);
CREATE INDEX STATE_COLUMN_KEY_DEFINITION_STATE_IDX ON STATE_COLUMN_KEY_DEFINITION (STATE_ID);
CREATE UNIQUE INDEX STATE_COLUMN_KEY_DEFINITION_STATE_NAME_TYPE_IDX ON STATE_COLUMN_KEY_DEFINITION (STATE_ID, NAME, DEFINITION_TYPE);
CREATE INDEX STATE_COLUMN_DATA_MAPPING_STATE_IDX ON STATE_COLUMN_DATA_MAPPING (STATE_ID);
CREATE INDEX MONITOR_LOG_EVENT_USER_ID ON MONITOR_LOG_EVENT (USER_ID);
CREATE INDEX MONITOR_LOG_EVENT_PROJECT_ID ON MONITOR_LOG_EVENT (PROJECT_ID);
CREATE INDEX MONITOR_LOG_EVENT_USER_AND_PROJECT_ID ON MONITOR_LOG_EVENT (USER_ID, PROJECT_ID);

-- CREATE UNIQUE INDEX
CREATE EXTENSION IF NOT EXISTS PG_TRGM;

CREATE UNIQUE INDEX IF NOT EXISTS STATE_COLUMN_DATA_COMP_UX
    ON PUBLIC.STATE_COLUMN_DATA (COLUMN_ID, DATA_INDEX);
CREATE INDEX STATE_COLUMN_DATA_COLUMN_IDX
    ON PUBLIC.STATE_COLUMN_DATA (COLUMN_ID);
CREATE INDEX STATE_COLUMN_DATA_TRGM_IDX
    ON PUBLIC.STATE_COLUMN_DATA USING GIN (DATA_VALUE PUBLIC.GIN_TRGM_OPS);


-- CREATE ENUM TYPE FOR ACTION_TYPE
CREATE TYPE ACTION_TYPE_ENUM AS ENUM ('SLIDER', 'TEXT', 'YES/NO', 'DROPDOWN');

-- CREATE THE MAIN TABLE
CREATE TABLE STATE_ACTION_DEFINITION (
    ID VARCHAR(36) PRIMARY KEY, -- AUTOMATICALLY GENERATE A UUID IF NOT PROVIDED
    STATE_ID VARCHAR(36) NOT NULL,                       -- FOREIGN KEY, IF NEEDED, CAN BE DEFINED HERE
    ACTION_TYPE ACTION_TYPE_ENUM NOT NULL,       -- ENUM TYPE FOR ACTION TYPE
    FIELD VARCHAR(255) NOT NULL,                 -- OPTIONAL FIELD NAME
    REMOTE_URL VARCHAR(4000) DEFAULT NULL,            -- DEFAULTS TO FALSE IF NOT PROVIDED
    FIELD_OPTIONS JSON NOT NULL,                -- FIELD OPTIONS AS RAW JSON
    CREATED_DATE TIMESTAMPTZ DEFAULT NOW()        -- AUTOMATICALLY SET TO CURRENT TIMESTAMP
);
CREATE INDEX STATE_ACTION_DEFINITION_STATE_IDX ON STATE_ACTION_DEFINITION (STATE_ID);

----------------------------------------
------ METADATA / SETTINGS COLUMNS ------
----------------------------------------
-- Add metadata column to WORKFLOW_NODE for storing UI state (collapsed, custom settings, etc.)
ALTER TABLE WORKFLOW_NODE ADD COLUMN IF NOT EXISTS METADATA JSONB NULL;

-- Add settings column to USER_PROFILE for user preferences
ALTER TABLE USER_PROFILE ADD COLUMN IF NOT EXISTS SETTINGS JSONB NULL;

-- Add settings column to USER_PROJECT for project-specific settings
ALTER TABLE USER_PROJECT ADD COLUMN IF NOT EXISTS SETTINGS JSONB NULL;

-- Add properties JSONB column to STATE for StateProperties model
ALTER TABLE STATE ADD COLUMN IF NOT EXISTS PROPERTIES JSONB NULL;