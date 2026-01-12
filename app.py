import streamlit as st
import openai
import instructor
from pydantic import BaseModel, Field
from typing import List

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
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 深度架构模型 (解决文档太简略的问题)
# ==========================================
class EngineeringSpec(BaseModel):
    project_name: str = Field(..., description="Project Name (Creative & Catchy)")
    one_liner: str = Field(..., description="A single sentence explaining the value prop.")
    
    # 核心升级：增加实施步骤
    architecture_logic: str = Field(..., description="Explain the system data flow clearly.")
    implementation_steps: List[str] = Field(..., description="5 concrete steps to build the MVP (Step 1, Step 2...).")
    
    core_tech_stack: List[str] = Field(..., description="Specific libraries/tools (e.g., PyTorch, React, AWS Lambda).")
    
    # 核心升级：增加风险分析
    critical_risks: str = Field(..., description="What is the biggest technical bottleneck?")
    
    estimated_budget: str = Field(..., description="Time & Cost estimation.")

# ==========================================
# 3. 智能引擎 (支持双语)
# ==========================================

def get_system_prompt(language_mode):
    if language_mode == "English for Investors":
        return """
        You are 'Lingshi' (Spirit & Insight), a Venture Builder AI.
        
        **CRITICAL RULE**: No matter what language the user speaks, you MUST reply and ask questions in **ENGLISH**.
        
        Your Goal: Turn the user's raw field notes into a high-level technical product spec.
        Behavior:
        1. Act like a pragmatic Product Manager.
        2. Ask clarifying questions about logic, frequency, and current workarounds.
        3. Do NOT talk about feelings. Talk about SYSTEMS.
        """
    else:
        return """
        你是‘灵识’，一个务实的技术产品经理。
        目标：将用户的观察转化为技术需求。
        行为：
        1. 拒绝煽情，关注业务逻辑、频率、现有替代方案。
        2. 每次只问一个核心问题。
        """

def get_chat_response(history, api_key, language_mode):
    client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    sys_prompt = get_system_prompt(language_mode)
    messages = [{"role": "system", "content": sys_prompt}]
    
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0.5
    )
    return response.choices[0].message.content

def generate_blueprint(history, api_key, language_mode):
    client = instructor.from_openai(
        openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com"),
        mode=instructor.Mode.JSON
    )
    
    # 强制蓝图无论如何都用英文生成（如果选了英文模式）
    lang_instruction = "Output MUST be in ENGLISH." if language_mode == "English for Investors" else "输出中文。"
    
    system_prompt = f"""
    You are the Engineering Brain of Lingshi. Generate a deep, detailed technical blueprint.
    {lang_instruction}
    
    Requirements:
    1. 'implementation_steps' must be detailed (e.g., 'Step 1: Scrape data using Selenium...').
    2. 'architecture_logic' should describe how data moves.
    3. Be specific about tech stack (naming specific libraries).
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
# 4. 界面逻辑
# ==========================================

# 初始化
if "messages" not in st.session_state:
    st.session_state.messages = []
if "blueprint" not in st.session_state:
    st.session_state.blueprint = None

# --- 侧边栏 ---
with st.sidebar:
    st.title("🌿 Lingshi Protocol")
    
    # 语言切换器
    language_mode = st.radio(
        "Interface Language",
        ["Chinese (中文模式)", "English for Investors"],
        index=0
    )
    
    st.markdown("---")
    
    # === 关键修改：智能兼容模式 ===
    # 初始化 api_key 为空
    api_key = ""
    
    # 1. 尝试从云端/本地秘密里拿 Key (加了 try-except 就不怕报错了)
    try:
        if "DEEPSEEK_API_KEY" in st.secrets:
            api_key = st.secrets["DEEPSEEK_API_KEY"]
            st.success("✅ License Active (Sponsor Mode)") 
    except Exception:
        # 如果本地没有配置 secrets.toml，这里会报错，但我们用 pass 跳过，假装无事发生
        pass

    # 2. 如果上面没拿到 Key（说明是在本地，或者云端没配好），显示输入框
    if not api_key:
        api_key = st.text_input("DeepSeek Key", type="password")
        if not api_key:
            st.info("请输入 Key 开始使用")
    
    # 重置按钮
    if st.button("🔄 Reset / 重置"):
        st.session_state.messages = []
        st.session_state.blueprint = None
        st.rerun()

# --- 主区域 ---
st.title("灵识 · Venture Builder Agent")
if language_mode == "English for Investors":
    st.caption("Translating Tacit Knowledge into Engineering Assets.")
else:
    st.caption("从田野笔记到工程蓝图")

col_chat, col_blue = st.columns([3, 2], gap="large")

# 左侧：聊天
with col_chat:
    if not st.session_state.messages:
        first_msg = "你好，我是灵识。请告诉我你的发现..." if "Chinese" in language_mode else "Hello, I am Lingshi. Tell me about your field observation..."
        st.session_state.messages.append({"role": "assistant", "content": first_msg})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    placeholder = "输入观察..." if "Chinese" in language_mode else "Type your observation here..."
    if prompt := st.chat_input(placeholder):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        if api_key:
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    # 传入语言模式
                    resp = get_chat_response(st.session_state.messages, api_key, language_mode)
                    st.markdown(resp)
                    st.session_state.messages.append({"role": "assistant", "content": resp})

# 右侧：蓝图
with col_blue:
    btn_text = "✨ 生成工程蓝图" if "Chinese" in language_mode else "✨ Generate Blueprint"
    
    if st.button(btn_text, type="primary", use_container_width=True):
        if not api_key:
            st.warning("API Key Required")
        elif len(st.session_state.messages) < 2:
            st.warning("Needs more context.")
        else:
            with st.spinner("Architecting..."):
                try:
                    bp = generate_blueprint(st.session_state.messages, api_key, language_mode)
                    st.session_state.blueprint = bp
                except Exception as e:
                    st.error(str(e))

    if st.session_state.blueprint:
        b = st.session_state.blueprint
        
        with st.container(border=True):
            st.markdown(f"<div class='blueprint-header'>🚀 {b.project_name}</div>", unsafe_allow_html=True)
            st.markdown(f"*{b.one_liner}*")
            
            st.markdown("---")
            
            # 逻辑架构
            st.markdown("**🧠 System Logic:**")
            st.info(b.architecture_logic)
            
            # 实施步骤 (这是为了解决'太简略'的问题)
            st.markdown("**📅 Implementation Roadmap:**")
            for i, step in enumerate(b.implementation_steps, 1):
                st.markdown(f"**{i}.** {step}")
            
            st.markdown("---")
            
            # 技术栈
            st.markdown("**🛠 Tech Stack:**")
            stack_html = "".join([f"<span class='tech-pill'>{item}</span>" for item in b.core_tech_stack])
            st.markdown(stack_html, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 风险与预算
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**⚠️ Critical Risk:**")
                st.markdown(f"<small>{b.critical_risks}</small>", unsafe_allow_html=True)
            with col2:
                st.markdown("**💰 Budget:**")
                st.markdown(f"<small>{b.estimated_budget}</small>", unsafe_allow_html=True)
