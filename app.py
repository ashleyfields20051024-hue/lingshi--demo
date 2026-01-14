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
# 2. Internationalization (i18n)
# ==========================================
def t(en_text, zh_text):
    """Translation helper based on selected language"""
    return zh_text if "Chinese" in st.session_state.get("language_mode", "Chinese") else en_text

# ==========================================
# 3. Supabase Connection (Robust SDK)
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
# 4. Engineering Models
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
# 5. Socratic Engine (Robust State Machine)
# ==========================================
STATE_TOKEN = "[STATE: ALIGNED]"

def get_system_prompt(phase, language_mode):
    is_chinese = "Chinese" in language_mode
    if is_chinese:
        base_prompt = "你是'灵识'，一个专注于 AI 安全的技术产品经理。你的目标是在构建方案前引导用户对齐系统约束。请用中文回复。"
    else:
        base_prompt = "You are 'Lingshi' (Spirit & Insight), a Venture Builder AI focused on AI Safety. Your goal is to elicit system constraints before architecting solutions. Reply strictly in ENGLISH."
    
    if phase == "clarifying":
        instruction = (
            f"\n\nPHASE: AMBIGUITY CHECK.\n"
            "1. Analyze if the user's problem description is specific enough for engineering.\n"
            "2. If vague, REFUSE to provide a solution. Instead, ask 2-3 targeted multiple-choice questions.\n"
            "3. ONLY when you have sufficient information, append the exact token '{STATE_TOKEN}' at the very end of your message."
        )
        return base_prompt + instruction
    else:
        instruction = "\n\nPHASE: ALIGNMENT REACHED. Acknowledge the alignment and wait for the user to trigger generation."
        return base_prompt + instruction

def get_chat_response(history, api_key, current_phase, language_mode):
    client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    sys_prompt = get_system_prompt(current_phase, language_mode)
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

