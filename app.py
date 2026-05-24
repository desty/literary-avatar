"""Avatar — Streamlit Web UI for Literary Character AI Agents."""

import streamlit as st

import sys
sys.path.insert(0, ".")

from src.character.engine import CharacterEngine
from src.character.arc_tracker import load_arc
from src.character.logic_extractor import load_logic
from src.memory.persistent import PersistentMemory

# --- Character registry ---
CHARACTERS = {
    "sherlock_holmes": {
        "name": "Sherlock Holmes",
        "novel": "The Adventures of Sherlock Holmes (1892)",
        "author": "Arthur Conan Doyle",
        "avatar": "🔍",
        "color": "#4FC3F7",
    },
    "elizabeth_bennet": {
        "name": "Elizabeth Bennet",
        "novel": "Pride and Prejudice (1813)",
        "author": "Jane Austen",
        "avatar": "📖",
        "color": "#F48FB1",
    },
}

# --- Page config ---
st.set_page_config(
    page_title="Avatar — Literary Character AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_engine(character_id: str) -> CharacterEngine:
    """Initialize or retrieve cached character engine."""
    persistent = PersistentMemory(character_id)
    engine = CharacterEngine(character_id, persistent_memory=persistent)
    return engine


def get_engine() -> CharacterEngine:
    """Get the current character engine from session state."""
    char_id = st.session_state.get("character_id", "sherlock_holmes")
    key = f"engine_{char_id}"

    if key not in st.session_state:
        st.session_state[key] = init_engine(char_id)

    return st.session_state[key]


def reset_engine():
    """Reset the current character engine."""
    char_id = st.session_state.get("character_id", "sherlock_holmes")
    key = f"engine_{char_id}"
    if key in st.session_state:
        st.session_state[key].reset()
        del st.session_state[key]
    st.session_state["messages"] = []


# --- Session state defaults ---
if "character_id" not in st.session_state:
    st.session_state.character_id = "sherlock_holmes"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "timeline_pos" not in st.session_state:
    st.session_state.timeline_pos = -1  # -1 = full knowledge


# --- Sidebar ---
with st.sidebar:
    st.title("📚 Avatar")
    st.caption("Literary Character AI Agent")

    st.divider()

    # Character selector
    st.subheader("Character")
    char_options = {v["name"]: k for k, v in CHARACTERS.items()}
    current_name = CHARACTERS[st.session_state.character_id]["name"]

    selected_name = st.selectbox(
        "Choose character",
        options=list(char_options.keys()),
        index=list(char_options.keys()).index(current_name),
        label_visibility="collapsed",
    )
    new_char_id = char_options[selected_name]

    if new_char_id != st.session_state.character_id:
        st.session_state.character_id = new_char_id
        st.session_state.messages = []
        st.session_state.timeline_pos = -1
        st.rerun()

    char_info = CHARACTERS[st.session_state.character_id]
    st.caption(f"*{char_info['novel']}* by {char_info['author']}")

    st.divider()

    # Timeline control
    st.subheader("Narrative Timeline")
    arc = load_arc(st.session_state.character_id)
    max_pos = len(arc) if arc else 0

    if max_pos > 0:
        use_full = st.checkbox("Full knowledge", value=(st.session_state.timeline_pos == -1))

        if use_full:
            st.session_state.timeline_pos = -1
            engine = get_engine()
            engine.set_narrative_position(None)
            st.caption(f"Character knows all {max_pos} story events.")
        else:
            pos = st.slider(
                "Story position",
                min_value=0,
                max_value=max_pos,
                value=max_pos if st.session_state.timeline_pos == -1 else st.session_state.timeline_pos,
                help="Character only knows events up to this position",
            )
            st.session_state.timeline_pos = pos
            engine = get_engine()
            engine.set_narrative_position(pos)

            if pos == 0:
                st.caption("⚠️ Before any story — character has no story knowledge.")
            elif arc and pos <= len(arc):
                snapshot = arc[pos - 1]
                st.caption(f"After: *{snapshot.get('story_title', f'Chapter {pos}')}*")
                with st.expander("Emotional state"):
                    st.write(snapshot.get("emotional_state", "Unknown"))
    else:
        st.caption("No arc data available for this character.")

    st.divider()

    # BDI state
    st.subheader("Mental State (BDI)")
    engine = get_engine()
    bdi = engine.bdi_state

    if any(bdi.values()):
        if bdi.get("beliefs"):
            st.markdown("**Beliefs**")
            for b in bdi["beliefs"]:
                st.caption(f"• {b}")
        if bdi.get("desires"):
            st.markdown("**Desires**")
            for d in bdi["desires"]:
                st.caption(f"• {d}")
        if bdi.get("intentions"):
            st.markdown("**Intentions**")
            for i in bdi["intentions"]:
                st.caption(f"• {i}")
    else:
        st.caption("No mental state yet. Start a conversation.")

    st.divider()

    # Behavioral logic summary
    logic = load_logic(st.session_state.character_id)
    if logic:
        with st.expander(f"Behavioral Rules ({logic['total_rules']} total)"):
            by_cat = logic.get("by_category", {})
            for cat, count in by_cat.items():
                st.caption(f"• {cat}: {count} rules")

    st.divider()

    # Actions
    if st.button("🔄 Reset Conversation", use_container_width=True):
        reset_engine()
        st.rerun()


# --- Main chat area ---
char_info = CHARACTERS[st.session_state.character_id]
st.header(f"{char_info['avatar']} {char_info['name']}")
st.caption(f"{char_info['novel']} — {char_info['author']}")

# Display message history
for msg in st.session_state.messages:
    role = msg["role"]
    if role == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant", avatar=char_info["avatar"]):
            st.write(msg["content"])

# Chat input
if prompt := st.chat_input(f"Talk to {char_info['name']}..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Get character response
    engine = get_engine()
    with st.chat_message("assistant", avatar=char_info["avatar"]):
        with st.spinner("Thinking..."):
            response = engine.respond(prompt)
        st.write(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

    # Refresh sidebar BDI
    st.rerun()
