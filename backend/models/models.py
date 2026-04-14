"""
SQLAlchemy ORM 模型

对照 Java 的 JPA/Hibernate @Entity，这里用 Python 的 SQLAlchemy 2.0 风格。

Java:                               Python (SQLAlchemy):
@Entity                             class Document(Base):
@Table(name="documents")               __tablename__ = "documents"
@Id @GeneratedValue                    id = mapped_column(Integer, primary_key=True)
@Column                                title = mapped_column(String)
@ManyToOne                             chunks = relationship(...)
"""

from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime, ForeignKey, Index, Integer,
    String, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    documents: Mapped[list["Document"]] = relationship(
        back_populates="knowledge_base", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="knowledge_base"
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kb_id: Mapped[Optional[int]] = mapped_column(ForeignKey("knowledge_bases.id", ondelete="CASCADE"))
    title: Mapped[Optional[str]] = mapped_column(String(500))
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)   # pdf / md / txt
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    knowledge_base: Mapped[Optional["KnowledgeBase"]] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

    # JSONB 上的 GIN 索引（对应 init.sql 里的 idx_documents_metadata）
    __table_args__ = (
        Index("idx_documents_metadata_orm", "metadata", postgresql_using="gin"),
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[Optional[int]] = mapped_column(Integer)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    # pgvector 列：1536 维，对应 OpenAI text-embedding-3-small
    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(1536))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    document: Mapped["Document"] = relationship(back_populates="chunks")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kb_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("knowledge_bases.id", ondelete="SET NULL")
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    knowledge_base: Mapped[Optional["KnowledgeBase"]] = relationship(
        back_populates="conversations"
    )
