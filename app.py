import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os
import re
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

load_dotenv()

# ─── PAGE CONFIG (must be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="Feedback Insight Report",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── DARK MODE STATE ──────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False

# ─── THEME VARIABLES ──────────────────────────────────────────────────────────
if st.session_state["dark_mode"]:
    BG         = "#0f1117"
    SURFACE    = "#1e2130"
    TEXT       = "#e8eaf0"
    SUBTEXT    = "#9ca3af"
    BORDER     = "#2e3347"
    CARD_BG    = "#1e2130"
    TEXTAREA   = "#1e2130"
    CHART_BG   = "#1e2130"
    CHART_TEXT = "#e8eaf0"
    TOGGLE_LABEL = "☀️ Light Mode"
else:
    BG         = "#f8f9fb"
    SURFACE    = "#ffffff"
    TEXT       = "#1a1a2e"
    SUBTEXT    = "#6b7280"
    BORDER     = "#d1d5db"
    CARD_BG    = "#ffffff"
    TEXTAREA   = "#ffffff"
    CHART_BG   = "#f8f9fb"
    CHART_TEXT = "#1a1a2e"
    TOGGLE_LABEL = "🌙 Dark Mode"

# ─── INJECT THEME CSS ─────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stApp"],
    [data-testid="stMainBlockContainer"],
    section.main > div {{
        background-color: {BG} !important;
        color: {TEXT} !important;
    }}
    [data-testid="stHeader"] {{ background: transparent !important; }}

    /* All text elements */
    p, span, label, div, h1, h2, h3, h4, li {{
        color: {TEXT} !important;
    }}

    /* Hero banner */
    .hero {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        color: white !important;
        margin-bottom: 1.5rem;
        text-align: center;
    }}
    .hero h1, .hero p {{ color: white !important; }}
    .hero h1 {{ font-size: 2rem; margin: 0 0 0.4rem 0; }}
    .hero p  {{ font-size: 1.05rem; opacity: 0.9; margin: 0; }}

    /* Report cards */
    .report-card {{
        background: {CARD_BG} !important;
        border-radius: 12px;
        padding: 1.4rem 1.8rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        border-left: 5px solid #667eea;
        color: {TEXT} !important;
    }}
    .report-card p, .report-card li, .report-card h1,
    .report-card h2, .report-card h3, .report-card span {{
        color: {TEXT} !important;
    }}

    /* Buttons */
    .stButton > button {{
        border-radius: 8px !important;
        font-weight: 600 !important;
        background-color: {SURFACE} !important;
        color: {TEXT} !important;
        border: 1.5px solid {BORDER} !important;
    }}
    .stButton > button:hover {{
        border-color: #667eea !important;
        color: #667eea !important;
    }}

    /* Primary generate button */
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
        border: none !important;
    }}

    /* Text area */
    textarea {{
        border-radius: 10px !important;
        border: 1.5px solid {BORDER} !important;
        background: {TEXTAREA} !important;
        color: {TEXT} !important;
    }}

    /* Input label */
    .stTextArea label {{ color: {TEXT} !important; }}

    /* Download buttons */
    [data-testid="stDownloadButton"] > button {{
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }}

    /* Spinner + success text */
    .stSpinner > div {{ color: {TEXT} !important; }}
    .stAlert {{ background: {SURFACE} !important; color: {TEXT} !important; }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {SURFACE} !important;
    }}
</style>
""", unsafe_allow_html=True)

# ─── GROQ CLIENT ──────────────────────────────────────────────────────────────
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ─── SAMPLE FEEDBACK ──────────────────────────────────────────────────────────
SAMPLE_FEEDBACK = """The onboarding flow is really confusing, took me 20 minutes to figure out.
Love the new dashboard UI, it looks very clean and modern.
Checkout process keeps timing out on mobile — lost my order twice.
Support team responded in under 5 minutes, incredibly helpful!
The app crashes every time I try to upload a file larger than 10MB.
Notifications are spammy, I'm getting too many emails every day.
Search feature is super fast and accurate, saves me a lot of time.
Wish there was a dark mode option.
Pricing page is unclear — couldn't tell what's included in each plan.
The mobile app feels sluggish compared to the web version.
Really happy with the recent performance improvements, pages load much faster.
Password reset flow is broken, never received the reset email."""

# ─── DARK MODE TOGGLE ─────────────────────────────────────────────────────────
toggle_col, _ = st.columns([1, 5])
with toggle_col:
    if st.button(TOGGLE_LABEL, key="theme_toggle"):
        st.session_state["dark_mode"] = not st.session_state["dark_mode"]
        st.rerun()

# ─── HERO SECTION ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>📊 Customer Feedback → Insight Report</h1>
    <p>Paste raw feedback and get a structured AI-powered report with sentiment analysis in seconds.</p>
</div>
""", unsafe_allow_html=True)

