from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from dhanrakshak_app.database import Base

class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    kind = Column(String(50), nullable=False, index=True)
    input_text = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    meta = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<LogEntry(id={self.id}, kind='{self.kind}', created_at='{self.created_at}')>"