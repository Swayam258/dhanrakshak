from pydantic import BaseModel
from typing import List, Optional

class Health(BaseModel):
    status: str

class AdviceIn(BaseModel):
    prompt: str
    language: str = "hi"

class AdviceOut(BaseModel):
    advice: str

class FraudIn(BaseModel):
    text: str

class FraudOut(BaseModel):
    risk: str
    score: float
    matches: List[str]

class STTOut(BaseModel):
    text: str

class TTSIn(BaseModel):
    text: str
    language: Optional[str] = "hi"