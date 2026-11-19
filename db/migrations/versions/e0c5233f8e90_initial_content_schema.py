"""DOC 6.4-B v1.2: complete 25-table foundation requested by WP42-S8.1.

Frozen SQL SHA256: ad6c25c96f0103f9c28711a6f3e2a8f671cbb3258548e9df84242b2b18a54553
Migration does not read mutable project documents or run application metadata.create_all.
"""

from pathlib import Path

from alembic import context, op

revision = "e0c5233f8e90"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    script = Path(__file__).with_name("0001_initial_schema.sql").read_text(encoding="utf-8")
    if context.is_offline_mode():
        op.execute(script)
    else:
        op.get_bind().exec_driver_sql(script)


def downgrade() -> None:
    op.drop_constraint("fk_users_avatar_media_id", "users", type_="foreignkey")
    op.drop_constraint("fk_users_cover_media_id", "users", type_="foreignkey")
    op.drop_table("user_blocks")
    op.drop_table("media_cleanup_jobs")
    op.drop_table("trending_tag_snapshots")
    op.drop_table("trending_dish_snapshots")
    op.drop_table("trending_post_snapshots")
    op.drop_table("trending_runs")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("notifications")
    op.drop_table("reports")
    op.drop_table("collection_items")
    op.drop_table("collections")
    op.drop_table("follows")
    op.drop_table("likes")
    op.drop_table("post_tags")
    op.drop_table("post_images")
    op.drop_table("posts")
    op.drop_table("tags")
    op.drop_table("restaurants")
    op.drop_table("dishes")
    op.drop_table("media_assets")
    op.drop_table("user_devices")
    op.drop_table("revoked_tokens")
    op.drop_table("password_resets")
    op.drop_table("users")
    # Extensions belong to the database environment, not this application's rows.
    # Alembic itself keeps alembic_version empty at base; do not drop it mid-migration.
