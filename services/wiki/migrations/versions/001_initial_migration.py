"""Initial migration

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create pages table
    op.create_table(
        "pages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("section", sa.String(100), nullable=True),
        sa.Column("order_index", sa.Integer(), server_default="0"),
        sa.Column("status", sa.String(20), server_default="published"),
        sa.Column("is_public", sa.Boolean(), server_default="true"),
        sa.Column("word_count", sa.Integer(), server_default="0"),
        sa.Column("content_size_kb", sa.Float(), server_default="0.0"),
        sa.Column("is_orphaned", sa.Boolean(), server_default="false"),
        sa.Column("orphaned_from", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_system_page", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["pages.id"],
        ),
        sa.ForeignKeyConstraint(
            ["orphaned_from"],
            ["pages.id"],
        ),
        sa.UniqueConstraint("slug", name="pages_slug_key"),
    )

    # Create wiki_config table
    op.create_table(
        "wiki_config",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.UniqueConstraint("key", name="wiki_config_key_key"),
    )

    # Create oversized_page_notifications table
    op.create_table(
        "oversized_page_notifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("current_size_kb", sa.Float(), nullable=False),
        sa.Column("max_size_kb", sa.Float(), nullable=False),
        sa.Column("resolution_due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "notified_users", postgresql.JSON(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("resolved", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["page_id"], ["pages.id"], ondelete="CASCADE"),
    )

    # Create comments table
    op.create_table(
        "comments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_comment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_recommendation", sa.Boolean(), server_default="false"),
        sa.Column("thread_depth", sa.Integer(), server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(["page_id"], ["pages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["parent_comment_id"], ["comments.id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint("thread_depth <= 5", name="max_thread_depth"),
    )

    # Create page_links table
    op.create_table(
        "page_links",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("from_page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("link_text", sa.String(255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(["from_page_id"], ["pages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_page_id"], ["pages.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("from_page_id", "to_page_id", name="unique_page_link"),
    )

    # Create index_entries table
    op.create_table(
        "index_entries",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("term", sa.String(255), nullable=False),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("is_keyword", sa.Boolean(), server_default="false"),
        sa.Column("is_manual", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(["page_id"], ["pages.id"], ondelete="CASCADE"),
    )

    # Create page_versions table
    op.create_table(
        "page_versions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("diff_data", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(["page_id"], ["pages.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("page_id", "version", name="unique_page_version"),
    )

    # Create images table
    op.create_table(
        "images",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("uuid", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.UniqueConstraint("uuid", name="images_uuid_key"),
    )

    # Create page_images table
    op.create_table(
        "page_images",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(["page_id"], ["pages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["image_id"], ["images.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("page_id", "image_id", name="unique_page_image"),
    )

    # Create indexes for pages table
    op.create_index("idx_pages_parent", "pages", ["parent_id"])
    op.create_index("idx_pages_section", "pages", ["section"])
    op.create_index("idx_pages_slug", "pages", ["slug"])
    op.create_index("idx_pages_status", "pages", ["status"])
    # Partial indexes
    op.execute(
        "CREATE INDEX idx_pages_orphaned ON pages(is_orphaned) WHERE is_orphaned = TRUE"
    )
    op.execute(
        "CREATE INDEX idx_pages_system ON pages(is_system_page) WHERE is_system_page = TRUE"
    )

    # Create indexes for comments table
    op.create_index("idx_comments_page", "comments", ["page_id"])
    op.create_index("idx_comments_parent", "comments", ["parent_comment_id"])
    op.create_index("idx_comments_depth", "comments", ["thread_depth"])

    # Create indexes for page_links table
    op.create_index("idx_links_from", "page_links", ["from_page_id"])
    op.create_index("idx_links_to", "page_links", ["to_page_id"])

    # Create indexes for index_entries table
    op.create_index("idx_index_term", "index_entries", ["term"])
    op.create_index("idx_index_page", "index_entries", ["page_id"])
    # Partial indexes
    op.execute(
        "CREATE INDEX idx_index_keyword ON index_entries(is_keyword) WHERE is_keyword = TRUE"
    )
    op.execute(
        "CREATE INDEX idx_index_manual ON index_entries(is_manual) WHERE is_manual = TRUE"
    )

    # Create indexes for page_versions table
    op.create_index("idx_versions_page", "page_versions", ["page_id"])
    op.create_index(
        "idx_versions_version",
        "page_versions",
        ["page_id", "version"],
        postgresql_ops={"version": "DESC"},
    )

    # Create indexes for oversized_page_notifications table
    op.create_index("idx_oversized_page", "oversized_page_notifications", ["page_id"])
    op.create_index(
        "idx_oversized_resolved", "oversized_page_notifications", ["resolved"]
    )
    op.create_index(
        "idx_oversized_due_date",
        "oversized_page_notifications",
        ["resolution_due_date"],
    )

    # Create indexes for images table
    op.create_index("idx_images_uuid", "images", ["uuid"])

    # Create indexes for page_images table
    op.create_index("idx_page_images_page", "page_images", ["page_id"])
    op.create_index("idx_page_images_image", "page_images", ["image_id"])


def downgrade():
    # Drop indexes
    op.drop_index("idx_page_images_image", table_name="page_images")
    op.drop_index("idx_page_images_page", table_name="page_images")
    op.drop_index("idx_images_uuid", table_name="images")
    op.drop_index("idx_oversized_due_date", table_name="oversized_page_notifications")
    op.drop_index("idx_oversized_resolved", table_name="oversized_page_notifications")
    op.drop_index("idx_oversized_page", table_name="oversized_page_notifications")
    op.drop_index("idx_versions_version", table_name="page_versions")
    op.drop_index("idx_versions_page", table_name="page_versions")
    op.execute("DROP INDEX IF EXISTS idx_index_manual")
    op.execute("DROP INDEX IF EXISTS idx_index_keyword")
    op.drop_index("idx_index_page", table_name="index_entries")
    op.drop_index("idx_index_term", table_name="index_entries")
    op.drop_index("idx_links_to", table_name="page_links")
    op.drop_index("idx_links_from", table_name="page_links")
    op.drop_index("idx_comments_depth", table_name="comments")
    op.drop_index("idx_comments_parent", table_name="comments")
    op.drop_index("idx_comments_page", table_name="comments")
    op.execute("DROP INDEX IF EXISTS idx_pages_system")
    op.execute("DROP INDEX IF EXISTS idx_pages_orphaned")
    op.drop_index("idx_pages_status", table_name="pages")
    op.drop_index("idx_pages_slug", table_name="pages")
    op.drop_index("idx_pages_section", table_name="pages")
    op.drop_index("idx_pages_parent", table_name="pages")

    # Drop tables (in reverse order due to foreign keys)
    op.drop_table("page_images")
    op.drop_table("images")
    op.drop_table("page_versions")
    op.drop_table("index_entries")
    op.drop_table("page_links")
    op.drop_table("comments")
    op.drop_table("oversized_page_notifications")
    op.drop_table("wiki_config")
    op.drop_table("pages")
