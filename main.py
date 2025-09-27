import io
import os
import base64
from typing import Optional

from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from gtts import gTTS

import google.generativeai as genai
# --- New Import for Asynchronous Handling ---
from starlette.concurrency import run_in_threadpool

# Corrected: All imports are now relative to the current package
from dhanrakshak_app.database import Base, engine, get_db
from sqlalchemy import text

# --- FIX 1: Correctly import LogEntry here (it was incorrectly nested/indented before) ---
from dhanrakshak_app.models import LogEntry
from dhanrakshak_app.schemas import AdviceIn, AdviceOut, FraudIn, FraudOut, STTOut, TTSIn, Health
from dhanrakshak_app.ml_fraud import fraud_scorer


# Add this function directly in main.py
def test_db_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


# Load environment (.env)
load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="DhanRakshak API", version="1.0")


@app.get("/")
def root():
    return {"message": "Welcome to DhanRakshak API"}


# CORS (allow Streamlit frontend)
origins = ["http://localhost:8501", "http://127.0.0.1:8501", "*"]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ---- Google Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
model = None
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # --- FIX 2: Change the model name from 'gemini-pro' to 'gemini-2.5-flash' ---
    model = genai.GenerativeModel('gemini-2.5-flash')

ADVICE_SYSTEM = """You are DhanRakshak, a friendly financial literacy helper for rural India.
Keep answers simple, practical, and scam-aware. Use the requested language when possible.
Focus on:
- Simple budgeting tips (50-30-20 rule)
- Scam awareness (never share OTP, KYC scams)
- Basic banking and savings advice
- Government schemes awareness
- Digital payment safety

Always provide practical, actionable advice in simple language that rural users can understand.
"""


@app.get("/api/v1/health", response_model=Health)
def health():
    return Health(status="ok")


# --- Made async and wrapped blocking I/O calls (Gemini API, DB operations) in run_in_threadpool ---
@app.post("/api/v1/advice", response_model=AdviceOut)
async def advice(inp: AdviceIn, db: Session = Depends(get_db)):
    # If no Gemini key, return a friendly placeholder
    if not model:
        text = f"(demo) You asked: {inp.prompt}. Tip: Never share your OTP. Make a simple budget using the 50-30-20 rule. Always verify before clicking suspicious links."
    else:
        try:
            # Create the prompt for Gemini
            prompt = f"""
{ADVICE_SYSTEM}

Language to respond in: {inp.language}
User Question: {inp.prompt}

Please provide helpful financial advice in the requested language, keeping it simple and practical for rural Indian users.
"""

            # Run the blocking Gemini call in a separate thread
            response = await run_in_threadpool(model.generate_content, prompt)
            text = response.text

        except Exception as e:
            # Fallback if Gemini API fails
            text = f"Sorry, I'm having trouble connecting right now. Here's a quick tip: Never share your OTP with anyone, and always verify suspicious messages by calling your bank directly."
            print(f"Gemini API error: {e}")

    # Log the interaction (DB operations are blocking, so wrap them)
    await run_in_threadpool(db.add, LogEntry(kind="advice", input_text=inp.prompt, meta=f"lang={inp.language}"))
    await run_in_threadpool(db.commit)
    return AdviceOut(advice=text)


# --- Made async and wrapped blocking calls (fraud_scorer, DB operations) in run_in_threadpool ---
@app.post("/api/v1/fraud-score", response_model=FraudOut)
async def fraud_score(inp: FraudIn, db: Session = Depends(get_db)):
    # Run synchronous fraud scoring in a separate thread
    risk, score, hits = await run_in_threadpool(fraud_scorer.score_text, inp.text)

    await run_in_threadpool(db.add, LogEntry(kind="fraud", input_text=inp.text, score=score, meta=";".join(hits)))
    await run_in_threadpool(db.commit)
    return FraudOut(risk=risk, score=score, matches=hits)


