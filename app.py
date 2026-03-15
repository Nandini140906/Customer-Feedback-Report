import streamlit as st
from groq import Groq
from dotenv import load_dotenv
load_dotenv()
import os
import re
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from fpdf import FPDF

# ── LIGHT MODE (must be first Streamlit call) ──────────────────────────────
st.set_page_config(page_title="Feedback Insight Report", page_icon="📊", layout="centered")

st.markdown("""
<style>
    /* Force light mode regardless of system preference */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
        background-color: #f8f9fb !important;
        color: #1a1a2e !important;
    }
    [data-testid="stSidebar"] { background-color: #ffffff !important; }
    .stTextArea textarea {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
        border: 1.5px solid #d0d4de !important;
        border-radius: 10px !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }
    .stDownloadButton > button {
        background: #ffffff !important;
        color: #667eea !important;
        border: 2px solid #667eea !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
    .report-box {
        background: #ffffff;
        border-radius: 14px;
        padding: 2rem;
        border: 1px solid #e2e6ef;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        margin-top: 1rem;
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .hero-tagline {
        color: #6b7280;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .badge {
        display: inline-block;
        background: #eef0ff;
        color: #667eea;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-bottom: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# ── HEADER / TAGLINE ──────────────────────────────────────────────────────
st.markdown('<div class="hero-title">📊 Feedback Insight Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-tagline">Transform raw customer feedback into a structured weekly report — in seconds.</div>', unsafe_allow_html=True)
st.markdown('<span class="badge">⚡ Powered by LLaMA 3.3 · 70B via Groq</span>', unsafe_allow_html=True)

# ── GROQ CLIENT ───────────────────────────────────────────────────────────
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ── SAMPLE DATA ───────────────────────────────────────────────────────────
SAMPLE_FEEDBACK = """The onboarding flow is really confusing, I had no idea where to start.
Love the clean UI — best I've used in this category.
Checkout is painfully slow, took 3 minutes to complete an order.
Support team resolved my issue in under 10 minutes, very impressed.
Mobile app crashes on Android 13, happened twice today.
The dashboard is intuitive but needs dark mode desperately.
Pricing page is unclear — I didn't know which plan included API access.
Great product overall, just wish there were more integrations.
Search functionality is broken — returns irrelevant results.
Billing support was unhelpful and slow to respond."""

col_sample, _ = st.columns([1, 3])
with col_sample:
    if st.button("🎲 Load Sample Data"):
        st.session_state["feedback_text"] = SAMPLE_FEEDBACK

# ── TEXT INPUT ────────────────────────────────────────────────────────────
feedback_input = st.text_area(
    "Paste customer feedback here (one per line or as a block):",
    height=230,
    placeholder="e.g.\n'The onboarding was confusing'\n'Love the UI but checkout is slow'\n'Support team was very helpful'...",
    value=st.session_state.get("feedback_text", ""),
    key="feedback_area"
)

# ── HELPERS ───────────────────────────────────────────────────────────────

def extract_sentiment_scores(report_text: str) -> dict:
    """Parse rough sentiment % from the Overall Sentiment section."""
    scores = {"Positive": 0, "Neutral": 0, "Negative": 0}
    section = re.search(r"Overall Sentiment.*?(?=##|\Z)", report_text, re.S | re.I)
    if section:
        text = section.group()
        for key in scores:
            match = re.search(rf"{key}[:\s~]*(\d+)\s*%", text, re.I)
            if match:
                scores[key] = int(match.group(1))
    # Fallback: count positive/negative keywords
    if all(v == 0 for v in scores.values()):
        pos_kw = len(re.findall(r"\b(love|great|excellent|good|helpful|fast|easy|best)\b", report_text, re.I))
        neg_kw = len(re.findall(r"\b(slow|bad|broken|crash|confusing|poor|issue|problem)\b", report_text, re.I))
        total = pos_kw + neg_kw or 1
        scores["Positive"] = round(pos_kw / total * 100)
        scores["Negative"] = round(neg_kw / total * 100)
        scores["Neutral"] = max(0, 100 - scores["Positive"] - scores["Negative"])
    return scores


def render_sentiment_chart(scores: dict):
    """Render a clean horizontal bar chart for sentiment scores."""
    labels = list(scores.keys())
    values = list(scores.values())
    colors = ["#4ade80", "#94a3b8", "#f87171"]

    fig, ax = plt.subplots(figsize=(6, 2.2))
    fig.patch.set_facecolor("#f8f9fb")
    ax.set_facecolor("#f8f9fb")

    bars = ax.barh(labels, values, color=colors, height=0.5, edgecolor="none")
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{val}%", va="center", ha="left", fontsize=11, fontweight="bold", color="#1a1a2e")

    ax.set_xlim(0, 115)
    ax.set_xlabel("Score (%)", fontsize=9, color="#6b7280")
    ax.set_title("Sentiment Breakdown", fontsize=12, fontweight="bold", color="#1a1a2e", pad=10)
    ax.tick_params(colors="#1a1a2e", labelsize=10)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.xaxis.set_visible(False)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def generate_pdf(report_text: str) -> bytes:
    """Generate a clean PDF from the report text."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(40, 40, 80)
    pdf.cell(0, 12, "Weekly Customer Insight Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 140)
    pdf.cell(0, 8, "Generated by Feedback Insight Engine", ln=True, align="C")
    pdf.ln(4)
    pdf.set_draw_color(200, 200, 220)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # Body — strip markdown symbols, render section headers distinctly
    pdf.set_text_color(30, 30, 50)
    for line in report_text.split("\n"):
        clean = line.strip()
        if not clean:
            pdf.ln(3)
            continue
        if clean.startswith("## "):
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(80, 60, 160)
            pdf.cell(0, 9, clean[3:], ln=True)
            pdf.set_text_color(30, 30, 50)
        elif clean.startswith("- ") or clean.startswith("• "):
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(5)
            pdf.multi_cell(0, 6, "• " + clean[2:])
        elif clean == "---":
            pdf.set_draw_color(200, 200, 220)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, clean)

    return bytes(pdf.output())


# ── GENERATE BUTTON ───────────────────────────────────────────────────────
if st.button("⚡ Generate Insight Report", use_container_width=True):
    if not feedback_input.strip():
        st.warning("Please paste some feedback first.")
    else:
        with st.spinner("Analyzing feedback with AI..."):

            prompt = f"""
You are a product analyst at a startup. Analyze the following raw customer feedback 
and generate a clean, structured Weekly Insight Report.

Format your response EXACTLY like this:

## 📈 Overall Sentiment
[One line: Positive / Negative / Mixed with a % breakdown — e.g. Positive 60% / Neutral 20% / Negative 20%]

## 🔥 Top Themes (max 5)
[Bullet points of the most repeated topics]

## 😠 Key Complaints
[Bullet points of the most critical pain points customers mentioned]

## 🌟 What Customers Love
[Bullet points of positive things customers mentioned]

## ✅ Suggested Actions for the Team
[3-5 concrete actionable suggestions based on the feedback]

## 📝 Executive Summary
[2-3 lines a founder can copy-paste into their team standup]

---
RAW FEEDBACK:
{feedback_input}
"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            report = response.choices[0].message.content

        st.success("✅ Report generated!")
        st.markdown("---")

        # ── SENTIMENT CHART ──────────────────────────────────────────────
        st.subheader("📊 Sentiment Overview")
        scores = extract_sentiment_scores(report)
        render_sentiment_chart(scores)
        st.markdown("")

        # ── REPORT BODY ──────────────────────────────────────────────────
        st.markdown('<div class="report-box">', unsafe_allow_html=True)
        st.markdown(report)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        # ── DOWNLOAD BUTTONS ─────────────────────────────────────────────
        dl_col1, dl_col2 = st.columns(2)

        with dl_col1:
            pdf_bytes = generate_pdf(report)
            st.download_button(
                label="📄 Download as PDF",
                data=pdf_bytes,
                file_name="weekly_insight_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        with dl_col2:
            st.download_button(
                label="📥 Download as .txt",
                data=report,
                file_name="weekly_insight_report.txt",
                mime="text/plain",
                use_container_width=True
            )