# ─── SAMPLE DATA BUTTON ───────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🎲 Load Sample Feedback", use_container_width=True):
        st.session_state["feedback_box"] = SAMPLE_FEEDBACK
        st.rerun()

# ─── TEXT INPUT ───────────────────────────────────────────────────────────────
if "feedback_box" not in st.session_state:
    st.session_state["feedback_box"] = ""

feedback_input = st.text_area(
    "Paste customer feedback here (one entry per line or as a block):",
    height=250,
    placeholder="e.g.\n'The onboarding was confusing'\n'Love the UI but checkout is slow'\n'Support team was very helpful'...",
    key="feedback_box",
)

# ─── SENTIMENT CHART HELPERS ──────────────────────────────────────────────────
def parse_sentiment_scores(report_text: str) -> dict:
    """Extract % breakdown from the Overall Sentiment section, fallback to keyword count."""
    section_match = re.search(
        r"Overall Sentiment.*?\n(.+?)(?=\n##|\Z)", report_text, re.DOTALL | re.IGNORECASE
    )
    section = section_match.group(1).strip() if section_match else report_text

    percentages = re.findall(r"(\w+)[:\s]+(\d+)%", section, re.IGNORECASE)
    if percentages:
        scores = {}
        for label, pct in percentages:
            key = label.capitalize()
            if key in ("Positive", "Negative", "Neutral", "Mixed"):
                scores[key] = int(pct)
        if scores:
            return scores

    # Fallback: keyword count across full report
    text_lower = report_text.lower()
    pos = len(re.findall(r"\b(positive|great|love|excellent|happy|fast|helpful)\b", text_lower))
    neg = len(re.findall(r"\b(negative|bad|crash|slow|confus|broken|issue|problem)\b", text_lower))
    neu = max(1, (pos + neg) // 4)
    total = pos + neg + neu or 1
    return {
        "Positive": round(pos / total * 100),
        "Negative": round(neg / total * 100),
        "Neutral":  round(neu / total * 100),
    }


def render_sentiment_chart(scores: dict, dark: bool = False) -> bytes:
    """Return a PNG horizontal bar chart as bytes, themed for dark or light mode."""
    labels = list(scores.keys())
    values = list(scores.values())
    palette = {
        "Positive": "#22c55e",
        "Negative": "#ef4444",
        "Neutral":  "#f59e0b",
        "Mixed":    "#8b5cf6",
    }
    bar_colors = [palette.get(l, "#667eea") for l in labels]

    bg_color   = "#1e2130" if dark else "#f8f9fb"
    text_color = "#e8eaf0" if dark else "#1a1a2e"

    fig, ax = plt.subplots(figsize=(6, 3))
    bars = ax.barh(labels, values, color=bar_colors, height=0.5, edgecolor="none")
    ax.set_xlim(0, 115)
    ax.set_xlabel("Percentage (%)", fontsize=10, color=text_color)
    ax.set_title("Sentiment Breakdown", fontsize=12, fontweight="bold", pad=10, color=text_color)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(text_color)
    ax.tick_params(left=False, colors=text_color)
    ax.set_facecolor(bg_color)
    fig.patch.set_facecolor(bg_color)
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_width() + 1.5,
            bar.get_y() + bar.get_height() / 2,
            f"{val}%", va="center", fontsize=10, fontweight="bold", color=text_color,
        )
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ─── PDF GENERATION ───────────────────────────────────────────────────────────
def generate_pdf(report_text: str, chart_png_bytes: bytes) -> bytes:
    """Build a polished PDF and return as bytes."""
    from reportlab.platypus import Image as RLImage

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.85 * inch, rightMargin=0.85 * inch,
        topMargin=0.9 * inch,  bottomMargin=0.9 * inch,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Title"],
        fontSize=22, textColor=colors.HexColor("#667eea"), spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=11, textColor=colors.HexColor("#555555"), spaceAfter=14,
    )
    h2_style = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=13, textColor=colors.HexColor("#764ba2"),
        spaceBefore=14, spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, leading=15, textColor=colors.HexColor("#222222"),
    )

    story = []
    story.append(Paragraph("Customer Feedback Insight Report", title_style))
    story.append(Paragraph("AI-powered analysis — generated by Feedback Insight Tool", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb"), spaceAfter=12))

    # Embed chart — pass BytesIO directly so no temp file is needed on disk
    if chart_png_bytes:
        img = RLImage(io.BytesIO(chart_png_bytes), width=4.5 * inch, height=2.2 * inch)
        story.append(img)
        story.append(Spacer(1, 10))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb"), spaceAfter=10))

    # Render report lines
    for line in report_text.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 4))
            continue
        clean = re.sub(r"[*_`~]", "", line)
        if clean.startswith("## "):
            story.append(Paragraph(clean[3:], h2_style))
        elif clean.startswith("# "):
            story.append(Paragraph(clean[2:], h2_style))
        elif clean.startswith("- ") or clean.startswith("* "):
            story.append(Paragraph(f"&bull;&nbsp;&nbsp;{clean[2:]}", body_style))
        elif clean.startswith("---"):
            story.append(HRFlowable(width="100%", thickness=0.5,
                                    color=colors.HexColor("#e5e7eb"), spaceAfter=6))
        else:
            story.append(Paragraph(clean, body_style))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ─── GENERATE BUTTON ──────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