# --- Made async and wrapped multiple blocking calls in run_in_threadpool ---
@app.post("/api/v1/fraud-score-advanced", response_model=FraudOut)
async def fraud_score_advanced(inp: FraudIn, db: Session = Depends(get_db)):
    # First get the basic ML score
    risk, score, hits = await run_in_threadpool(fraud_scorer.score_text, inp.text)

    # If Gemini is available, get additional analysis
    if model:
        try:
            gemini_prompt = f"""
Analyze this message for potential fraud indicators. Look for:
- Urgency tactics
- Requests for personal information (OTP, passwords, bank details)
- Suspicious links or phone numbers
- Too-good-to-be-true offers
- Impersonation of banks/government agencies
- Poor grammar or spelling (common in scams)

Message to analyze: "{inp.text}"

Respond with just: HIGH_RISK, MEDIUM_RISK, or LOW_RISK and briefly explain why.
"""
            # Run the blocking Gemini call in a separate thread
            response = await run_in_threadpool(model.generate_content, gemini_prompt)
            gemini_analysis = response.text.strip()

            # Adjust risk based on Gemini's analysis
            if "HIGH_RISK" in gemini_analysis.upper():
                if risk != "high":
                    risk = "high" if score > 1.0 else "medium"
                    score = min(score + 0.5, 3.0)  # Boost score but cap it
            elif "MEDIUM_RISK" in gemini_analysis.upper() and risk == "low":
                risk = "medium"
                score = max(score, 1.0)

        except Exception as e:
            print(f"Gemini fraud analysis error: {e}")

    await run_in_threadpool(db.add,
                            LogEntry(kind="fraud_advanced", input_text=inp.text, score=score, meta=";".join(hits)))
    await run_in_threadpool(db.commit)
    return FraudOut(risk=risk, score=score, matches=hits)


# ---- Speech-to-Text (local Whisper OR placeholder)
USE_LOCAL_WHISPER = bool(os.getenv("USE_LOCAL_WHISPER", "0") == "1")
if USE_LOCAL_WHISPER:
    try:
        import whisper

        whisper_model = whisper.load_model("base")
    except ImportError:
        print("Whisper not installed. STT will be disabled.")
        USE_LOCAL_WHISPER = False


@app.post("/api/v1/stt", response_model=STTOut)
async def stt(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if USE_LOCAL_WHISPER:
        audio_bytes = await file.read()
        tmp = "temp_audio.wav"

        # Wrap blocking file I/O operations
        await run_in_threadpool(lambda: open(tmp, "wb").write(audio_bytes))

        # Run heavy blocking Whisper transcription in a separate thread
        result = await run_in_threadpool(whisper_model.transcribe, tmp)
        text = result.get("text", "").strip()

        # Wrap blocking file I/O operations
        await run_in_threadpool(os.remove, tmp)
    else:
        text = "(demo) STT is disabled; enable by setting USE_LOCAL_WHISPER=1 and installing whisper+torch."

    await run_in_threadpool(db.add, LogEntry(kind="stt", meta=file.filename))
    await run_in_threadpool(db.commit)
    return STTOut(text=text)


# --- Made async and wrapped blocking TTS generation and DB operations in run_in_threadpool ---
@app.post("/api/v1/tts")
async def tts(inp: TTSIn, db: Session = Depends(get_db)):
    try:
        # Define a helper function to encapsulate the blocking gTTS/base64 logic
        def generate_audio():
            tts_obj = gTTS(text=inp.text, lang=inp.language or "hi")
            buf = io.BytesIO()
            tts_obj.write_to_fp(buf)
            buf.seek(0)
            return base64.b64encode(buf.read()).decode("utf-8")

        # Run the blocking function in a separate thread
        audio_b64 = await run_in_threadpool(generate_audio)

        await run_in_threadpool(db.add, LogEntry(kind="tts", input_text=inp.text, meta=f"lang={inp.language}"))
        await run_in_threadpool(db.commit)
        return {"audio_base64": audio_b64, "mime": "audio/mpeg"}
    except Exception as e:
        print(f"TTS error: {e}")
        return {"error": "Failed to generate audio", "audio_base64": "", "mime": ""}


@app.get("/ping")
def ping():
    return {"message": "pong"}
