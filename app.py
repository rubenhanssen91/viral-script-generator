import streamlit as st
import anthropic
import os
import json
import re
import base64
import requests
from datetime import datetime
from pathlib import Path

# Try to import YouTube transcript API
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    YOUTUBE_AVAILABLE = True
except:
    YOUTUBE_AVAILABLE = False

# ============================================================
# PERSISTENT STORAGE (Supabase)
# ============================================================

def get_supabase_config():
    """Get Supabase config from secrets"""
    try:
        if hasattr(st, 'secrets'):
            return {
                "url": st.secrets.get('SUPABASE_URL', ''),
                "key": st.secrets.get('SUPABASE_KEY', '')
            }
    except:
        pass
    return {
        "url": os.environ.get('SUPABASE_URL', ''),
        "key": os.environ.get('SUPABASE_KEY', '')
    }

def load_persistent_sources():
    """Load knowledge sources from Supabase"""
    config = get_supabase_config()
    if not config['url'] or not config['key']:
        return None
    
    try:
        url = f"{config['url']}/rest/v1/knowledge_sources?select=*&order=created_at.desc"
        headers = {
            "apikey": config['key'],
            "Authorization": f"Bearer {config['key']}"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            sources = response.json()
            return {"sources": sources, "active_builtin": list(BUILT_IN_KNOWLEDGE.keys())}
    except Exception as e:
        st.warning(f"Could not load sources: {e}")
    return None

def save_source_to_db(source):
    """Save a single knowledge source to Supabase"""
    config = get_supabase_config()
    if not config['url'] or not config['key']:
        return False
    
    try:
        url = f"{config['url']}/rest/v1/knowledge_sources"
        headers = {
            "apikey": config['key'],
            "Authorization": f"Bearer {config['key']}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        payload = {
            "name": source.get('name'),
            "url": source.get('url'),
            "extracted_advice": source.get('extracted_advice'),
            "active": source.get('active', True),
            "transcript_words": source.get('transcript_words')
        }
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"Could not save source: {e}")
    return False

