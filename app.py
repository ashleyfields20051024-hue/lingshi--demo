import streamlit as st
import openai
import instructor
from pydantic import BaseModel, Field
from typing import List
import json
from datetime import datetime
from st_supabase_connection import SupabaseConnection, execute_query

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
# 2. Supabase 连接初始化
# ==========================================
@st.cache_resource
def init_supabase():
    """Initialize Supabase connection using Streamlit Secrets"""
    return st.connection(
        name="supabase",
        type=SupabaseConnection
    )

supabase = init_supabase()

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
        base_prompt = """
        You are 'Lingshi' (Spirit & Insight), a Venture Builder AI focused on AI Safety and Engineering Precision.
        **CRITICAL RULE**: Reply and ask questions in **ENGLISH**.
        """
    else:
        base_prompt = """
        你是'灵识'，一个专注于 AI 安全和工程精准度的技术产品经理。
        """

    if phase == "clarifying":
        if language_mode == "English for Investors":
            return base_prompt + """
            **PHASE: AMBIGUITY CHECK (The Guardrail)**
            Your Goal: Analyze if the user's problem description is specific enough to build an engineering spec.
            Behavior:
            1. If the input is vague, REFUSE to offer a solution.
            2. Instead, generate 2-3 specific, multiple-choice questions to clarify constraints (e.g., scale, frequency, technical environment).
            3. Do NOT talk about feelings. Talk about SYSTEMS.
            4. When you feel you have enough information, you MUST end your message with the exact phrase: "Constraints Aligned."
            """
        else:
            return base_prompt + """
            **阶段：歧义检查（护栏）**
            目标：分析用户的描述是否足够具体以构建工程规格。
            行为：
            1. 如果输入模糊，拒绝提供解决方案。
            2. 生成 2-3 个具体的选择题来澄清约束（例如：频率、规模、现有环境）。
            3. 每次只关注系统逻辑。
            4. 当你认为信息足够时，必须在回复末尾加上： "Constraints Aligned."
            """
    else:
        # Aligned phase
        if language_mode == "English for Investors":
            return base_prompt + """
            **PHASE: ALIGNMENT REACHED**
            The constraints are clear. You are now ready to help the user generate the final blueprint.
            Acknowledge the alignment and wait for the user to trigger the generation.
            """
        else:
            return base_prompt + """
            **阶段：对齐完成**
            约束已明确。你现在准备好帮助用户生成最终蓝图。
            确认对齐并等待用户触发生成。
            """

def get_chat_response(history, api_key, language_mode, current_phase):
    client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    sys_prompt = get_system_prompt(language_mode, current_phase)
    messages = [{"role": "system", "content": sys_prompt}]
    
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0.3 # Lower temperature for more precise elicitation
    )
    content = response.choices[0].message.content
    
    # Check for phase transition
    new_phase = current_phase
    if "Constraints Aligned" in content:
        new_phase = "aligned"
        
    return content, new_phase

