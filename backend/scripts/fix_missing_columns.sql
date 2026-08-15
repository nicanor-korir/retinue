-- Fix missing context intelligence columns
-- Run this if alembic migration didn't apply correctly

-- Add columns to conversations table (if they don't exist)
DO $$
BEGIN
    -- Add context_summary column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations'
        AND column_name = 'context_summary'
    ) THEN
        ALTER TABLE conversations
        ADD COLUMN context_summary JSONB DEFAULT '{}';
        RAISE NOTICE 'Added context_summary column to conversations';
    ELSE
        RAISE NOTICE 'context_summary column already exists';
    END IF;

    -- Add active_entities column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversations'
        AND column_name = 'active_entities'
    ) THEN
        ALTER TABLE conversations
        ADD COLUMN active_entities JSONB DEFAULT '{}';
        RAISE NOTICE 'Added active_entities column to conversations';
    ELSE
        RAISE NOTICE 'active_entities column already exists';
    END IF;
END $$;

-- Add columns to conversation_messages table (if they don't exist)
DO $$
BEGIN
    -- Add extracted_entities column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversation_messages'
        AND column_name = 'extracted_entities'
    ) THEN
        ALTER TABLE conversation_messages
        ADD COLUMN extracted_entities JSONB DEFAULT '{}';
        RAISE NOTICE 'Added extracted_entities column to conversation_messages';
    ELSE
        RAISE NOTICE 'extracted_entities column already exists';
    END IF;

    -- Add intent_classification column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversation_messages'
        AND column_name = 'intent_classification'
    ) THEN
        ALTER TABLE conversation_messages
        ADD COLUMN intent_classification VARCHAR(50);
        RAISE NOTICE 'Added intent_classification column to conversation_messages';
    ELSE
        RAISE NOTICE 'intent_classification column already exists';
    END IF;

    -- Add semantic_summary column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'conversation_messages'
        AND column_name = 'semantic_summary'
    ) THEN
        ALTER TABLE conversation_messages
        ADD COLUMN semantic_summary TEXT;
        RAISE NOTICE 'Added semantic_summary column to conversation_messages';
    ELSE
        RAISE NOTICE 'semantic_summary column already exists';
    END IF;
END $$;

-- Verify columns were added
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name IN ('conversations', 'conversation_messages')
AND column_name IN ('context_summary', 'active_entities', 'extracted_entities', 'intent_classification', 'semantic_summary')
ORDER BY table_name, column_name;
