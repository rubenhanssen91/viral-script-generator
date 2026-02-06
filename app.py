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
.stExpander { border: 1px solid #333; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# KNOWLEDGE BASE
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
✅ DO: Personal stories, rhetorical questions, strong opinions, specific examples, curiosity builders, flowing conversational sentences
❌ DON'T: "Let's dive in", "Furthermore", "In conclusion", generic statements, staccato AI writing, em dashes
"""

EXAMPLE_PROJECTS = ["Poundbury", "Cayalá", "Le Plessis-Robinson", "Brandevoort", "Heulebrug", "Seaside", "Celebration", "Jakriborg"]
EXAMPLE_EXPERTS = ["Léon Krier", "Nikos Salingaros", "Christopher Alexander", "Andrés Duany", "James Howard Kunstler", "Chuck Marohn", "Ann Sussman"]

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
            st.warning("⚠️ Enter API key to generate")
    
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
                st.error("❌ No API key configured")
            elif not topic:
                st.error("❌ Enter a topic")
            elif not selected:
                st.error("❌ Select at least one formula")
            else:
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
                        st.success("💾 Saved to history")
                    elif err:
                        st.error(err)
    with col2:
        st.metric("Selected", len(selected))

# ------------------------------------------------------------
# FULL SCRIPT
# ------------------------------------------------------------
elif mode == "📝 Full Script":
    st.header("📝 Full Script Generator")
    
    # Core inputs
    idea = st.text_area("💡 Video Idea *", height=100, placeholder="What's the main concept of this video?")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        structure = st.selectbox("📐 Structure", list(STORY_STRUCTURES.keys()))
    with col2:
        length = st.selectbox("⏱️ Length", ["5 min", "8 min", "12 min", "15 min", "20 min"])
    with col3:
        style = st.selectbox("🎭 Style", ["Discovery/Personal", "Educational", "Opinion/Rant", "Case Study"])
    
    st.divider()
    st.subheader("🎛️ Optional Inputs")
    st.caption("Toggle the sections you want to use")
    
    # Optional inputs with toggles
    col1, col2 = st.columns(2)
    
    with col1:
        # Must-includes
        use_must_include = st.checkbox("✅ Must-Include Points", value=False)
        must_include = ""
        if use_must_include:
            must_include = st.text_area("Key points that MUST appear:", height=80, 
                placeholder="- The cost savings of traditional design\n- Reference to the 2019 study\n- Mention human-scale streets")
        
        # Specific examples
        use_examples = st.checkbox("🏘️ Specific Examples/Projects", value=False)
        examples = ""
        if use_examples:
            examples = st.text_area("Projects to feature:", height=80,
                placeholder="Poundbury, Cayalá, Le Plessis-Robinson...")
            st.caption(f"Suggestions: {', '.join(EXAMPLE_PROJECTS[:5])}")
        
        # Experts to quote
        use_experts = st.checkbox("🎓 Experts to Quote", value=False)
        experts = ""
        if use_experts:
            experts = st.text_area("Names to reference:", height=60,
                placeholder="Léon Krier, Nikos Salingaros...")
            st.caption(f"Suggestions: {', '.join(EXAMPLE_EXPERTS[:4])}")
        
        # Avoid
        use_avoid = st.checkbox("🚫 Avoid / Don't Include", value=False)
        avoid = ""
        if use_avoid:
            avoid = st.text_area("Topics or angles to skip:", height=60,
                placeholder="Don't mention politics, avoid the US examples...")
        
        # Personal angle
        use_personal = st.checkbox("👤 Personal Angle", value=False)
        personal = ""
        if use_personal:
            personal = st.text_area("Personal story or connection:", height=60,
                placeholder="I visited this place last year and...")
    
    with col2:
        # Target emotion
        use_emotion = st.checkbox("💫 Target Emotion", value=False)
        emotion = ""
        if use_emotion:
            emotion = st.selectbox("What should viewers feel?", 
                ["", "Wonder & Awe", "Outrage & Frustration", "Hope & Inspiration", "Curiosity & Intrigue", "Nostalgia", "Motivation to Act"])
        
        # Controversy level
        use_controversy = st.checkbox("🔥 Controversy Level", value=False)
        controversy = ""
        if use_controversy:
            controversy = st.select_slider("How provocative?", 
                options=["Safe", "Mildly Edgy", "Provocative", "Very Controversial"])
        
        # Audience level
        use_audience = st.checkbox("👥 Audience Level", value=False)
        audience = ""
        if use_audience:
            audience = st.selectbox("Who is this for?",
                ["", "Complete Newcomers", "Casual Enthusiasts", "Knowledgeable Fans", "Professionals"])
        
        # Hook style
        use_hook = st.checkbox("🎣 Opening Hook Style", value=False)
        hook_style = ""
        if use_hook:
            hook_options = ["Surprise me"] + list(HOOK_FORMULAS.keys())
            hook_style = st.selectbox("Pick a hook formula:", hook_options)
        
        # CTA
        use_cta = st.checkbox("📢 Call-to-Action", value=False)
        cta = ""
        if use_cta:
            cta = st.selectbox("What should viewers do?",
                ["", "Subscribe for more", "Check out the course", "Visit the website", "Share this video", "Just think differently", "Join the movement"])
        
        # Key statistic
        use_stat = st.checkbox("📊 Key Statistic", value=False)
        stat = ""
        if use_stat:
            stat = st.text_input("Compelling number to build around:",
                placeholder="85% of people prefer traditional architecture")
        
        # B-roll
        use_broll = st.checkbox("🎬 B-Roll Available", value=False)
        broll = ""
        if use_broll:
            broll = st.text_area("What footage do you have?", height=60,
                placeholder="Drone shots of Poundbury, street-level Amsterdam...")
        
        # Sponsor
        use_sponsor = st.checkbox("💰 Sponsor Integration", value=False)
        sponsor = ""
        if use_sponsor:
            sponsor = st.text_input("Sponsor product/message:",
                placeholder="Skillshare - learning platform")
    
    st.divider()
    
    # Generate button
    if st.button("🚀 Generate Full Script", type="primary", use_container_width=True):
        if not has_api_key():
            st.error("❌ No API key configured")
        elif not idea:
            st.error("❌ Enter a video idea")
        else:
            # Build prompt with all inputs
            beats = ", ".join(STORY_STRUCTURES[structure])
            words = int(length.split()[0]) * 150
            
            prompt = f"""Write a YouTube script as Ruben Hanssen (The Aesthetic City, 209k subscribers).

CORE REQUIREMENTS:
- Idea: {idea}
- Structure: {structure} ({beats})
- Target length: {words} words ({length})
- Style: {style}

{RUBEN_STYLE}
"""
            
            # Add optional inputs
            if must_include:
                prompt += f"\nMUST INCLUDE these points:\n{must_include}\n"
            if examples:
                prompt += f"\nFEATURE these specific projects/places:\n{examples}\n"
            if experts:
                prompt += f"\nQUOTE or reference these experts:\n{experts}\n"
            if avoid:
                prompt += f"\nAVOID these topics/angles:\n{avoid}\n"
            if personal:
                prompt += f"\nWEAVE IN this personal angle:\n{personal}\n"
            if emotion:
                prompt += f"\nTARGET EMOTION: Make viewers feel {emotion}\n"
            if controversy:
                prompt += f"\nCONTROVERSY LEVEL: {controversy}\n"
            if audience:
                prompt += f"\nAUDIENCE: Written for {audience}\n"
            if hook_style and hook_style != "Surprise me":
                prompt += f"\nOPENING HOOK: Use the '{hook_style}' formula\n"
            if cta:
                prompt += f"\nCALL-TO-ACTION: End with '{cta}'\n"
            if stat:
                prompt += f"\nKEY STATISTIC to build around: {stat}\n"
            if broll:
                prompt += f"\nAVAILABLE B-ROLL (reference in script): {broll}\n"
            if sponsor:
                prompt += f"\nSPONSOR INTEGRATION: Naturally weave in {sponsor}\n"
            
            prompt += """

SCRIPT REQUIREMENTS:
- Start with a powerful hook (first 10 seconds is crucial)
- Include [B-ROLL: description] markers throughout
- Add pattern interrupts every 30-45 seconds
- Use specific examples, not generic statements
- Write in Ruben's conversational voice with flowing sentences
- Include curiosity loops and open loops
- End with the specified CTA or a thought-provoking conclusion

Write the full script now:"""

            with st.spinner("✍️ Writing your script..."):
                result, err = generate(prompt, 10000)
                if result:
                    st.markdown("### 📜 Your Script")
                    st.markdown(result)
                    save_to_history("script", result, {"idea": idea})
                    
                    # Quality indicators
                    word_count = len(result.split())
                    st.divider()
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Word Count", word_count)
                    with col2:
                        st.metric("Est. Duration", f"{word_count // 150} min")
                    with col3:
                        st.metric("B-Roll Cues", result.count("[B-ROLL"))
                    
                    st.download_button("📥 Download Script", result, "script.md", use_container_width=True)
                elif err:
                    st.error(err)

# ------------------------------------------------------------
# SCRIPT ANALYZER
# ------------------------------------------------------------
elif mode == "🔬 Script Analyzer":
    st.header("🔬 Script Analyzer")
    st.write("Analyze any script for viral potential and voice match")
    
    script = st.text_area("Paste script to analyze", height=300)
    
    if st.button("🔍 Analyze Script", type="primary"):
        if not has_api_key():
            st.error("❌ No API key configured")
        elif not script:
            st.error("❌ Paste a script to analyze")
        else:
            prompt = f"""Analyze this YouTube script for The Aesthetic City channel (architecture/urbanism).

SCRIPT:
{script[:6000]}

Provide a detailed analysis:

## 📊 VIRAL POTENTIAL: X/100

| Metric | Score | Notes |
|--------|-------|-------|
| Hook Strength | /10 | |
| Retention Potential | /10 | |
| Curiosity Gaps | /10 | |
| Pattern Interrupts | /10 | |
| Emotional Engagement | /10 | |

## 🎤 VOICE AUTHENTICITY: X/100

| Metric | Score | Notes |
|--------|-------|-------|
| Conversational Tone | /10 | |
| Specific Examples | /10 | |
| Strong Opinions | /10 | |
| Personal Touch | /10 | |

## 🚨 AI PHRASES DETECTED
List any generic or AI-sounding phrases that should be rewritten.

## 🔴 WEAK SPOTS
Specific sentences or sections that need improvement, with line references.

## 🟢 STRONG SPOTS
What's working well - keep these elements.

## ✏️ REWRITE SUGGESTIONS
Provide improved versions of the weakest 3 sections.

## 💡 MISSING ELEMENTS
What could make this script stronger?

Be specific and actionable."""

            with st.spinner("🔍 Analyzing..."):
                result, err = generate(prompt, 4000)
                if result:
                    st.markdown(result)
                    save_to_history("analysis", result)
                elif err:
                    st.error(err)

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
        if not has_api_key():
            st.error("❌ No API key configured")
        elif not hook_a or not hook_b:
            st.error("❌ Enter both hooks")
        else:
            prompt = f"""Compare these two YouTube hooks for The Aesthetic City (architecture/urbanism channel).

TOPIC: {topic}

HOOK A:
{hook_a}

HOOK B:
{hook_b}

Analyze each hook:

## Hook A Analysis
| Metric | Score |
|--------|-------|
| Curiosity | /10 |
| Specificity | /10 |
| Emotional Pull | /10 |
| Voice Authenticity | /10 |
| CTR Prediction | /10 |
| **TOTAL** | /50 |

## Hook B Analysis
| Metric | Score |
|--------|-------|
| Curiosity | /10 |
| Specificity | /10 |
| Emotional Pull | /10 |
| Voice Authenticity | /10 |
| CTR Prediction | /10 |
| **TOTAL** | /50 |

## 🏆 WINNER: [A or B]
Detailed reasoning for why this hook will perform better.

## 💡 HOOK C (Improved Version)
Combine the best elements of both into an even better hook."""

            with st.spinner("⚔️ Comparing..."):
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
    
    tab1, tab2 = st.tabs(["📝 Titles", "🖼️ Thumbnails"])
    
    with tab1:
        topic = st.text_input("Video topic", key="title_topic")
        angle = st.text_input("Specific angle (optional)", placeholder="Focus on the controversy / the solution / the history...")
        
        if st.button("Generate 10 Titles", type="primary", key="gen_titles"):
            if not has_api_key():
                st.error("❌ No API key configured")
            elif not topic:
                st.error("❌ Enter a topic")
            else:
                prompt = f"""Generate 10 YouTube titles for The Aesthetic City channel.

TOPIC: {topic}
{"ANGLE: " + angle if angle else ""}

Requirements:
- Under 60 characters each
- Create curiosity gap
- Be specific (use names, places, numbers when possible)
- Match Ruben's style (not clickbaity, but compelling)

Format as a table:

| # | Title | CTR Score | Why It Works |
|---|-------|-----------|--------------|
| 1 | ... | X/10 | ... |

Then mark your TOP 3 recommendations with reasoning."""

                with st.spinner("✍️ Generating titles..."):
                    result, err = generate(prompt, 2000)
                    if result:
                        st.markdown(result)
                        save_to_history("titles", result, {"topic": topic})
                    elif err:
                        st.error(err)
    
    with tab2:
        topic = st.text_input("Video topic", key="thumb_topic")
        title = st.text_input("Video title (optional)", key="thumb_title")
        
        if st.button("Generate Thumbnail Ideas", type="primary", key="gen_thumbs"):
            if not has_api_key():
                st.error("❌ No API key configured")
            elif not topic:
                st.error("❌ Enter a topic")
            else:
                prompt = f"""Generate 5 thumbnail concepts for The Aesthetic City YouTube channel.

TOPIC: {topic}
{"TITLE: " + title if title else ""}

For each thumbnail, provide:

## Thumbnail 1: [Name]
- **Visual**: What's in the image (be specific)
- **Text Overlay**: 3-5 words max
- **Colors**: Color scheme
- **Emotion**: What feeling it creates
- **CTR Score**: X/10
- **Why It Works**: Brief explanation

Focus on:
- Before/after contrasts
- Beautiful vs ugly comparisons  
- Dramatic architectural imagery
- Human elements for relatability

Mark your #1 recommendation."""

                with st.spinner("🎨 Generating thumbnail ideas..."):
                    result, err = generate(prompt, 2000)
                    if result:
                        st.markdown(result)
                        save_to_history("thumbnails", result, {"topic": topic})
                    elif err:
                        st.error(err)

# ------------------------------------------------------------
# KNOWLEDGE BASE
# ------------------------------------------------------------
elif mode == "📚 Knowledge Base":
    st.header("📚 Knowledge Base")
    
    tab1, tab2 = st.tabs(["Hook Formulas", "Story Structures"])
    
    with tab1:
        for name, data in HOOK_FORMULAS.items():
            power = data["power"]
            emoji = "🔥" if power >= 9 else "⚡" if power >= 7 else "💡"
            with st.expander(f"{emoji} {name} (Power: {power}/10)"):
                st.markdown(f"**Template:** *{data['template']}*")
                st.markdown(f"**Example:** {data['example']}")
    
    with tab2:
        for name, beats in STORY_STRUCTURES.items():
            with st.expander(f"📐 {name}"):
                for i, beat in enumerate(beats, 1):
                    st.markdown(f"{i}. **{beat}**")

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
                st.markdown(item['content'][:2000] + "..." if len(item['content']) > 2000 else item['content'])
                if item['metadata']:
                    st.caption(f"Metadata: {item['metadata']}")
                st.download_button(
                    "📥 Download", 
                    item['content'], 
                    f"{item['type']}_{item['timestamp'][:10]}.md",
                    key=f"dl_{i}"
                )
        
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()

# Footer
st.divider()
st.caption("v6 • The Aesthetic City • Hook Generator • Script Writer • Analyzer • A/B Testing • Titles & Thumbnails")