def update_source_in_db(source_id, updates):
    """Update a source in Supabase"""
    config = get_supabase_config()
    if not config['url'] or not config['key']:
        return False
    
    try:
        url = f"{config['url']}/rest/v1/knowledge_sources?id=eq.{source_id}"
        headers = {
            "apikey": config['key'],
            "Authorization": f"Bearer {config['key']}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        response = requests.patch(url, headers=headers, json=updates)
        return response.status_code in [200, 204]
    except:
        return False

def delete_source_from_db(source_id):
    """Delete a source from Supabase"""
    config = get_supabase_config()
    if not config['url'] or not config['key']:
        return False
    
    try:
        url = f"{config['url']}/rest/v1/knowledge_sources?id=eq.{source_id}"
        headers = {
            "apikey": config['key'],
            "Authorization": f"Bearer {config['key']}"
        }
        response = requests.delete(url, headers=headers)
        return response.status_code in [200, 204]
    except:
        return False

def save_persistent_sources(data):
    """Compatibility wrapper - not used with Supabase"""
    return True

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
# THE VIRAL VIDEO PLAYBOOK (Full Knowledge Base)
# ============================================================

VIRAL_PLAYBOOK = """
# THE VIRAL VIDEO PLAYBOOK
A Master Guide to Scripting, Hooking, and Retaining Viewers
Synthesized from 9 creator masterclasses: MrBeast, Kallaway, Ed from Film Booth, Jon Dorman
Compiled for The Aesthetic City

## 1. FOUNDATIONAL MINDSET

### The Algorithm Is the Audience
Replace "algorithm" with "audience" — the sentence still works. If people are clicking and watching, the video gets promoted. Period.

### Quality Over Quantity
One killer video outperforms ten average ones. The video with 30M views didn't require 30x the effort — maybe 2-3x, with a much better idea.

### Content Psychology = Expectations vs Reality
When reality beats expectations, people stay. When expectations beat reality, they leave. Your title sets expectation, intro confirms it, body exceeds it.

## 2. IDEATION & PACKAGING

### The Interestingness Filter (Kallaway)
Score every fact 1-100 on "shock value" (distance between what they know and what you tell them). Only build videos around facts scoring 70+.

### The Friction Test (Film Booth)
If an idea practically writes itself, it will work. If you're forcing it, put it on the back burner.

### Dorman's Three Questions (Educational Content)
1. What do you want the viewer to DO?
2. What do they need to FEEL to take that action?
3. What do they need to KNOW?

### Title Principles
- Keep under 50 characters (truncation on mobile)
- Make it so interesting they'd wonder about it before bed
- More extreme = higher CTR, but you MUST deliver on the extremity

### Thumbnail Philosophy
- Viewer must instantly understand what you're conveying AND feel emotion
- Title creates interest, thumbnail creates intrigue (don't restate the title)
- Close your eyes, envision yourself about to click — what does it look like?

## 3. THE HOOK (First 5 Seconds)

### Kallaway's 3-Step Hook Formula
1. **Context Lean**: Clarify the topic + get viewer leaning in (common ground, benefit, metaphor, or mind-blowing fact)
2. **Scroll-Stop Interjection**: Single stun-gun line using "but," "however," "yet" — reverses the lean
3. **Contrarian Snapback**: Opposite direction of initial lean. Bigger shock = stronger hook.

**Example (8M views):**
- Context lean: "The tech in the Vegas Sphere is insane. Biggest screen ever, 20x bigger than IMAX."
- Scroll-stop: "But get this, the screen is actually the least impressive part."
- Snapback: "Because the most impressive part is the audio. This is going to blow your mind."

### The Nine Hook Formats
1. **Secret Reveal** - Teases unknown insight. Best for news, tips.
2. **Case Study** - Brand/person that achieved unexpected result.
3. **Comparison** - Optimal vs suboptimal creates instant contrast.
4. **Question** - Plants curiosity question directly.
5. **Education** - Step-by-step process preview.
6. **List** - Ordered set of items.
7. **Contrarian** - Bold against-the-grain take in first sentence.
8. **Personal Experience** - First-person story setup.
9. **Problem** - Agitates pain point to set up solution.

### Four Hook Commandments
1. **Alignment**: Visual hook, spoken hook, text-on-screen must match
2. **Speed to Value**: Zero delay, zero fluff
3. **Clarity**: Topic must be unmistakable
4. **Curiosity**: Must open a question in viewer's mind

### Visual Hooks
Eyes perceive faster than ears process. 3-5 bold words on screen + compelling visual = 10x more powerful than spoken-word alone.

### Staccato in the Hook
Short. Punchy. Compress sentences in the hook. Expand into longer sentences after the hook for rhythm variety.

## 4. THE INTRO (First 60 Seconds)

### Click Confirmation
First lines must CONFIRM and ideally BEAT expectations set by title. Fail to confirm = viewers bounce feeling misled.

### The Five-Part Intro Framework
1. **Context**: State what the video is about. Click-confirm immediately.
2. **Relevance/Stakes**: Why this maps to their problem. Amplify stakes.
3. **Contrast**: Their common belief vs your contrarian approach.
4. **Proof**: Credentials/results that validate your claim.
5. **Plan**: Preview structure. "These are the five steps..."

### The Trust Ladder (First 3 Minutes)
1. **Crowd Verification**: High sub/view count (social proof)
2. **Proof Signaling**: State your results early
3. **First Dopamine Hit (~60 sec)**: Race to deliver first non-obvious value
4. **Second Dopamine Hit**: Two golden nuggets = pattern. They're hooked.

### Speed to List Rule
Start your first point within 55 seconds. Delay beyond = significantly fewer stay.

### Time Allocation
Spend 50%+ of working time on idea, title, packaging, and first 2 minutes. Intro = "beachfront property." Outro = "rural farmland."

## 5. THE BODY (Sustaining Attention)

### Story Structures
- **Breakdown**: Complex concepts in building blocks (Secret Reveal, Question, Contrarian)
- **Newscaster**: Factual recounting (Secret Reveal, Question, Problem)
- **Case Study**: Frameworks that achieved results (Case Study, Question, Comparison)
- **Listicle**: Ordered list of atomic items (List, Problem)
- **Problem-Solver**: Agitate pain → solution (Problem, Question, Contrarian)
- **Tutorial**: Step-by-step to one outcome (Education, List)
- **Personal Story**: First-person lessons (Personal Experience, Problem)

### The 2-1-3-4 Ordering Method
Put your SECOND-BEST point first. BEST point second. Then 3rd, 4th, etc.

Why: Creates ascending value pattern. First amazing + second MORE amazing = subconscious pattern that value is increasing. They stay expecting trend to continue.

### The Value Loop (Each Point)
1. **Context**: What it is, explained simply
2. **Application**: How to do it with examples (walk-away value)
3. **Framing**: Why it matters, how it fits the puzzle

### Rehooking Between Points
Mini-hooks that bridge sections: "That point was critical, but if you don't couple it with this next one, the whole strategy falls apart."

### The Dance: But and Therefore
Between every beat, the word should be "but" or "therefore," never "and then."
- "And then" = boring pile of detail
- "But" = conflict loop
- "Therefore" = consequence

## 6. RETENTION (Keeping Viewers to the End)

### Pattern Interrupts (Country Roads vs Highway)
Highway = autopilot, zone out. Country roads = alert, scenery changes. Your video needs country roads.
- Multiple camera angles
- Switch talking head ↔ b-roll
- Physically move (pick up camera, vlog a few lines)
- Even 3 seconds of single camera without cut can lose people

### Relatability
Broad relatable examples = broader audience that stays. Cold sponge hitting ground resonates more than specialized tool.

### Subverting Expectations
When something bounces that should splat = funny (expectations violated). Set up expected outcome, deliver different one.

### Raising the Stakes
Make them realize WHY what you're about to say is critical.
- Not "this might hurt" → "this will melt your fingers to the bone"
- Not "this helps" → "without this, I'd have no following, no business, no lifestyle"

### The Payoff
Keep a payoff at the end. Even slow moments survive if viewers need to see who wins / what the conclusion is.

### Immersion Momentum
Longer they watch = more likely to keep watching. Front-load effort. Primary job = get them immersed, then hold them there.

## 7. THE OUTRO & ENGAGEMENT

### The Fortune Cookie
Leave lasting positive impression. Summarize points, remind of pain solved, confirm reality beat expectations. Converts passive → active engagers.

### The Forever Loop
Literal verbal transition to another video + end card. "If you liked this but you're still unclear on X, watch this next." Turns videos into episodes → binge chain.

### Emotional Transfer
Six buckets: Awe/inspiration, Amusement/humor, Excitement/joy, Anger/outrage, Surprise/shock/curiosity, Sadness/empathy.
Greater emotional transfer = more shares (people share to transfer emotion).

### Native Embed CTAs
Never break "hypnotic state" with disconnected ads. Use natural value ramps that complement the topic.

Kallaway's data: 7.4% unique viewer-to-subscriber rate (vs 0.5% average) while NEVER asking for subscriptions. If value is good enough, people know to subscribe.

## 8. PRODUCTION WORKFLOW

### Six-Step Script Process
1. Research: Mine for high-shock facts. Score 1-100. Keep top 5-10.
2. Target Emotion: Write it at top of page. Filter every decision through it.
3. Pick Hook Format: Study what's working, apply one of nine formats.
4. Pick Story Structure: Choose from seven, write outline, slot in facts.
5. Write Script: Layer facts, add transitions. Tell it like to a friend.
6. Emotional Gut-Check: Does this drive target emotion? If not, revise.

### Four-Question Script Checklist
1. Is this story interesting?
2. Is this as compressed as possible?
3. Does the hook actually hook me?
4. What emotion do I feel when I finish?

### Productivity Principles
- **Parkinson's Law**: Cut time in half, you'll still finish. Urgency forces focus.
- **80% Rule**: 80% quality is often enough. Final 20% rarely worth the time.
- **Environment Matters**: Natural light, pleasant workspace dramatically affect output.
- **10-Minute Walk**: When stuck, walk outside. Come back. Answers work themselves out.

## 9. APPLYING TO THE AESTHETIC CITY

### Shock Value Lives in the Data Gap
Audience suspects traditional architecture is better but hasn't seen compiled proof: 77% UK preference for traditional styles, Beaux-Arts collapse, economic premium on walkable neighborhoods.

### Contrarian Hook Fits Naturally
Your niche IS contrarian. Schools teach one thing. Public wants another. Perfect for 3-step hook formula.

### Visual Hooks Are Your Superpower
Stunning classical architecture, detailed drawings, before/after urban comparisons. 3-5 word text overlay on sweeping classical building shot stops scrollers faster than any talking head.

### Trust Ladder Favors Your Growth Phase
200K+ subs, millions of views = crowd verification cleared. Proof signals strong (consulting, summer school, Academy). Get through trust ladder faster → more time for body/retention.

### Bingeability Through the Canon
Classical architecture has natural knowledge hierarchy: proportion, orders, urban composition, street design, civic buildings. Forever-loop transitions build curriculum-like binge path.
"""

# ============================================================
# BUILT-IN KNOWLEDGE BASE
# ============================================================

BUILT_IN_KNOWLEDGE = {
    "viral_playbook": {
        "name": "📖 Viral Video Playbook",
        "source": "MrBeast, Kallaway, Film Booth, Jon Dorman — synthesized for TAC",
        "active": True,
        "full_text": VIRAL_PLAYBOOK,
        "principles": [
            "Algorithm = Audience. If people click and watch, it gets promoted.",
            "Quality over quantity. One killer video beats ten average ones.",
            "Content = expectations vs reality. Reality must beat expectations.",
            "Score facts 1-100 on shock value. Only use 70+ facts.",
            "Titles under 50 chars. Extreme = higher CTR (but must deliver).",
            "Kallaway's 3-step hook: Context Lean → Scroll-Stop → Contrarian Snapback",
            "Four hook commandments: Alignment, Speed to Value, Clarity, Curiosity",
            "Visual hooks are 10x more powerful than spoken-word alone",
            "First 60 seconds must confirm AND beat title expectations",
            "Trust ladder: Crowd verification → Proof → First dopamine hit → Second hit",
            "Speed to list: Start first point within 55 seconds",
            "2-1-3-4 ordering: Second-best first, best second, then descending",
            "Value loop for each point: Context → Application → Framing",
            "Rehook between points to prevent drop-off at transitions",
            "But/Therefore between beats, never 'and then'",
            "Pattern interrupts every 30-45 sec (country roads, not highway)",
            "Raise stakes: 'melt your fingers' not 'might hurt'",
            "Payoff at end keeps viewers through slow moments",
            "Fortune cookie outro: summarize, remind of pain solved",
            "Forever loop: verbal transition to next video + end card",
            "Spend 50%+ of time on idea, title, packaging, first 2 minutes"
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
    "1. Secret Reveal": {"template": "Teases an unknown insight the viewer doesn't have", "example": "What if I told you the most beautiful cities were built without architects?", "best_for": "news, tips, product releases", "power": 9},
    "2. Case Study": {"template": "Brand/person that achieved unexpected result", "example": "How one developer built the most beloved neighborhood in Europe.", "best_for": "educational content", "power": 9},
    "3. Comparison": {"template": "Optimal vs suboptimal creates instant contrast", "example": "These two neighborhoods look similar. One attracts millions.", "best_for": "before/after, traditional vs modern", "power": 9},
    "4. Question": {"template": "Plants curiosity question directly in viewer's mind", "example": "Why do millions of tourists visit this tiny village every year?", "best_for": "challenges, common questions", "power": 8},
    "5. Contrarian": {"template": "Bold against-the-grain take in the very first sentence", "example": "Everything architecture school taught you is wrong.", "best_for": "opinion pieces, myth-busting", "power": 10},
    "6. Problem": {"template": "Agitates a specific pain point to set up solution", "example": "Our cities are becoming unlivable. But there's a solution.", "best_for": "how-to, solutions content", "power": 8},
    "7. Personal Experience": {"template": "First-person story setup", "example": "I spent 3 years visiting 50 cities to discover why some places feel magical.", "best_for": "travel, discovery videos", "power": 9},
    "8. List": {"template": "Ordered set of items", "example": "7 design secrets that make old cities feel so alive.", "best_for": "listicles, rapid-fire content", "power": 7},
    "9. Education": {"template": "Step-by-step process preview", "example": "These are the 5 principles behind every beautiful street.", "best_for": "tutorials, frameworks", "power": 7},
}

STORY_STRUCTURES = {
    "Breakdown": {"beats": ["Hook", "Concept Overview", "Component 1", "Component 2", "Component 3", "Synthesis", "Application"], "best_for": "Explaining complex concepts", "hooks": ["Secret Reveal", "Question", "Contrarian"]},
    "Case Study": {"beats": ["Example Intro", "Context/History", "Transformation", "Key Factors", "Principles", "Application", "Forever Loop"], "best_for": "Project deep-dives", "hooks": ["Case Study", "Comparison", "Question"]},
    "Problem-Solver": {"beats": ["Pain Point", "Consequences", "Promise", "Solution Framework", "Evidence", "Action Steps", "Vision"], "best_for": "How-to content", "hooks": ["Problem", "Contrarian", "Question"]},
    "Myth-Busting": {"beats": ["Common Belief", "Why It Seems True", "The Counter-Evidence", "The Real Truth", "Examples", "Implications", "Reframe"], "best_for": "Challenging assumptions", "hooks": ["Contrarian", "Secret Reveal", "Question"]},
    "Personal Story": {"beats": ["Hook Moment", "Context", "Challenge", "Journey", "Discovery", "Lesson", "Application"], "best_for": "Travel/discovery content", "hooks": ["Personal Experience", "Question", "Problem"]},
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

def chat_generate(messages, system_prompt, max_tokens=4000):
    """Generate with full conversation history"""
    client = get_client()
    if not client:
        return None, "❌ No API key configured."
    try:
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages
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
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        full_text = " ".join([snippet.text for snippet in transcript])
        return full_text, None
    except Exception as e:
        return None, f"Could not get transcript: {e}"

def init_knowledge_state():
    """Initialize knowledge sources in session state, loading from Supabase"""
    if "knowledge_loaded" not in st.session_state:
        st.session_state.knowledge_loaded = False
    
    if not st.session_state.knowledge_loaded:
        saved = load_persistent_sources()
        if saved:
            st.session_state.knowledge_sources = saved.get("sources", [])
            st.session_state.active_builtin = saved.get("active_builtin", list(BUILT_IN_KNOWLEDGE.keys()))
            st.session_state.knowledge_loaded = True
        else:
            if "knowledge_sources" not in st.session_state:
                st.session_state.knowledge_sources = []
            if "active_builtin" not in st.session_state:
                st.session_state.active_builtin = list(BUILT_IN_KNOWLEDGE.keys())

def save_knowledge_state():
    """Compatibility function - individual saves happen directly"""
    return True

def reload_sources():
    """Force reload sources from database"""
    st.session_state.knowledge_loaded = False
    init_knowledge_state()

def get_active_knowledge(include_full_playbook=True):
    """Get all active knowledge as text for prompts"""
    init_knowledge_state()
    knowledge_text = ""
    
    # Built-in knowledge
    for key in st.session_state.active_builtin:
        if key in BUILT_IN_KNOWLEDGE:
            kb = BUILT_IN_KNOWLEDGE[key]
            # For viral_playbook, include full text if requested
            if key == "viral_playbook" and include_full_playbook and "full_text" in kb:
                knowledge_text += f"\n\n{kb['full_text']}"
            else:
                knowledge_text += f"\n\n### {kb['name']}\n"
                knowledge_text += "\n".join([f"- {p}" for p in kb['principles']])
    
    # Custom sources
    for source in st.session_state.knowledge_sources:
        if source.get('active', True):
            knowledge_text += f"\n\n### {source['name']} (from: {source['url']})\n"
            knowledge_text += source.get('extracted_advice', '')
    
    return knowledge_text

def get_workshop_system_prompt():
    """Get the system prompt for Script Workshop mode"""
    knowledge = get_active_knowledge(include_full_playbook=True)
    
    return f"""You are a viral video script development partner for The Aesthetic City, a YouTube channel about classical architecture and traditional urbanism with 209,000 subscribers.

Your role is to help Ruben develop video scripts through conversation — brainstorming, challenging ideas, suggesting structures, and refining hooks.

KNOWLEDGE BASE (apply these principles in every suggestion):
{knowledge}

YOUR APPROACH:
1. Ask clarifying questions to understand the core idea
2. Challenge weak points and suggest improvements
3. Reference specific principles from the Viral Video Playbook
4. Suggest hook formats, structures, and retention tactics
5. Help develop the script iteratively through dialogue
6. When suggesting hooks, use Kallaway's 3-step formula: Context Lean → Scroll-Stop → Contrarian Snapback
7. Apply the 2-1-3-4 ordering when structuring points

VOICE GUIDELINES:
- Write suggestions in Ruben's natural voice (flowing sentences, verbal tics, no AI clichés)
- Be direct and practical, not sycophantic
- Reference specific playbook principles when making suggestions
- Push back when ideas are weak — be a tough collaborator

When asked to generate a full script, follow the Six-Step Process from the playbook and output a complete, ready-to-record script with [B-ROLL: description] markers."""

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
        "🛠️ Script Workshop",
        "🎣 Hook Generator",
        "📝 Quick Script", 
        "🔬 Script Analyzer",
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
# SCRIPT WORKSHOP (New Chat-Based Mode)
# ------------------------------------------------------------
if mode == "🛠️ Script Workshop":
    st.header("🛠️ Script Workshop")
    st.caption("Develop your script through conversation. I'll use the Viral Video Playbook to guide our brainstorm.")
    
    # Initialize workshop state
    if "workshop_messages" not in st.session_state:
        st.session_state.workshop_messages = []
    if "workshop_script" not in st.session_state:
        st.session_state.workshop_script = ""
    if "workshop_title" not in st.session_state:
        st.session_state.workshop_title = ""
    
    # Layout: Chat on left, Script preview on right
    col_chat, col_script = st.columns([2, 1])
    
    with col_chat:
        # Starting point input
        if not st.session_state.workshop_messages:
            st.markdown("### Start Your Script")
            
            with st.form("workshop_start"):
                main_idea = st.text_area(
                    "What's your video about?", 
                    height=100,
                    placeholder="The main idea or topic you want to cover..."
                )
                
                key_points = st.text_area(
                    "Key points you want to make (optional)",
                    height=100,
                    placeholder="• Point 1\n• Point 2\n• Point 3"
                )
                
                target_length = st.selectbox("Target length", ["5-8 min", "8-12 min", "12-15 min", "15-20 min"])
                
                submitted = st.form_submit_button("🚀 Start Workshop", type="primary", use_container_width=True)
                
                if submitted and main_idea:
                    # Create initial user message
                    user_msg = f"I want to make a video about: {main_idea}"
                    if key_points:
                        user_msg += f"\n\nKey points I want to cover:\n{key_points}"
                    user_msg += f"\n\nTarget length: {target_length}"
                    
                    st.session_state.workshop_messages.append({
                        "role": "user",
                        "content": user_msg
                    })
                    st.session_state.workshop_title = main_idea[:50]
                    
                    # Get initial response
                    with st.spinner("🎬 Analyzing your idea..."):
                        system_prompt = get_workshop_system_prompt()
                        response, err = chat_generate(
                            st.session_state.workshop_messages,
                            system_prompt,
                            max_tokens=2000
                        )
                        
                        if response:
                            st.session_state.workshop_messages.append({
                                "role": "assistant",
                                "content": response
                            })
                    
                    st.rerun()
        
        else:
            # Show conversation
            st.markdown("### Conversation")
            
            # Messages container
            for i, msg in enumerate(st.session_state.workshop_messages):
                if msg["role"] == "user":
                    st.markdown(f"**You:** {msg['content']}")
                else:
                    st.markdown(f"**Workshop:** {msg['content']}")
                st.divider()
            
            # Chat input
            with st.form("workshop_chat", clear_on_submit=True):
                user_input = st.text_area(
                    "Your message",
                    height=80,
                    placeholder="Ask questions, give feedback, request changes...",
                    key="workshop_input"
                )
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    send = st.form_submit_button("💬 Send", type="primary", use_container_width=True)
                with col2:
                    generate_script = st.form_submit_button("📝 Generate Script", use_container_width=True)
                with col3:
                    reset = st.form_submit_button("🗑️ Reset", use_container_width=True)
                
                if send and user_input:
                    st.session_state.workshop_messages.append({
                        "role": "user",
                        "content": user_input
                    })
                    
                    with st.spinner("Thinking..."):
                        system_prompt = get_workshop_system_prompt()
                        response, err = chat_generate(
                            st.session_state.workshop_messages,
                            system_prompt,
                            max_tokens=2000
                        )
                        
                        if response:
                            st.session_state.workshop_messages.append({
                                "role": "assistant",
                                "content": response
                            })
                        elif err:
                            st.error(err)
                    
                    st.rerun()
                
                if generate_script:
                    # Add script generation request
                    st.session_state.workshop_messages.append({
                        "role": "user",
                        "content": "Based on our discussion, please generate the full script now. Include [B-ROLL: description] markers and follow the playbook principles we discussed. Make it ready to record."
                    })
                    
                    with st.spinner("✍️ Writing full script..."):
                        system_prompt = get_workshop_system_prompt()
                        response, err = chat_generate(
                            st.session_state.workshop_messages,
                            system_prompt,
                            max_tokens=8000
                        )
                        
                        if response:
                            st.session_state.workshop_messages.append({
                                "role": "assistant",
                                "content": response
                            })
                            st.session_state.workshop_script = response
                            save_to_history("workshop_script", response, {"title": st.session_state.workshop_title})
                        elif err:
                            st.error(err)
                    
                    st.rerun()
                
                if reset:
                    st.session_state.workshop_messages = []
                    st.session_state.workshop_script = ""
                    st.session_state.workshop_title = ""
                    st.rerun()
            
            # Quick action buttons
            st.markdown("### Quick Actions")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🎣 Suggest 3 hooks", use_container_width=True):
                    st.session_state.workshop_messages.append({
                        "role": "user",
                        "content": "Give me 3 different hook options using different formats from the playbook. For each, use Kallaway's 3-step formula (context lean, scroll-stop, contrarian snapback)."
                    })
                    with st.spinner("Generating hooks..."):
                        response, _ = chat_generate(st.session_state.workshop_messages, get_workshop_system_prompt(), 1500)
                        if response:
                            st.session_state.workshop_messages.append({"role": "assistant", "content": response})
                    st.rerun()
            with col2:
                if st.button("📐 Suggest structure", use_container_width=True):
                    st.session_state.workshop_messages.append({
                        "role": "user",
                        "content": "Recommend the best story structure for this video and outline the beats using the 2-1-3-4 ordering method."
                    })
                    with st.spinner("Analyzing structure..."):
                        response, _ = chat_generate(st.session_state.workshop_messages, get_workshop_system_prompt(), 1500)
                        if response:
                            st.session_state.workshop_messages.append({"role": "assistant", "content": response})
                    st.rerun()
            with col3:
                if st.button("🎯 Title & Thumbnail", use_container_width=True):
                    st.session_state.workshop_messages.append({
                        "role": "user",
                        "content": "Suggest 5 title options (under 50 chars each) and thumbnail concepts that complement them. Apply the playbook principles."
                    })
                    with st.spinner("Generating titles..."):
                        response, _ = chat_generate(st.session_state.workshop_messages, get_workshop_system_prompt(), 1500)
                        if response:
                            st.session_state.workshop_messages.append({"role": "assistant", "content": response})
                    st.rerun()
    
    with col_script:
        st.markdown("### 📜 Script Preview")
        
        if st.session_state.workshop_script:
            st.markdown(st.session_state.workshop_script[:3000] + "..." if len(st.session_state.workshop_script) > 3000 else st.session_state.workshop_script)
            
            st.divider()
            
            word_count = len(st.session_state.workshop_script.split())
            st.metric("Words", word_count)
            st.metric("~Duration", f"{word_count // 150} min")
            
            st.download_button(
                "📥 Download Script",
                st.session_state.workshop_script,
                f"script_{st.session_state.workshop_title.replace(' ', '_')[:20]}.md",
                use_container_width=True
            )
        else:
            st.info("Script will appear here once generated.")
            
            # Show conversation summary
            if st.session_state.workshop_messages:
                st.markdown("**Working on:** " + st.session_state.workshop_title)
                st.caption(f"{len(st.session_state.workshop_messages)} messages in conversation")

# ------------------------------------------------------------
# HOOK GENERATOR
# ------------------------------------------------------------
elif mode == "🎣 Hook Generator":
    st.header("🎣 Hook Generator")
    
    st.subheader("Select Hook Formats")
    st.caption("From Kallaway's 9 proven formats")
    
    cols = st.columns(3)
    selected = []
    for i, (name, data) in enumerate(HOOK_FORMULAS.items()):
        with cols[i % 3]:
            power_emoji = "🔥" if data["power"] >= 9 else "⚡" if data["power"] >= 7 else "💡"
            if st.checkbox(f"{power_emoji} {name}", value=data["power"] >= 9, key=f"h{i}", help=data["best_for"]):
                selected.append(name)
    
    st.divider()
    topic = st.text_input("📝 Video Topic", placeholder="Why cities stopped being beautiful")
    context = st.text_area("Additional context (optional)", placeholder="Key angle, specific examples, target emotion...", height=80)
    
    if st.button("🚀 Generate Hooks", type="primary", use_container_width=True):
        if not has_api_key():
            st.error("❌ No API key")
        elif not topic or not selected:
            st.error("❌ Enter topic and select at least one format")
        else:
            formulas = "\n".join([f"- {n}: {HOOK_FORMULAS[n]['template']} (best for: {HOOK_FORMULAS[n]['best_for']})" for n in selected])
            knowledge = get_active_knowledge(include_full_playbook=True)
            
            prompt = f"""Generate YouTube hooks for The Aesthetic City channel.

TOPIC: {topic}
{f"CONTEXT: {context}" if context else ""}

FORMATS TO USE:
{formulas}

KNOWLEDGE BASE:
{knowledge}

For each format, generate 2 hooks using Kallaway's 3-step formula:
1. Context Lean (establish topic + lean in)
2. Scroll-Stop Interjection (single line with "but/however/yet")
3. Contrarian Snapback (opposite direction, bigger shock = better)

Also provide:
- Power score (1-10) with reasoning
- Suggested thumbnail text (3-5 words)
- Which story structure pairs best with this hook

Be specific to architecture/urbanism. Write in Ruben's natural voice."""

            with st.spinner(f"Generating {len(selected)*2} hooks..."):
                result, err = generate(prompt, 5000)
                if result:
                    st.markdown("### Generated Hooks")
                    st.markdown(result)
                    save_to_history("hooks", result, {"topic": topic})
                elif err:
                    st.error(err)

# ------------------------------------------------------------
# QUICK SCRIPT
# ------------------------------------------------------------
elif mode == "📝 Quick Script":
    st.header("📝 Quick Script Generator")
    st.caption("For when you know exactly what you want. For brainstorming, use Script Workshop.")
    
    # Core inputs
    idea = st.text_area("💡 Video Idea *", height=100, placeholder="What's the main concept?")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        structure = st.selectbox("📐 Structure", list(STORY_STRUCTURES.keys()))
        st.caption(f"Best for: {STORY_STRUCTURES[structure]['best_for']}")
    with col2:
        length = st.selectbox("⏱️ Length", ["5 min", "8 min", "12 min", "15 min", "20 min"])
    with col3:
        hook_format = st.selectbox("🎣 Hook Format", ["Auto-select"] + list(HOOK_FORMULAS.keys()))
    
    st.divider()
    
    with st.expander("🎛️ Advanced Options", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            must_include = st.text_area("✅ Must-include points", height=80, placeholder="Key facts, examples, arguments...")
            experts = st.text_input("🎓 Experts to reference", placeholder="Léon Krier, Christopher Alexander...")
            emotion = st.selectbox("💫 Target emotion", ["Auto", "Awe/Inspiration", "Outrage", "Hope", "Curiosity", "Nostalgia"])
        
        with col2:
            examples = st.text_input("🏘️ Specific projects", placeholder="Poundbury, Cayalá, Le Plessis-Robinson...")
            avoid = st.text_input("🚫 Avoid topics", placeholder="Things to skip...")
            cta = st.selectbox("📢 Call-to-action", ["None", "Subscribe", "Check course", "Share video"])
    
    st.divider()
    
    if st.button("🚀 Generate Script", type="primary", use_container_width=True):
        if not has_api_key():
            st.error("❌ No API key")
        elif not idea:
            st.error("❌ Enter a video idea")
        else:
            beats = ", ".join(STORY_STRUCTURES[structure]["beats"])
            words = int(length.split()[0]) * 150
            knowledge = get_active_knowledge(include_full_playbook=True)
            
            prompt = f"""Write a complete YouTube script for The Aesthetic City channel (209K subscribers, classical architecture and traditional urbanism).

IDEA: {idea}
STRUCTURE: {structure} - Beats: {beats}
LENGTH: ~{words} words ({length})
{f"HOOK FORMAT: {hook_format}" if hook_format != "Auto-select" else ""}

KNOWLEDGE BASE (apply these principles throughout):
{knowledge}
"""
            if must_include: prompt += f"\nMUST INCLUDE:\n{must_include}"
            if examples: prompt += f"\nFEATURE PROJECTS: {examples}"
            if experts: prompt += f"\nREFERENCE EXPERTS: {experts}"
            if avoid: prompt += f"\nAVOID: {avoid}"
            if emotion != "Auto": prompt += f"\nTARGET EMOTION: {emotion}"
            if cta != "None": prompt += f"\nCTA: {cta}"
            
            prompt += """

REQUIREMENTS:
1. Use Kallaway's 3-step hook formula (context lean → scroll-stop → snapback)
2. Apply 2-1-3-4 ordering (second-best point first, best second)
3. Include [B-ROLL: description] markers throughout
4. Rehook between major sections
5. Use "but" and "therefore" between beats, not "and then"
6. First dopamine hit within 60 seconds
7. Pattern interrupts every 30-45 seconds (suggest visuals/camera changes)
8. Fortune cookie outro with forever loop to related video
9. Write in Ruben's voice: flowing sentences, verbal tics, no AI clichés

Generate the complete, ready-to-record script:"""

            with st.spinner("✍️ Writing script..."):
                result, err = generate(prompt, 10000)
                if result:
                    st.markdown("### 📜 Your Script")
                    st.markdown(result)
                    save_to_history("script", result, {"idea": idea})
                    
                    word_count = len(result.split())
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Words", word_count)
                    col2.metric("Duration", f"~{word_count // 150} min")
                    col3.metric("B-Roll Cues", result.count("[B-ROLL"))
                    
                    st.download_button("📥 Download Script", result, "script.md", use_container_width=True)
                elif err:
                    st.error(err)

# ------------------------------------------------------------
# SCRIPT ANALYZER
# ------------------------------------------------------------
elif mode == "🔬 Script Analyzer":
    st.header("🔬 Script Analyzer")
    st.caption("Analyze your script against the Viral Video Playbook")
    
    script = st.text_area("Paste your script", height=300)
    
    if st.button("🔍 Analyze Script", type="primary", use_container_width=True):
        if not has_api_key():
            st.error("❌ No API key")
        elif not script:
            st.error("❌ Paste a script to analyze")
        else:
            knowledge = get_active_knowledge(include_full_playbook=True)
            
            prompt = f"""Analyze this script for The Aesthetic City channel against the Viral Video Playbook principles.

SCRIPT:
{script[:8000]}

KNOWLEDGE BASE TO EVALUATE AGAINST:
{knowledge}

Provide a thorough analysis:

## 📊 VIRAL SCORE: X/100

### Hook Analysis
- Does it use Kallaway's 3-step formula? (Context lean, scroll-stop, snapback)
- Which hook format is it using?
- Score: /10

### Intro Analysis (First 60 seconds)
- Click confirmation present?
- Five-part framework applied? (Context, Stakes, Contrast, Proof, Plan)
- First dopamine hit timing?
- Score: /10

### Body Structure
- Which story structure is being used?
- Is 2-1-3-4 ordering applied?
- Rehooking between sections?
- But/Therefore or and-then transitions?
- Score: /10

### Retention Tactics
- Pattern interrupts (B-roll, camera changes)?
- Stakes raised throughout?
- Payoff maintained?
- Score: /10

### Voice Match
- Does it match Ruben's natural voice?
- Any AI clichés present?
- Score: /10

## 🚨 CRITICAL ISSUES
Specific problems with line references.

## ✅ STRENGTHS
What's working well.

## ✏️ SUGGESTED REWRITES
Improved versions of weak sections, applying playbook principles."""

            with st.spinner("Analyzing..."):
                result, err = generate(prompt, 5000)
                if result:
                    st.markdown(result)
                    save_to_history("analysis", result)
                elif err:
                    st.error(err)

# ------------------------------------------------------------
# KNOWLEDGE SOURCES
# ------------------------------------------------------------
elif mode == "📚 Knowledge Sources":
    st.header("📚 Knowledge Sources")
    st.write("The knowledge that powers your script generation")
    
    tab1, tab2, tab3 = st.tabs(["📖 Built-in Knowledge", "➕ Add YouTube Video", "📹 Custom Sources"])
    
    with tab1:
        st.subheader("Built-in Knowledge Base")
        
        init_knowledge_state()
        
        for key, kb in BUILT_IN_KNOWLEDGE.items():
            is_active = key in st.session_state.active_builtin
            
            with st.expander(f"{'✅' if is_active else '❌'} {kb['name']}", expanded=(key == "viral_playbook")):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.caption(f"Source: {kb['source']}")
                with col2:
                    if st.button("Toggle", key=f"toggle_{key}"):
                        if is_active:
                            st.session_state.active_builtin.remove(key)
                        else:
                            st.session_state.active_builtin.append(key)
                        save_knowledge_state()
                        st.rerun()
                
                if key == "viral_playbook" and "full_text" in kb:
                    st.markdown("**Full Playbook:**")
                    st.markdown(kb["full_text"][:5000] + "..." if len(kb["full_text"]) > 5000 else kb["full_text"])
                else:
                    st.markdown("**Principles:**")
                    for principle in kb['principles']:
                        st.markdown(f"- {principle}")
    
    with tab2:
        st.subheader("➕ Add YouTube Video as Knowledge Source")
        st.write("Extract creator advice from YouTube videos")
        
        source_name = st.text_input("Name this source", placeholder="e.g., 'MrBeast Retention Tips'")
        youtube_url = st.text_input("YouTube URL (optional)", placeholder="https://www.youtube.com/watch?v=...")
        
        st.divider()
        
        method = st.radio("Transcript method:", [
            "📝 Paste transcript manually",
            "🤖 Auto-transcribe from URL"
        ], index=0)
        
        transcript = None
        
        if method == "📝 Paste transcript manually":
            manual_transcript = st.text_area("Paste transcript here:", height=200)
            if manual_transcript:
                transcript = manual_transcript
                st.success(f"✅ Transcript ready ({len(transcript.split())} words)")
        else:
            if not YOUTUBE_AVAILABLE:
                st.warning("⚠️ YouTube transcript API not available")
            elif youtube_url:
                if st.button("🎬 Fetch Transcript"):
                    video_id = extract_video_id(youtube_url)
                    if video_id:
                        with st.spinner("Fetching..."):
                            transcript, err = get_youtube_transcript(video_id)
                        if transcript:
                            st.session_state['temp_transcript'] = transcript
                            st.success(f"✅ Got transcript ({len(transcript.split())} words)")
                        else:
                            st.error(err)
                
                if 'temp_transcript' in st.session_state:
                    transcript = st.session_state['temp_transcript']
        
        if st.button("🧠 Extract Advice", type="primary", disabled=not transcript):
            if not source_name:
                st.error("❌ Name this source")
            elif not has_api_key():
                st.error("❌ No API key")
            else:
                with st.spinner("Extracting..."):
                    prompt = f"""Analyze this YouTube video transcript and extract ACTIONABLE ADVICE for creating viral YouTube videos.

TRANSCRIPT:
{transcript[:15000]}

Extract:
1. Main principles/tips shared
2. Specific techniques mentioned
3. Do's and Don'ts
4. Any frameworks or formulas

Format as bullet-point list of clear, actionable principles.
Focus on VIDEO CREATION advice, not the content topic itself."""

                    advice, err = generate(prompt, 3000)
                
                if advice:
                    st.session_state['pending_source'] = {
                        "name": source_name,
                        "url": youtube_url or "manual paste",
                        "transcript_words": len(transcript.split()),
                        "extracted_advice": advice,
                        "active": True
                    }
                    st.rerun()
        
        if 'pending_source' in st.session_state:
            st.markdown("### Extracted Advice")
            st.markdown(st.session_state['pending_source']['extracted_advice'])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Add to Knowledge Base", type="primary", use_container_width=True):
                    if save_source_to_db(st.session_state['pending_source']):
                        st.success("✅ Added!")
                        del st.session_state['pending_source']
                        st.session_state.knowledge_loaded = False
                        st.rerun()
            with col2:
                if st.button("❌ Discard", use_container_width=True):
                    del st.session_state['pending_source']
                    st.rerun()
    
    with tab3:
        st.subheader("📹 Your Custom Sources")
        
        init_knowledge_state()
        
        if not st.session_state.knowledge_sources:
            st.info("No custom sources yet.")
        else:
            for i, source in enumerate(st.session_state.knowledge_sources):
                is_active = source.get('active', True)
                
                with st.expander(f"{'✅' if is_active else '❌'} {source['name']}"):
                    st.caption(f"Source: {source['url']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Toggle", key=f"toggle_custom_{i}"):
                            source_id = source.get('id')
                            if source_id:
                                update_source_in_db(source_id, {"active": not is_active})
                            st.session_state.knowledge_loaded = False
                            st.rerun()
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_{i}"):
                            source_id = source.get('id')
                            if source_id:
                                delete_source_from_db(source_id)
                            st.session_state.knowledge_loaded = False
                            st.rerun()
                    
                    st.markdown(source.get('extracted_advice', ''))

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
                content = item['content']
                st.markdown(content[:3000] + "..." if len(content) > 3000 else content)
                st.download_button("📥 Download", content, f"{item['type']}.md", key=f"dl_{i}")
        
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()

# Footer
st.divider()
st.caption("v8 • Script Workshop + Viral Video Playbook • The Aesthetic City")
