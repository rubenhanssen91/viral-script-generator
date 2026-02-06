import streamlit as st
import anthropic
import os
import json
import re
from datetime import datetime
from pathlib import Path

# Try to import YouTube transcript API
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    YOUTUBE_AVAILABLE = True
except:
    YOUTUBE_AVAILABLE = False

# ============================================================
# CONFIG
# ============================================================

def get_api_key():
    try:
        if hasattr(st, 'secrets') and 'ANTHROPIC_API_KEY' in st.secrets:
            return st.secrets['ANTHROPIC_API_KEY']
    except:
        pass
    if os.environ.get('ANTHROPIC_API_KEY'):
        return os.environ.get('ANTHROPIC_API_KEY')
    return st.session_state.get('api_key', '')

# Page config
st.set_page_config(
    page_title="🎬 Viral Script Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# BUILT-IN KNOWLEDGE BASE
# ============================================================

BUILT_IN_KNOWLEDGE = {
    "youtube_strategy": {
        "name": "📺 YouTube Strategy Fundamentals",
        "source": "Industry best practices",
        "active": True,
        "principles": [
            "Hook viewers in the first 5-10 seconds with a pattern interrupt or bold statement",
            "Create curiosity gaps that promise revelation later in the video",
            "Use pattern interrupts every 30-45 seconds to maintain attention",
            "Include specific examples rather than generic advice",
            "End with a clear call-to-action",
            "Structure content as a journey from problem to solution",
            "Address viewer objections directly within the content",
            "Use open loops to keep viewers watching",
            "Make the viewer feel something - emotion drives retention",
            "The title and thumbnail are 80% of the battle"
        ]
    },
    "ruben_voice": {
        "name": "🎤 Ruben's Writing Voice",
        "source": "The Aesthetic City channel analysis",
        "active": True,
        "principles": [
            "Write in long, flowing sentences that connect ideas naturally - not staccato AI writing",
            "Use verbal tics: 'quite frankly', 'by the way', 'and not only that', 'honestly', 'I think'",
            "Include parenthetical asides mid-sentence for authenticity",
            "Stack evidence casually: 'X found this, Y found the same, our study confirmed it'",
            "Give experts character: 'Krier is not your ordinary urban planner'",
            "Frame as a journey: mystery to discovery to revelation",
            "Use 'but' to connect contrasting ideas, not 'This isn't X... this is Y'",
            "Avoid em dashes (—), use commas or 'but' instead",
            "Never use: 'Let's dive in', 'Furthermore', 'In conclusion', 'without further ado'",
            "Avoid rhetorical one-liners and mic-drop sentences - too TED-talk",
            "Include disclaimers and rambling that feels human and unscripted"
        ]
    },
    "retention_tactics": {
        "name": "📈 Retention Tactics",
        "source": "YouTube analytics best practices",
        "active": True,
        "principles": [
            "Front-load value - don't save the best for last",
            "Use 'But first...' or 'Before we get there...' to create open loops",
            "Preview what's coming: 'In a moment, I'll show you...'",
            "Break complex topics into numbered lists viewers can follow",
            "Use pattern interrupts: change pace, show B-roll, ask questions",
            "Create mini-cliffhangers within the video",
            "Address the skeptic: 'Now you might be thinking...'",
            "Payoff open loops before the end to satisfy viewers"
        ]
    },
    "architecture_expertise": {
        "name": "🏛️ Architecture & Urbanism Context",
        "source": "The Aesthetic City domain knowledge",
        "active": True,
        "principles": [
            "Reference key figures: Léon Krier, Christopher Alexander, Nikos Salingaros, Andrés Duany",
            "Use specific project examples: Poundbury, Cayalá, Le Plessis-Robinson, Seaside, Jakriborg",
            "Contrast traditional vs modernist approaches with concrete examples",
            "Connect architectural choices to human wellbeing and psychology",
            "Reference neuroscience and biophilia research when relevant",
            "Acknowledge the complexity - avoid oversimplification",
            "Ground arguments in visual evidence the viewer can see"
        ]
    }
}

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

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_client():
    api_key = get_api_key()
    return anthropic.Anthropic(api_key=api_key) if api_key else None

def generate(prompt, max_tokens=4000):
    client = get_client()
    if not client:
        return None, "❌ No API key configured. Add it in Settings → Secrets."
    try:
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text, None
    except Exception as e:
        return None, f"❌ {e}"

def save_to_history(type, content, metadata={}):
    if "history" not in st.session_state:
        st.session_state.history = []
    st.session_state.history.append({
        "type": type,
        "content": content,
        "metadata": metadata,
        "timestamp": datetime.now().isoformat()
    })

def has_api_key():
    return bool(get_api_key())

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_youtube_transcript(video_id):
    """Get transcript from YouTube video"""
    if not YOUTUBE_AVAILABLE:
        return None, "YouTube transcript API not available"
    try:
        # New API (v1.0+): instantiate and call fetch()
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        
        # Extract text from FetchedTranscriptSnippet objects
        full_text = " ".join([snippet.text for snippet in transcript])
        return full_text, None
    except Exception as e:
        return None, f"Could not get transcript: {e}"

def init_knowledge_state():
    """Initialize knowledge sources in session state"""
    if "knowledge_sources" not in st.session_state:
        st.session_state.knowledge_sources = []
    if "active_builtin" not in st.session_state:
        st.session_state.active_builtin = list(BUILT_IN_KNOWLEDGE.keys())

def get_active_knowledge():
    """Get all active knowledge as text for prompts"""
    init_knowledge_state()
    knowledge_text = ""
    
    # Built-in knowledge
    for key in st.session_state.active_builtin:
        if key in BUILT_IN_KNOWLEDGE:
            kb = BUILT_IN_KNOWLEDGE[key]
            knowledge_text += f"\n\n### {kb['name']}\n"
            knowledge_text += "\n".join([f"- {p}" for p in kb['principles']])
    
    # Custom sources
    for source in st.session_state.knowledge_sources:
        if source.get('active', True):
            knowledge_text += f"\n\n### {source['name']} (from: {source['url']})\n"
            knowledge_text += source.get('extracted_advice', '')
    
    return knowledge_text

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("🎬 Viral Script Generator")
    st.caption("For The Aesthetic City")
    
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
        else:
            st.warning("⚠️ Enter API key")
    
    st.divider()
    
    mode = st.radio("Mode", [
        "🎣 Hook Generator",
        "📝 Full Script", 
        "🔬 Script Analyzer",
        "⚔️ A/B Test Hooks",
        "🎯 Titles & Thumbnails",
        "📚 Knowledge Sources",
        "📜 History"
    ])
    
    st.divider()
    
    # Show active knowledge sources count
    init_knowledge_state()
    builtin_count = len(st.session_state.active_builtin)
    custom_count = len([s for s in st.session_state.knowledge_sources if s.get('active', True)])
    st.caption(f"📚 {builtin_count} built-in + {custom_count} custom sources active")

# ============================================================
# MAIN CONTENT
# ============================================================

st.title("🎬 Viral Script Generator")

# ------------------------------------------------------------
# HOOK GENERATOR
# ------------------------------------------------------------
if mode == "🎣 Hook Generator":
    st.header("🎣 Hook Generator")
    
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
            if not has_api_key():
                st.error("❌ No API key")
            elif not topic or not selected:
                st.error("❌ Enter topic and select formulas")
            else:
                formulas = "\n".join([f"- {n}: {HOOK_FORMULAS[n]['template']}" for n in selected])
                knowledge = get_active_knowledge()
                
                prompt = f"""Generate YouTube hooks for "The Aesthetic City" channel.

TOPIC: {topic}

FORMULAS TO USE:
{formulas}

KNOWLEDGE BASE TO APPLY:
{knowledge}

Generate 2 hooks per formula with:
1. Hook text (1-2 sentences)
2. Score (1-10) + reasoning  
3. Thumbnail text (3-5 words)

Be specific to architecture/urbanism."""

                with st.spinner(f"Generating {len(selected)*2} hooks..."):
                    result, err = generate(prompt, 5000)
                    if result:
                        st.markdown("### Generated Hooks")
                        st.markdown(result)
                        save_to_history("hooks", result, {"topic": topic})
                    elif err:
                        st.error(err)
    with col2:
        st.metric("Selected", len(selected))

# ------------------------------------------------------------
# FULL SCRIPT
# ------------------------------------------------------------
elif mode == "📝 Full Script":
    st.header("📝 Full Script Generator")
    
    # Knowledge source selector
    with st.expander("🎯 Select Knowledge Sources", expanded=False):
        st.caption("Choose which sources to use for this script")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Built-in Sources:**")
            init_knowledge_state()
            for key, kb in BUILT_IN_KNOWLEDGE.items():
                is_active = key in st.session_state.active_builtin
                if st.checkbox(kb['name'], value=is_active, key=f"kb_{key}"):
                    if key not in st.session_state.active_builtin:
                        st.session_state.active_builtin.append(key)
                else:
                    if key in st.session_state.active_builtin:
                        st.session_state.active_builtin.remove(key)
        
        with col2:
            st.markdown("**Custom Sources:**")
            if st.session_state.knowledge_sources:
                for i, source in enumerate(st.session_state.knowledge_sources):
                    is_active = source.get('active', True)
                    if st.checkbox(f"📹 {source['name']}", value=is_active, key=f"cs_{i}"):
                        st.session_state.knowledge_sources[i]['active'] = True
                    else:
                        st.session_state.knowledge_sources[i]['active'] = False
            else:
                st.caption("No custom sources yet. Add YouTube videos in Knowledge Sources mode.")
        
        use_single_source = st.checkbox("🎯 Use ONLY one source (ignore others)", value=False)
        if use_single_source:
            all_sources = [(k, BUILT_IN_KNOWLEDGE[k]['name']) for k in st.session_state.active_builtin]
            all_sources += [(f"custom_{i}", s['name']) for i, s in enumerate(st.session_state.knowledge_sources) if s.get('active')]
            if all_sources:
                single_source = st.selectbox("Select single source:", [s[1] for s in all_sources])
    
    # Core inputs
    idea = st.text_area("💡 Video Idea *", height=100, placeholder="What's the main concept?")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        structure = st.selectbox("📐 Structure", list(STORY_STRUCTURES.keys()))
    with col2:
        length = st.selectbox("⏱️ Length", ["5 min", "8 min", "12 min", "15 min", "20 min"])
    with col3:
        style = st.selectbox("🎭 Style", ["Discovery/Personal", "Educational", "Opinion/Rant", "Case Study"])
    
    st.divider()
    st.subheader("🎛️ Optional Inputs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        use_must_include = st.checkbox("✅ Must-Include Points")
        must_include = st.text_area("Key points:", height=80, key="mi") if use_must_include else ""
        
        use_examples = st.checkbox("🏘️ Specific Examples")
        examples = st.text_area("Projects:", height=60, key="ex") if use_examples else ""
        
        use_experts = st.checkbox("🎓 Experts to Quote")
        experts = st.text_area("Names:", height=60, key="exp") if use_experts else ""
        
        use_avoid = st.checkbox("🚫 Avoid Topics")
        avoid = st.text_area("Don't include:", height=60, key="av") if use_avoid else ""
        
        use_personal = st.checkbox("👤 Personal Angle")
        personal = st.text_area("Story:", height=60, key="pa") if use_personal else ""
    
    with col2:
        use_emotion = st.checkbox("💫 Target Emotion")
        emotion = st.selectbox("Feeling:", ["Wonder", "Outrage", "Hope", "Curiosity", "Nostalgia"], key="em") if use_emotion else ""
        
        use_controversy = st.checkbox("🔥 Controversy Level")
        controversy = st.select_slider("Level:", ["Safe", "Edgy", "Provocative", "Controversial"], key="con") if use_controversy else ""
        
        use_audience = st.checkbox("👥 Audience Level")
        audience = st.selectbox("For:", ["Newcomers", "Enthusiasts", "Professionals"], key="aud") if use_audience else ""
        
        use_hook = st.checkbox("🎣 Hook Style")
        hook_style = st.selectbox("Formula:", ["Surprise me"] + list(HOOK_FORMULAS.keys()), key="hs") if use_hook else ""
        
        use_cta = st.checkbox("📢 Call-to-Action")
        cta = st.selectbox("Action:", ["Subscribe", "Check course", "Share video", "Think differently"], key="cta") if use_cta else ""
        
        use_stat = st.checkbox("📊 Key Statistic")
        stat = st.text_input("Number:", key="stat") if use_stat else ""
    
    st.divider()
    
    if st.button("🚀 Generate Full Script", type="primary", use_container_width=True):
        if not has_api_key():
            st.error("❌ No API key")
        elif not idea:
            st.error("❌ Enter a video idea")
        else:
            beats = ", ".join(STORY_STRUCTURES[structure])
            words = int(length.split()[0]) * 150
            knowledge = get_active_knowledge()
            
            prompt = f"""Write a YouTube script as Ruben Hanssen (The Aesthetic City, 209k subs).

IDEA: {idea}
STRUCTURE: {structure} ({beats})
LENGTH: {words} words ({length})
STYLE: {style}

KNOWLEDGE BASE TO APPLY:
{knowledge}
"""
            if must_include: prompt += f"\nMUST INCLUDE:\n{must_include}"
            if examples: prompt += f"\nFEATURE PROJECTS:\n{examples}"
            if experts: prompt += f"\nQUOTE EXPERTS:\n{experts}"
            if avoid: prompt += f"\nAVOID:\n{avoid}"
            if personal: prompt += f"\nPERSONAL ANGLE:\n{personal}"
            if emotion: prompt += f"\nTARGET EMOTION: {emotion}"
            if controversy: prompt += f"\nCONTROVERSY: {controversy}"
            if audience: prompt += f"\nAUDIENCE: {audience}"
            if hook_style and hook_style != "Surprise me": prompt += f"\nHOOK STYLE: {hook_style}"
            if cta: prompt += f"\nCTA: {cta}"
            if stat: prompt += f"\nKEY STAT: {stat}"
            
            prompt += """

REQUIREMENTS:
- Powerful hook in first 10 seconds
- [B-ROLL: description] markers
- Pattern interrupts every 30-45 sec
- Apply ALL principles from the knowledge base above
- Conversational, flowing sentences

Write the full script:"""

            with st.spinner("✍️ Writing..."):
                result, err = generate(prompt, 10000)
                if result:
                    st.markdown("### 📜 Your Script")
                    st.markdown(result)
                    save_to_history("script", result, {"idea": idea})
                    
                    word_count = len(result.split())
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Words", word_count)
                    col2.metric("Duration", f"{word_count // 150} min")
                    col3.metric("B-Roll Cues", result.count("[B-ROLL"))
                    
                    st.download_button("📥 Download", result, "script.md", use_container_width=True)
                elif err:
                    st.error(err)

# ------------------------------------------------------------
# SCRIPT ANALYZER
# ------------------------------------------------------------
elif mode == "🔬 Script Analyzer":
    st.header("🔬 Script Analyzer")
    
    script = st.text_area("Paste script to analyze", height=300)
    
    if st.button("🔍 Analyze", type="primary"):
        if not has_api_key():
            st.error("❌ No API key")
        elif not script:
            st.error("❌ Paste a script")
        else:
            knowledge = get_active_knowledge()
            prompt = f"""Analyze this script for The Aesthetic City channel.

SCRIPT:
{script[:6000]}

EVALUATE AGAINST THIS KNOWLEDGE BASE:
{knowledge}

Provide:

## 📊 VIRAL SCORE: X/100
| Metric | Score | Notes |
|--------|-------|-------|
| Hook | /10 | |
| Retention | /10 | |
| Curiosity Gaps | /10 | |
| Pattern Interrupts | /10 | |
| Emotion | /10 | |

## 🎤 VOICE MATCH: X/100
How well does it match Ruben's style from the knowledge base?

## 🚨 PROBLEMS
Specific issues with line references.

## ✅ STRENGTHS
What works well.

## ✏️ REWRITES
Improved versions of weak sections."""

            with st.spinner("Analyzing..."):
                result, err = generate(prompt, 4000)
                if result:
                    st.markdown(result)
                    save_to_history("analysis", result)
                elif err:
                    st.error(err)

# ------------------------------------------------------------
# A/B TEST
# ------------------------------------------------------------
elif mode == "⚔️ A/B Test Hooks":
    st.header("⚔️ A/B Test Hooks")
    
    col1, col2 = st.columns(2)
    with col1:
        hook_a = st.text_area("Hook A", height=100, key="ha")
    with col2:
        hook_b = st.text_area("Hook B", height=100, key="hb")
    
    topic = st.text_input("Topic context")
    
    if st.button("⚔️ Compare", type="primary"):
        if not has_api_key():
            st.error("❌ No API key")
        elif not hook_a or not hook_b:
            st.error("❌ Enter both hooks")
        else:
            prompt = f"""Compare these hooks for The Aesthetic City.

TOPIC: {topic}
HOOK A: {hook_a}
HOOK B: {hook_b}

Score each on Curiosity, Specificity, Emotion, Voice, CTR (each /10).
Declare WINNER with reasoning.
Suggest improved HOOK C combining the best of both."""

            with st.spinner("Comparing..."):
                result, err = generate(prompt, 2000)
                if result:
                    st.markdown(result)
                    save_to_history("ab_test", result)
                elif err:
                    st.error(err)

# ------------------------------------------------------------
# TITLES & THUMBNAILS
# ------------------------------------------------------------
elif mode == "🎯 Titles & Thumbnails":
    st.header("🎯 Titles & Thumbnails")
    
    tab1, tab2 = st.tabs(["Titles", "Thumbnails"])
    
    with tab1:
        topic = st.text_input("Topic", key="tt")
        if st.button("Generate 10 Titles", type="primary", key="gt"):
            if not has_api_key():
                st.error("❌ No API key")
            elif not topic:
                st.error("❌ Enter topic")
            else:
                prompt = f"""Generate 10 YouTube titles for The Aesthetic City.
TOPIC: {topic}

Format as table with Title, CTR Score (/10), Why It Works.
Mark TOP 3 recommendations."""

                with st.spinner("Generating..."):
                    result, err = generate(prompt, 2000)
                    if result:
                        st.markdown(result)
                        save_to_history("titles", result)
                    elif err:
                        st.error(err)
    
    with tab2:
        topic = st.text_input("Topic", key="tht")
        if st.button("Generate Thumbnail Ideas", type="primary", key="gth"):
            if not has_api_key():
                st.error("❌ No API key")
            elif not topic:
                st.error("❌ Enter topic")
            else:
                prompt = f"""Generate 5 thumbnail concepts for The Aesthetic City.
TOPIC: {topic}

For each: Visual, Text (3-5 words), Colors, Emotion, CTR Score.
Focus on before/after, beautiful vs ugly contrasts."""

                with st.spinner("Generating..."):
                    result, err = generate(prompt, 2000)
                    if result:
                        st.markdown(result)
                        save_to_history("thumbnails", result)
                    elif err:
                        st.error(err)

# ------------------------------------------------------------
# KNOWLEDGE SOURCES
# ------------------------------------------------------------
elif mode == "📚 Knowledge Sources":
    st.header("📚 Knowledge Sources")
    st.write("View, edit, and add knowledge that powers your script generation")
    
    tab1, tab2, tab3 = st.tabs(["📖 Built-in Knowledge", "➕ Add YouTube Video", "📹 Custom Sources"])
    
    with tab1:
        st.subheader("Built-in Knowledge Base")
        st.caption("These are the core principles used when generating scripts. Toggle them on/off.")
        
        init_knowledge_state()
        
        for key, kb in BUILT_IN_KNOWLEDGE.items():
            is_active = key in st.session_state.active_builtin
            
            with st.expander(f"{'✅' if is_active else '❌'} {kb['name']}", expanded=False):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.caption(f"Source: {kb['source']}")
                with col2:
                    if st.button("Toggle", key=f"toggle_{key}"):
                        if is_active:
                            st.session_state.active_builtin.remove(key)
                        else:
                            st.session_state.active_builtin.append(key)
                        st.rerun()
                
                st.markdown("**Principles:**")
                for principle in kb['principles']:
                    st.markdown(f"- {principle}")
    
    with tab2:
        st.subheader("➕ Add YouTube Video as Knowledge Source")
        st.write("Extract creator advice from YouTube videos and add to your knowledge base")
        
        source_name = st.text_input("Name this source", placeholder="e.g., 'MrBeast Retention Tips'")
        youtube_url = st.text_input("YouTube URL (optional)", placeholder="https://www.youtube.com/watch?v=...")
        
        st.divider()
        
        # Two methods: auto-transcribe or manual paste
        method = st.radio("Transcript method:", [
            "📝 Paste transcript manually (recommended for cloud)",
            "🤖 Auto-transcribe (works locally, blocked on cloud)"
        ], index=0)
        
        transcript = None
        
        if method == "📝 Paste transcript manually (recommended for cloud)":
            st.caption("Copy transcript from YouTube (click '...' → 'Show transcript' on any video)")
            manual_transcript = st.text_area("Paste transcript here:", height=200, 
                placeholder="Paste the full transcript text here...")
            if manual_transcript:
                transcript = manual_transcript
                st.success(f"✅ Transcript ready ({len(transcript.split())} words)")
        
        else:  # Auto-transcribe
            if not YOUTUBE_AVAILABLE:
                st.warning("⚠️ YouTube transcript API not available")
            elif not youtube_url:
                st.info("Enter a YouTube URL above")
            else:
                if st.button("🎬 Fetch Transcript", type="secondary"):
                    video_id = extract_video_id(youtube_url)
                    if not video_id:
                        st.error("❌ Invalid YouTube URL")
                    else:
                        with st.spinner("📝 Getting transcript..."):
                            transcript, err = get_youtube_transcript(video_id)
                        if err:
                            st.error(f"❌ {err}")
                            st.info("💡 Try pasting the transcript manually instead")
                        else:
                            st.session_state['temp_transcript'] = transcript
                            st.success(f"✅ Got transcript ({len(transcript.split())} words)")
                
                # Check if we have a fetched transcript
                if 'temp_transcript' in st.session_state:
                    transcript = st.session_state['temp_transcript']
        
        st.divider()
        
        # Extract advice button
        if st.button("🧠 Extract Advice from Transcript", type="primary", disabled=not transcript):
            if not source_name:
                st.error("❌ Name this source")
            elif not has_api_key():
                st.error("❌ No API key for extraction")
            elif not transcript:
                st.error("❌ No transcript available")
            else:
                with st.spinner("🧠 Extracting actionable advice..."):
                    extract_prompt = f"""Analyze this YouTube video transcript and extract ACTIONABLE ADVICE for creating YouTube videos.

TRANSCRIPT:
{transcript[:15000]}

Extract:
1. The main principles/tips shared
2. Specific techniques mentioned  
3. Do's and Don'ts
4. Any frameworks or formulas

Format as a bullet-point list of clear, actionable principles that can be applied when writing scripts.
Focus on VIDEO CREATION advice, not the content topic itself.
Be specific and practical."""

                    advice, err = generate(extract_prompt, 3000)
                
                if err:
                    st.error(err)
                else:
                    st.markdown("### 📋 Extracted Advice")
                    st.markdown(advice)
                    
                    # Save button
                    if st.button("✅ Add to Knowledge Base", type="primary", key="save_source"):
                        new_source = {
                            "name": source_name,
                            "url": youtube_url or "manual paste",
                            "transcript_words": len(transcript.split()),
                            "extracted_advice": advice,
                            "added": datetime.now().isoformat(),
                            "active": True
                        }
                        st.session_state.knowledge_sources.append(new_source)
                        if 'temp_transcript' in st.session_state:
                            del st.session_state['temp_transcript']
                        st.success(f"✅ Added '{source_name}' to your knowledge base!")
                        st.rerun()
    
    with tab3:
        st.subheader("📹 Your Custom Sources")
        
        init_knowledge_state()
        
        if not st.session_state.knowledge_sources:
            st.info("No custom sources yet. Add YouTube videos in the 'Add YouTube Video' tab.")
        else:
            for i, source in enumerate(st.session_state.knowledge_sources):
                is_active = source.get('active', True)
                
                with st.expander(f"{'✅' if is_active else '❌'} {source['name']}", expanded=False):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.caption(f"Source: {source['url']}")
                        st.caption(f"Added: {source['added'][:10]}")
                    with col2:
                        if st.button("Toggle", key=f"toggle_custom_{i}"):
                            st.session_state.knowledge_sources[i]['active'] = not is_active
                            st.rerun()
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{i}"):
                            st.session_state.knowledge_sources.pop(i)
                            st.rerun()
                    
                    st.markdown("**Extracted Advice:**")
                    st.markdown(source.get('extracted_advice', 'No advice extracted'))
        
        st.divider()
        
        # Export/Import
        st.subheader("💾 Export / Import")
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.knowledge_sources:
                export_data = json.dumps(st.session_state.knowledge_sources, indent=2)
                st.download_button("📥 Export Custom Sources", export_data, "knowledge_sources.json")
        with col2:
            uploaded = st.file_uploader("📤 Import Sources", type="json")
            if uploaded:
                try:
                    imported = json.load(uploaded)
                    st.session_state.knowledge_sources.extend(imported)
                    st.success(f"✅ Imported {len(imported)} sources")
                    st.rerun()
                except:
                    st.error("❌ Invalid JSON file")

# ------------------------------------------------------------
# HISTORY
# ------------------------------------------------------------
elif mode == "📜 History":
    st.header("📜 History")
    
    if "history" not in st.session_state or not st.session_state.history:
        st.info("No generations yet.")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"{item['type'].upper()} — {item['timestamp'][:16]}"):
                st.markdown(item['content'][:2000] + "..." if len(item['content']) > 2000 else item['content'])
                st.download_button("📥 Download", item['content'], f"{item['type']}.md", key=f"dl_{i}")
        
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()

# Footer
st.divider()
st.caption("v7 • Knowledge-powered script generation for The Aesthetic City")
