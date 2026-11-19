"""Explicit metadata frozen from DOC 6.4-B v1.2 (25 tables, 161 columns)."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

metadata = sa.MetaData()

users = sa.Table(
    "users",
    metadata,
    sa.Column(
        "id",
        sa.BigInteger(),
        sa.Identity(always=False),
        nullable=False,
    ),
    sa.Column("email", sa.Text(), nullable=False),
    sa.Column("email_normalized", sa.Text(), nullable=False),
    sa.Column("username", sa.Text(), nullable=True),
    sa.Column("username_normalized", sa.Text(), nullable=True),
    sa.Column("password_hash", sa.Text(), nullable=False),
    sa.Column("display_name", sa.Text(), nullable=False),
    sa.Column("bio", sa.Text(), nullable=True),
    sa.Column("city", sa.Text(), nullable=True),
    sa.Column("social_links", pg.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.Column(
        "public_profile_fields",
        pg.ARRAY(sa.Text()),
        server_default=sa.text("'{}'::text[]"),
        nullable=False,
    ),
    sa.Column("avatar_media_id", pg.UUID(as_uuid=True), nullable=True),
    sa.Column("cover_media_id", pg.UUID(as_uuid=True), nullable=True),
    sa.Column("token_version", sa.Integer(), server_default=sa.text("0"), nullable=False),
    sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.Column(
        "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.PrimaryKeyConstraint("id", name="pk_users"),
    sa.UniqueConstraint("email_normalized", name="uq_users_email_normalized"),
    sa.UniqueConstraint("username_normalized", name="uq_users_username_normalized"),
    sa.UniqueConstraint("avatar_media_id", name="uq_users_avatar_media_id"),
    sa.UniqueConstraint("cover_media_id", name="uq_users_cover_media_id"),
    sa.CheckConstraint(
        "(username IS NULL) = (username_normalized IS NULL)", name="ck_users_username_pair"
    ),
    sa.CheckConstraint("btrim(display_name) <> ''", name="ck_users_display_name"),
    sa.CheckConstraint("jsonb_typeof(social_links) = 'object'", name="ck_users_social_links"),
    sa.CheckConstraint(
        (
            "public_profile_fields <@ ARRAY['displayName','bio','avatarUrl','coverU"
            "rl','city','socialLinks']::text[] AND "
            "array_position(public_profile_fields, NULL) IS NULL"
        ),
        name="ck_users_public_fields",
    ),
    sa.CheckConstraint("token_version >= 0", name="ck_users_token_version"),
)

password_resets = sa.Table(
    "password_resets",
    metadata,
    sa.Column(
        "id",
        sa.BigInteger(),
        sa.Identity(always=False),
        nullable=False,
    ),
    sa.Column("user_id", sa.BigInteger(), nullable=False),
    sa.Column("otp_hash", sa.Text(), nullable=False),
    sa.Column("failed_attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.Column("otp_expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("reset_token_hash", sa.Text(), nullable=True),
    sa.Column("reset_expires_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint("id", name="pk_password_resets"),
    sa.UniqueConstraint("reset_token_hash", name="uq_password_resets_reset_token_hash"),
    sa.CheckConstraint("failed_attempts BETWEEN 0 AND 5", name="ck_password_resets_attempts"),
    sa.CheckConstraint("otp_expires_at > created_at", name="ck_password_resets_otp_time"),
    sa.CheckConstraint(
        (
            "(verified_at IS NULL AND reset_token_hash IS NULL AND reset_expires_at"
            " IS NULL) OR (verified_at IS NOT NULL AND reset_token_hash IS NOT NULL"
            " AND reset_expires_at IS NOT NULL)"
        ),
        name="ck_password_resets_grant_fields",
    ),
    sa.CheckConstraint(
        "consumed_at IS NULL OR verified_at IS NOT NULL", name="ck_password_resets_consumed"
    ),
    sa.ForeignKeyConstraint(
        ["user_id"],
        ["users.id"],
        name="fk_password_resets_user_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
)

revoked_tokens = sa.Table(
    "revoked_tokens",
    metadata,
    sa.Column("jti", pg.UUID(as_uuid=True), nullable=False),
    sa.Column("user_id", sa.BigInteger(), nullable=False),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column(
        "revoked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.PrimaryKeyConstraint("jti", name="pk_revoked_tokens"),
    sa.ForeignKeyConstraint(
        ["user_id"],
        ["users.id"],
        name="fk_revoked_tokens_user_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
)

user_devices = sa.Table(
    "user_devices",
    metadata,
    sa.Column(
        "id",
        sa.BigInteger(),
        sa.Identity(always=False),
        nullable=False,
    ),
    sa.Column("user_id", sa.BigInteger(), nullable=False),
    sa.Column("push_token", sa.Text(), nullable=False),
    sa.Column("platform", sa.Text(), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.Column(
        "last_active_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    ),
    sa.PrimaryKeyConstraint("id", name="pk_user_devices"),
    sa.UniqueConstraint("push_token", name="uq_user_devices_push_token"),
    sa.CheckConstraint("platform IN ('android','web')", name="ck_user_devices_platform"),
    sa.ForeignKeyConstraint(
        ["user_id"],
        ["users.id"],
        name="fk_user_devices_user_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
)

media_assets = sa.Table(
    "media_assets",
    metadata,
    sa.Column("id", pg.UUID(as_uuid=True), nullable=False),
    sa.Column("owner_id", sa.BigInteger(), nullable=False),
    sa.Column("purpose", sa.Text(), nullable=False),
    sa.Column("state", sa.Text(), server_default=sa.text("'PENDING'"), nullable=False),
    sa.Column("provider", sa.Text(), nullable=False),
    sa.Column("storage_key", sa.Text(), nullable=False),
    sa.Column("url", sa.Text(), nullable=False),
    sa.Column("input_size_bytes", sa.BigInteger(), nullable=False),
    sa.Column("stored_size_bytes", sa.BigInteger(), nullable=False),
    sa.Column("mime_type", sa.Text(), nullable=False),
    sa.Column("width", sa.Integer(), nullable=False),
    sa.Column("height", sa.Integer(), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint("id", name="pk_media_assets"),
    sa.UniqueConstraint("provider", "storage_key", name="uq_media_assets_provider_storage_key"),
    sa.CheckConstraint("purpose IN ('POST','AVATAR','COVER')", name="ck_media_assets_purpose"),
    sa.CheckConstraint(
        "state IN ('PENDING','ATTACHED','DELETE_PENDING','DELETED')", name="ck_media_assets_state"
    ),
    sa.CheckConstraint(
        "input_size_bytes > 0 AND stored_size_bytes > 0", name="ck_media_assets_size"
    ),
    sa.CheckConstraint(
        "mime_type IN ('image/jpeg','image/png','image/webp')", name="ck_media_assets_mime"
    ),
    sa.CheckConstraint(
        "width BETWEEN 1 AND 1600 AND height BETWEEN 1 AND 1600", name="ck_media_assets_dimensions"
    ),
    sa.CheckConstraint("expires_at > created_at", name="ck_media_assets_expiry"),
    sa.CheckConstraint(
        (
            "(state = 'PENDING' AND consumed_at IS NULL AND deleted_at IS NULL) OR "
            "(state = 'ATTACHED' AND consumed_at IS NOT NULL AND deleted_at IS "
            "NULL) OR (state = 'DELETE_PENDING' AND deleted_at IS NULL) OR (state ="
            " 'DELETED' AND deleted_at IS NOT NULL)"
        ),
        name="ck_media_assets_lifecycle",
    ),
    sa.ForeignKeyConstraint(
        ["owner_id"],
        ["users.id"],
        name="fk_media_assets_owner_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
)

dishes = sa.Table(
    "dishes",
    metadata,
    sa.Column(
        "id",
        sa.BigInteger(),
        sa.Identity(always=False),
        nullable=False,
    ),
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("name_normalized", sa.Text(), nullable=False),
    sa.Column("is_seed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.PrimaryKeyConstraint("id", name="pk_dishes"),
    sa.UniqueConstraint("name_normalized", name="uq_dishes_name_normalized"),
    sa.CheckConstraint("btrim(name) <> '' AND btrim(name_normalized) <> ''", name="ck_dishes_name"),
)

restaurants = sa.Table(
    "restaurants",
    metadata,
    sa.Column(
        "id",
        sa.BigInteger(),
        sa.Identity(always=False),
        nullable=False,
    ),
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("name_normalized", sa.Text(), nullable=False),
    sa.Column("address", sa.Text(), nullable=True),
    sa.Column("latitude", sa.Double(), nullable=True),
    sa.Column("longitude", sa.Double(), nullable=True),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.PrimaryKeyConstraint("id", name="pk_restaurants"),
    sa.CheckConstraint(
        (
            "(latitude IS NULL AND longitude IS NULL) OR (latitude IS NOT NULL AND "
            "longitude IS NOT NULL AND latitude BETWEEN -90 AND 90 AND longitude "
            "BETWEEN -180 AND 180)"
        ),
        name="ck_restaurants_coordinates",
    ),
)

tags = sa.Table(
    "tags",
    metadata,
    sa.Column(
        "id",
        sa.BigInteger(),
        sa.Identity(always=False),
        nullable=False,
    ),
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("name_normalized", sa.Text(), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.PrimaryKeyConstraint("id", name="pk_tags"),
    sa.UniqueConstraint("name_normalized", name="uq_tags_name_normalized"),
    sa.CheckConstraint("btrim(name) <> '' AND btrim(name_normalized) <> ''", name="ck_tags_name"),
)

posts = sa.Table(
    "posts",
    metadata,
    sa.Column(
        "id",
        sa.BigInteger(),
        sa.Identity(always=False),
        nullable=False,
    ),
    sa.Column("user_id", sa.BigInteger(), nullable=False),
    sa.Column("dish_id", sa.BigInteger(), nullable=False),
    sa.Column("restaurant_id", sa.BigInteger(), nullable=True),
    sa.Column("caption", sa.Text(), nullable=True),
    sa.Column("feeling", sa.Text(), nullable=True),
    sa.Column("location_name", sa.Text(), nullable=True),
    sa.Column("location_address", sa.Text(), nullable=True),
    sa.Column("latitude", sa.Double(), nullable=True),
    sa.Column("longitude", sa.Double(), nullable=True),
    sa.Column("price_range", sa.Text(), nullable=True),
    sa.Column(
        "recipe_ingredients",
        pg.ARRAY(sa.Text()),
        server_default=sa.text("'{}'::text[]"),
        nullable=False,
    ),
    sa.Column(
        "recipe_steps", pg.ARRAY(sa.Text()), server_default=sa.text("'{}'::text[]"), nullable=False
    ),
    sa.Column("is_hidden", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.Column(
        "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.PrimaryKeyConstraint("id", name="pk_posts"),
    sa.CheckConstraint(
        (
            "(latitude IS NULL AND longitude IS NULL) OR (latitude IS NOT NULL AND "
            "longitude IS NOT NULL AND latitude BETWEEN -90 AND 90 AND longitude "
            "BETWEEN -180 AND 180)"
        ),
        name="ck_posts_coordinates",
    ),
    sa.CheckConstraint(
        "price_range IN ('UNDER_50K','FROM_50K_TO_100K','FROM_100K_TO_200K','ABOVE_200K')",
        name="ck_posts_price_range",
    ),
    sa.ForeignKeyConstraint(
        ["user_id"],
        ["users.id"],
        name="fk_posts_user_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
    sa.ForeignKeyConstraint(
        ["dish_id"],
        ["dishes.id"],
        name="fk_posts_dish_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
    sa.ForeignKeyConstraint(
        ["restaurant_id"],
        ["restaurants.id"],
        name="fk_posts_restaurant_id",
        onupdate="RESTRICT",
        ondelete="SET NULL",
        use_alter=False,
    ),
)

post_images = sa.Table(
    "post_images",
    metadata,
    sa.Column(
        "id",
        sa.BigInteger(),
        sa.Identity(always=False),
        nullable=False,
    ),
    sa.Column("post_id", sa.BigInteger(), nullable=False),
    sa.Column("media_id", pg.UUID(as_uuid=True), nullable=False),
    sa.Column("position", sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint("id", name="pk_post_images"),
    sa.UniqueConstraint("media_id", name="uq_post_images_media_id"),
    sa.UniqueConstraint(
        "post_id",
        "position",
        name="uq_post_images_post_id_position",
        deferrable=True,
        initially="IMMEDIATE",
    ),
    sa.CheckConstraint("position >= 0", name="ck_post_images_position"),
    sa.ForeignKeyConstraint(
        ["post_id"],
        ["posts.id"],
        name="fk_post_images_post_id",
        onupdate="RESTRICT",
        ondelete="CASCADE",
        use_alter=False,
    ),
    sa.ForeignKeyConstraint(
        ["media_id"],
        ["media_assets.id"],
        name="fk_post_images_media_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
)

post_tags = sa.Table(
    "post_tags",
    metadata,
    sa.Column("post_id", sa.BigInteger(), nullable=False),
    sa.Column("tag_id", sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint("post_id", "tag_id", name="pk_post_tags"),
    sa.ForeignKeyConstraint(
        ["post_id"],
        ["posts.id"],
        name="fk_post_tags_post_id",
        onupdate="RESTRICT",
        ondelete="CASCADE",
        use_alter=False,
    ),
    sa.ForeignKeyConstraint(
        ["tag_id"],
        ["tags.id"],
        name="fk_post_tags_tag_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
)

likes = sa.Table(
    "likes",
    metadata,
    sa.Column("user_id", sa.BigInteger(), nullable=False),
    sa.Column("post_id", sa.BigInteger(), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.PrimaryKeyConstraint("user_id", "post_id", name="pk_likes"),
    sa.ForeignKeyConstraint(
        ["user_id"],
        ["users.id"],
        name="fk_likes_user_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
    sa.ForeignKeyConstraint(
        ["post_id"],
        ["posts.id"],
        name="fk_likes_post_id",
        onupdate="RESTRICT",
        ondelete="CASCADE",
        use_alter=False,
    ),
)

follows = sa.Table(
    "follows",
    metadata,
    sa.Column("follower_id", sa.BigInteger(), nullable=False),
    sa.Column("followee_id", sa.BigInteger(), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.PrimaryKeyConstraint("follower_id", "followee_id", name="pk_follows"),
    sa.CheckConstraint("follower_id <> followee_id", name="ck_follows_not_self"),
    sa.ForeignKeyConstraint(
        ["follower_id"],
        ["users.id"],
        name="fk_follows_follower_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
    sa.ForeignKeyConstraint(
        ["followee_id"],
        ["users.id"],
        name="fk_follows_followee_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
)

collections = sa.Table(
    "collections",
    metadata,
    sa.Column(
        "id",
        sa.BigInteger(),
        sa.Identity(always=False),
        nullable=False,
    ),
    sa.Column("user_id", sa.BigInteger(), nullable=False),
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("name_normalized", sa.Text(), nullable=False),
    sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.PrimaryKeyConstraint("id", name="pk_collections"),
    sa.UniqueConstraint(
        "user_id", "name_normalized", name="uq_collections_user_id_name_normalized"
    ),
    sa.CheckConstraint(
        "btrim(name) <> '' AND btrim(name_normalized) <> ''", name="ck_collections_name"
    ),
    sa.ForeignKeyConstraint(
        ["user_id"],
        ["users.id"],
        name="fk_collections_user_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
)

collection_items = sa.Table(
    "collection_items",
    metadata,
    sa.Column("collection_id", sa.BigInteger(), nullable=False),
    sa.Column("post_id", sa.BigInteger(), nullable=False),
    sa.Column(
        "added_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.PrimaryKeyConstraint("collection_id", "post_id", name="pk_collection_items"),
    sa.ForeignKeyConstraint(
        ["collection_id"],
        ["collections.id"],
        name="fk_collection_items_collection_id",
        onupdate="RESTRICT",
        ondelete="CASCADE",
        use_alter=False,
    ),
    sa.ForeignKeyConstraint(
        ["post_id"],
        ["posts.id"],
        name="fk_collection_items_post_id",
        onupdate="RESTRICT",
        ondelete="CASCADE",
        use_alter=False,
    ),
)

reports = sa.Table(
    "reports",
    metadata,
    sa.Column(
        "id",
        sa.BigInteger(),
        sa.Identity(always=False),
        nullable=False,
    ),
    sa.Column("reporter_id", sa.BigInteger(), nullable=False),
    sa.Column("post_id", sa.BigInteger(), nullable=True),
    sa.Column("original_post_id", sa.BigInteger(), nullable=False),
    sa.Column("reason", sa.Text(), nullable=False),
    sa.Column("evidence_snapshot", pg.JSONB(), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.PrimaryKeyConstraint("id", name="pk_reports"),
    sa.UniqueConstraint(
        "reporter_id", "original_post_id", name="uq_reports_reporter_id_original_post_id"
    ),
    sa.CheckConstraint("btrim(reason) <> ''", name="ck_reports_reason"),
    sa.CheckConstraint("jsonb_typeof(evidence_snapshot) = 'object'", name="ck_reports_snapshot"),
    sa.CheckConstraint(
        "post_id IS NULL OR post_id = original_post_id", name="ck_reports_original_post"
    ),
    sa.ForeignKeyConstraint(
        ["reporter_id"],
        ["users.id"],
        name="fk_reports_reporter_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
    sa.ForeignKeyConstraint(
        ["post_id"],
        ["posts.id"],
        name="fk_reports_post_id",
        onupdate="RESTRICT",
        ondelete="SET NULL",
        use_alter=False,
    ),
)

notifications = sa.Table(
    "notifications",
    metadata,
    sa.Column(
        "id",
        sa.BigInteger(),
        sa.Identity(always=False),
        nullable=False,
    ),
    sa.Column("user_id", sa.BigInteger(), nullable=False),
    sa.Column("actor_id", sa.BigInteger(), nullable=True),
    sa.Column("post_id", sa.BigInteger(), nullable=True),
    sa.Column("type", sa.Text(), nullable=False),
    sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.PrimaryKeyConstraint("id", name="pk_notifications"),
    sa.CheckConstraint("type IN ('LIKE','SAVE','FOLLOW')", name="ck_notifications_type"),
    sa.ForeignKeyConstraint(
        ["user_id"],
        ["users.id"],
        name="fk_notifications_user_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
    sa.ForeignKeyConstraint(
        ["actor_id"],
        ["users.id"],
        name="fk_notifications_actor_id",
        onupdate="RESTRICT",
        ondelete="SET NULL",
        use_alter=False,
    ),
    sa.ForeignKeyConstraint(
        ["post_id"],
        ["posts.id"],
        name="fk_notifications_post_id",
        onupdate="RESTRICT",
        ondelete="SET NULL",
        use_alter=False,
    ),
)

chat_sessions = sa.Table(
    "chat_sessions",
    metadata,
    sa.Column(
        "id",
        sa.BigInteger(),
        sa.Identity(always=False),
        nullable=False,
    ),
    sa.Column("user_id", sa.BigInteger(), nullable=False),
    sa.Column("context_json", pg.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint("id", name="pk_chat_sessions"),
    sa.CheckConstraint("jsonb_typeof(context_json) = 'object'", name="ck_chat_sessions_context"),
    sa.CheckConstraint(
        "ended_at IS NULL OR ended_at >= created_at", name="ck_chat_sessions_end_time"
    ),
    sa.ForeignKeyConstraint(
        ["user_id"],
        ["users.id"],
        name="fk_chat_sessions_user_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
)

chat_messages = sa.Table(
    "chat_messages",
    metadata,
    sa.Column(
        "id",
        sa.BigInteger(),
        sa.Identity(always=False),
        nullable=False,
    ),
    sa.Column("session_id", sa.BigInteger(), nullable=False),
    sa.Column("reply_to_id", sa.BigInteger(), nullable=True),
    sa.Column("role", sa.Text(), nullable=False),
    sa.Column("content", sa.Text(), nullable=False),
    sa.Column("status", sa.Text(), nullable=False),
    sa.Column("post_draft", pg.JSONB(), nullable=True),
    sa.Column("processing_version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
    sa.Column("processing_expires_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.Column(
        "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.PrimaryKeyConstraint("id", name="pk_chat_messages"),
    sa.UniqueConstraint("reply_to_id", name="uq_chat_messages_reply_to_id"),
    sa.CheckConstraint("role IN ('user','assistant')", name="ck_chat_messages_role"),
    sa.CheckConstraint(
        "status IN ('PENDING','OK','FAILED','FALLBACK')", name="ck_chat_messages_status"
    ),
    sa.CheckConstraint(
        (
            "(role = 'user' AND reply_to_id IS NULL) OR (role = 'assistant' AND "
            "reply_to_id IS NOT NULL)"
        ),
        name="ck_chat_messages_reply",
    ),
    sa.CheckConstraint(
        (
            "post_draft IS NULL OR (jsonb_typeof(post_draft) = 'object' AND role = "
            "'assistant' AND status IN ('OK','FALLBACK'))"
        ),
        name="ck_chat_messages_draft",
    ),
    sa.CheckConstraint(
        (
            "(role = 'user' AND status = 'OK' AND processing_version = 0 AND "
            "processing_expires_at IS NULL) OR (role = 'assistant' AND "
            "processing_version >= 1 AND ((status = 'PENDING' AND "
            "processing_expires_at IS NOT NULL) OR (status <> 'PENDING' AND "
            "processing_expires_at IS NULL)))"
        ),
        name="ck_chat_messages_processing",
    ),
    sa.ForeignKeyConstraint(
        ["session_id"],
        ["chat_sessions.id"],
        name="fk_chat_messages_session_id",
        onupdate="RESTRICT",
        ondelete="CASCADE",
        use_alter=False,
    ),
    sa.ForeignKeyConstraint(
        ["reply_to_id"],
        ["chat_messages.id"],
        name="fk_chat_messages_reply_to_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
)

trending_runs = sa.Table(
    "trending_runs",
    metadata,
    sa.Column(
        "id",
        sa.BigInteger(),
        sa.Identity(always=False),
        nullable=False,
    ),
    sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
    sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
    sa.Column("formula_version", sa.Text(), nullable=False),
    sa.Column(
        "published_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.PrimaryKeyConstraint("id", name="pk_trending_runs"),
    sa.CheckConstraint("window_end > window_start", name="ck_trending_runs_window"),
)

trending_post_snapshots = sa.Table(
    "trending_post_snapshots",
    metadata,
    sa.Column("run_id", sa.BigInteger(), nullable=False),
    sa.Column("post_id", sa.BigInteger(), nullable=False),
    sa.Column("score", sa.Numeric(), nullable=False),
    sa.PrimaryKeyConstraint("run_id", "post_id", name="pk_trending_post_snapshots"),
    sa.ForeignKeyConstraint(
        ["run_id"],
        ["trending_runs.id"],
        name="fk_trending_post_snapshots_run_id",
        onupdate="RESTRICT",
        ondelete="CASCADE",
        use_alter=False,
    ),
    sa.ForeignKeyConstraint(
        ["post_id"],
        ["posts.id"],
        name="fk_trending_post_snapshots_post_id",
        onupdate="RESTRICT",
        ondelete="CASCADE",
        use_alter=False,
    ),
)

trending_dish_snapshots = sa.Table(
    "trending_dish_snapshots",
    metadata,
    sa.Column("run_id", sa.BigInteger(), nullable=False),
    sa.Column("dish_id", sa.BigInteger(), nullable=False),
    sa.Column("score", sa.Numeric(), nullable=False),
    sa.PrimaryKeyConstraint("run_id", "dish_id", name="pk_trending_dish_snapshots"),
    sa.ForeignKeyConstraint(
        ["run_id"],
        ["trending_runs.id"],
        name="fk_trending_dish_snapshots_run_id",
        onupdate="RESTRICT",
        ondelete="CASCADE",
        use_alter=False,
    ),
    sa.ForeignKeyConstraint(
        ["dish_id"],
        ["dishes.id"],
        name="fk_trending_dish_snapshots_dish_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
)

trending_tag_snapshots = sa.Table(
    "trending_tag_snapshots",
    metadata,
    sa.Column("run_id", sa.BigInteger(), nullable=False),
    sa.Column("tag_id", sa.BigInteger(), nullable=False),
    sa.Column("score", sa.Numeric(), nullable=False),
    sa.PrimaryKeyConstraint("run_id", "tag_id", name="pk_trending_tag_snapshots"),
    sa.ForeignKeyConstraint(
        ["run_id"],
        ["trending_runs.id"],
        name="fk_trending_tag_snapshots_run_id",
        onupdate="RESTRICT",
        ondelete="CASCADE",
        use_alter=False,
    ),
    sa.ForeignKeyConstraint(
        ["tag_id"],
        ["tags.id"],
        name="fk_trending_tag_snapshots_tag_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
)

media_cleanup_jobs = sa.Table(
    "media_cleanup_jobs",
    metadata,
    sa.Column(
        "id",
        sa.BigInteger(),
        sa.Identity(always=False),
        nullable=False,
    ),
    sa.Column("media_id", pg.UUID(as_uuid=True), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.Column(
        "next_attempt_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    ),
    sa.Column("attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
    sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("last_error_code", sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint("id", name="pk_media_cleanup_jobs"),
    sa.UniqueConstraint("media_id", name="uq_media_cleanup_jobs_media_id"),
    sa.CheckConstraint("attempts >= 0", name="ck_media_cleanup_jobs_attempts"),
    sa.ForeignKeyConstraint(
        ["media_id"],
        ["media_assets.id"],
        name="fk_media_cleanup_jobs_media_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
)

user_blocks = sa.Table(
    "user_blocks",
    metadata,
    sa.Column("blocker_id", sa.BigInteger(), nullable=False),
    sa.Column("blocked_id", sa.BigInteger(), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    ),
    sa.PrimaryKeyConstraint("blocker_id", "blocked_id", name="pk_user_blocks"),
    sa.CheckConstraint("blocker_id <> blocked_id", name="ck_user_blocks_not_self"),
    sa.ForeignKeyConstraint(
        ["blocker_id"],
        ["users.id"],
        name="fk_user_blocks_blocker_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
    sa.ForeignKeyConstraint(
        ["blocked_id"],
        ["users.id"],
        name="fk_user_blocks_blocked_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=False,
    ),
)

users.append_constraint(
    sa.ForeignKeyConstraint(
        ["avatar_media_id"],
        ["media_assets.id"],
        name="fk_users_avatar_media_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=True,
    )
)
users.append_constraint(
    sa.ForeignKeyConstraint(
        ["cover_media_id"],
        ["media_assets.id"],
        name="fk_users_cover_media_id",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
        use_alter=True,
    )
)
sa.Index(
    "uq_password_resets_open_user",
    password_resets.c.user_id,
    unique=True,
    postgresql_where=sa.text("invalidated_at IS NULL AND consumed_at IS NULL"),
)
sa.Index("ix_revoked_tokens_expiry", revoked_tokens.c.expires_at, unique=False)
sa.Index("ix_user_devices_user", user_devices.c.user_id, unique=False)
sa.Index(
    "ix_media_assets_state_expiry", media_assets.c.state, media_assets.c.expires_at, unique=False
)
sa.Index(
    "ix_media_assets_owner_created",
    media_assets.c.owner_id,
    media_assets.c.created_at,
    media_assets.c.id,
    unique=False,
)
sa.Index(
    "ix_dishes_name_search",
    dishes.c.name_normalized,
    unique=False,
    postgresql_using="gin",
    postgresql_ops={"name_normalized": "gin_trgm_ops"},
)
sa.Index(
    "ix_restaurants_coordinates", restaurants.c.latitude, restaurants.c.longitude, unique=False
)
sa.Index(
    "ix_restaurants_name_search",
    restaurants.c.name_normalized,
    unique=False,
    postgresql_using="gin",
    postgresql_ops={"name_normalized": "gin_trgm_ops"},
)
sa.Index(
    "ix_posts_feed",
    posts.c.created_at.desc(),
    posts.c.id.desc(),
    unique=False,
    postgresql_where=sa.text("is_hidden = false"),
)
sa.Index(
    "ix_posts_author", posts.c.user_id, posts.c.created_at.desc(), posts.c.id.desc(), unique=False
)
sa.Index(
    "ix_posts_dish", posts.c.dish_id, posts.c.created_at.desc(), posts.c.id.desc(), unique=False
)
sa.Index("ix_posts_restaurant", posts.c.restaurant_id, unique=False)
sa.Index("ix_post_tags_tag_post", post_tags.c.tag_id, post_tags.c.post_id, unique=False)
sa.Index("ix_likes_post_created", likes.c.post_id, likes.c.created_at, unique=False)
sa.Index(
    "ix_follows_followee",
    follows.c.followee_id,
    follows.c.created_at,
    follows.c.follower_id,
    unique=False,
)
sa.Index(
    "uq_collections_one_default",
    collections.c.user_id,
    unique=True,
    postgresql_where=sa.text("is_default = true"),
)
sa.Index(
    "ix_collections_owner_created",
    collections.c.user_id,
    collections.c.created_at,
    collections.c.id,
    unique=False,
)
sa.Index("ix_collection_items_post", collection_items.c.post_id, unique=False)
sa.Index(
    "ix_collection_items_cursor",
    collection_items.c.collection_id,
    collection_items.c.added_at.desc(),
    collection_items.c.post_id.desc(),
    unique=False,
)
sa.Index("ix_reports_post", reports.c.post_id, unique=False)
sa.Index(
    "ix_notifications_inbox",
    notifications.c.user_id,
    notifications.c.created_at.desc(),
    notifications.c.id.desc(),
    unique=False,
)
sa.Index(
    "ix_notifications_unread",
    notifications.c.user_id,
    unique=False,
    postgresql_where=sa.text("read_at IS NULL"),
)
sa.Index(
    "ix_chat_sessions_owner_cursor",
    chat_sessions.c.user_id,
    chat_sessions.c.created_at.desc(),
    chat_sessions.c.id.desc(),
    unique=False,
)
sa.Index(
    "ix_chat_messages_history",
    chat_messages.c.session_id,
    chat_messages.c.created_at,
    chat_messages.c.id,
    unique=False,
)
sa.Index(
    "ix_chat_messages_session_reply",
    chat_messages.c.session_id,
    chat_messages.c.reply_to_id,
    unique=False,
)
sa.Index(
    "ix_trending_runs_published",
    trending_runs.c.published_at.desc(),
    trending_runs.c.id.desc(),
    unique=False,
)
sa.Index(
    "ix_trending_post_snapshots_ranking",
    trending_post_snapshots.c.run_id,
    trending_post_snapshots.c.score.desc(),
    trending_post_snapshots.c.post_id.desc(),
    unique=False,
)
sa.Index(
    "ix_trending_dish_snapshots_ranking",
    trending_dish_snapshots.c.run_id,
    trending_dish_snapshots.c.score.desc(),
    trending_dish_snapshots.c.dish_id.desc(),
    unique=False,
)
sa.Index(
    "ix_trending_tag_snapshots_ranking",
    trending_tag_snapshots.c.run_id,
    trending_tag_snapshots.c.score.desc(),
    trending_tag_snapshots.c.tag_id.desc(),
    unique=False,
)
sa.Index(
    "ix_media_cleanup_jobs_pending",
    media_cleanup_jobs.c.next_attempt_at,
    media_cleanup_jobs.c.id,
    unique=False,
    postgresql_where=sa.text("completed_at IS NULL"),
)

# Preserve DDL dictionary comments so autogenerate does not propose deleting them.
metadata.tables["users"].comment = "T01 — Tài khoản và hồ sơ; REQ-001…006, 013…015; NFR-06/07."
metadata.tables["users"].c.id.comment = "Mã dòng do DB sinh; API ánh xạ sang GraphQL ID."
metadata.tables["users"].c.email.comment = "Email gốc, riêng tư."
metadata.tables[
    "users"
].c.email_normalized.comment = "Khóa đăng nhập chuẩn hóa; không bỏ dấu email."
metadata.tables["users"].c.username.comment = "Handle tùy chọn, O9."
metadata.tables["users"].c.username_normalized.comment = "Khóa handle chuẩn hóa; đi cặp username."
metadata.tables["users"].c.password_hash.comment = "Hash bcrypt; không trả API/log."
metadata.tables["users"].c.display_name.comment = "Tên lưu bắt buộc; công khai tùy allowlist, O4."
metadata.tables["users"].c.bio.comment = "Giới thiệu; NULL nghĩa chưa có."
metadata.tables["users"].c.city.comment = "Thành phố hồ sơ; API chỉnh sửa còn mở."
metadata.tables[
    "users"
].c.social_links.comment = "Object liên kết hồ sơ; không chứa thông tin xác thực."
metadata.tables[
    "users"
].c.public_profile_fields.comment = (
    "Allowlist công khai; mặc định không công khai trường tùy chọn, O4."
)
metadata.tables[
    "users"
].c.avatar_media_id.comment = "Asset ảnh đại diện; service kiểm AVATAR và owner."
metadata.tables["users"].c.cover_media_id.comment = "Asset ảnh bìa; service kiểm COVER và owner."
metadata.tables["users"].c.token_version.comment = "Phiên bản thu hồi JWT của tài khoản."
metadata.tables[
    "users"
].c.is_active.comment = "Cờ vận hành theo security; không tạo API admin, O14."
metadata.tables["users"].c.created_at.comment = "Thời điểm tạo, trả UTC qua API."
metadata.tables[
    "users"
].c.updated_at.comment = "Thời điểm thay đổi; service cập nhật, không có trigger tự động."
metadata.tables[
    "password_resets"
].comment = "T02 — Một yêu cầu OTP và grant reset; REQ-003…005, NFR-06."
metadata.tables["password_resets"].c.id.comment = "Mã dòng do DB sinh; API ánh xạ sang GraphQL ID."
metadata.tables[
    "password_resets"
].c.user_id.comment = "Tài khoản có thật; không tạo dòng cho email không tồn tại."
metadata.tables["password_resets"].c.otp_hash.comment = "Hash OTP có khóa phụ ngoài DB."
metadata.tables["password_resets"].c.failed_attempts.comment = "Số lần nhập sai; 0…5."
metadata.tables["password_resets"].c.created_at.comment = "Thời điểm tạo, trả UTC qua API."
metadata.tables["password_resets"].c.otp_expires_at.comment = "Service cấp created_at + 10 phút."
metadata.tables["password_resets"].c.verified_at.comment = "Lần xác minh thành công duy nhất."
metadata.tables[
    "password_resets"
].c.invalidated_at.comment = "Hủy do resend, quá số lần sai hoặc dọn yêu cầu cũ."
metadata.tables[
    "password_resets"
].c.reset_token_hash.comment = "Hash grant; chỉ có sau verify, không lưu bản rõ."
metadata.tables["password_resets"].c.reset_expires_at.comment = "Service cấp verified_at + 15 phút."
metadata.tables["password_resets"].c.consumed_at.comment = "Grant đã sử dụng thành công."
metadata.tables["revoked_tokens"].comment = "T03 — Thu hồi một JWT phiên; REQ-006."
metadata.tables["revoked_tokens"].c.jti.comment = "Định danh token phiên, không phải refresh token."
metadata.tables["revoked_tokens"].c.user_id.comment = "Chủ token."
metadata.tables["revoked_tokens"].c.expires_at.comment = "Hạn token; dọn sau hạn."
metadata.tables["revoked_tokens"].c.revoked_at.comment = "Thời điểm thu hồi."
metadata.tables["user_devices"].comment = "T04 — Đăng ký thiết bị push, đề xuất hợp đồng O12."
metadata.tables["user_devices"].c.id.comment = "Mã dòng do DB sinh; API ánh xạ sang GraphQL ID."
metadata.tables["user_devices"].c.user_id.comment = "Chủ hiện tại của token."
metadata.tables["user_devices"].c.push_token.comment = "Token provider; bí mật, không log."
metadata.tables["user_devices"].c.platform.comment = "android hoặc web."
metadata.tables["user_devices"].c.created_at.comment = "Thời điểm tạo, trả UTC qua API."
metadata.tables[
    "user_devices"
].c.last_active_at.comment = "Lần hoạt động gần nhất, service cập nhật."
metadata.tables["media_assets"].comment = "T05 — Metadata upload; REQ-010/014, NFR-05."
metadata.tables["media_assets"].c.id.comment = "uploadId do BE sinh, không mặc định DB."
metadata.tables["media_assets"].c.owner_id.comment = "Người upload."
metadata.tables["media_assets"].c.purpose.comment = "POST, AVATAR hoặc COVER."
metadata.tables["media_assets"].c.state.comment = "PENDING, ATTACHED, DELETE_PENDING, DELETED."
metadata.tables[
    "media_assets"
].c.provider.comment = "Tên provider; cùng storage_key tạo khóa duy nhất."
metadata.tables["media_assets"].c.storage_key.comment = "Định danh xóa tại provider."
metadata.tables["media_assets"].c.url.comment = "URL tài nguyên đã xử lý; không chứng minh quyền."
metadata.tables[
    "media_assets"
].c.input_size_bytes.comment = "Số byte đầu vào, dương; kiểm giới hạn 10 MB ở adapter."
metadata.tables["media_assets"].c.stored_size_bytes.comment = "Số byte sau xử lý, dương."
metadata.tables["media_assets"].c.mime_type.comment = "image/jpeg, image/png hoặc image/webp."
metadata.tables["media_assets"].c.width.comment = "Chiều rộng sau xử lý, 1…1600 px."
metadata.tables["media_assets"].c.height.comment = "Chiều cao sau xử lý, 1…1600 px."
metadata.tables["media_assets"].c.created_at.comment = "Thời điểm tạo, trả UTC qua API."
metadata.tables["media_assets"].c.expires_at.comment = "Hạn asset chưa gắn; TTL chờ O5."
metadata.tables["media_assets"].c.consumed_at.comment = "Lần tiêu thụ đầu."
metadata.tables["media_assets"].c.deleted_at.comment = "Provider đã dọn thành công."
metadata.tables["dishes"].comment = "T06 — Danh mục món chuẩn hóa; REQ-009/022/023/027."
metadata.tables["dishes"].c.id.comment = "Mã dòng do DB sinh; API ánh xạ sang GraphQL ID."
metadata.tables["dishes"].c.name.comment = "Tên có dấu để hiển thị."
metadata.tables["dishes"].c.name_normalized.comment = "Khóa chuẩn hóa dùng chung; không rỗng."
metadata.tables["dishes"].c.is_seed.comment = "Dòng từ bộ dữ liệu mẫu."
metadata.tables["dishes"].c.created_at.comment = "Thời điểm tạo, trả UTC qua API."
metadata.tables["restaurants"].comment = "T07 — Quán chuẩn hóa tùy chọn; REQ-009/021/023, O13."
metadata.tables["restaurants"].c.id.comment = "Mã dòng do DB sinh; API ánh xạ sang GraphQL ID."
metadata.tables["restaurants"].c.name.comment = "Tên quán; không UNIQUE vì có chi nhánh."
metadata.tables[
    "restaurants"
].c.name_normalized.comment = "Khóa tìm kiếm; không dùng tự động gộp quán."
metadata.tables["restaurants"].c.address.comment = "Địa chỉ chuẩn hóa nếu có."
metadata.tables["restaurants"].c.latitude.comment = "Vĩ độ; phải cùng có/cùng thiếu longitude."
metadata.tables["restaurants"].c.longitude.comment = "Kinh độ."
metadata.tables["restaurants"].c.created_at.comment = "Thời điểm tạo, trả UTC qua API."
metadata.tables["tags"].comment = "T08 — Thẻ; phạm vi đang mâu thuẫn C01, không cam kết bật v1."
metadata.tables["tags"].c.id.comment = "Mã dòng do DB sinh; API ánh xạ sang GraphQL ID."
metadata.tables["tags"].c.name.comment = "Nhãn có dấu."
metadata.tables["tags"].c.name_normalized.comment = "Khóa chuẩn hóa duy nhất."
metadata.tables["tags"].c.created_at.comment = "Thời điểm tạo, trả UTC qua API."
metadata.tables["posts"].comment = "T09 — Bài món ăn; REQ-007…012."
metadata.tables["posts"].c.id.comment = "Mã dòng do DB sinh; API ánh xạ sang GraphQL ID."
metadata.tables["posts"].c.user_id.comment = "Tác giả từ principal, không tin client."
metadata.tables["posts"].c.dish_id.comment = "Món bắt buộc."
metadata.tables["posts"].c.restaurant_id.comment = "Quán chuẩn hóa; xóa quán chuyển NULL."
metadata.tables["posts"].c.caption.comment = "Nội dung bài, chưa chốt giới hạn/quan hệ với feeling."
metadata.tables["posts"].c.feeling.comment = "Cảm nhận theo API, O11."
metadata.tables["posts"].c.location_name.comment = "Tên địa điểm nhập tự do."
metadata.tables["posts"].c.location_address.comment = "Địa chỉ nhập tự do."
metadata.tables["posts"].c.latitude.comment = "Tọa độ bài, không lưu vị trí truy vấn."
metadata.tables["posts"].c.longitude.comment = "Kinh độ đi cặp latitude."
metadata.tables["posts"].c.price_range.comment = "Phân khúc giá bốn giá trị; O3."
metadata.tables["posts"].c.recipe_ingredients.comment = "Danh sách nguyên liệu theo thứ tự."
metadata.tables["posts"].c.recipe_steps.comment = "Các bước công thức theo thứ tự."
metadata.tables["posts"].c.is_hidden.comment = "Cờ lọc; báo cáo không tự bật cờ."
metadata.tables["posts"].c.created_at.comment = "Thời điểm tạo, trả UTC qua API."
metadata.tables[
    "posts"
].c.updated_at.comment = "Thời điểm thay đổi; service cập nhật, không có trigger tự động."
metadata.tables["post_images"].comment = "T10 — Ảnh và thứ tự trong bài; REQ-010/011."
metadata.tables["post_images"].c.id.comment = "Mã dòng do DB sinh; API ánh xạ sang GraphQL ID."
metadata.tables["post_images"].c.post_id.comment = "Bài chứa ảnh."
metadata.tables["post_images"].c.media_id.comment = "Asset dùng tối đa một dòng ảnh bài."
metadata.tables["post_images"].c.position.comment = "Vị trí từ 0; không yêu cầu liền số."
metadata.tables["post_tags"].comment = "T11 — Liên kết bài–thẻ; phạm vi C01."
metadata.tables["post_tags"].c.post_id.comment = "Bài được gắn thẻ."
metadata.tables["post_tags"].c.tag_id.comment = "Thẻ tồn tại."
metadata.tables["likes"].comment = "T12 — Thích bài; REQ-016."
metadata.tables["likes"].c.user_id.comment = "Người thích."
metadata.tables["likes"].c.post_id.comment = "Bài được thích."
metadata.tables["likes"].c.created_at.comment = "Thời điểm tạo, trả UTC qua API."
metadata.tables["follows"].comment = "T13 — Theo dõi; REQ-018."
metadata.tables["follows"].c.follower_id.comment = "Người theo dõi."
metadata.tables["follows"].c.followee_id.comment = "Người được theo dõi."
metadata.tables["follows"].c.created_at.comment = "Thời điểm tạo, trả UTC qua API."
metadata.tables["collections"].comment = "T14 — Bộ lưu bài, gồm bộ mặc định; REQ-001/017."
metadata.tables["collections"].c.id.comment = "Mã dòng do DB sinh; API ánh xạ sang GraphQL ID."
metadata.tables["collections"].c.user_id.comment = "Chủ bộ sưu tập."
metadata.tables["collections"].c.name.comment = "Tên hiển thị, không rỗng."
metadata.tables["collections"].c.name_normalized.comment = "Tên chuẩn hóa trong phạm vi một chủ."
metadata.tables["collections"].c.is_default.comment = "Đánh dấu bộ Đã lưu."
metadata.tables["collections"].c.created_at.comment = "Thời điểm tạo, trả UTC qua API."
metadata.tables["collection_items"].comment = "T15 — Bài lưu trong bộ; REQ-017."
metadata.tables["collection_items"].c.collection_id.comment = "Bộ sưu tập."
metadata.tables["collection_items"].c.post_id.comment = "Bài được lưu."
metadata.tables["collection_items"].c.added_at.comment = "Thời điểm thêm, dùng cursor."
metadata.tables["reports"].comment = "T16 — Báo cáo và bằng chứng riêng tư; REQ-020, O2/O12."
metadata.tables["reports"].c.id.comment = "Mã dòng do DB sinh; API ánh xạ sang GraphQL ID."
metadata.tables["reports"].c.reporter_id.comment = "Người báo cáo."
metadata.tables["reports"].c.post_id.comment = "Bài còn tồn tại; SET NULL khi xóa."
metadata.tables["reports"].c.original_post_id.comment = "ID lịch sử bất biến, cố ý không FK."
metadata.tables["reports"].c.reason.comment = "Lý do không rỗng."
metadata.tables[
    "reports"
].c.evidence_snapshot.comment = "Object bằng chứng riêng tư chụp khi khóa bài."
metadata.tables["reports"].c.created_at.comment = "Thời điểm tạo, trả UTC qua API."
metadata.tables["notifications"].comment = "T17 — Thông báo trong app; REQ-016/018/019."
metadata.tables["notifications"].c.id.comment = "Mã dòng do DB sinh; API ánh xạ sang GraphQL ID."
metadata.tables["notifications"].c.user_id.comment = "Người nhận."
metadata.tables["notifications"].c.actor_id.comment = "Người gây sự kiện; NULL khi target mất."
metadata.tables[
    "notifications"
].c.post_id.comment = "Bài của LIKE/SAVE; NULL sau xóa hoặc với FOLLOW."
metadata.tables["notifications"].c.type.comment = "LIKE, SAVE, FOLLOW; SAVE chờ O12."
metadata.tables[
    "notifications"
].c.read_at.comment = "NULL là chưa đọc; không liên quan đã gửi push."
metadata.tables["notifications"].c.created_at.comment = "Thời điểm tạo, trả UTC qua API."
metadata.tables["chat_sessions"].comment = "T18 — Phiên trợ lý thuộc một người dùng; REQ-025."
metadata.tables["chat_sessions"].c.id.comment = "Mã dòng do DB sinh; API ánh xạ sang GraphQL ID."
metadata.tables["chat_sessions"].c.user_id.comment = "Chủ phiên."
metadata.tables[
    "chat_sessions"
].c.context_json.comment = "Ngữ cảnh object, không lưu bí mật hoặc lịch sử GPS."
metadata.tables["chat_sessions"].c.created_at.comment = "Thời điểm tạo, trả UTC qua API."
metadata.tables["chat_sessions"].c.ended_at.comment = "Phiên mở khi NULL; chưa có UC đóng/xóa."
metadata.tables[
    "chat_messages"
].comment = "T19 — Câu hỏi, phản hồi, draft và lượt xử lý; REQ-025/026, NFR-04/15."
metadata.tables["chat_messages"].c.id.comment = "Mã dòng do DB sinh; API ánh xạ sang GraphQL ID."
metadata.tables["chat_messages"].c.session_id.comment = "Phiên sở hữu."
metadata.tables["chat_messages"].c.reply_to_id.comment = "Câu hỏi gốc; chỉ assistant có."
metadata.tables["chat_messages"].c.role.comment = "user hoặc assistant."
metadata.tables["chat_messages"].c.content.comment = "Nội dung; assistant PENDING dùng chuỗi rỗng."
metadata.tables["chat_messages"].c.status.comment = "PENDING, OK, FAILED, FALLBACK."
metadata.tables["chat_messages"].c.post_draft.comment = "Object bản nháp; không tự tạo posts."
metadata.tables[
    "chat_messages"
].c.processing_version.comment = "user=0; assistant từ 1, tăng khi nhận retry."
metadata.tables[
    "chat_messages"
].c.processing_expires_at.comment = "Bắt buộc với assistant PENDING, còn lại NULL."
metadata.tables["chat_messages"].c.created_at.comment = "Thời điểm tạo, trả UTC qua API."
metadata.tables[
    "chat_messages"
].c.updated_at.comment = "Thời điểm thay đổi; service cập nhật, không có trigger tự động."
metadata.tables["trending_runs"].comment = "T20 — Một lần xuất bản snapshot; REQ-024."
metadata.tables["trending_runs"].c.id.comment = "Mã dòng do DB sinh; API ánh xạ sang GraphQL ID."
metadata.tables[
    "trending_runs"
].c.window_start.comment = "Đầu cửa sổ 7 ngày theo yêu cầu, service tính."
metadata.tables["trending_runs"].c.window_end.comment = "Cuối cửa sổ, lớn hơn đầu."
metadata.tables[
    "trending_runs"
].c.formula_version.comment = "Định danh công thức; không chứa công thức tự đặt."
metadata.tables["trending_runs"].c.published_at.comment = "Lúc công bố nguyên tử."
metadata.tables["trending_post_snapshots"].comment = "T21 — Điểm post theo run; REQ-024."
metadata.tables["trending_post_snapshots"].c.run_id.comment = "Lần công bố."
metadata.tables["trending_post_snapshots"].c.post_id.comment = "Đối tượng được tính điểm."
metadata.tables[
    "trending_post_snapshots"
].c.score.comment = "Điểm không tự giới hạn precision/scale hoặc không âm trước O7."
metadata.tables["trending_dish_snapshots"].comment = "T22 — Điểm dish theo run; REQ-024."
metadata.tables["trending_dish_snapshots"].c.run_id.comment = "Lần công bố."
metadata.tables["trending_dish_snapshots"].c.dish_id.comment = "Đối tượng được tính điểm."
metadata.tables[
    "trending_dish_snapshots"
].c.score.comment = "Điểm không tự giới hạn precision/scale hoặc không âm trước O7."
metadata.tables["trending_tag_snapshots"].comment = "T23 — Điểm tag theo run; REQ-024, phạm vi C01."
metadata.tables["trending_tag_snapshots"].c.run_id.comment = "Lần công bố."
metadata.tables["trending_tag_snapshots"].c.tag_id.comment = "Đối tượng được tính điểm."
metadata.tables[
    "trending_tag_snapshots"
].c.score.comment = "Điểm không tự giới hạn precision/scale hoặc không âm trước O7."
metadata.tables["media_cleanup_jobs"].comment = "T24 — Hàng đợi dọn ảnh bền vững; NFR-05/10."
metadata.tables[
    "media_cleanup_jobs"
].c.id.comment = "Mã dòng do DB sinh; API ánh xạ sang GraphQL ID."
metadata.tables[
    "media_cleanup_jobs"
].c.media_id.comment = "Asset cần dọn, tối đa một job mỗi asset."
metadata.tables["media_cleanup_jobs"].c.created_at.comment = "Thời điểm tạo, trả UTC qua API."
metadata.tables["media_cleanup_jobs"].c.next_attempt_at.comment = "Lần thử tiếp theo."
metadata.tables["media_cleanup_jobs"].c.attempts.comment = "Số lần thử đã ghi nhận, không âm."
metadata.tables["media_cleanup_jobs"].c.completed_at.comment = "NULL nghĩa còn việc."
metadata.tables[
    "media_cleanup_jobs"
].c.last_error_code.comment = "Mã lỗi đã làm sạch; không response hoặc bí mật provider."
metadata.tables["user_blocks"].comment = "T25 — Quan hệ block nạp sẵn; REQ-028, không có API tạo."
metadata.tables["user_blocks"].c.blocker_id.comment = "Người thực hiện chặn trong fixture."
metadata.tables["user_blocks"].c.blocked_id.comment = "Người bị chặn."
metadata.tables["user_blocks"].c.created_at.comment = "Thời điểm tạo, trả UTC qua API."
