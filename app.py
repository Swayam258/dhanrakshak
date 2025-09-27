import os
import base64
from io import BytesIO
import requests
from dotenv import load_dotenv
import streamlit as st

# ---- Gamification state (put near top of app.py) ----
from datetime import date

if "money_score" not in st.session_state:
    st.session_state.money_score = 0
if "risk_score" not in st.session_state:
    st.session_state.risk_score = 100  # start at 100, reduce for risky msgs


if "completed_lessons" not in st.session_state:
    st.session_state.completed_lessons = set()
if "last_visit" not in st.session_state:
    st.session_state.last_visit = date.today()
if "streak" not in st.session_state:
    st.session_state.streak = 1

# simple daily streak logic
today = date.today()
if st.session_state.last_visit != today:
    if (today - st.session_state.last_visit).days == 1:
        st.session_state.streak += 1
    else:
        st.session_state.streak = 1
    st.session_state.last_visit = today


# ---------- Config ----------
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

ASSETS_DIR = "assets"
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.png")      # favicon + header logo
HERO_PATH = os.path.join(ASSETS_DIR, "green_hero.png")    # opening splash image

st.set_page_config(
    page_title="DhanRakshak",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "💰",
    layout="centered",
)

# ---------- Helpers ----------
def brand_header(active: str = "Home"):
    # Logo + Brand line
    c1, c2 = st.columns([1, 6])
    with c1:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=64)
    with c2:
        st.markdown(
            """
            <div style="margin-top:4px">
                <div style="font-weight:800;font-size:28px;line-height:1">DhanRakshak</div>
                <div style="color:#607080; margin-top:-2px;">Your Digital Wealth Guardian</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Top ribbon
    st.markdown(
        """
        <div style="padding:10px 14px;border-radius:12px;
            background:linear-gradient(90deg,#0b3d2e,#156b4d);
            color:white;display:flex;align-items:center;gap:10px;margin:8px 0 16px 0;">
            <span style="font-weight:800;letter-spacing:.3px;">DhanRakshak</span>
            <span style="background:#e6f5ef;color:#156b4d;font-weight:800;
                        border-radius:999px;padding:2px 8px;margin-left:8px;">भारत • Learn • Protect</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_splash():
    # Full-screen style splash with hero image and CTA
    st.markdown(
        """
        <style>
            .splash-wrap{
                display:flex;flex-direction:column;align-items:center;justify-content:center;
                min-height:86vh; text-align:center;
            }
            .splash-title{font-size:42px;font-weight:800;margin-top:16px}
            .splash-sub{font-size:18px;color:#5b6573;margin-top:6px}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="splash-wrap">', unsafe_allow_html=True)
    if os.path.exists(HERO_PATH):
        st.image(HERO_PATH, use_container_width=True)
    st.markdown(
        """
        <div class="splash-title">DHANRAKSHAK</div>
        <div class="splash-sub">Your Digital Wealth Guardian • Learn • Ask • Protect • Voice</div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    if st.button("Enter App", type="primary", use_container_width=False):
        st.session_state["entered_app"] = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Splash gating ----------
if "entered_app" not in st.session_state:
    st.session_state["entered_app"] = False

if not st.session_state["entered_app"]:
    render_splash()
    st.stop()

# ---------- App (after splash) ----------
brand_header(active="Home")


# Main tabs (Home + features)
tab_home, tab_learn, tab_ask, tab_protect, tab_voice = st.tabs(
    ["Home", "Learn", "Ask", "Protect (Fraud Check)", "Voice"]
)
# ---- Lessons content (EN + HI) ----
LESSONS = {
    "Long-Term Investing": {
        "story": {
            "en": """**The Tale of Two Farmers 🌾**

Once in a small village, two friends, Sameer and Rohan, each got a small plot of land and some money.

Sameer was impatient and planted tomatoes to get quick results. He harvested fast, earned a little profit each time, and felt smart.

Rohan bought a small mango **sapling**. Friends laughed: “It’ll take years!” But he watered it daily and waited.

For a couple of years, Sameer kept growing tomatoes—small profits, hard work each season, and the soil slowly lost fertility. Rohan had only a slowly growing tree.

After five years the change came. Sameer still worked hard for small gains. Rohan’s mango tree became strong and finally bore fruit. He sold the mangoes for **much larger profits** than Sameer ever made, and with **less work** each year. The tree kept giving fruit for decades.

Rohan’s tree became **steady, growing wealth**. Sameer stayed stuck in short, tiring cycles.
""",
            "hi": """**दो किसानों की कहानी 🌾**

एक गाँव में दो दोस्त, समीर और रोहन, को छोटी ज़मीन और थोड़ा पैसा मिला…

समीर ने जल्दी मुनाफ़े के लिए टमाटर लगाए—हर सीजन थोड़ी कमाई, बहुत मेहनत, मिट्टी थकने लगी।  
रोहन ने **आम का पौधा** लगाया, रोज़ पानी दिया और इंतजार किया। लोग हँसते रहे—“सालों लगेंगे!”

पाँच साल बाद—रोहन का पेड़ मजबूत होकर फल देने लगा: **कम मेहनत, ज़्यादा कमाई**; हर साल फल बढ़ते गए।  
समीर उसी छोटी कमाई के चक्र में फँसा रहा। रोहन का पेड़ **स्थायी, बढ़ती दौलत** बन गया।
"""
        },
        "concepts": {
            "en": """
**Concept: Long-Term Investing** - **Compounding:** returns earn returns (₹10,000 @12% ≈ ₹96k in ~20 yrs)  
- **Ride volatility:** patience beats timing  
- **Use for big goals:** retirement, house, education
""",
            "hi": """
**सिद्धांत: दीर्घकालिक निवेश** - **चक्रवृद्धि:** रिटर्न पर भी रिटर्न  
- **उतार-चढ़ाव सहना:** समय के साथ धैर्य फायदेमंद  
- **बड़े लक्ष्य:** रिटायरमेंट, घर, पढ़ाई
"""
        },
        "quiz": [
            {"q_en": "Who represents long-term investing?", "q_hi": "दीर्घकालिक निवेशक कौन है?",
             "options_en": ["Sameer", "Rohan"], "options_hi": ["समीर", "रोहन"], "answer": 1},
            {"q_en": "Tree giving more fruit each year shows…", "q_hi": "हर साल ज्यादा फल किसका संकेत है?",
             "options_en": ["Volatility", "Compounding"], "options_hi": ["उतार-चढ़ाव", "चक्रवृद्धि"], "answer": 1},
        ]
    },

    "Short-Term Investing": {
        "story": {
            "en": """**The Tale of Two Shopkeepers 🛍️**

Anya sold trendy bands during a festival—**quick profit**, then sales vanished.  
Priya built a small store & brand—**slow start**, then stable income with loyal customers.

Short-term is like Anya’s stall (fast but temporary). Longer-term is like Priya’s shop (steady & scalable).
""",
            "hi": """**दो दुकानदारों की कहानी 🛍️**

आन्या ने त्योहार में ट्रेंडी बैंड बेचे—**तुरंत मुनाफ़ा**, फिर बिक्री बंद।  
प्रिया ने छोटी दुकान/ब्रांड बनाया—**धीमी शुरुआत**, पर स्थिर आय।

शॉर्ट-टर्म = तेज़ पर अस्थायी; लॉन्ग-टर्म = धीमा पर स्थिर।
"""
        },
        "concepts": {
            "en": """
**Concept: Short-Term Investing** - Event/news driven, liquid, near-term goals  
- Risks: time heavy, fees/taxes, higher loss risk
""",
            "hi": """
**सिद्धांत: अल्पकालिक निवेश** - घटनाओं/समाचार से लाभ, अधिक तरलता  
- जोखिम: समय/शुल्क/टैक्स, नुकसान की आशंका
"""
        },
        "quiz": [
            {"q_en": "Goal of short-term investing?", "q_hi": "अल्पकालिक निवेश का लक्ष्य?",
             "options_en": ["Decades of wealth", "Profit from brief moves"],
             "options_hi": ["दशकों में धन", "छोटे उतार-चढ़ाव से लाभ"], "answer": 1},
        ]
    },

    "Saving Goals": {
        "story": {
            "en": """**The Trip to Goa 🌴**

Akash saved “whenever possible” → inconsistent.  
Priya set a **SMART goal**: “₹30k in 6 months”, auto-saved ₹5k/month → achieved exactly.
""",
            "hi": """**गोवा यात्रा 🌴**

आकाश का “जब भी हो” बचत → अनियमित।  
प्रिया ने **SMART** लक्ष्य बनाया: “6 महीने में ₹30k”, हर माह ₹5k ऑटो-सेव → समय पर पूरा।
"""
        },
        "concepts": {
            "en": """
**Concept: SMART Goals** — Specific, Measurable, Achievable, Relevant, Time-bound
""",
            "hi": """
**SMART लक्ष्य** — विशेष, मापनीय, प्राप्त-योग्य, प्रासंगिक, समयबद्ध
"""
        },
        "quiz": [
            {"q_en": "“₹30k in 6 months” matches…", "q_hi": "“6 महीने में ₹30k” किससे मेल खाता है?",
             "options_en": ["Measurable & Time-bound", "Relevant & Achievable"],
             "options_hi": ["मापनीय व समयबद्ध", "प्रासंगिक व प्राप्त-योग्य"], "answer": 0},
        ]
    },

    "Debt": {
        "story": {
            "en": """**Two Brothers and a Loan 💰**

Karan used a ₹1L loan for a job-oriented course → promotion, higher income (good debt).  
Rohan used it for a luxury phone + trip → EMIs hurt cash flow (bad debt).
""",
            "hi": """**दो भाई और कर्ज़ 💰**

करण ने ₹1 लाख लोन स्किल/कोर्स में लगाया → प्रमोशन, आमदनी बढ़ी (अच्छा कर्ज़)।  
रोहन ने लक्ज़री फ़ोन + ट्रिप पर खर्च किया → EMI ने बजट दबाया (बुरा कर्ज़)।
"""
        },
        "concepts": {
            "en": """
**Debt** — Good debt builds income/assets; Bad debt funds consumption. **Interest** = cost of borrowing.
""",
            "hi": """
**कर्ज़** — अच्छा कर्ज़ आय/संपत्ति बढ़ाए; बुरा कर्ज़ खपत पर। **ब्याज़** = उधार की लागत।
"""
        },
        "quiz": [
            {"q_en": "Loan for a job-oriented course is…", "q_hi": "रोज़गार-उन्मुख कोर्स का लोन…",
             "options_en": ["Bad debt", "Good debt"], "options_hi": ["बुरा कर्ज़", "अच्छा कर्ज़"], "answer": 1},
        ]
    },

    "Goal Setting & Wise Spending": {
        "story": {
            "en": """**The Three Jars & The Bonus 🏺💸**

Leo split money randomly among jars → slow progress.  
Maya prioritized short/mid/long-term and auto-saved → hit all goals.  
Bonus: Arjun blew ₹10k impulsively; Sameer split into Need, Value, Goal → benefits lasted.
""",
            "hi": """**तीन गुल्लक और बोनस 🏺💸**

लियो ने पैसे बेतरतीब बाँटे → प्रगति धीमी।  
माया ने शॉर्ट/मिड/लॉन्ग-टर्म प्राथमिकता व ऑटो-सेव किया → सब लक्ष्य पूरे।  
बोनस: अर्जुन ने ₹10k बहा दिए; समीर ने आवश्यकता/मूल्य/लक्ष्य में बाँटा → लाभ टिके।
"""
        },
        "concepts": {
            "en": """
**Concepts** — Prioritize goals (short/mid/long), Needs vs Wants, 24-hour rule, budget & auto-save.
""",
            "hi": """
**सिद्धांत** — लक्ष्यों की प्राथमिकता, आवश्यकता बनाम चाहत, 24-घंटे नियम, बजट और ऑटो-सेव।
"""
        },
        "quiz": [
            {"q_en": "Maya’s key difference vs Leo?", "q_hi": "माया ने लियो से अलग क्या किया?",
             "options_en": ["Earned more money", "Used a prioritized plan"],
             "options_hi": ["ज़्यादा कमाई", "प्राथमिकता-आधारित योजना"], "answer": 1},
        ]
    },

    "Pradhan Mantri Jan Dhan Yojana (PMJDY)": {
        "story": {
            "en": """**The Tale of Meena’s First Bank Account 🏦**

Meena, a vegetable seller, kept savings in a box at home. Through **PMJDY**, she opened a **zero-balance bank account** with help. She received a **RuPay debit card**, **accident insurance**, and government subsidies started coming **directly** to her account.  
Now she saves safely in the bank and pays with her card—more security, less risk.
""",
            "hi": """**मीना का पहला बैंक खाता 🏦**

सब्ज़ी बेचने वाली मीना अपनी बचत घर के डिब्बे में रखती थी। **PMJDY** से उसने **शून्य-बैलेंस खाता** खुलवाया, **RuPay कार्ड** व **बीमा कवर** मिला और सरकारी सब्सिडी **सीधे खाते में** आने लगी।  
अब वह बैंक में सुरक्षित बचत करती है और कार्ड से भुगतान करती है—ज़्यादा सुरक्षा, कम जोखिम।
"""
        },
        "concepts": {
            "en": """
**Concept: PMJDY** - Zero-balance account for all households.  
- Free RuPay debit card & accident insurance.  
- Direct Benefit Transfer (DBT) of subsidies.  
- Improves financial inclusion & savings safety.
""",
            "hi": """
**सिद्धांत: PMJDY** - हर परिवार के लिए शून्य-बैलेंस खाता।  
- निःशुल्क RuPay कार्ड व दुर्घटना बीमा।  
- सब्सिडी सीधे खाते में (DBT)।  
- वित्तीय समावेशन और सुरक्षित बचत।
"""
        },
        "quiz": [
            {"q_en": "Main benefit of PMJDY?", "q_hi": "PMJDY का मुख्य लाभ?",
             "options_en": ["Free education", "Zero-balance bank account"],
             "options_hi": ["मुफ़्त शिक्षा", "शून्य-बैलेंस खाता"], "answer": 1},
            {"q_en": "Which card is given under PMJDY?", "q_hi": "PMJDY में कौन सा कार्ड मिलता है?",
             "options_en": ["Visa", "RuPay"], "options_hi": ["वीज़ा", "RuPay"], "answer": 1},
        ]
    },

    "Pradhan Mantri Gramin Digital Saksharta Abhiyan (PMGDISHA)": {
        "story": {
            "en": """**The Tale of Ram’s Digital Journey 💻**

Farmer Ram enrolled in **PMGDISHA** and learned to use a smartphone, bank app, pay electricity bills, and UPI. He can now **apply for schemes himself**, reducing dependency and saving time.
""",
            "hi": """**राम की डिजिटल यात्रा 💻**

किसान राम ने **PMGDISHA** में प्रशिक्षण लिया—स्मार्टफोन, बैंक ऐप, बिजली बिल भुगतान और UPI सीखा। अब वे खुद योजनाओं के लिए आवेदन कर पाते हैं—निर्भरता कम, समय की बचत।
"""
        },
        "concepts": {
            "en": """
**Concept: PMGDISHA** - Free digital literacy for rural citizens.  
- Learn smartphone, internet, online banking, UPI.  
- Aim: at least **one digitally literate person per household**.
""",
            "hi": """
**सिद्धांत: PMGDISHA** - ग्रामीण नागरिकों के लिए मुफ़्त डिजिटल साक्षरता।  
- स्मार्टफोन, इंटरनेट, ऑनलाइन बैंकिंग, UPI का प्रशिक्षण।  
- लक्ष्य: **हर परिवार से कम-से-कम एक** डिजिटल साक्षर।
"""
        },
        "quiz": [
            {"q_en": "Goal of PMGDISHA?", "q_hi": "PMGDISHA का लक्ष्य?",
             "options_en": ["Free food for farmers", "1 digitally literate per household"],
             "options_hi": ["किसानों को मुफ़्त भोजन", "हर घर से 1 डिजिटल साक्षर"], "answer": 1},
            {"q_en": "Which is taught under PMGDISHA?", "q_hi": "PMGDISHA में क्या सिखाया जाता है?",
             "options_en": ["UPI payments", "Car driving"],
             "options_hi": ["UPI भुगतान", "गाड़ी चलाना"], "answer": 0},
        ]
    },

    "PM Kisan Samman Nidhi (PM-KISAN)": {
        "story": {
            "en": """**The Tale of Sita’s Support 🌾**

Sita, a small farmer, registered for **PM-KISAN** and started receiving **₹6,000 per year** directly to her bank (3 installments). This steady support helped her buy seeds/fertilizers on time and reduced debt.
""",
            "hi": """**सीता की सहायता 🌾**

सीता, एक छोटी किसान, **PM-KISAN** में पंजीकृत हुईं और **₹6,000 वार्षिक** (3 किस्त) सीधे बैंक में मिलने लगे। इससे समय पर बीज-खाद खरीदे और कर्ज़ का बोझ घटा।
"""
        },
        "concepts": {
            "en": """
**Concept: PM-KISAN** - Income support for small/marginal farmers.  
- ₹6,000 per year in **3 installments** via DBT.  
- Helps buy inputs on time; reduces debt.
""",
            "hi": """
**सिद्धांत: PM-KISAN** - छोटे/सीमान्त किसानों के लिए आय सहायता।  
- **3 किस्तों** में ₹6,000/वर्ष (DBT)।  
- समय पर इनपुट खरीद; कर्ज़ में कमी।
"""
        },
        "quiz": [
            {"q_en": "Yearly amount under PM-KISAN?", "q_hi": "PM-KISAN में वार्षिक राशि?",
             "options_en": ["₹10,000", "₹6,000"], "options_hi": ["₹10,000", "₹6,000"], "answer": 1},
            {"q_en": "PM-KISAN is paid in how many installments?", "q_hi": "PM-KISAN कितनी किस्तों में दिया जाता है?",
             "options_en": ["3", "12"], "options_hi": ["3", "12"], "answer": 0},
        ]
    },
}

ALL_LESSONS = list(LESSONS.keys())
LANGS = {"English": "en", "हिन्दी": "hi"}

# --- Home ---
with tab_home:
    st.subheader("Our Mission")
    st.write(
        """
        **DhanRakshak** empowers users—especially in rural and semi-urban India—to make safe,
        smart money decisions. We provide:
        - **Simple financial advice** in regional languages  
        - **Fraud awareness & checks** for common scams (OTP/KYC/lottery, etc.)  
        - **Voice accessibility** so anyone can use it comfortably  
        """
    )
    st.subheader("What you can do here")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 📘 Learn\nShort, practical lessons.")
    with c2:
        st.markdown("### 🤖 Ask\nGet AI-powered guidance.")
    with c3:
        st.markdown("### 🛡️ Protect\nCheck risky messages.")
    st.info("Tip: Never share OTPs. For fraud, call helpline **1930**.")

# --- Learn (static sample content for now) ---
# --- Learn tab ---
# --- Learn tab ---
with tab_learn:
    # Progress header
    st.markdown(
        f"**Progress:** {len(st.session_state.completed_lessons)}/{len(ALL_LESSONS)} lessons • "
        f"🔥 Streak: {st.session_state.streak} days"
    )
    st.divider()

    # Language + lesson selection
    c1, c2 = st.columns([1, 2])
    with c1:
        lang_label = st.selectbox("Language / भाषा चुनें", list(LANGS.keys()), index=0)
        lang = LANGS[lang_label]
    with c2:
        lesson = st.selectbox("Choose a lesson", ALL_LESSONS, index=0)

    lesson_data = LESSONS[lesson]

    # Story (full text)
    st.markdown(f"## {lesson}")
    st.markdown(lesson_data["story"][lang])

    # Concepts
    with st.expander("Concepts / सिद्धांत", expanded=True):
        st.markdown(lesson_data["concepts"][lang])

    # --- Quiz (no instant reveal; require Submit) ---
    st.markdown("### Quiz")

    responses = {}
    for i, q in enumerate(lesson_data["quiz"], start=1):
        q_text = q["q_en"] if lang == "en" else q["q_hi"]
        opts   = q["options_en"] if lang == "en" else q["options_hi"]
        responses[i] = st.radio(f"{i}. {q_text}", opts, key=f"{lesson}_q{i}")

    if st.button("Submit Quiz"):
        correct = 0
        for i, q in enumerate(lesson_data["quiz"], start=1):
            opts = q["options_en"] if lang == "en" else q["options_hi"]
            if opts.index(responses[i]) == q["answer"]:
                st.success(f"Q{i}: ✅ Correct")
                correct += 1
                st.session_state.money_score += 10   # +10 coins per correct
            else:
                right = q["options_en"][q["answer"]] if lang == "en" \
                        else q["options_hi"][q["answer"]]
                st.error(f"Q{i}: ❌ Incorrect — Correct: {right}")
        st.markdown(f"**Your Score:** {correct} / {len(lesson_data['quiz'])}")

    # Completion + badge
    c3, c4 = st.columns([1, 2])
    with c3:
        if st.button("Mark Lesson Complete ✅"):
            st.session_state.completed_lessons.add(lesson)
            st.toast(f"Marked '{lesson}' complete!", icon="✅")
    with c4:
        if lesson in st.session_state.completed_lessons:
            st.success("Completed ✔")

    # Overall achievement
    if len(st.session_state.completed_lessons) == len(ALL_LESSONS):
        st.success("🏆 Achievement unlocked: Financial Guru")




# --- Ask (AI advice) ---
with tab_ask:
    st.subheader("Ask for Advice (AI)")
    q = st.text_input("Your question")
    lang = st.selectbox("Language", ["en", "hi", "pa", "gu", "bn", "ta"], index=1)
    if st.button("Get Advice"):
        if not q.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Thinking..."):
                try:
                    r = requests.post(
                        f"{BACKEND_URL}/api/v1/advice",
                        json={"prompt": q, "language": lang},
                        timeout=60,
                    )
                    r.raise_for_status()
                    st.success(r.json().get("advice", ""))
                except Exception as e:
                    st.error(f"Error: {e}")

# --- Protect (Fraud Check) ---
with tab_protect:
    st.subheader("Paste a message to check risk")
    msg = st.text_area(
        "Message",
        height=160,
        placeholder="Dear customer, urgent! Your KYC is suspended..."
    )
    if st.button("Check Risk"):
        if not msg.strip():
            st.warning("Please paste a message.")
        else:
            try:
                r = requests.post(
                    f"{BACKEND_URL}/api/v1/fraud-score",
                    json={"text": msg},
                    timeout=30,
                )
                r.raise_for_status()
                data = r.json()
                st.write(f"**Risk:** `{data.get('risk')}` • **Score:** `{data.get('score', 0):.2f}`")
                matches = data.get("matches") or []
                if matches:
                    st.caption("Matched rules: " + ", ".join(matches))
            except Exception as e:
                st.error(f"Error: {e}")

# Re-defining the tab_protect to add unique keys and score updates
with tab_protect:
    st.subheader("Paste a message to check risk")
    msg = st.text_area(
        "Message",
        height=160,
        placeholder="Dear customer, urgent! Your KYC is suspended...",
        key="fraud_message"   # unique key
    )

    if st.button("Check Risk", key="check_risk_btn"):
        if not msg.strip():
            st.warning("Please paste a message.")
        else:
            try:
                r = requests.post(
                    f"{BACKEND_URL}/api/v1/fraud-score",
                    json={"text": msg},
                    timeout=30,
                )
                r.raise_for_status()
                fraud_result = r.json()

                st.write(f"**Risk:** `{fraud_result.get('risk')}` • **Score:** `{fraud_result.get('score', 0):.2f}`")
                matches = fraud_result.get("matches") or []
                if matches:
                    st.caption("Matched rules: " + ", ".join(matches))

                # ---- Update Risk Score safely (bounded 0..100) ----
                if fraud_result.get("risk") == "High":
                    st.session_state.risk_score -= 10
                elif fraud_result.get("risk") == "Medium":
                    st.session_state.risk_score -= 5
                else:
                    st.session_state.risk_score += 2

                st.session_state.risk_score = max(0, min(100, st.session_state.risk_score))

            except Exception as e:
                st.error(f"Error: {e}")

# --- Voice (STT & TTS placeholders; your backend endpoints already wired) ---
with tab_voice:
    st.subheader("Speech Tools")
    st.caption("Upload audio for STT, or type text to synthesize speech (gTTS).")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Speech-to-Text (STT)**")
        audio_file = st.file_uploader("Upload audio (wav/mp3)", type=["wav", "mp3", "m4a"])
        if st.button("Transcribe"):
            if audio_file:
                files = {"file": (audio_file.name, audio_file.getvalue(), audio_file.type)}
                try:
                    r = requests.post(f"{BACKEND_URL}/api/v1/stt", files=files, timeout=120)
                    r.raise_for_status()
                    st.success(r.json().get("text", ""))
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please upload an audio file.")

    with c2:
        st.markdown("**Text-to-Speech (TTS)**")
        tts_text = st.text_area("Text to speak", "नमस्ते! यह धनरक्षक है।")
        tts_lang = st.selectbox("Language (gTTS)", ["hi", "en", "bn", "ta", "pa", "gu"], index=0)
        if st.button("Generate Audio"):
            try:
                r = requests.post(
                    f"{BACKEND_URL}/api/v1/tts",
                    json={"text": tts_text, "language": tts_lang},
                    timeout=60,
                )
            # Expecting base64 MP3 from backend
                r.raise_for_status()
                data = r.json()
                audio_b64 = data.get("audio_base64")
                if audio_b64:
                    audio_bytes = base64.b64decode(audio_b64)
                    st.audio(BytesIO(audio_bytes), format="audio/mp3")
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("<hr/>", unsafe_allow_html=True)

# --- Sidebar Dashboard ---
st.sidebar.header("🎮 Progress Dashboard")
st.sidebar.metric("💰 Money Score", st.session_state.money_score)
st.sidebar.metric("🛡️ Risk Score", f"{st.session_state.risk_score}/100")
st.sidebar.metric("🔥 Streak", f"{st.session_state.streak} days")
st.sidebar.metric("Lessons Completed", f"{len(st.session_state.completed_lessons)}/{len(ALL_LESSONS)}")