def generate_blueprint(history, api_key, language_mode):
    client = instructor.from_openai(
        openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com"),
        mode=instructor.Mode.JSON
    )
    
    lang_instruction = "Output MUST be in ENGLISH." if language_mode == "English for Investors" else "输出中文。"
    
    system_prompt = f"""
    You are the Engineering Brain of Lingshi. Generate a deep, detailed technical blueprint based on the ALIGNED constraints.
    {lang_instruction}
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    return client.chat.completions.create(
        model="deepseek-chat",
        response_model=EngineeringSpec,
        messages=messages
    )

# ==========================================
# 5. Supabase 数据库操作
# ==========================================

def save_blueprint_to_supabase(blueprint: EngineeringSpec, messages: List[dict], language_mode: str):
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
        
        execute_query(supabase.table("problem_assets").insert(data), ttl=0)
        return True
    except Exception as e:
        st.error(f"保存失败: {str(e)}")
        return False

def fetch_recent_projects(limit=5):
    try:
        response = execute_query(
            supabase.table("problem_assets")
            .select("project_name, created_at")
            .order("created_at", desc=True)
            .limit(limit),
            ttl=0
        )
        return response.data if response.data else []
    except Exception as e:
        st.error(f"加载历史记录失败: {str(e)}")
        return []

# ==========================================
# 6. 界面逻辑
# ==========================================

# 初始化
if "messages" not in st.session_state:
    st.session_state.messages = []
if "blueprint" not in st.session_state:
    st.session_state.blueprint = None
if "conversation_phase" not in st.session_state:
    st.session_state.conversation_phase = "clarifying"

# --- 侧边栏 ---
with st.sidebar:
    st.title("🌿 Lingshi Protocol")
    
    language_mode = st.radio(
        "Interface Language",
        ["Chinese (中文模式)", "English for Investors"],
        index=0
    )
    
    st.markdown("---")
    
    api_key = ""
    try:
        if "DEEPSEEK_API_KEY" in st.secrets:
            api_key = st.secrets["DEEPSEEK_API_KEY"]
            st.success("✅ License Active") 
    except Exception:
        pass

    if not api_key:
        api_key = st.text_input("DeepSeek Key", type="password")
    
    if st.button("🔄 Reset / 重置"):
        st.session_state.messages = []
        st.session_state.blueprint = None
        st.session_state.conversation_phase = "clarifying"
        st.rerun()
    
    st.markdown("---")
    st.subheader("📚 Recent Projects")
    recent_projects = fetch_recent_projects(5)
    if recent_projects:
        for project in recent_projects:
            st.markdown(f"""
            <div class='history-item'>
                <div class='history-title'>{project.get('project_name', 'Untitled')}</div>
                <div class='history-date'>{project.get('created_at', '')[:16]}</div>
            </div>
            """, unsafe_allow_html=True)

# --- 主区域 ---
st.title("灵识 · Socratic Venture Builder")
st.caption("AI Safety Mode: Enforcing Constraint Alignment before Engineering.")

# 状态指示器
if st.session_state.conversation_phase == "clarifying":
    st.markdown('<div class="phase-badge phase-clarifying">⚠️ Clarifying Constraints</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="phase-badge phase-aligned">✅ Constraints Aligned</div>', unsafe_allow_html=True)

col_chat, col_blue = st.columns([3, 2], gap="large")

# 左侧：聊天
with col_chat:
    if not st.session_state.messages:
        first_msg = "你好，我是灵识。请描述你观察到的问题，我将协助你进行约束对齐。" if "Chinese" in language_mode else "Hello, I am Lingshi. Describe the problem you observed, and I will help you align constraints."
        st.session_state.messages.append({"role": "assistant", "content": first_msg})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Input observation..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        if api_key:
            with st.chat_message("assistant"):
                with st.spinner("Analyzing Constraints..."):
                    resp, next_phase = get_chat_response(
                        st.session_state.messages, 
                        api_key, 
                        language_mode, 
                        st.session_state.conversation_phase
                    )
                    st.markdown(resp)
                    st.session_state.messages.append({"role": "assistant", "content": resp})
                    
                    if next_phase != st.session_state.conversation_phase:
                        st.session_state.conversation_phase = next_phase
                        st.rerun()

# 右侧：蓝图
with col_blue:
    is_aligned = st.session_state.conversation_phase == "aligned"
    btn_text = "✨ 生成工程蓝图" if "Chinese" in language_mode else "✨ Generate Blueprint"
    
    # 按钮逻辑：仅在对齐后启用
    if not is_aligned:
        st.button(btn_text, disabled=True, help="Need more details. Please answer the clarifying questions first.")
        st.info("💡 **Why is this disabled?** To ensure AI Safety, we require a clear understanding of system constraints before architecting solutions.")
    else:
        if st.button(btn_text, type="primary", use_container_width=True):
            with st.spinner("Architecting..."):
                try:
                    bp = generate_blueprint(st.session_state.messages, api_key, language_mode)
                    st.session_state.blueprint = bp
                    if save_blueprint_to_supabase(bp, st.session_state.messages, language_mode):
                        st.toast("✅ Asset Minted & Saved on Protocol!")
                        st.rerun()
                except Exception as e:
                    st.error(str(e))

    if st.session_state.blueprint:
        b = st.session_state.blueprint
        with st.container(border=True):
            st.markdown(f"<div class='blueprint-header'>🚀 {b.project_name}</div>", unsafe_allow_html=True)
            st.markdown(f"*{b.one_liner}*")
            st.markdown("---")
            st.markdown("**🧠 System Logic:**")
            st.info(b.architecture_logic)
            st.markdown("**📅 Implementation Roadmap:**")
            for i, step in enumerate(b.implementation_steps, 1):
                st.markdown(f"**{i}.** {step}")
            st.markdown("---")
            st.markdown("**🛠 Tech Stack:**")
            stack_html = "".join([f"<span class='tech-pill'>{item}</span>" for item in b.core_tech_stack])
            st.markdown(stack_html, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**⚠️ Critical Risk:**")
                st.markdown(f"<small>{b.critical_risks}</small>", unsafe_allow_html=True)
            with col2:
                st.markdown("**💰 Budget:**")
                st.markdown(f"<small>{b.estimated_budget}</small>", unsafe_allow_html=True)
