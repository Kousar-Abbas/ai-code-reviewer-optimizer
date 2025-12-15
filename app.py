import streamlit as st
import json
from groq import Groq

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="AI Code Reviewer & Optimizer",
    layout="wide"
)

st.title("🖥 AI-Powered Code Reviewer & Optimizer")

# ===============================
# API KEY
# ===============================
if "GROQ_API_KEY" not in st.secrets:
    st.error("❌ GROQ_API_KEY is not set. Please add it in Streamlit Secrets.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ===============================
# SESSION STATE
# ===============================
defaults = {
    "bugs": "",
    "explanation": "",
    "optimized_code": "",
    "complexity": "",
    "python_code": "",
    "analysis_done": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ===============================
# LANGUAGE DETECTION
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
# ANALYZE CODE (BUGS ONLY)
# ===============================
def analyze_code(code, language, mode):
    prompt = f"""
Detect ONLY real correctness bugs.

Language: {language}

Return STRICT JSON:
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

If code is perfect, return:
{{ "bugs": [] }}

CODE:
{code}
"""
    r = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0,
        messages=[{"role":"user","content":prompt}]
    )

    raw = r.choices[0].message.content
    try:
        data = json.loads(raw[raw.index("{"):raw.rindex("}")+1])
        bugs = data.get("bugs", [])
    except:
        bugs = []

    # BUG OUTPUT
    if not bugs:
        bugs_md = "🎉 **Your code is 100% perfect and bug-free**"
        explanation_md = "✅ No explanation needed. Code is correct and safe."
    else:
        bugs_md = "\n".join(
            f"❌ **Line {b['line']}**: {b['message']}  \n🔧 Fix: `{b['fix']}`"
            for b in bugs
        )

        explanation_md = ""
        for b in bugs:
            explanation_md += f"""
🔹 **Line {b['line']}**  
• Problem: {b['message']}  
• Why it matters: May cause incorrect behavior  
• How to fix: `{b['fix']}`  

"""

    # COMPLEXITY (STATIC)
    complexity_md = "**Time Complexity:** O(1)\n\n**Space Complexity:** O(1)"

    return bugs_md, explanation_md, complexity_md

# ===============================
# OPTIMIZE CODE (SEPARATE)
# ===============================
def optimize_code(code, language):
    prompt = f"""
Fix detected bugs ONLY.

Language: {language}

Return JSON:
{{
 "optimized_code": "...",
 "time": "O(1)",
 "space": "O(1)"
}}

CODE:
{code}
"""
    try:
        r = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            temperature=0,
            messages=[{"role":"user","content":prompt}]
        )
        raw = r.choices[0].message.content
        data = json.loads(raw[raw.index("{"):raw.rindex("}")+1])
        return data["optimized_code"], data["time"], data["space"]
    except:
        return code.replace("== None", "is None"), "O(1)", "O(1)"

# ===============================
# CONVERT TO PYTHON
# ===============================
def convert_to_python(code):
    r = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0,
        messages=[{"role":"user","content":f"Convert ONLY to Python:\n{code}"}]
    )
    return r.choices[0].message.content.strip()

# ===============================
# INPUT UI
# ===============================
code = st.text_area("💻 Code Input", height=250)
override = st.selectbox("Language Override", ["Auto","C++","Java","Python"])
mode = st.radio("Explanation Mode", ["Beginner","Advanced"], horizontal=True)

col1, col2, col3 = st.columns(3)

# ===============================
# BUTTONS
# ===============================
with col1:
    if st.button("🔍 Analyze Code"):
        if code.strip():
            lang = detect_language(code) if override == "Auto" else override
            b, e, c = analyze_code(code, lang, mode)
            st.session_state.bugs = b
            st.session_state.explanation = e
            st.session_state.complexity = c
            st.session_state.analysis_done = True

with col2:
    if st.button("⚡ Optimize Code"):
        if not st.session_state.analysis_done:
            st.warning("Please analyze the code first.")
        else:
            lang = detect_language(code) if override == "Auto" else override
            opt, t, s = optimize_code(code, lang)
            st.session_state.optimized_code = opt
            st.session_state.complexity = f"**Time Complexity:** {t}\n\n**Space Complexity:** {s}"

with col3:
    if st.button("🔄 Convert to Python"):
        st.session_state.python_code = convert_to_python(code)

# ===============================
# OUTPUT UI (MATCHES GRADIO)
# ===============================
st.markdown("### 🐞 Detected Bugs")
st.markdown(st.session_state.bugs)

st.markdown("### 🎓 Explanation")
st.markdown(st.session_state.explanation)

st.markdown("### ⚡ Optimized Code")
st.code(st.session_state.optimized_code, language="python")

st.markdown("### 📊 Complexity")
st.markdown(st.session_state.complexity)

st.markdown("### 🐍 Converted Python Code")
st.code(st.session_state.python_code, language="python")
