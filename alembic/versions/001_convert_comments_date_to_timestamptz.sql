-- Migration: Convert comments.date and images.uploaded_at from TIMESTAMP to TIMESTAMPTZ
--
-- This migration handles existing data by treating naive timestamps as UTC.
-- Execute this in Supabase SQL Editor BEFORE deploying backend code changes.
--
-- Author: Claude Code
-- Date: 2025-12-17

BEGIN;

-- ==============================================================================
-- STEP 1: Migrate comments.date column
-- ==============================================================================

-- Add temporary column with TIMESTAMPTZ type
ALTER TABLE comments
ADD COLUMN date_new TIMESTAMPTZ;

-- Copy existing data, treating naive timestamps as UTC
-- If date is NULL, leave it NULL
UPDATE comments
SET date_new = date AT TIME ZONE 'UTC'
WHERE date IS NOT NULL;

-- Drop the old column
ALTER TABLE comments
DROP COLUMN date;

-- Rename the new column to 'date'
ALTER TABLE comments
RENAME COLUMN date_new TO date;

-- Add default for new records (UTC now)
ALTER TABLE comments
ALTER COLUMN date SET DEFAULT NOW();

-- ==============================================================================
-- STEP 2: Migrate images.uploaded_at column
-- ==============================================================================

-- Add temporary column with TIMESTAMPTZ type
ALTER TABLE images
ADD COLUMN uploaded_at_new TIMESTAMPTZ;

-- Copy existing data, treating naive timestamps as UTC
-- If uploaded_at is NULL, leave it NULL
UPDATE images
SET uploaded_at_new = uploaded_at AT TIME ZONE 'UTC'
WHERE uploaded_at IS NOT NULL;

-- Drop the old column
ALTER TABLE images
DROP COLUMN uploaded_at;

-- Rename the new column to 'uploaded_at'
ALTER TABLE images
RENAME COLUMN uploaded_at_new TO uploaded_at;

-- Add default for new records (UTC now)
ALTER TABLE images
ALTER COLUMN uploaded_at SET DEFAULT NOW();

-- ==============================================================================
-- STEP 3: Verify the changes
-- ==============================================================================

DO $$
DECLARE
    comments_type TEXT;
    images_type TEXT;
BEGIN
    -- Check comments.date column type
    SELECT data_type INTO comments_type
    FROM information_schema.columns
    WHERE table_name = 'comments'
    AND column_name = 'date';

    -- Check images.uploaded_at column type
    SELECT data_type INTO images_type
    FROM information_schema.columns
    WHERE table_name = 'images'
    AND column_name = 'uploaded_at';

    -- Verify both columns are now TIMESTAMPTZ
    IF comments_type = 'timestamp with time zone' AND images_type = 'timestamp with time zone' THEN
        RAISE NOTICE 'Migration successful!';
        RAISE NOTICE 'comments.date is now: %', comments_type;
        RAISE NOTICE 'images.uploaded_at is now: %', images_type;
    ELSE
        RAISE EXCEPTION 'Migration failed! comments.date: %, images.uploaded_at: %',
                        comments_type, images_type;
    END IF;
END $$;

COMMIT;

-- ==============================================================================
-- POST-MIGRATION VERIFICATION QUERIES
-- ==============================================================================

-- Run these queries after migration to verify success:

-- 1. Check column types
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name IN ('comments', 'images')
  AND column_name IN ('date', 'uploaded_at')
ORDER BY table_name, column_name;
-- Expected: data_type = 'timestamp with time zone'

-- 2. Check sample data with timezone
SELECT
    id,
    date,
    date AT TIME ZONE 'Asia/Ho_Chi_Minh' AS date_vietnam,
    EXTRACT(TIMEZONE FROM date) AS timezone_offset
FROM comments
WHERE date IS NOT NULL
LIMIT 5;
-- Expected: timezone_offset = 0 (UTC)

-- 3. Check images sample data with timezone
SELECT
    id,
    uploaded_at,
    uploaded_at AT TIME ZONE 'Asia/Ho_Chi_Minh' AS uploaded_at_vietnam,
    EXTRACT(TIMEZONE FROM uploaded_at) AS timezone_offset
FROM images
WHERE uploaded_at IS NOT NULL
LIMIT 5;
-- Expected: timezone_offset = 0 (UTC)

-- ==============================================================================
-- ROLLBACK PLAN (if needed)
-- ==============================================================================

-- If you need to rollback this migration, run:
/*
BEGIN;

-- Rollback comments.date
ALTER TABLE comments ADD COLUMN date_old TIMESTAMP;
UPDATE comments SET date_old = date::TIMESTAMP WHERE date IS NOT NULL;
ALTER TABLE comments DROP COLUMN date;
ALTER TABLE comments RENAME COLUMN date_old TO date;

-- Rollback images.uploaded_at
ALTER TABLE images ADD COLUMN uploaded_at_old TIMESTAMP;
UPDATE images SET uploaded_at_old = uploaded_at::TIMESTAMP WHERE uploaded_at IS NOT NULL;
ALTER TABLE images DROP COLUMN uploaded_at;
ALTER TABLE images RENAME COLUMN uploaded_at_old TO uploaded_at;

COMMIT;
*/
