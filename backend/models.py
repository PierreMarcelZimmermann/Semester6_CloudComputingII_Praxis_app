from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ImageAnalysisResult(Base):
    __tablename__ = 'image_analysis_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_hash = Column(String(64), unique=True, nullable=False)
    caption_text = Column(String(255), nullable=True)
    caption_confidence = Column(Float, nullable=True)