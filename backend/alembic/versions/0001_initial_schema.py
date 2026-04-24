"""initial schema — todas as tabelas da Fase 1

Revision ID: 0001
Revises:
Create Date: 2026-04-24

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── roles ──────────────────────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
    )

    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ── user_roles ─────────────────────────────────────────────────────────
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
    )

    # ── tipsters ───────────────────────────────────────────────────────────
    op.create_table(
        "tipsters",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("bio", sa.Text, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── youtube_channels ───────────────────────────────────────────────────
    op.create_table(
        "youtube_channels",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tipster_id", sa.Integer, sa.ForeignKey("tipsters.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("channel_name", sa.String(255), nullable=False),
        sa.Column("channel_url", sa.String(512), nullable=False),
        sa.Column("channel_external_id", sa.String(255), unique=True, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("monitoring_frequency_minutes", sa.Integer, nullable=False, server_default="60"),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_video_published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_video_analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_successful_analysis_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failed_analysis_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_irrelevant_video_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("monitoring_status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_youtube_channels_last_checked_at", "youtube_channels", ["last_checked_at"])

    # ── videos ─────────────────────────────────────────────────────────────
    op.create_table(
        "videos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("channel_id", sa.Integer, sa.ForeignKey("youtube_channels.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("youtube_video_id", sa.String(50), unique=True, nullable=False),
        sa.Column("youtube_url", sa.String(512), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("thumbnail_url", sa.String(512), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="discovered"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_videos_channel_published", "videos", ["channel_id", "published_at"])

    # ── video_analyses ─────────────────────────────────────────────────────
    op.create_table(
        "video_analyses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("video_id", sa.Integer, sa.ForeignKey("videos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("analysis_url_slug", sa.String(255), unique=True, nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("analysis_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("content_scope", sa.String(50), nullable=True),
        sa.Column("summary_text", sa.Text, nullable=True),
        sa.Column("games_detected_count", sa.Integer, server_default="0"),
        sa.Column("ideas_detected_count", sa.Integer, server_default="0"),
        sa.Column("actionable_ideas_count", sa.Integer, server_default="0"),
        sa.Column("warnings_count", sa.Integer, server_default="0"),
        sa.Column("no_value_count", sa.Integer, server_default="0"),
        sa.Column("review_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("reviewer_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("model_version", sa.String(100), nullable=True),
        sa.Column("prompt_version", sa.String(100), nullable=True),
        sa.Column("schema_version", sa.String(100), nullable=True),
        sa.Column("raw_output_json", sa.JSON, nullable=True),
        sa.Column("normalized_output_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_video_analyses_video_analyzed", "video_analyses", ["video_id", "analyzed_at"])

    # ── video_transcripts ──────────────────────────────────────────────────
    op.create_table(
        "video_transcripts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("video_id", sa.Integer, sa.ForeignKey("videos.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("transcript_source", sa.String(50), nullable=True),
        sa.Column("language_code", sa.String(10), nullable=True),
        sa.Column("raw_transcript_text", sa.Text, nullable=True),
        sa.Column("normalized_transcript_text", sa.Text, nullable=True),
        sa.Column("has_timestamps", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── transcript_segments ────────────────────────────────────────────────
    op.create_table(
        "transcript_segments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("video_id", sa.Integer, sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transcript_id", sa.Integer, sa.ForeignKey("video_transcripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_seconds", sa.Float, nullable=True),
        sa.Column("end_seconds", sa.Float, nullable=True),
        sa.Column("raw_text", sa.Text, nullable=True),
        sa.Column("normalized_text", sa.Text, nullable=True),
        sa.Column("segment_type", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── competitions ───────────────────────────────────────────────────────
    op.create_table(
        "competitions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("season", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── teams ──────────────────────────────────────────────────────────────
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── team_aliases ───────────────────────────────────────────────────────
    op.create_table(
        "team_aliases",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("team_id", sa.Integer, sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alias", sa.String(255), nullable=False),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_team_aliases_alias", "team_aliases", ["alias"])

    # ── games ──────────────────────────────────────────────────────────────
    op.create_table(
        "games",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("competition_id", sa.Integer, sa.ForeignKey("competitions.id"), nullable=True),
        sa.Column("home_team_id", sa.Integer, sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("away_team_id", sa.Integer, sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("round_label", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="scheduled"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_games_scheduled_at", "games", ["scheduled_at"])

    # ── game_aliases ───────────────────────────────────────────────────────
    op.create_table(
        "game_aliases",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("game_id", sa.Integer, sa.ForeignKey("games.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alias", sa.String(255), nullable=False),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── game_ideas ─────────────────────────────────────────────────────────
    op.create_table(
        "game_ideas",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("game_id", sa.Integer, sa.ForeignKey("games.id"), nullable=True),
        sa.Column("tipster_id", sa.Integer, sa.ForeignKey("tipsters.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("video_id", sa.Integer, sa.ForeignKey("videos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("video_analysis_id", sa.Integer, sa.ForeignKey("video_analyses.id"), nullable=True),
        sa.Column("segment_id", sa.Integer, sa.ForeignKey("transcript_segments.id"), nullable=True),
        sa.Column("source_timestamp_start", sa.Float, nullable=True),
        sa.Column("source_timestamp_end", sa.Float, nullable=True),
        sa.Column("idea_type", sa.String(50), nullable=False),
        sa.Column("market_type", sa.String(50), nullable=False, server_default="no_specific_market"),
        sa.Column("selection_label", sa.String(255), nullable=True),
        sa.Column("sentiment_direction", sa.String(50), nullable=True),
        sa.Column("confidence_band", sa.String(20), nullable=True),
        sa.Column("confidence_expression_text", sa.Text, nullable=True),
        sa.Column("belief_text", sa.Text, nullable=True),
        sa.Column("fear_text", sa.Text, nullable=True),
        sa.Column("entry_text", sa.Text, nullable=True),
        sa.Column("avoid_text", sa.Text, nullable=True),
        sa.Column("rationale_text", sa.Text, nullable=True),
        sa.Column("condition_text", sa.Text, nullable=True),
        sa.Column("source_excerpt", sa.Text, nullable=True),
        sa.Column("is_actionable", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("needs_review", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("extraction_confidence", sa.Float, nullable=True),
        sa.Column("review_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_game_ideas_game_tipster", "game_ideas", ["game_id", "tipster_id"])
    op.create_index("ix_game_ideas_video_id", "game_ideas", ["video_id"])

    # ── idea_conditions ────────────────────────────────────────────────────
    op.create_table(
        "idea_conditions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("idea_id", sa.Integer, sa.ForeignKey("game_ideas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("condition_type", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("condition_text", sa.Text, nullable=True),
        sa.Column("is_inferred", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── idea_reasons ───────────────────────────────────────────────────────
    op.create_table(
        "idea_reasons",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("idea_id", sa.Integer, sa.ForeignKey("game_ideas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason_category", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("reason_text", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── idea_labels ────────────────────────────────────────────────────────
    op.create_table(
        "idea_labels",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("idea_id", sa.Integer, sa.ForeignKey("game_ideas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(50), nullable=False),
    )

    # ── idea_reviews ───────────────────────────────────────────────────────
    op.create_table(
        "idea_reviews",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("idea_id", sa.Integer, sa.ForeignKey("game_ideas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("previous_data_json", sa.JSON, nullable=True),
        sa.Column("new_data_json", sa.JSON, nullable=True),
        sa.Column("review_notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── video_analysis_reviews ─────────────────────────────────────────────
    op.create_table(
        "video_analysis_reviews",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("video_analysis_id", sa.Integer, sa.ForeignKey("video_analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("review_notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── game_results ───────────────────────────────────────────────────────
    op.create_table(
        "game_results",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("game_id", sa.Integer, sa.ForeignKey("games.id", ondelete="RESTRICT"), unique=True, nullable=False),
        sa.Column("home_score", sa.Integer, nullable=True),
        sa.Column("away_score", sa.Integer, nullable=True),
        sa.Column("both_teams_scored", sa.Boolean, nullable=True),
        sa.Column("total_goals", sa.Integer, nullable=True),
        sa.Column("corners_total", sa.Integer, nullable=True),
        sa.Column("cards_total", sa.Integer, nullable=True),
        sa.Column("result_source", sa.String(100), nullable=True),
        sa.Column("is_manual", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_by_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── idea_evaluations ───────────────────────────────────────────────────
    op.create_table(
        "idea_evaluations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("idea_id", sa.Integer, sa.ForeignKey("game_ideas.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("evaluation_type", sa.String(50), nullable=False),
        sa.Column("evaluation_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("is_hit", sa.Boolean, nullable=True),
        sa.Column("is_partial_hit", sa.Boolean, nullable=True),
        sa.Column("manual_required", sa.Boolean, server_default="false"),
        sa.Column("evaluation_notes", sa.Text, nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evaluated_by_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_idea_evaluations_idea_id", "idea_evaluations", ["idea_id"])

    # ── audit_events ───────────────────────────────────────────────────────
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer, nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("actor_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_payload_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_events_entity", "audit_events", ["entity_type", "entity_id", "created_at"])

    # ── processing_jobs ────────────────────────────────────────────────────
    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", sa.Integer, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("payload_json", sa.JSON, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("processing_jobs")
    op.drop_table("audit_events")
    op.drop_table("idea_evaluations")
    op.drop_table("game_results")
    op.drop_table("video_analysis_reviews")
    op.drop_table("idea_reviews")
    op.drop_table("idea_labels")
    op.drop_table("idea_reasons")
    op.drop_table("idea_conditions")
    op.drop_table("game_ideas")
    op.drop_table("game_aliases")
    op.drop_table("games")
    op.drop_table("team_aliases")
    op.drop_table("teams")
    op.drop_table("competitions")
    op.drop_table("transcript_segments")
    op.drop_table("video_transcripts")
    op.drop_table("video_analyses")
    op.drop_table("videos")
    op.drop_table("youtube_channels")
    op.drop_table("tipsters")
    op.drop_table("user_roles")
    op.drop_table("users")
    op.drop_table("roles")
