import streamlit as st
import anthropic
import os
import json
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIG - Works locally and on Streamlit Cloud
# ============================================================

def get_api_key():
    """Get API key from secrets, env, or session"""
    # Try Streamlit secrets first (for cloud deployment)
    try:
        if hasattr(st, 'secrets') and 'ANTHROPIC_API_KEY' in st.secrets:
            return st.secrets['ANTHROPIC_API_KEY']
    except:
        pass
    # Then environment variable
    if os.environ.get('ANTHROPIC_API_KEY'):
        return os.environ.get('ANTHROPIC_API_KEY')
    # Then session state (user input)
    return st.session_state.get('api_key', '')

# Page config
st.set_page_config(
    page_title="🎬 Viral Script Generator v5",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #0f3460;
    margin: 5px 0;
}
.score-high { color: #00ff88; font-size: 24px; font-weight: bold; }
.score-medium { color: #ffdd00; font-size: 24px; font-weight: bold; }
.score-low { color: #ff4444; font-size: 24px; font-weight: bold; }
.hook-card {
    background: #1e1e2e;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
    border-left: 4px solid #6366f1;
}
.comparison-better { background-color: rgba(0, 255, 136, 0.1); }
.comparison-worse { background-color: rgba(255, 68, 68, 0.1); }
</style>
""", unsafe_allow_html=True)

# ============================================================
# KNOWLEDGE BASE (Same as v4, abbreviated for space)
# ============================================================

HOOK_FORMULAS = {
    "1. Shocking Question": {"template": "What if I told you [shocking fact]?", "example": "What if I told you the most beautiful cities were built without architects?", "power": 9},
    "2. Contradictory Statement": {"template": "Everyone thinks X, but actually Y", "example": "Everyone thinks modern buildings are progress. But they're actually making us miserable.", "power": 9},
    "3. Time-Bound Problem": {"template": "In the next [time], [dire prediction]", "example": "In the next 10 years, half of our historic city centers could be demolished.", "power": 8},
    "4. Personal Stakes": {"template": "I spent [time/money] to discover [secret]", "example": "I spent 3 years visiting 50 cities to discover why some places feel magical.", "power": 10},
    "5. Authority Challenge": {"template": "[Famous person/institution] is wrong about [topic]", "example": "Le Corbusier was wrong about everything. Here's the proof.", "power": 9},
    "6. Before/After Tease": {"template": "This went from [bad state] to [amazing state]", "example": "This parking lot became the most beloved neighborhood in Europe.", "power": 8},
    "7. Secret Reveal": {"template": "[Group] doesn't want you to know [secret]", "example": "Developers don't want you to know this about beautiful buildings.", "power": 7},
    "8. Countdown Pattern": {"template": "Only [number] things separate [current] from [desired]", "example": "Only 3 decisions separate an ugly suburb from a beautiful town.", "power": 7},
    "9. Negative Hook": {"template": "Stop doing [common mistake]. Do this instead.", "example": "Stop building parking lots. Build this instead.", "power": 8},
    "10. The Unthinkable": {"template": "[Person/Place] did the unthinkable and [result]", "example": "King Charles did the unthinkable and built his own town.", "power": 9},
    "11. Mystery Question": {"template": "Why does [surprising phenomenon]?", "example": "Why do millions of tourists visit this tiny village every year?", "power": 8},
    "12. Comparison Hook": {"template": "This [thing] vs this [thing]. One attracts millions.", "example": "These two neighborhoods look similar. One attracts millions.", "power": 8},
    "13. Bold Prediction": {"template": "This will be the [superlative] of [topic]", "example": "This will be the most important video about cities you'll ever watch.", "power": 7},
    "14. Hidden History": {"template": "The [adjective] story behind [famous thing]", "example": "The incredible story behind Europe's most beautiful new neighborhood.", "power": 9},
    "15. Problem Statement": {"template": "[Widespread problem]. But there's a solution.", "example": "Our cities are becoming unlivable. But there's a solution.", "power": 8},
    "16. The Reveal": {"template": "I finally discovered why [mystery]", "example": "I finally discovered why old buildings feel better than new ones.", "power": 8},
    "17. Contrarian Take": {"template": "[Popular opinion] is destroying [thing we value]", "example": "Our obsession with efficiency is destroying our cities.", "power": 9},
    "18. Promise Hook": {"template": "By the end of this video, you'll know [specific knowledge]", "example": "By the end of this video, you'll know exactly why beautiful places work.", "power": 7},
}

STORY_STRUCTURES = {
    "Discovery Arc": ["Hook", "Mystery", "Investigation", "Expert Insights", "Revelation", "Application", "Implications"],
    "Problem-Solution": ["Problem", "Consequences", "Promise", "Solution", "Evidence", "Action", "Vision"],
    "Myth-Busting": ["Myth", "Logic", "Evidence", "Truth", "Examples", "Implications", "Reframe"],
    "Case Study": ["Example", "Context", "Transformation", "Factors", "Principles", "Application", "Next Steps"],
}

RUBEN_STYLE = """
✅ DO: Personal stories, rhetorical questions, strong opinions, specific examples, curiosity builders
❌ DON'T: "Let's dive in", "Furthermore", "In conclusion", generic statements
"""

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_client():
    api_key = get_api_key()
    return anthropic.Anthropic(api_key=api_key) if api_key else None

def generate(prompt, max_tokens=4000):
    client = get_client()
    if not client:
        return None, "❌ No API key"
    try:
        msg = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=max_tokens, messages=[{"role": "user", "content": prompt}])
        return msg.content[0].text, None
    except Exception as e:
        return None, f"❌ {e}"

def save_to_history(type, content, metadata={}):
    """Save generation to session history"""
    if "history" not in st.session_state:
        st.session_state.history = []
    st.session_state.history.append({
        "type": type,
        "content": content,
        "metadata": metadata,
        "timestamp": datetime.now().isoformat()
    })
    return None

def load_transcript_samples():
    """Load transcript samples (if available locally)"""
    # These paths only work locally, gracefully return empty on cloud
    possible_paths = [
        Path("/Users/rubenhanssen_macmini/Documents/Aesthetic City Brain/Video Transcripts"),
        Path.home() / "Documents/Aesthetic City Brain/Video Transcripts",
    ]
    samples = []
    for path in possible_paths:
        if path.exists():
            for f in list(path.glob("*.txt"))[:5]:
                try:
                    samples.append({"name": f.stem, "content": f.read_text()[:3000]})
                except:
                    pass
            break
    return samples

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("🎬 Viral Script Generator")
    
    # Check if API key is in secrets (cloud) or needs user input
    has_secret_key = False
    try:
        has_secret_key = hasattr(st, 'secrets') and 'ANTHROPIC_API_KEY' in st.secrets
    except:
        pass
    
    if has_secret_key:
        st.success("✅ API Key configured")
    else:
        if "api_key" not in st.session_state:
            st.session_state.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        
        api_key = st.text_input("API Key", value=st.session_state.api_key, type="password")
        if api_key:
            st.session_state.api_key = api_key
            st.success("✅ Ready")
    
    st.divider()
    
    mode = st.radio("Mode", [
        "🎣 Hook Generator",
        "📝 Full Script", 
        "🔬 Script Analyzer",
        "⚔️ A/B Test Hooks",
        "🎯 Titles & Thumbnails",
        "📚 Knowledge Base",
        "📜 History"
    ])
    
    st.divider()
    st.caption(f"Hooks: 18 | Structures: 4")
    if "history" in st.session_state:
        st.caption(f"Generated: {len(st.session_state.history)} items")

# ============================================================
# MAIN
# ============================================================

st.title("🎬 Viral Script Generator v5")

# ------------------------------------------------------------
# HOOK GENERATOR
# ------------------------------------------------------------
if mode == "🎣 Hook Generator":
    st.header("🎣 Hook Generator")
    
    # Visual formula selector
    st.subheader("Select Formulas")
    cols = st.columns(6)
    selected = []
    for i, (name, data) in enumerate(HOOK_FORMULAS.items()):
        with cols[i % 6]:
            power_emoji = "🔥" if data["power"] >= 9 else "⚡" if data["power"] >= 7 else "💡"
            if st.checkbox(f"{power_emoji} {name.split('. ')[1][:12]}", value=data["power"] >= 8, key=f"h{i}"):
                selected.append(name)
    
    st.divider()
    
    topic = st.text_input("📝 Topic", placeholder="Why cities stopped being beautiful")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🚀 Generate Hooks", type="primary", use_container_width=True):
            if topic and selected and st.session_state.api_key:
                formulas = "\n".join([f"- {n}: {HOOK_FORMULAS[n]['template']}" for n in selected])
                prompt = f"""Generate YouTube hooks for "The Aesthetic City" channel.

TOPIC: {topic}

FORMULAS:
{formulas}

{RUBEN_STYLE}

For each formula, generate 2 hooks with:
1. Hook text (1-2 sentences)
2. Score (1-10) + reasoning
3. Thumbnail text (3-5 words)

Be specific to architecture/urbanism. Sound like Ruben."""

                with st.spinner(f"Generating {len(selected)*2} hooks..."):
                    result, err = generate(prompt, 5000)
                    if result:
                        st.markdown("### Generated Hooks")
                        st.markdown(result)
                        save_to_history("hooks", result, {"topic": topic})
                        st.success("💾 Saved")
                    elif err:
                        st.error(err)
    with col2:
        st.metric("Selected", len(selected))

# ------------------------------------------------------------
# FULL SCRIPT
# ------------------------------------------------------------
elif mode == "📝 Full Script":
    st.header("📝 Full Script Generator")
    
    idea = st.text_area("Video Idea", height=100)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        structure = st.selectbox("Structure", list(STORY_STRUCTURES.keys()))
    with col2:
        length = st.selectbox("Length", ["5 min", "8 min", "12 min", "15 min"])
    with col3:
        style = st.selectbox("Style", ["Discovery/Personal", "Educational", "Opinion/Rant"])
    
    if st.button("🚀 Generate Script", type="primary"):
        if idea and st.session_state.api_key:
            beats = ", ".join(STORY_STRUCTURES[structure])
            words = int(length.split()[0]) * 150
            
            prompt = f"""Write a YouTube script as Ruben Hanssen (The Aesthetic City, 209k subs).

IDEA: {idea}
STRUCTURE: {structure} ({beats})
LENGTH: {words} words
STYLE: {style}

{RUBEN_STYLE}

Include:
- Powerful hook (first 10 seconds)
- [B-ROLL: description] markers
- Pattern interrupts every 30-45 sec
- Specific examples (Poundbury, Cayalá, etc.)
- Strong opinions

Write the full script:"""

            with st.spinner("Writing script..."):
                result, err = generate(prompt, 8000)
                if result:
                    st.markdown("### Your Script")
                    st.markdown(result)
                    save_to_history("script", result, {"idea": idea})
                    st.download_button("📥 Download", result, "script.md")

# ------------------------------------------------------------
# SCRIPT ANALYZER
# ------------------------------------------------------------
elif mode == "🔬 Script Analyzer":
    st.header("🔬 Script Analyzer")
    st.write("Analyze any script for viral potential and voice match")
    
    script = st.text_area("Paste script to analyze", height=300)
    
    col1, col2 = st.columns(2)
    with col1:
        compare_to_ruben = st.checkbox("Compare to Ruben's style", value=True)
    with col2:
        detailed_feedback = st.checkbox("Detailed feedback", value=True)
    
    if st.button("🔍 Analyze", type="primary"):
        if script and st.session_state.api_key:
            # Load a sample transcript for comparison
            samples = load_transcript_samples()
            sample_text = samples[0]["content"] if samples else "No samples available"
            
            prompt = f"""Analyze this YouTube script for The Aesthetic City channel.

SCRIPT TO ANALYZE:
{script[:4000]}

{"RUBEN'S ACTUAL STYLE (from transcript):" + sample_text[:1500] if compare_to_ruben and samples else ""}

Provide:

## 📊 VIRAL SCORE: X/100
- Hook strength (1-10)
- Retention potential (1-10)
- Curiosity gaps (1-10)
- Pattern interrupts (1-10)
- Emotional engagement (1-10)

## 🎤 VOICE MATCH: X/100
- Conversational tone (1-10)
- Personal stories (1-10)
- Strong opinions (1-10)
- Specific examples (1-10)
- AI phrases detected (list any)

## 🔴 WEAK SPOTS
[List specific sentences/sections that need work]

## 🟢 STRONG SPOTS  
[List what works well]

## ✏️ REWRITE SUGGESTIONS
[Provide improved versions of weak sections]

{"## 📐 COMPARISON TO RUBEN'S ACTUAL SCRIPTS" + chr(10) + "How does this compare to his real style?" if compare_to_ruben else ""}

Be specific and actionable."""

            with st.spinner("Analyzing..."):
                result, err = generate(prompt, 4000)
                if result:
                    st.markdown(result)
                    save_to_history("analysis", result)

# ------------------------------------------------------------
# A/B TEST HOOKS
# ------------------------------------------------------------
elif mode == "⚔️ A/B Test Hooks":
    st.header("⚔️ A/B Test Hooks")
    st.write("Compare two hooks and get AI feedback on which will perform better")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Hook A")
        hook_a = st.text_area("Enter Hook A", height=100, key="hook_a")
    with col2:
        st.subheader("Hook B")
        hook_b = st.text_area("Enter Hook B", height=100, key="hook_b")
    
    topic = st.text_input("Video topic (for context)")
    
    if st.button("⚔️ Compare Hooks", type="primary"):
        if hook_a and hook_b and st.session_state.api_key:
            prompt = f"""Compare these two YouTube hooks for The Aesthetic City (architecture/urbanism channel).

TOPIC: {topic}

HOOK A:
{hook_a}

HOOK B:
{hook_b}

Analyze each hook on:
1. Curiosity creation (1-10)
2. Specificity (1-10)
3. Emotional pull (1-10)
4. Voice authenticity (1-10)
5. CTR prediction (1-10)

Then declare a WINNER with detailed reasoning.

Finally, suggest an improved Hook C that combines the best of both."""

            with st.spinner("Comparing..."):
                result, err = generate(prompt, 2000)
                if result:
                    st.markdown("### 🏆 Comparison Results")
                    st.markdown(result)
                    save_to_history("ab_test", result)

# ------------------------------------------------------------
# TITLES & THUMBNAILS
# ------------------------------------------------------------
elif mode == "🎯 Titles & Thumbnails":
    st.header("🎯 Titles & Thumbnails")
    
    tab1, tab2 = st.tabs(["📝 Titles", "🖼️ Thumbnails"])
    
    with tab1:
        topic = st.text_input("Video topic")
        if st.button("Generate 10 Titles", type="primary"):
            if topic and st.session_state.api_key:
                prompt = f"""Generate 10 YouTube titles for The Aesthetic City.

TOPIC: {topic}

Each title should:
- Be under 60 characters
- Create curiosity
- Be specific (name places when possible)

Format:
1. [Title] — CTR: X/10 — Why it works: [reason]"""

                with st.spinner("Generating..."):
                    result, _ = generate(prompt, 2000)
                    if result:
                        st.markdown(result)
                        save_to_history("titles", result)
    
    with tab2:
        topic = st.text_input("Video topic", key="thumb_topic")
        title = st.text_input("Video title (optional)")
        if st.button("Generate Thumbnail Ideas", type="primary"):
            if topic and st.session_state.api_key:
                prompt = f"""Generate 5 thumbnail concepts for The Aesthetic City.

TOPIC: {topic}
{"TITLE: " + title if title else ""}

For each:
1. Visual (what's in the image)
2. Text overlay (3-5 words)
3. Emotion it creates
4. Why it would get clicks

Focus on before/after, beautiful vs ugly contrasts."""

                with st.spinner("Generating..."):
                    result, _ = generate(prompt, 2000)
                    if result:
                        st.markdown(result)
                        save_to_history("thumbnails", result)

# ------------------------------------------------------------
# KNOWLEDGE BASE
# ------------------------------------------------------------
elif mode == "📚 Knowledge Base":
    st.header("📚 Knowledge Base")
    
    tab1, tab2, tab3 = st.tabs(["Hook Formulas", "Structures", "Ruben's Transcripts"])
    
    with tab1:
        for name, data in HOOK_FORMULAS.items():
            power = data["power"]
            emoji = "🔥" if power >= 9 else "⚡" if power >= 7 else "💡"
            st.markdown(f"**{emoji} {name}** (Power: {power}/10)")
            st.markdown(f"- Template: *{data['template']}*")
            st.markdown(f"- Example: {data['example']}")
            st.divider()
    
    with tab2:
        for name, beats in STORY_STRUCTURES.items():
            st.markdown(f"### {name}")
            for i, beat in enumerate(beats, 1):
                st.markdown(f"{i}. {beat}")
            st.divider()
    
    with tab3:
        samples = load_transcript_samples()
        if samples:
            for s in samples:
                with st.expander(f"📄 {s['name']}"):
                    st.text(s['content'][:2000])
        else:
            st.info("No transcripts found")

# ------------------------------------------------------------
# HISTORY
# ------------------------------------------------------------
elif mode == "📜 History":
    st.header("📜 Generation History")
    
    if "history" not in st.session_state or not st.session_state.history:
        st.info("No generations yet. Start creating!")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"{item['type'].upper()} — {item['timestamp'][:16]}"):
                st.markdown(item['content'][:1000] + "..." if len(item['content']) > 1000 else item['content'])
                if item['metadata']:
                    st.caption(f"Metadata: {item['metadata']}")
        
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()

# Footer
st.divider()
st.caption("v5 • Hook Generator • Script Writer • Analyzer • A/B Testing • Titles • Thumbnails • History")
