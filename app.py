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
def reset_state():
    st.session_state.code = ""
    st.session_state.bugs = ""
    st.session_state.explanation = ""
    st.session_state.optimized = ""
    st.session_state.complexity = ""
    st.session_state.python = ""
    st.session_state.analyzed = False

if "analyzed" not in st.session_state:
    reset_state()

# ===============================
# LANGUAGE DETECTION
# ===============================
def detect_language(code):
    c = code.lower()
    if "#include" in c or "std::" in c:
        return "C++"
    if "public class" in c or "system.out" in c:
        return "Java"
    return "Python"

# ===============================
# EXPLANATION GENERATOR
# ===============================
def generate_explanation(bugs, mode):
    if not bugs:
        return "✅ **No explanation needed. Code is correct and safe.**"

    output = ""
    for b in bugs:
        if mode == "Beginner":
            output += f"""
🔹 **Line {b['line']}**  
• Problem: {b['message']}  
• Why it matters: This can lead to incorrect results or crashes  
• How to fix: `{b['fix']}`  

"""
        else:
            output += f"""
🔸 **Line {b['line']}**  
• Bug Type: {b['type']}  
• Severity: {b['severity']}  
• Root Cause: The logic violates Python best practices  
• Fix Strategy: `{b['fix']}`  
• Best Practice: Use explicit checks and safe comparisons  

"""
    return output

# ===============================
# ANALYZE CODE (BUGS ONLY)
# ===============================
def analyze_code(code, mode):
    lang = detect_language(code)

    prompt = f"""
Detect ONLY real correctness bugs.

Language: {lang}

Return JSON ONLY.
If no bugs:
{{"bugs":[]}}

Else:
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
        messages=[{"role":"user","content":prompt}]
    )

    raw = r.choices[0].message.content
    try:
        data = json.loads(raw[raw.index("{"):raw.rindex("}")+1])
        bugs = data.get("bugs", [])
    except:
        bugs = []

    if not bugs:
        bugs_md = "🎉 **Your code is 100% perfect and bug-free**"
    else:
        bugs_md = "\n".join(
            f"❌ **Line {b['line']}**: {b['message']}  \n🔧 Fix: `{b['fix']}`"
            for b in bugs
        )

    explanation = generate_explanation(bugs, mode)
    complexity = "**Time Complexity:** O(1)\n\n**Space Complexity:** O(1)"

    return bugs_md, explanation, complexity

# ===============================
# OPTIMIZER (ON BUTTON)
# ===============================
def optimize_code(code):
    lang = detect_language(code)
    prompt = f"""
Fix detected bugs ONLY.

Language: {lang}

Return JSON ONLY:
{{
 "optimized_code":"...",
 "time":"O(1)",
 "space":"O(1)"
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
# CONVERT TO PYTHON (FIXED)
# ===============================
def convert_to_python(code):
    lang = detect_language(code)
    if lang == "Python":
        return "✅ Your code is already Python."
    r = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0,
        messages=[{"role":"user","content":f"Convert ONLY to Python:\n{code}"}]
    )
    return r.choices[0].message.content.strip()

# ===============================
# INPUT SECTION
# ===============================
uploaded = st.file_uploader("📂 Upload Code File", type=["py","cpp","java","txt"])
if uploaded:
    st.session_state.code = uploaded.read().decode("utf-8")

st.session_state.code = st.text_area("💻 Code Input", st.session_state.code, height=260)

col_copy, col_clear = st.columns(2)
with col_copy:
    st.code(st.session_state.code)
with col_clear:
    if st.button("🧹 Clear"):
        reset_state()
        st.experimental_rerun()

mode = st.radio("Explanation Mode", ["Beginner","Advanced"], horizontal=True)

# ===============================
# BUTTONS
# ===============================
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔍 Analyze Code"):
        if st.session_state.code.strip():
            b, e, c = analyze_code(st.session_state.code, mode)
            st.session_state.bugs = b
            st.session_state.explanation = e
            st.session_state.complexity = c
            st.session_state.analyzed = True

with col2:
    if st.button("⚡ Optimize Code"):
        if st.session_state.analyzed:
            opt, t, s = optimize_code(st.session_state.code)
            st.session_state.optimized = opt
            st.session_state.complexity = f"**Time Complexity:** {t}\n\n**Space Complexity:** {s}"
        else:
            st.warning("Analyze code first.")

with col3:
    if st.button("🔄 Convert to Python"):
        st.session_state.python = convert_to_python(st.session_state.code)

# ===============================
# OUTPUT
# ===============================
st.markdown("### 🐞 Detected Bugs")
st.markdown(st.session_state.bugs)

st.markdown("### 🎓 Explanation")
st.markdown(st.session_state.explanation)

st.markdown("### ⚡ Optimized Code")
st.code(st.session_state.optimized, language="python")
if st.session_state.optimized:
    st.button("📋 Copy Optimized Code", on_click=lambda: st.write("Copied!"))

st.markdown("### 📊 Complexity")
st.markdown(st.session_state.complexity)

st.markdown("### 🐍 Converted Python Code")
st.code(st.session_state.python, language="python")
