import streamlit as st
import openai
import instructor
from pydantic import BaseModel, Field
from typing import List, Optional
import json
from datetime import datetime
from supabase import create_client, Client

# ==========================================
# 1. Page Configuration & Professional UI
# ==========================================
st.set_page_config(
    page_title="Lingshi Protocol v4.2",
    page_icon="🛡️",
    layout="wide"
)

# Professional Industrial Style
st.markdown("""
<style>
    /* Clean Badge Styles */
    .phase-badge {
        padding: 6px 14px;
        border-radius: 4px;
        font-size: 0.85em;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .phase-clarifying { background-color: #FFF4E5; color: #B76E00; border: 1px solid #FFD5A1; }
    .phase-aligned { background-color: #E6F4EA; color: #1E7E34; border: 1px solid #B7E1CD; }
    
    /* Blueprint Styling */
    .blueprint-container {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 20px;
    }
    .blueprint-header {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #1a1a1a;
        border-bottom: 2px solid #000;
        padding-bottom: 8px;
        margin-bottom: 16px;
    }
    .tech-pill {
        display: inline-block;
        background: #e9ecef;
        color: #495057;
        padding: 3px 10px;
        border-radius: 12px;
        font-family: 'SFMono-Regular', Consolas, monospace;
        font-size: 0.8em;
        margin: 3px;
        border: 1px solid #ced4da;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Supabase Connection (Robust SDK)
# ==========================================
def get_supabase_client():
    """Get Supabase client from secrets or session state fallback"""
    url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
    key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")
    
    if not url: url = st.session_state.get("manual_supabase_url")
    if not key: key = st.session_state.get("manual_supabase_key")
    
    if url and key:
        try:
            return create_client(url, key)
        except:
            return None
    return None

supabase = get_supabase_client()

# ==========================================
# 3. Engineering Models
# ==========================================
class EngineeringSpec(BaseModel):
    project_name: str = Field(..., description="Project Name (Creative & Catchy)")
    one_liner: str = Field(..., description="A single sentence explaining the value prop.")
    architecture_logic: str = Field(..., description="Explain the system data flow clearly.")
    implementation_steps: List[str] = Field(..., description="5 concrete steps to build the MVP.")
    core_tech_stack: List[str] = Field(..., description="Specific libraries/tools.")
    critical_risks: str = Field(..., description="What is the biggest technical bottleneck?")
    estimated_budget: str = Field(..., description="Time & Cost estimation.")

# ==========================================
# 4. Socratic Engine (Robust State Machine)
# ==========================================
STATE_TOKEN = "[STATE: ALIGNED]"

def get_system_prompt(phase):
    base_prompt = (
        "You are 'Lingshi' (Spirit & Insight), a Venture Builder AI focused on AI Safety. "
        "Your goal is to elicit system constraints before architecting solutions. "
        "Reply strictly in ENGLISH."
    )
    
    if phase == "clarifying":
        return (
            f"{base_prompt}\n\n"
            "PHASE: AMBIGUITY CHECK.\n"
            "1. Analyze if the user's problem description is specific enough for engineering.\n"
            "2. If vague, REFUSE to provide a solution. Instead, ask 2-3 targeted multiple-choice questions.\n"
            "3. ONLY when you have sufficient information, append the exact token '{STATE_TOKEN}' at the very end of your message."
        )
    else:
        return f"{base_prompt}\n\nPHASE: ALIGNMENT REACHED. Acknowledge the alignment and wait for the user to trigger generation."

def get_chat_response(history, api_key, current_phase):
    client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    sys_prompt = get_system_prompt(current_phase)
    messages = [{"role": "system", "content": sys_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    response = client.chat.completions.create(model="deepseek-chat", messages=messages, temperature=0.3)
    content = response.choices[0].message.content
    
    # Robust State Detection
    new_phase = current_phase
    if STATE_TOKEN in content:
        new_phase = "aligned"
        content = content.replace(STATE_TOKEN, "").strip()
        
    return content, new_phase

def generate_blueprint(history, api_key):
    client = instructor.from_openai(openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com"), mode=instructor.Mode.JSON)
    system_prompt = "You are the Engineering Brain of Lingshi. Generate a deep technical blueprint based on the aligned constraints. Output in ENGLISH."
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    return client.chat.completions.create(model="deepseek-chat", response_model=EngineeringSpec, messages=messages)

# ==========================================
# 5. Database Operations (History Restoration)
# ==========================================
def save_blueprint_to_supabase(blueprint: EngineeringSpec, messages: List[dict]):
    if not supabase: return False
    try:
        user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]
        raw_user_input = user_messages[-1] if user_messages else "N/A"
        data = {
            "project_name": blueprint.project_name,
            "one_liner": blueprint.one_liner,
            "full_blueprint": blueprint.model_dump_json(),
            "raw_user_input": raw_user_input,
            "conversation_log": json.dumps(messages, ensure_ascii=False),
            "language_mode": "English",
            "created_at": datetime.utcnow().isoformat()
        }
        supabase.table("problem_assets").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Save failed: {str(e)}")
        return False

def fetch_recent_projects(limit=10):
    if not supabase: return []
    try:
        # Fetch all columns for restoration
        response = supabase.table("problem_assets").select("*").order("created_at", desc=True).limit(limit).execute()
        return response.data if response.data else []
    except:
        return []

# ==========================================
# 6. Session State & Callbacks
# ==========================================
if "messages" not in st.session_state: st.session_state.messages = []
if "blueprint" not in st.session_state: st.session_state.blueprint = None
if "conversation_phase" not in st.session_state: st.session_state.conversation_phase = "clarifying"

def restore_project(project_data):
    """Callback to restore state from history"""
    try:
        st.session_state.messages = json.loads(project_data["conversation_log"])
        blueprint_json = json.loads(project_data["full_blueprint"])
        st.session_state.blueprint = EngineeringSpec(**blueprint_json)
        st.session_state.conversation_phase = "aligned"
        st.toast(f"⏪ Restored: {project_data['project_name']}")
    except Exception as e:
        st.error(f"Restoration failed: {str(e)}")

# ==========================================
# 7. Sidebar (Interactive History)
# ==========================================
with st.sidebar:
    st.title("🛡️ Lingshi Protocol")
    st.caption("v4.2 Robust MATS Edition")
    st.markdown("---")
    
    # API Key
    api_key = st.secrets.get("DEEPSEEK_API_KEY", "")
    if not api_key: api_key = st.text_input("DeepSeek Key", type="password")
    
    # Supabase Fallback
    if not supabase:
        st.warning("🔑 Supabase Offline")
        st.session_state["manual_supabase_url"] = st.text_input("URL", value=st.session_state.get("manual_supabase_url", ""))
        st.session_state["manual_supabase_key"] = st.text_input("Key", type="password", value=st.session_state.get("manual_supabase_key", ""))
        if st.button("🔌 Connect"): st.rerun()
    
    if st.button("🔄 New Session", use_container_width=True):
        st.session_state.messages = []; st.session_state.blueprint = None; st.session_state.conversation_phase = "clarifying"; st.rerun()
    
    st.markdown("---")
    st.subheader("⏪ Time Travel (History)")
    projects = fetch_recent_projects()
    if projects:
        for p in projects:
            date_str = p['created_at'][:10]
            if st.button(f"📄 {p['project_name']}\n({date_str})", key=f"hist_{p['id']}", use_container_width=True):
                restore_project(p)
                st.rerun()
    else:
        st.caption("No history found.")

# ==========================================
# 8. Main Interface
# ==========================================
st.title("Socratic Venture Builder")
st.caption("AI Safety Mode: Enforcing Constraint Alignment before Engineering.")

# Phase Indicator
if st.session_state.conversation_phase == "clarifying":
    st.markdown('<div class="phase-badge phase-clarifying">⚠️ Clarifying Constraints</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="phase-badge phase-aligned">✅ Constraints Aligned</div>', unsafe_allow_html=True)

col_chat, col_blue = st.columns([3, 2], gap="large")

with col_chat:
    # Chat History
    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "content": "Hello, I am Lingshi. Please describe the problem or system you wish to architect."})
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    
    # Chat Input
    if prompt := st.chat_input("Input observation..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    # Trigger Response
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        if api_key:
            with st.chat_message("assistant"):
                with st.spinner("Analyzing constraints..."):
                    resp, next_phase = get_chat_response(st.session_state.messages, api_key, st.session_state.conversation_phase)
                    st.markdown(resp)
                    st.session_state.messages.append({"role": "assistant", "content": resp})
                    if next_phase != st.session_state.conversation_phase:
                        st.session_state.conversation_phase = next_phase
                        st.rerun()
        else:
            st.error("Please provide a DeepSeek API Key in the sidebar.")

with col_blue:
    # Generation Logic
    if st.session_state.conversation_phase != "aligned":
        st.button("✨ Generate Blueprint", disabled=True, use_container_width=True)
        st.info("💡 AI is currently eliciting constraints. Answer the questions to proceed.")
        
        # Force Override Button
        if st.button("⚠️ Skip Questions & Force Generate", use_container_width=True, help="Bypass the Socratic loop if the AI is stuck."):
            st.session_state.conversation_phase = "aligned"
            st.rerun()
    else:
        if st.button("✨ Generate Blueprint", type="primary", use_container_width=True):
            with st.spinner("Architecting solution..."):
                try:
                    bp = generate_blueprint(st.session_state.messages, api_key)
                    st.session_state.blueprint = bp
                    if save_blueprint_to_supabase(bp, st.session_state.messages):
                        st.toast("✅ Asset Minted & Saved on Protocol!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Generation failed: {str(e)}")
    
    # Display Blueprint
    if st.session_state.blueprint:
        b = st.session_state.blueprint
        with st.container():
            st.markdown(f"""
            <div class="blueprint-container">
                <div class="blueprint-header">🚀 {b.project_name}</div>
                <p style="font-style: italic; color: #666;">{b.one_liner}</p>
                <div style="background: #fff; padding: 15px; border-left: 4px solid #000; margin: 15px 0;">
                    <strong>Architecture Logic:</strong><br>{b.architecture_logic}
                </div>
                <strong>Implementation Steps:</strong>
                <ol>
                    {"".join([f"<li>{step}</li>" for step in b.implementation_steps])}
                </ol>
                <strong>Critical Risk:</strong>
                <p style="color: #d93025;">{b.critical_risks}</p>
                <strong>Tech Stack:</strong><br>
                {"".join([f"<span class='tech-pill'>{item}</span>" for item in b.core_tech_stack])}
                <br><br>
                <small>Est. Budget: {b.estimated_budget}</small>
            </div>
            """, unsafe_allow_html=True)
