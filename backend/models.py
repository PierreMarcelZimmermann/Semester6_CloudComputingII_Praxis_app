from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ImageAnalysisResult(Base):
    __tablename__ = 'image_analysis_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    caption_text = Column(String(255), nullable=True)
    caption_confidence = Column(Float, nullable=True) 