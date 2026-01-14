import streamlit as st
import openai
import instructor
from pydantic import BaseModel, Field
from typing import List
import json
from datetime import datetime
from supabase import create_client, Client

# ==========================================
# 1. 界面配置 & 太阳朋克 CSS
# ==========================================
st.set_page_config(
    page_title="Lingshi Protocol",
    page_icon="🧘‍♂️",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #FDFCF5; color: #2F4F4F; }
    section[data-testid="stSidebar"] { background-color: #E8F5E9; }
    .stChatMessage { background-color: #ffffff; border: 1px solid #e0e0e0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stButton>button { background: linear-gradient(135deg, #D4AF37 0%, #C5A028 100%); color: white; border: none; }
    
    /* 蓝图卡片样式增强 */
    .blueprint-header { color: #1B5E20; font-family: 'Georgia', serif; border-bottom: 2px solid #D4AF37; padding-bottom: 10px; margin-bottom: 15px; }
    .tech-pill { display: inline-block; background: #263238; color: #80CBC4; padding: 2px 8px; border-radius: 4px; font-family: monospace; font-size: 0.9em; margin: 2px; }
    
    /* 历史记录样式 */
    .history-item { background: white; padding: 8px; margin: 5px 0; border-radius: 4px; border-left: 3px solid #D4AF37; }
    .history-title { font-weight: bold; color: #1B5E20; }
    .history-date { font-size: 0.8em; color: #666; }
    
    /* 状态标签样式 */
    .phase-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 10px;
    }
    .phase-clarifying { background-color: #FFF3E0; color: #E65100; border: 1px solid #FFE0B2; }
    .phase-aligned { background-color: #E8F5E9; color: #2E7D32; border: 1px solid #C8E6C9; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Supabase 连接初始化 (官方库方式)
# ==========================================
@st.cache_resource
def init_supabase():
    """Initialize Supabase client with simplified secret retrieval"""
    try:
        # 最直接的读取方式
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        
        # 备选读取方式 (兼容旧格式)
        if not url:
            url = st.secrets.get("supabase", {}).get("url")
        if not key:
            key = st.secrets.get("supabase", {}).get("key")
            
        if not url or not key:
            st.error(f"❌ Credentials Missing. Found keys: {list(st.secrets.keys())}")
            return None
            
        return create_client(url, key)
    except Exception as e:
        st.error(f"⚠️ Supabase Connection Error: {str(e)}")
        return None

supabase: Client = init_supabase()

# ==========================================
# 3. 深度架构模型
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
# 4. 智能引擎 (Socratic State Machine)
# ==========================================

def get_system_prompt(language_mode, phase):
    if language_mode == "English for Investors":
        base_prompt = "You are 'Lingshi' (Spirit & Insight), a Venture Builder AI focused on AI Safety. Reply in ENGLISH."
    else:
        base_prompt = "你是'灵识'，一个专注于 AI 安全的技术产品经理。"

    if phase == "clarifying":
        return base_prompt + " PHASE: AMBIGUITY CHECK. If vague, REFUSE solution. Ask 2-3 multiple-choice questions. End with 'Constraints Aligned' when ready."
    else:
        return base_prompt + " PHASE: ALIGNMENT REACHED. Acknowledge and wait for generation."

def get_chat_response(history, api_key, language_mode, current_phase):
    client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    sys_prompt = get_system_prompt(language_mode, current_phase)
    messages = [{"role": "system", "content": sys_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    response = client.chat.completions.create(model="deepseek-chat", messages=messages, temperature=0.3)
    content = response.choices[0].message.content
    new_phase = "aligned" if "Constraints Aligned" in content else current_phase
    return content, new_phase

def generate_blueprint(history, api_key, language_mode):
    client = instructor.from_openai(openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com"), mode=instructor.Mode.JSON)
    lang_instruction = "Output MUST be in ENGLISH." if language_mode == "English for Investors" else "输出中文。"
    system_prompt = f"You are the Engineering Brain of Lingshi. Generate a deep technical blueprint. {lang_instruction}"
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    return client.chat.completions.create(model="deepseek-chat", response_model=EngineeringSpec, messages=messages)

# ==========================================
# 5. Supabase 数据库操作 (官方库方式)
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
        st.error(f"保存失败: {str(e)}")
        return False

def fetch_recent_projects(limit=5):
    if not supabase: return []
    try:
        response = supabase.table("problem_assets").select("project_name, created_at").order("created_at", desc=True).limit(limit).execute()
        return response.data if response.data else []
    except:
        return []

# ==========================================
# 6. 界面逻辑
# ==========================================

if "messages" not in st.session_state: st.session_state.messages = []
if "blueprint" not in st.session_state: st.session_state.blueprint = None
if "conversation_phase" not in st.session_state: st.session_state.conversation_phase = "clarifying"

with st.sidebar:
    st.title("🌿 Lingshi Protocol")
    language_mode = st.radio("Interface Language", ["Chinese (中文模式)", "English for Investors"])
    st.markdown("---")
    api_key = st.secrets.get("DEEPSEEK_API_KEY", "")
    if not api_key: api_key = st.text_input("DeepSeek Key", type="password")
    if st.button("🔄 Reset / 重置"):
        st.session_state.messages = []; st.session_state.blueprint = None; st.session_state.conversation_phase = "clarifying"; st.rerun()
    st.markdown("---")
    st.subheader("📚 Recent Projects")
    for p in fetch_recent_projects():
        st.markdown(f"<div class='history-item'><div class='history-title'>{p.get('project_name')}</div><div class='history-date'>{p.get('created_at')[:16]}</div></div>", unsafe_allow_html=True)

st.title("灵识 · Socratic Venture Builder")
if st.session_state.conversation_phase == "clarifying":
    st.markdown('<div class="phase-badge phase-clarifying">⚠️ Clarifying Constraints</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="phase-badge phase-aligned">✅ Constraints Aligned</div>', unsafe_allow_html=True)

col_chat, col_blue = st.columns([3, 2], gap="large")

with col_chat:
    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "content": "你好，我是灵识。请描述你观察到的问题。" if "Chinese" in language_mode else "Hello, I am Lingshi. Describe the problem."})
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    if prompt := st.chat_input("Input..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        if api_key:
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    resp, next_phase = get_chat_response(st.session_state.messages, api_key, language_mode, st.session_state.conversation_phase)
                    st.markdown(resp); st.session_state.messages.append({"role": "assistant", "content": resp})
                    if next_phase != st.session_state.conversation_phase:
                        st.session_state.conversation_phase = next_phase; st.rerun()

with col_blue:
    if st.session_state.conversation_phase != "aligned":
        st.button("✨ 生成工程蓝图", disabled=True)
        st.info("💡 Please answer the clarifying questions first.")
    else:
        if st.button("✨ 生成工程蓝图", type="primary", use_container_width=True):
            with st.spinner("Architecting..."):
                try:
                    bp = generate_blueprint(st.session_state.messages, api_key, language_mode)
                    st.session_state.blueprint = bp
                    if save_blueprint_to_supabase(bp, st.session_state.messages, language_mode):
                        st.toast("✅ Saved!"); st.rerun()
                except Exception as e: st.error(str(e))
    if st.session_state.blueprint:
        b = st.session_state.blueprint
        with st.container(border=True):
            st.markdown(f"<div class='blueprint-header'>🚀 {b.project_name}</div>", unsafe_allow_html=True)
            st.markdown(f"*{b.one_liner}*")
            st.info(b.architecture_logic)
            for i, step in enumerate(b.implementation_steps, 1): st.markdown(f"**{i}.** {step}")
            stack_html = "".join([f"<span class='tech-pill'>{item}</span>" for item in b.core_tech_stack])
            st.markdown(stack_html, unsafe_allow_html=True)
