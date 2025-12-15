import sqlite3
import json
from datetime import datetime

DB_PATH = "meetings.db"


def init_db():
    """تهيئة قاعدة البيانات وإنشاء الجدول في حالة عدم وجوده."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS meetings (
                id TEXT PRIMARY KEY,
                sales_id TEXT,
                meeting_date TEXT,
                analysis_json TEXT,
                pdfs_json TEXT,
                followup_json TEXT,
                scoring_json TEXT
            )
        """)
        conn.commit()


def save_meeting_result(sales_id, analysis, pdfs, followup):
    """
    تخزين بيانات اجتماع في قاعدة البيانات.
    sales_id: من الـ sidebar في Streamlit
    analysis: JSON يحتوي على التحليل
    pdfs: قائمة من الـ PDF (اسم الملف + الوصف)
    followup: JSON يحتوي على خطة المتابعة والـ scoring
    """
    meeting_id = datetime.now().strftime("%Y%m%d-%H%M%S")  # استخدام توقيت دقيق كـ ID فريد
    meeting_date = datetime.now().isoformat()

    scoring = followup.get("sales_scoring", {})

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
       
        c.execute("""
            SELECT 1 FROM meetings WHERE id = ?
        """, (meeting_id,))
        if c.fetchone():
            return "Meeting already exists in the database."

        c.execute("""
            INSERT INTO meetings (id, sales_id, meeting_date, analysis_json, pdfs_json, followup_json, scoring_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            meeting_id,
            sales_id,
            meeting_date,
            json.dumps(analysis, ensure_ascii=False),
            json.dumps(pdfs, ensure_ascii=False),
            json.dumps(followup, ensure_ascii=False),
            json.dumps(scoring, ensure_ascii=False)
        ))
        conn.commit()

    return meeting_id


def load_all_meetings():
    """
    تحميل جميع الاجتماعات المخزنة في قاعدة البيانات.
    يرجع قائمة من الاجتماعات:
    [
      {
        "id": ...,
        "sales_id": ...,
        "meeting_date": ...,
        "analysis": {...},
        "pdfs": [...],
        "followup": {...},
        "scoring": {...}
      }
    ]
    """
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, sales_id, meeting_date, analysis_json, pdfs_json, followup_json, scoring_json
            FROM meetings
            ORDER BY meeting_date DESC
        """)
        rows = c.fetchall()

    meetings = []
    for r in rows:
        meetings.append({
            "id": r[0],
            "sales_id": r[1],
            "meeting_date": r[2],
            "analysis": json.loads(r[3]),
            "pdfs": json.loads(r[4]),
            "followup": json.loads(r[5]),
            "scoring": json.loads(r[6]),
        })
    return meetings