def generate_blueprint(history, api_key, language_mode):
    client = instructor.from_openai(openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com"), mode=instructor.Mode.JSON)
    is_chinese = "Chinese" in language_mode
    lang_instruction = "输出中文。" if is_chinese else "Output in ENGLISH."
    system_prompt = f"You are the Engineering Brain of Lingshi. Generate a deep technical blueprint based on the aligned constraints. {lang_instruction}"
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    return client.chat.completions.create(model="deepseek-chat", response_model=EngineeringSpec, messages=messages)

# ==========================================
# 6. Database Operations (History Restoration)
# ==========================================
def save_blueprint_to_supabase(blueprint: EngineeringSpec, messages: List[dict], language_mode: str):
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
            "language_mode": language_mode,
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
        response = supabase.table("problem_assets").select("*").order("created_at", desc=True).limit(limit).execute()
        return response.data if response.data else []
    except:
        return []

# ==========================================
# 7. Session State & Callbacks
# ==========================================
if "messages" not in st.session_state: st.session_state.messages = []
if "blueprint" not in st.session_state: st.session_state.blueprint = None
if "conversation_phase" not in st.session_state: st.session_state.conversation_phase = "clarifying"
if "language_mode" not in st.session_state: st.session_state.language_mode = "Chinese (中文模式)"

def restore_project(project_data):
    """Callback to restore state from history"""
    try:
        st.session_state.messages = json.loads(project_data["conversation_log"])
        blueprint_json = json.loads(project_data["full_blueprint"])
        st.session_state.blueprint = EngineeringSpec(**blueprint_json)
        st.session_state.conversation_phase = "aligned"
        st.session_state.language_mode = project_data.get("language_mode", "Chinese (中文模式)")
        st.toast(f"⏪ {t('Restored', '已恢复')}: {project_data['project_name']}")
    except Exception as e:
        st.error(f"Restoration failed: {str(e)}")

# ==========================================
# 8. Sidebar (Interactive History)
# ==========================================
with st.sidebar:
    st.title(t("🛡️ Lingshi Protocol", "🛡️ 灵识协议"))
    st.caption(f"v4.2 {t('Robust MATS Edition', '稳健 MATS 版')}")
    
    # Language Toggle
    st.session_state.language_mode = st.radio(
        t("Interface Language", "界面语言"), 
        ["Chinese (中文模式)", "English for Investors"],
        index=0 if "Chinese" in st.session_state.language_mode else 1
    )
    st.markdown("---")
    
    # API Key
    api_key = st.secrets.get("DEEPSEEK_API_KEY", "")
    if not api_key: api_key = st.text_input(t("DeepSeek Key", "DeepSeek 密钥"), type="password")
    
    # Supabase Fallback
    if not supabase:
        st.warning(t("🔑 Supabase Offline", "🔑 Supabase 离线"))
        st.session_state["manual_supabase_url"] = st.text_input("URL", value=st.session_state.get("manual_supabase_url", ""))
        st.session_state["manual_supabase_key"] = st.text_input(t("Key", "密钥"), type="password", value=st.session_state.get("manual_supabase_key", ""))
        if st.button(t("🔌 Connect", "🔌 连接")): st.rerun()
    
    if st.button(t("🔄 New Session", "🔄 开启新会话"), use_container_width=True):
        st.session_state.messages = []; st.session_state.blueprint = None; st.session_state.conversation_phase = "clarifying"; st.rerun()
    
    st.markdown("---")
    st.subheader(t("⏪ Time Travel (History)", "⏪ 时间旅行 (历史记录)"))
    projects = fetch_recent_projects()
    if projects:
        for p in projects:
            date_str = p['created_at'][:10]
            if st.button(f"📄 {p['project_name']}\n({date_str})", key=f"hist_{p['id']}", use_container_width=True):
                restore_project(p)
                st.rerun()
    else:
        st.caption(t("No history found.", "暂无历史记录。"))

# ==========================================
# 9. Main Interface
# ==========================================
st.title(t("Socratic Venture Builder", "苏格拉底式创业构建器"))
st.caption(t("AI Safety Mode: Enforcing Constraint Alignment before Engineering.", "AI 安全模式：在工程构建前强制执行约束对齐。"))

# Phase Indicator
if st.session_state.conversation_phase == "clarifying":
    st.markdown(f'<div class="phase-badge phase-clarifying">⚠️ {t("Clarifying Constraints", "约束澄清中")}</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="phase-badge phase-aligned">✅ {t("Constraints Aligned", "约束已对齐")}</div>', unsafe_allow_html=True)

col_chat, col_blue = st.columns([3, 2], gap="large")

with col_chat:
    # Chat History
    if not st.session_state.messages:
        welcome_msg = t("Hello, I am Lingshi. Please describe the problem or system you wish to architect.", "你好，我是灵识。请描述你观察到的问题或想要构建的系统。")
        st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    
    # Chat Input
    if prompt := st.chat_input(t("Input observation...", "输入观察到的问题...")):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    # Trigger Response
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        if api_key:
            with st.chat_message("assistant"):
                with st.spinner(t("Analyzing constraints...", "正在分析约束...")):
                    resp, next_phase = get_chat_response(st.session_state.messages, api_key, st.session_state.conversation_phase, st.session_state.language_mode)
                    st.markdown(resp)
                    st.session_state.messages.append({"role": "assistant", "content": resp})
                    if next_phase != st.session_state.conversation_phase:
                        st.session_state.conversation_phase = next_phase
                        st.rerun()
        else:
            st.error(t("Please provide a DeepSeek API Key in the sidebar.", "请在侧边栏提供 DeepSeek API 密钥。"))

with col_blue:
    # Generation Logic
    if st.session_state.conversation_phase != "aligned":
        st.button(t("✨ Generate Blueprint", "✨ 生成工程蓝图"), disabled=True, use_container_width=True)
        st.info(t("💡 AI is currently eliciting constraints. Answer the questions to proceed.", "💡 AI 正在引导约束对齐。请回答问题以继续。"))
        
        # Force Override Button
        if st.button(t("⚠️ Skip Questions & Force Generate", "⚠️ 跳过提问并强制生成"), use_container_width=True, help=t("Bypass the Socratic loop if the AI is stuck.", "如果 AI 陷入循环，可跳过苏格拉底环节。")):
            st.session_state.conversation_phase = "aligned"
            st.rerun()
    else:
        if st.button(t("✨ Generate Blueprint", "✨ 生成工程蓝图"), type="primary", use_container_width=True):
            with st.spinner(t("Architecting solution...", "正在构建方案...")):
                try:
                    bp = generate_blueprint(st.session_state.messages, api_key, st.session_state.language_mode)
                    st.session_state.blueprint = bp
                    if save_blueprint_to_supabase(bp, st.session_state.messages, st.session_state.language_mode):
                        st.toast(t("✅ Asset Minted & Saved on Protocol!", "✅ 资产已铸造并保存至协议！"))
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
                    <strong>{t('Architecture Logic:', '架构逻辑：')}</strong><br>{b.architecture_logic}
                </div>
                <strong>{t('Implementation Steps:', '实施步骤：')}</strong>
                <ol>
                    {"".join([f"<li>{step}</li>" for step in b.implementation_steps])}
                </ol>
                <strong>{t('Critical Risk:', '核心风险：')}</strong>
                <p style="color: #d93025;">{b.critical_risks}</p>
                <strong>{t('Tech Stack:', '技术栈：')}</strong><br>
                {"".join([f"<span class='tech-pill'>{item}</span>" for item in b.core_tech_stack])}
                <br><br>
                <small>{t('Est. Budget:', '预估预算：')} {b.estimated_budget}</small>
            </div>
            """, unsafe_allow_html=True)
