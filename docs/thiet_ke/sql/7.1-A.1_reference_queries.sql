-- DOC 7.1-A.1 / DB S6 WBS 6.2.2 / version 1.5 / 2026-11-16
-- Q06 aligns BE DOC 7.1 v1.5 section 7 at 5061503; not a team approval.
-- Q08 pool and Q15 internal Tag acceptance remain pending Lead/DB decisions.
-- REFERENCE ONLY: load into a disposable PostgreSQL 16 database with DOC 6.4 DDL.
-- PREPARE is session-local. No permanent schema changes, migrations or provider calls.
-- Repository validates principal, first in [1,50], cursor context and parameter pairs.
SET search_path = public, pg_catalog;
SET TIME ZONE 'UTC';

-- Q01: normalization of catalog/query text. Never use unaccent for email.
PREPARE s6_normalize(text) AS
SELECT lower(public.unaccent(btrim(regexp_replace($1, '[[:space:]]+', ' ', 'g')))) AS normalized;

-- Q02: latest feed. viewer, first, after_created_at, after_id.
PREPARE s6_feed_latest(bigint, integer, timestamptz, bigint) AS
WITH page AS MATERIALIZED (
    SELECT p.id, p.user_id, p.dish_id, p.caption, p.created_at, p.updated_at
    FROM posts p
    WHERE NOT p.is_hidden
      AND ($1 IS NULL OR NOT EXISTS (
        SELECT 1 FROM user_blocks b
        WHERE (b.blocker_id = $1 AND b.blocked_id = p.user_id)
           OR (b.blocker_id = p.user_id AND b.blocked_id = $1)
    ))
      AND ($3 IS NULL OR (p.created_at, p.id) < ($3, $4))
    ORDER BY p.created_at DESC, p.id DESC
    LIMIT ($2 + 1)
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
       CASE WHEN $1 IS NULL THEN NULL ELSE EXISTS (
           SELECT 1 FROM likes x WHERE x.user_id = $1 AND x.post_id = p.id
       ) END AS is_liked,
       CASE WHEN $1 IS NULL THEN NULL ELSE EXISTS (
           SELECT 1 FROM collection_items ci JOIN collections c ON c.id = ci.collection_id
           WHERE c.user_id = $1 AND ci.post_id = p.id
       ) END AS is_saved,
       coalesce(i.images, '[]'::jsonb) AS images
FROM page p JOIN dishes d ON d.id = p.dish_id
LEFT JOIN like_counts l ON l.post_id = p.id LEFT JOIN images i ON i.post_id = p.id
ORDER BY p.created_at DESC, p.id DESC;

-- Q03: direct detail eligibility. viewer, post_id. Does not expose user private columns.
PREPARE s6_post_visible(bigint, bigint) AS
SELECT p.id, p.user_id, p.dish_id, p.restaurant_id, p.caption, p.created_at
FROM posts p WHERE p.id = $2 AND NOT p.is_hidden AND ($1 IS NULL OR NOT EXISTS (
        SELECT 1 FROM user_blocks b
        WHERE (b.blocker_id = $1 AND b.blocked_id = p.user_id)
           OR (b.blocker_id = p.user_id AND b.blocked_id = $1)
    ));

-- Q04: author's posts, same visibility and cursor policy as latest.
PREPARE s6_author_posts(bigint, bigint, integer, timestamptz, bigint) AS
SELECT p.id, p.dish_id, p.created_at FROM posts p
WHERE p.user_id = $2 AND NOT p.is_hidden AND ($1 IS NULL OR NOT EXISTS (
        SELECT 1 FROM user_blocks b
        WHERE (b.blocker_id = $1 AND b.blocked_id = p.user_id)
           OR (b.blocker_id = p.user_id AND b.blocked_id = $1)
    ))
  AND ($4 IS NULL OR (p.created_at, p.id) < ($4, $5))
ORDER BY p.created_at DESC, p.id DESC LIMIT ($3 + 1);

-- Q05: saved posts. owner, collection_id, first, after_added_at, after_post_id.
-- Service distinguishes missing/foreign collection before executing.
PREPARE s6_saved_posts(bigint, bigint, integer, timestamptz, bigint) AS
SELECT p.id, ci.added_at FROM collection_items ci
JOIN collections c ON c.id = ci.collection_id JOIN posts p ON p.id = ci.post_id
WHERE c.user_id = $1 AND c.id = $2 AND NOT p.is_hidden AND ($1 IS NULL OR NOT EXISTS (
        SELECT 1 FROM user_blocks b
        WHERE (b.blocker_id = $1 AND b.blocked_id = p.user_id)
           OR (b.blocker_id = p.user_id AND b.blocked_id = $1)
    ))
  AND ($4 IS NULL OR (ci.added_at, ci.post_id) < ($4, $5))
ORDER BY ci.added_at DESC, ci.post_id DESC LIMIT ($3 + 1);

-- Q06: viewer, raw_query, type or NULL, first, after_relevance, after_type_rank, after_id.
-- BE relevance: exact=3, prefix=2, substring=1; max across fields; no fuzzy-only hits.
-- POST fields are dish name and normalized caption, not restaurant/location_name.
-- Repository validates all three cursor values together and query/type/viewer context.
PREPARE s6_search(bigint, text, text, integer, integer, integer, bigint) AS
WITH q AS (
    SELECT lower(public.unaccent(btrim(regexp_replace($2, '[[:space:]]+', ' ', 'g')))) AS value
), candidates AS (
    SELECT 1 AS type_rank, 'DISH'::text AS kind, d.id, d.name AS title,
           ARRAY[d.name_normalized] AS fields
    FROM dishes d WHERE $3 IS NULL OR $3 = 'DISH'
    UNION ALL
    SELECT 2, 'RESTAURANT', r.id, r.name, ARRAY[r.name_normalized]
    FROM restaurants r WHERE $3 IS NULL OR $3 = 'RESTAURANT'
    UNION ALL
    SELECT 3, 'POST', p.id, d.name,
           ARRAY[d.name_normalized,
             lower(public.unaccent(btrim(regexp_replace(coalesce(p.caption,''), '[[:space:]]+', ' ', 'g'))))]
    FROM posts p JOIN dishes d ON d.id = p.dish_id
    WHERE ($3 IS NULL OR $3 = 'POST') AND NOT p.is_hidden
      AND ($1 IS NULL OR NOT EXISTS (
        SELECT 1 FROM user_blocks b
        WHERE (b.blocker_id = $1 AND b.blocked_id = p.user_id)
           OR (b.blocker_id = p.user_id AND b.blocked_id = $1)
    ))
), scored AS (
    SELECT c.type_rank, c.kind, c.id, c.title,
           (SELECT max(CASE WHEN f.value = q.value THEN 3
                           WHEN position(q.value IN f.value) = 1 THEN 2
                           WHEN position(q.value IN f.value) > 0 THEN 1
                           ELSE 0 END)
            FROM unnest(c.fields) AS f(value)) AS relevance
    FROM candidates c CROSS JOIN q WHERE q.value <> ''
)
SELECT relevance, type_rank, kind, id, title FROM scored
WHERE relevance > 0
  AND ($5 IS NULL OR relevance < $5
       OR (relevance = $5 AND (type_rank, id) > ($6, $7)))
ORDER BY relevance DESC, type_rank ASC, id ASC LIMIT ($4 + 1);

-- Q07: bounding-box CANDIDATES ONLY. min_lat, max_lat, min_lon, max_lon.
-- When min_lon > max_lon the box crosses the antimeridian.
-- No LIMIT: service computes distance, filters 5km, sorts, then takes 50.
PREPARE s6_nearby_candidates(double precision, double precision, double precision, double precision) AS
SELECT id, name, latitude, longitude FROM restaurants
WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND latitude BETWEEN $1 AND $2
  AND (($3 <= $4 AND longitude BETWEEN $3 AND $4)
       OR ($3 > $4 AND (longitude >= $3 OR longitude <= $4)))
ORDER BY id;

-- Q08: CATALOG BASELINE ONLY: proves an existing entity can be selected.
-- Not acceptance of BE's proposed 40-item (28 trending / 12 seed) pool or RNG/reason.
PREPARE s6_random_dish AS
SELECT id, name FROM dishes ORDER BY random() LIMIT 1;

-- Q09: score input from ONE statement snapshot.
-- end_at. BE v1.3: post score=L+S; dish contribution=N+L+S, all weights fixed at 1.
-- S counts each surviving user/post once across collections, using MIN(current added_at).
-- Window [end_at-7d,end_at). Current surviving relationships, not historical event counts.
-- Keep new posts with zero interaction score: they still contribute +1 to their dish.
PREPARE s6_score_posts(timestamptz) AS
WITH bounds AS (
    SELECT $1 - interval '7 days' AS lo, $1 AS hi
), eligible AS MATERIALIZED (
    SELECT p.id, p.dish_id, p.created_at FROM posts p CROSS JOIN bounds w
    WHERE NOT p.is_hidden AND p.created_at < w.hi
), lc AS (
    SELECT l.post_id, count(*)::numeric AS n
    FROM likes l JOIN eligible e ON e.id = l.post_id CROSS JOIN bounds w
    WHERE l.created_at >= w.lo AND l.created_at < w.hi GROUP BY l.post_id
), saver_pairs AS (
    SELECT ci.post_id, c.user_id, min(ci.added_at) AS first_current_save
    FROM collection_items ci JOIN collections c ON c.id = ci.collection_id
    JOIN eligible e ON e.id = ci.post_id
    GROUP BY ci.post_id, c.user_id
), sc AS (
    SELECT s.post_id, count(*)::numeric AS n FROM saver_pairs s CROSS JOIN bounds w
    WHERE s.first_current_save >= w.lo AND s.first_current_save < w.hi GROUP BY s.post_id
), scored AS (
    SELECT e.id AS post_id, e.dish_id,
           CASE WHEN e.created_at >= w.lo THEN 1 ELSE 0 END AS new_post,
           coalesce(l.n,0) AS likes_7d, coalesce(s.n,0) AS savers_7d,
           coalesce(l.n,0) + coalesce(s.n,0) AS score,
           CASE WHEN e.created_at >= w.lo THEN 1 ELSE 0 END
               + coalesce(l.n,0) + coalesce(s.n,0) AS dish_score
    FROM eligible e CROSS JOIN bounds w LEFT JOIN lc l ON l.post_id = e.id
    LEFT JOIN sc s ON s.post_id = e.id
)
SELECT post_id, dish_id, new_post, likes_7d, savers_7d, score, dish_score
FROM scored WHERE dish_score > 0 ORDER BY post_id;

-- Q10-Q14: publication orchestration. All publication writers use the SAME lock.
-- Caller: BEGIN; lock -> reject obsolete end_at -> parent locks -> publish -> COMMIT.
-- False means skip this publication; never ignore the boolean.
PREPARE s6_publish_lock AS SELECT pg_try_advisory_xact_lock(7101, 1) AS acquired;
PREPARE s6_latest_run AS
SELECT id, window_start, window_end, formula_version, published_at FROM trending_runs
ORDER BY window_end DESC, published_at DESC, id DESC LIMIT 1;
PREPARE s6_lock_posts(bigint[]) AS
SELECT id FROM posts WHERE id = ANY($1) ORDER BY id FOR SHARE;
PREPARE s6_lock_dishes(bigint[]) AS
SELECT id FROM dishes WHERE id = ANY($1) ORDER BY id FOR KEY SHARE;
PREPARE s6_lock_tags(bigint[]) AS
SELECT id FROM tags WHERE id = ANY($1) ORDER BY id FOR KEY SHARE;

-- Q14 above is reserved for the pending Tag design; not called by baseline publication.
-- Q15: POST_DISH_BASELINE only: atomically store run + post/dish snapshots.
-- Not acceptance of the proposed three-group publication; Tag formula/activation pending.
-- end_at, formula_version, array of {post_id,dish_id,score,dish_score}.
-- This JSON is internal transport of computed rows, not a new persistent schema.
-- Service validates unique posts, scores from Q09 and all expected parent locks.
PREPARE s6_publish_bundle(timestamptz, text, jsonb) AS
WITH staged AS MATERIALIZED (
    SELECT x.post_id, x.dish_id, x.score, x.dish_score
    FROM jsonb_to_recordset($3)
        AS x(post_id bigint, dish_id bigint, score numeric, dish_score numeric)
), new_run AS (
    INSERT INTO trending_runs(window_start, window_end, formula_version, published_at)
    VALUES ($1 - interval '7 days', $1, $2, clock_timestamp()) RETURNING id
), p AS (
    INSERT INTO trending_post_snapshots(run_id, post_id, score)
    SELECT r.id, s.post_id, s.score FROM staged s CROSS JOIN new_run r RETURNING post_id
), d AS (
    INSERT INTO trending_dish_snapshots(run_id, dish_id, score)
    SELECT r.id, s.dish_id, sum(s.dish_score) FROM staged s CROSS JOIN new_run r
    GROUP BY r.id, s.dish_id RETURNING dish_id
)
SELECT r.id AS run_id, (SELECT count(*) FROM p) AS post_count,
       (SELECT count(*) FROM d) AS dish_count, 0 AS tag_count
FROM new_run r;

-- Q16-Q18: snapshot reads. viewer, run_id, first, after_score, after_target_id.
-- Validate that run exists, cursor refers to that run and score is numeric.
PREPARE s6_trending_posts(bigint, bigint, integer, numeric, bigint) AS
SELECT s.post_id AS id, s.score, p.dish_id
FROM trending_post_snapshots s JOIN posts p ON p.id = s.post_id
WHERE s.run_id = $2 AND NOT p.is_hidden AND ($1 IS NULL OR NOT EXISTS (
        SELECT 1 FROM user_blocks b
        WHERE (b.blocker_id = $1 AND b.blocked_id = p.user_id)
           OR (b.blocker_id = p.user_id AND b.blocked_id = $1)
    ))
  AND ($4 IS NULL OR (s.score, s.post_id) < ($4, $5))
ORDER BY s.score DESC, s.post_id DESC LIMIT ($3 + 1);

PREPARE s6_trending_dishes(bigint, bigint, integer, numeric, bigint) AS
SELECT s.dish_id AS id, d.name, s.score, r.published_at, r.window_end
FROM trending_dish_snapshots s JOIN dishes d ON d.id = s.dish_id
JOIN trending_runs r ON r.id = s.run_id
WHERE s.run_id = $2 AND EXISTS (
    SELECT 1 FROM trending_post_snapshots ps JOIN posts p ON p.id = ps.post_id
    WHERE ps.run_id = s.run_id AND p.dish_id = s.dish_id
      AND NOT p.is_hidden AND ($1 IS NULL OR NOT EXISTS (
        SELECT 1 FROM user_blocks b
        WHERE (b.blocker_id = $1 AND b.blocked_id = p.user_id)
           OR (b.blocker_id = p.user_id AND b.blocked_id = $1)
    ))
)
AND ($4 IS NULL OR (s.score, s.dish_id) < ($4, $5))
ORDER BY s.score DESC, s.dish_id DESC LIMIT ($3 + 1);

-- Q18: reserved Tag read; API v1 has no Tag field, internal job still needs approval.
PREPARE s6_trending_tags(bigint, bigint, integer, numeric, bigint) AS
SELECT s.tag_id AS id, t.name, s.score, r.published_at, r.window_end
FROM trending_tag_snapshots s JOIN tags t ON t.id = s.tag_id
JOIN trending_runs r ON r.id = s.run_id
WHERE s.run_id = $2 AND EXISTS (
    SELECT 1 FROM trending_post_snapshots ps JOIN posts p ON p.id = ps.post_id
    JOIN post_tags pt ON pt.post_id = p.id AND pt.tag_id = s.tag_id
    WHERE ps.run_id = s.run_id AND NOT p.is_hidden AND ($1 IS NULL OR NOT EXISTS (
        SELECT 1 FROM user_blocks b
        WHERE (b.blocker_id = $1 AND b.blocked_id = p.user_id)
           OR (b.blocker_id = p.user_id AND b.blocked_id = $1)
    ))
)
AND ($4 IS NULL OR (s.score, s.tag_id) < ($4, $5))
ORDER BY s.score DESC, s.tag_id DESC LIMIT ($3 + 1);

-- Q19: bounded AI input. viewer, raw dish/restaurant query (may be empty), max_items.
-- max_items proposal 10, <=20; service budget and public projection required.
PREPARE s6_ai_context(bigint, text, integer) AS
WITH q AS (SELECT lower(public.unaccent(btrim(regexp_replace($2, '[[:space:]]+', ' ', 'g')))) AS value)
SELECT p.id AS post_id, d.id AS dish_id, d.name AS dish_name,
       r.id AS restaurant_id, r.name AS restaurant_name,
       left(coalesce(p.caption,''),200) AS caption_excerpt
FROM posts p JOIN dishes d ON d.id = p.dish_id
LEFT JOIN restaurants r ON r.id = p.restaurant_id CROSS JOIN q
WHERE NOT p.is_hidden AND ($1 IS NULL OR NOT EXISTS (
        SELECT 1 FROM user_blocks b
        WHERE (b.blocker_id = $1 AND b.blocked_id = p.user_id)
           OR (b.blocker_id = p.user_id AND b.blocked_id = $1)
    ))
  AND (q.value = '' OR position(q.value IN d.name_normalized) > 0
       OR position(q.value IN coalesce(r.name_normalized,'')) > 0)
ORDER BY p.created_at DESC, p.id DESC LIMIT $3;

-- Q20: validate post references returned by AI; caller compares requested IDs to returned IDs.
PREPARE s6_ai_validate_posts(bigint, bigint[]) AS
SELECT p.id FROM posts p WHERE p.id = ANY($2) AND NOT p.is_hidden AND ($1 IS NULL OR NOT EXISTS (
        SELECT 1 FROM user_blocks b
        WHERE (b.blocker_id = $1 AND b.blocked_id = p.user_id)
           OR (b.blocker_id = p.user_id AND b.blocked_id = $1)
    ))
ORDER BY p.id;

-- Q21: internal history with persisted question/reply linkage plus owner and cursor.
-- viewer, session_id, first, after_time, after_id. Does not create client request correlation.
PREPARE s6_chat_history(bigint, bigint, integer, timestamptz, bigint) AS
SELECT m.id, m.session_id, m.reply_to_id, m.role, m.content, m.status, m.post_draft, m.created_at
FROM chat_messages m JOIN chat_sessions s ON s.id = m.session_id
WHERE s.user_id = $1 AND s.id = $2
  AND ($4 IS NULL OR (m.created_at,m.id) < ($4,$5))
ORDER BY m.created_at DESC,m.id DESC LIMIT ($3 + 1);

-- Q22: assistantSessions owner page + batched lastMessageAt, per API v0.8.
-- viewer, first, before_created_at, before_id. No context_json/private message content.
PREPARE s6_chat_sessions(bigint, integer, timestamptz, bigint) AS
WITH page AS MATERIALIZED (
    SELECT s.id, s.created_at FROM chat_sessions s
    WHERE s.user_id = $1 AND ($3 IS NULL OR (s.created_at,s.id) < ($3,$4))
    ORDER BY s.created_at DESC,s.id DESC LIMIT ($2 + 1)
), latest AS (
    SELECT m.session_id, max(m.created_at) AS last_message_at
    FROM chat_messages m JOIN page p ON p.id = m.session_id GROUP BY m.session_id
)
SELECT p.id,p.created_at,l.last_message_at FROM page p
LEFT JOIN latest l ON l.session_id = p.id
ORDER BY p.created_at DESC,p.id DESC;

-- Q23: owner inbox + GLOBAL unread count in one statement snapshot, even for an empty page.
-- viewer, first, before_created_at, before_id. items contains first+1 INTERNAL rows.
-- Service trims extra row, builds cursor and batches safe actor/target projection.
-- Raw identifiers do not substitute for hidden/block/profile permission checks.
PREPARE s6_notifications(bigint, integer, timestamptz, bigint) AS
WITH page AS MATERIALIZED (
    SELECT n.id,n.type,n.actor_id,n.post_id,n.read_at,n.created_at
    FROM notifications n WHERE n.user_id = $1
      AND ($3 IS NULL OR (n.created_at,n.id) < ($3,$4))
    ORDER BY n.created_at DESC,n.id DESC LIMIT ($2 + 1)
)
SELECT coalesce((SELECT jsonb_agg(to_jsonb(p) ORDER BY p.created_at DESC,p.id DESC)
                 FROM page p),'[]'::jsonb) AS items,
       (SELECT count(*) FROM notifications n
        WHERE n.user_id = $1 AND n.read_at IS NULL) AS unread_count;
