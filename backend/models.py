from sqlalchemy import Column, Integer, String, Float, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ImageAnalysisResult(Base):
    __tablename__ = 'image_analysis_results'

    id = Column(Integer, primary_key=True)
    caption_text = Column(String(255), nullable=True)
    caption_confidence = Column(Float, nullable=True)
    read_text = Column(JSON, nullable=True)  # Store recognized text and its bounding box

    def __repr__(self):
        return f"<ImageAnalysisResult(id={self.id}, caption_text={self.caption_text})>"
