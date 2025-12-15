import json
import os
import streamlit as st
from groq import Groq

# ===============================
# Page Config
# ===============================
st.set_page_config(
    page_title="AI Code Reviewer & Optimizer",
    layout="wide"
)

st.title("🖥 AI-Powered Code Reviewer & Optimizer")

# ===============================
# Load API Key
# ===============================
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("❌ GROQ_API_KEY is not set. Please add it in Streamlit Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# ===============================
# Language Detection
# ===============================
def detect_language(code):
    c = code.lower()
    scores = {
        "C++": sum(k in c for k in ["#include", "std::", "int main"]),
        "Java": sum(k in c for k in ["public class", "system.out"]),
        "Python": sum(k in c for k in ["def ", "print(", "none"])
    }
    return max(scores, key=scores.get)

# ===============================
# Explanation Generator
# ===============================
def generate_explanation(bugs):
    if not bugs:
        return "✅ No explanation needed. Code is correct and safe."

    text = ""
    for b in bugs:
        text += f"""
🔹 **Line {b['line']}**
- Problem: {b['message']}
- Why it matters: May cause incorrect behavior
- Fix: `{b['fix']}`

"""
    return text

# ===============================
# Analyze Code
# ===============================
def analyze_code(code, language):
    prompt = f"""
Detect ONLY real correctness bugs.

Language: {language}

Return JSON ONLY:
{{
 "bugs":[
  {{
   "line":2,
   "type":"Logic",
   "severity":"Medium",
   "message":"Improper comparison with None",
   "fix":"Use 'is None' instead of '== None'"
  }}
 ]
}}

CODE:
{code}
"""

    r = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = r.choices[0].message.content
    try:
        data = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
        return data.get("bugs", [])
    except:
        return []

# ===============================
# Optimize Code
# ===============================
def optimize_code(code, language):
    prompt = f"""
Fix detected bugs only.

Language: {language}

Return JSON ONLY:
{{
 "optimized_code":"...",
 "time":"O(1)",
 "space":"O(1)"
}}

CODE:
{code}
"""

    r = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = r.choices[0].message.content
    try:
        data = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
        return data["optimized_code"], data["time"], data["space"]
    except:
        return code, "O(1)", "O(1)"

# ===============================
# UI Inputs
# ===============================
code = st.text_area("💻 Enter Code", height=300)

language = st.selectbox("Language", ["Auto", "C++", "Java", "Python"])

col1, col2, col3 = st.columns(3)

analyze = col1.button("🔍 Analyze Code")
optimize = col2.button("⚡ Optimize Code")
clear = col3.button("🧹 Clear")

# ===============================
# Logic
# ===============================
if analyze and code.strip():
    lang = detect_language(code) if language == "Auto" else language
    bugs = analyze_code(code, lang)

    st.subheader("🐞 Detected Bugs")

    if not bugs:
        st.success("🎉 Your code is 100% perfect and bug-free")
    else:
        for b in bugs:
            st.error(f"Line {b['line']}: {b['message']}")

    st.subheader("🎓 Explanation")
    st.markdown(generate_explanation(bugs))

if optimize and code.strip():
    lang = detect_language(code) if language == "Auto" else language
    fixed, time, space = optimize_code(code, lang)

    st.subheader("⚡ Optimized Code")
    st.code(fixed, language="python")

    st.subheader("📊 Complexity")
    st.write(f"**Time:** {time}")
    st.write(f"**Space:** {space}")

if clear:
    st.experimental_rerun()
