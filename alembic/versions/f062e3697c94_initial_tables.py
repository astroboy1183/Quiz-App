"""initial_tables

Revision ID: f062e3697c94
Revises:
Create Date: 2026-05-02 22:07:43.792866

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "f062e3697c94"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),  # noqa: E501
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("avatar", sa.String(), nullable=True),
        sa.Column(
            "preferred_topic", sa.String(), nullable=False, server_default="Mixed"
        ),  # noqa: E501
        sa.Column(
            "preferred_difficulty", sa.String(), nullable=False, server_default="Medium"
        ),  # noqa: E501
        sa.Column("question_count", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("timer_duration", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "quiz_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),  # noqa: E501
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),  # noqa: E501
        sa.Column("topic", sa.String(), nullable=False),
        sa.Column("difficulty", sa.String(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_qs", sa.Integer(), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("time_taken", sa.Integer(), nullable=True),
        sa.Column("mode", sa.String(), nullable=False, server_default="solo"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "answers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),  # noqa: E501
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("quiz_sessions.id"),
            nullable=False,
        ),  # noqa: E501
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("correct_answer", sa.String(), nullable=False),
        sa.Column("user_answer", sa.String(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("topic", sa.String(), nullable=False),
        sa.Column("difficulty", sa.String(), nullable=False),
        sa.Column("time_taken", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("answers")
    op.drop_table("quiz_sessions")
    op.drop_table("users")
