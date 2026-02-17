from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import sqlite3
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# DATABASE SETUP
# -----------------------------
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS processed_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original TEXT,
    analysis TEXT,
    sentiment TEXT,
    timestamp TEXT
)
""")
conn.commit()


# -----------------------------
# REQUEST MODEL
# -----------------------------
class PipelineRequest(BaseModel):
    email: str
    source: str


# -----------------------------
# PIPELINE ENDPOINT
# -----------------------------
@app.post("/pipeline")
def run_pipeline(request: PipelineRequest):

    processed_items = []
    errors = []

    # 1️⃣ FETCH DATA FROM EXTERNAL API
    try:
        response = requests.get("https://jsonplaceholder.typicode.com/comments")
        data = response.json()[:5]  # Take only first 5 items
    except Exception as e:
        return {"error": f"Fetch error: {str(e)}"}

    # 2️⃣ PROCESS EACH ITEM
    for item in data:
        original_text = item["body"]

        try:
            # -----------------------------
            # MOCK AI ENRICHMENT
            # -----------------------------

            # Simple summary
            analysis = original_text[:100] + "..."

            # Simple sentiment logic
            if any(word in original_text.lower() for word in ["good", "great", "excellent", "love"]):
                sentiment = "enthusiastic"
            elif any(word in original_text.lower() for word in ["bad", "worst", "hate", "terrible"]):
                sentiment = "critical"
            else:
                sentiment = "objective"


            # -----------------------------
            # STORE IN DATABASE
            # -----------------------------
            timestamp = datetime.utcnow().isoformat()

            cursor.execute("""
                INSERT INTO processed_items (original, analysis, sentiment, timestamp)
                VALUES (?, ?, ?, ?)
            """, (original_text, analysis, sentiment, timestamp))

            conn.commit()

            processed_items.append({
                "original": original_text,
                "analysis": analysis,
                "sentiment": sentiment,
                "stored": True,
                "timestamp": timestamp
            })

        except Exception as e:
            errors.append(str(e))

    # 3️⃣ SEND MOCK NOTIFICATION
    notification_sent = True

    return {
        "items": processed_items,
        "notificationSent": notification_sent,
        "processedAt": datetime.utcnow().isoformat(),
        "errors": errors
    }
