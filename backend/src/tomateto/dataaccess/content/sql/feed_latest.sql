WITH page AS MATERIALIZED (
    SELECT p.id, p.user_id, p.dish_id, p.caption, p.created_at, p.updated_at
    FROM posts p
    WHERE NOT p.is_hidden AND (CAST(:author_id AS BIGINT) IS NULL OR p.user_id = CAST(:author_id AS BIGINT))
      AND NOT (p.user_id = ANY(CAST(:blocked_user_ids AS BIGINT[])))
      AND (CAST(:viewer_id AS BIGINT) IS NULL OR NOT EXISTS (
        SELECT 1 FROM user_blocks b
        WHERE (b.blocker_id = CAST(:viewer_id AS BIGINT) AND b.blocked_id = p.user_id)
           OR (b.blocker_id = p.user_id AND b.blocked_id = CAST(:viewer_id AS BIGINT))
    ))
      AND (CAST(:after_time AS TIMESTAMPTZ) IS NULL OR (p.created_at, p.id) < (CAST(:after_time AS TIMESTAMPTZ), CAST(:after_id AS BIGINT)))
    ORDER BY p.created_at DESC, p.id DESC
    LIMIT (CAST(:first AS INTEGER) + 1)
), like_counts AS (
    SELECT l.post_id, count(*) AS like_count
    FROM likes l JOIN page p ON p.id = l.post_id GROUP BY l.post_id
), images AS (
    SELECT pi.post_id,
           jsonb_agg(jsonb_build_object('imageId', pi.id, 'url', ma.url,
                     'position', pi.position) ORDER BY pi.position, pi.id) AS images
    FROM post_images pi JOIN page p ON p.id = pi.post_id
    JOIN media_assets ma ON ma.id = pi.media_id
    GROUP BY pi.post_id
)
SELECT p.id, p.user_id, p.dish_id, d.name AS dish_name, p.caption, p.created_at, p.updated_at,
       coalesce(l.like_count, 0) AS like_count,
       CASE WHEN CAST(:viewer_id AS BIGINT) IS NULL THEN NULL ELSE EXISTS (
           SELECT 1 FROM likes x WHERE x.user_id = CAST(:viewer_id AS BIGINT) AND x.post_id = p.id
       ) END AS is_liked,
       CASE WHEN CAST(:viewer_id AS BIGINT) IS NULL THEN NULL ELSE EXISTS (
           SELECT 1 FROM collection_items ci JOIN collections c ON c.id = ci.collection_id
           WHERE c.user_id = CAST(:viewer_id AS BIGINT) AND ci.post_id = p.id
       ) END AS is_saved,
       coalesce(i.images, '[]'::jsonb) AS images
FROM page p JOIN dishes d ON d.id = p.dish_id
LEFT JOIN like_counts l ON l.post_id = p.id LEFT JOIN images i ON i.post_id = p.id
ORDER BY p.created_at DESC, p.id DESC;
