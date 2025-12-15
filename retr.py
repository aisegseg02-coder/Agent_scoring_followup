import os
import json
from fuzzywuzzy import fuzz
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("ERROR: Missing GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

# -------------------------------------------
# LOAD PDF DESCRIPTIONS (Marketing_cached_data)
# -------------------------------------------

PDF_DB_PATH = r"E:\Rag\Sector_Engine\Marketing_cached_data.json"

if os.path.exists(PDF_DB_PATH):
    with open(PDF_DB_PATH, "r", encoding="utf-8") as f:
        PDF_DESCRIPTIONS = json.load(f)
else:
    PDF_DESCRIPTIONS = {}


def pdf_description_engine(pdf_name):
    """
    1) If description exists in cached DB → return it
    2) Else → Auto-generate human-level description based on keywords
    """

    # 1 — Check DB
    if pdf_name in PDF_DESCRIPTIONS:
        return PDF_DESCRIPTIONS[pdf_name]

    name = pdf_name.replace(".pdf", "").lower()

    # 2 — Auto keywords
    if "استراتيجي" in name or "خارطة" in name:
        return "هذا الملف يشرح خطوات عملية لوضع خطة نمو واضحة للمتجر وتحسين النتائج بشكل مستمر."

    if "ugc" in name or "المحتوى الذي يولده المستخدم" in name:
        return "ملف يوضح كيفية استخدام محتوى العملاء لبناء الثقة وزيادة التحويلات بتكلفة منخفضة."

    if "تسويق" in name:
        return "دليل تسويقي يحتوي أفكار وتكتيكات جاهزة للتطبيق في السوق السعودي."

    if "إعلان" in name or "حملات" in name:
        return "شرح مفصل لآليات حملات الإعلانات وأفضل طرق إدارة الميزانية."

    if "علامة" in name or "هوية" in name:
        return "دليل مختصر حول كيفية بناء هوية تجارية قوية ومتناسقة."

    # Default
    return "ملف ذو صلة بموضوع الاجتماع ويساعدك في فهم الخطوات بشكل أوضح."


# -------------------------------------------
# Extract client name (simple heuristic)
# -------------------------------------------

def extract_client_name(meeting_text):
    lines = meeting_text.split("\n")
    for line in lines:
        if "يارب سترك" in line and ":" in line:
            # Example: "0:04 - يارب سترك"
            return "نورة"  # hard-coded because from dialog she said "نورة"
    return "العميل"


# -------------------------------------------
# SECTOR PDF FETCHING
# -------------------------------------------

SECTOR_ENGINE_PATH = r"E:\Rag\Sector_Engine"

TOPIC_TO_SECTOR = {
    "متجر": "Marketing",
    "تسويق": "Marketing",
    "مبيعات": "Sales",
    "عميل": "Sales",
    "ميزانية": "Business",
    "فلوس": "Business",
    "سعر": "Business",
    "خدمة": "Marketing",
    "حملة": "Marketing",
    "مشاهير": "Marketing",
    "اعلان": "Marketing",
    "جودة": "Branding",
    "نتائج": "Marketing"
}

def fetch_similar_pdfs(meeting_text):
    detected_sectors = set()
    text = meeting_text.lower()

    for kw, sector in TOPIC_TO_SECTOR.items():
        if kw.lower() in text:
            detected_sectors.add(sector)

    matched = []
    for sector in detected_sectors:
        folder = os.path.join(SECTOR_ENGINE_PATH, sector)
        if os.path.exists(folder):
            for f in os.listdir(folder):
                if f.endswith(".pdf"):
                    matched.append(os.path.join(folder, f))

    ranked = rank_pdfs_based_on_relevance(matched, meeting_text)
    return ranked[:2]

def rank_pdfs_based_on_relevance(pdf_list, meeting_text):
    scored = []
    for pdf in pdf_list:
        score = fuzz.ratio(meeting_text.lower(), os.path.basename(pdf).lower())
        scored.append((pdf, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [p for p, s in scored]


# -------------------------------------------
# OBJECTION DETECTION
# -------------------------------------------

def detect_objection(meeting_text):
    t = meeting_text.lower()
    if "سعر" in t or "الفلوس" in t or "ميزانية" in t:
        return "money"
    if "نتيجة" in t or "نتائج" in t:
        return "expectations"
    if "جودة" in t:
        return "quality"
    if "وقت" in t:
        return "timeline"
    return "none"


# -------------------------------------------
# FOLLOW-UP 4-Stage Generation (Human-like)
# -------------------------------------------

def generate_followups(meeting_text):

    client_name = extract_client_name(meeting_text)
    objection = detect_objection(meeting_text)
    selected_pdfs = fetch_similar_pdfs(meeting_text)

    pdf1 = os.path.basename(selected_pdfs[0]) if len(selected_pdfs) > 0 else None
    pdf2 = os.path.basename(selected_pdfs[1]) if len(selected_pdfs) > 1 else None

    desc1 = pdf_description_engine(pdf1) if pdf1 else ""
    desc2 = pdf_description_engine(pdf2) if pdf2 else ""

    topic = "المتجر الإلكتروني" if "متجر" in meeting_text else "الخدمات التي ناقشناها"

    # FOLLOW-UP 1 
    f1 = f"""
مرحبًا {client_name}،

سعيد جدًا بالحديث اللي كان بينّا اليوم.  
ذكرتِ نقطة مهمة بخصوص **{topic}**، وحابب أرسلك ملف يساعدك تبدأي الصورة بشكل أوضح:

 **{pdf1}**  
 *{desc1}*

أي نقطة تودين نوضحها، أنا حاضر.
""".strip()

    #  FOLLOW-UP 2 
    f2 = f"""
مرحبًا {client_name}،

حابب أكمل معك على نفس النقطة عشان الصورة تكون مكتملة لك.  
أرفق لك ملف ثاني يعمّق نفس الفكرة اللي ركزتِ عليها:

 **{pdf2}**  
 *{desc2}*

إذا في جانب حابين نستكشفه أكثر، خبريني.
""".strip()

    # ------------------- FOLLOW-UP 3 -------------------
    if objection == "money":
        f3 = f"""
مرحبًا {client_name}،

فهمت تمامًا تركيزك على الميزانية، وهذا طبيعي جدًا في بداية أي مشروع.  
عشان كذا جهزت لك **3 خيارات مرنة** تخلّي القرار سهل عليك:

• باقة البداية — أقل التزام  
• باقة الوسط — توازن ممتاز  
• الباقة الكاملة — أعلى عائد وأسرع نتائج  

أقدر أرسللك مقارنة واضحة بينهم.
""".strip()

    elif objection == "expectations":
        f3 = f"""
مرحبًا {client_name}،

ذكرتِ أنك حابة تشوفي النتائج قبل أي خطوة—وهذا منطقي ومهم.  
جهزت لك **دليل قصص نجاح حقيقية** يوضح النتائج اللي حققناها مع مشاريع مشابهة.

جاهز أفصل لك كيف نكرر نفس النتائج في مشروعك.
""".strip()

    elif objection == "quality":
        f3 = f"""
مرحبًا {client_name}،

تمامًا فاهم حرصك على الجودة.  
أقدر أرسل لك **عينات من شغل الفريق** + **نتائج سابقة** تثبت مستوى التنفيذ.

أي نقطة تبينها بالتفصيل، جاهز لها.
""".strip()

    elif objection == "timeline":
        f3 = f"""
مرحبًا {client_name}،

ذكرتِ وقت التنفيذ، فجهزت لك **Timeline بسيط وواضح من 3 مراحل**  
عشان يكون عندك تصور كامل من البداية.

أرسله لك لو حابة نراجعه معًا.
""".strip()

    else:
        f3 = f"مرحبًا {client_name}، فقط أتابع معك لو حابة نكمل أي نقطة من النقاط."

    # ------------------- FOLLOW-UP 4 -------------------
    f4 = f"""
مرحبًا {client_name}،

بعد ما غطينا أغلب النقاط، جاهزين نرتّب الخطوة اللي تريحك.  
أقترح نحجز مكالمة قصيرة نحدد فيها الباقة المناسبة لك.

اختاري الوقت اللي يناسبك، وأنا جاهز.
""".strip()

    # ------------------- FOLLOW-UP TIMING -------------------

    schedule = {
        "followup_1_time": "بعد 2–3 ساعات من الاجتماع",
        "followup_2_time": "اليوم التالي 10 صباحًا",
        "followup_3_time": "بعد 48 ساعة حسب تفاعل العميل",
        "followup_4_time": "بعد 72–96 ساعة (مرحلة الإغلاق)"
    }

    return {
        "client_name": client_name,
        "objection": objection,
        "selected_pdf_1": pdf1,
        "selected_pdf_2": pdf2,
        "pdf1_description": desc1,
        "pdf2_description": desc2,
        "followup_1": f1,
        "followup_2": f2,
        "followup_3": f3,
        "followup_4": f4,
        "schedule": schedule
    }


# -------------------------------------------
# RUN
# -------------------------------------------

def analyze_meeting(meeting_text):
    result = generate_followups(meeting_text)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    text = open("meeting.txt", "r", encoding="utf-8").read()
    analyze_meeting(text)
