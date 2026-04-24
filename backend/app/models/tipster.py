from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Tipster(Base):
    __tablename__ = "tipsters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    # active | inactive
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    channels: Mapped[list["YoutubeChannel"]] = relationship("YoutubeChannel", back_populates="tipster")