generate_clicked = st.button("⚡ Generate Insight Report", use_container_width=True, type="primary")

if generate_clicked:
    if not feedback_input.strip():
        st.warning("⚠️ Please paste some feedback first, or click **Load Sample Feedback** above.")
    else:
        with st.spinner("🤖 Analyzing feedback with AI — hang tight..."):
            prompt = f"""
You are a product analyst at a startup. Analyze the following raw customer feedback
and generate a clean, structured Weekly Insight Report.

Format your response EXACTLY like this:

## 📈 Overall Sentiment
One line: Positive / Negative / Mixed with a % breakdown e.g. Positive: 60%, Negative: 30%, Neutral: 10%

## 🔥 Top Themes (max 5)
Bullet points of the most repeated topics

## 😠 Key Complaints
Bullet points of the most critical pain points customers mentioned

## 🌟 What Customers Love
Bullet points of positive things customers mentioned

## ✅ Suggested Actions for the Team
3-5 concrete actionable suggestions based on the feedback

## 📝 Executive Summary
2-3 lines a founder can copy-paste into their team standup

---
RAW FEEDBACK:
{feedback_input}
"""
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1200,
            )
            report = response.choices[0].message.content

        # Parse sentiment & build chart
        scores     = parse_sentiment_scores(report)
        chart_bytes = render_sentiment_chart(scores, dark=st.session_state.get("dark_mode", False))

        # Build PDF
        pdf_bytes = generate_pdf(report, chart_bytes)

        # ── Display results ────────────────────────────────────────────────────
        st.success("✅ Report generated successfully!")
        st.markdown("---")

        # Sentiment chart
        st.subheader("📊 Sentiment Breakdown")
        st.image(chart_bytes, use_container_width=False, width=580)
        st.markdown("<br>", unsafe_allow_html=True)

        # Report in styled cards
        st.subheader("📄 Full Insight Report")
        for section in re.split(r"(?=## )", report):
            if section.strip():
                st.markdown(f'<div class="report-card">{section}</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Download buttons
        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                label="📥 Download as PDF",
                data=pdf_bytes,
                file_name="weekly_insight_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        with dl2:
            st.download_button(
                label="📄 Download as .txt",
                data=report,
                file_name="weekly_insight_report.txt",
                mime="text/plain",
                use_container_width=True,
            )

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; color:#9ca3af; font-size:0.85rem;'>"
    "Built with Streamlit &middot; Powered by Groq LLaMA 3.3 &middot; &copy; 2025 Feedback Insights"
    "</p>",
    unsafe_allow_html=True,
)