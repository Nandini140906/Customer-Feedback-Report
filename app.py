import streamlit as st
from groq import Groq

import os
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# --- PAGE SETUP ---
st.set_page_config(page_title="Feedback Insight Report", page_icon="📊")
st.title("📊 Customer Feedback → Weekly Insight Report")
st.markdown("Paste your raw customer feedback below and get a structured report instantly.")

# --- INPUT ---
feedback_input = st.text_area(
    "Paste customer feedback here (one per line or as a block):",
    height=250,
    placeholder="e.g.\n'The onboarding was confusing'\n'Love the UI but checkout is slow'\n'Support team was very helpful'..."
)

# --- GENERATE BUTTON ---
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
[One line: Positive / Negative / Mixed with a % breakdown if possible]

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

        st.success("Report generated!")
        st.markdown("---")
        st.markdown(report)

        st.download_button(
            label="📥 Download Report as .txt",
            data=report,
            file_name="weekly_insight_report.txt",
            mime="text/plain"
        )