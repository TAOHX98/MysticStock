import streamlit as st
import time
import datetime
from borax.calendars.lunardate import LunarDate

# ==========================================
# 一、 全局视觉与状态管理
# ==========================================

st.set_page_config(
    page_title="玄学推演系统 (纯血架构)",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* 墨砚黑背景及字体颜色 */
    .stApp {
        background-color: #0d0f12; /* 墨砚黑 */
        color: #e0e0e0;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 太极图CSS动画 */
    @keyframes spin { 100% { transform: rotate(360deg); } }
    .taichi-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 40px;
    }
    .taichi {
        box-sizing: border-box;
        width: 250px;
        height: 250px;
        border-radius: 50%;
        background: linear-gradient(to left, #fff 50%, #000 50%);
        border: 2px solid #555;
        animation: spin 5s linear infinite;
        position: relative;
        box-shadow: 0 0 40px rgba(255, 255, 255, 0.1);
    }
    .taichi::before, .taichi::after {
        content: "";
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
        width: 125px;
        height: 125px;
        border-radius: 50%;
    }
    .taichi::before {
        top: 0;
        background: #fff;
        border: 31.25px solid #000;
    }
    .taichi::after {
        bottom: 0;
        background: #000;
        border: 31.25px solid #fff;
    }
    </style>
""", unsafe_allow_html=True)

# 状态管理
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'spiritual_power' not in st.session_state:
    st.session_state.spiritual_power = 20
if 'current_page' not in st.session_state:
    st.session_state.current_page = "main"
if 'deduction_data' not in st.session_state:
    st.session_state.deduction_data = {}
if 'selected_period' not in st.session_state:
    st.session_state.selected_period = "一个月"

# ==========================================
# 二、 底层系统映射表 (全局常量字典)
# ==========================================

# 1. 八卦二进制字典 (自下而上)
BAGUA_DICT = {
    'Qian': [1, 1, 1], 'Dui': [1, 1, 0], 'Li': [1, 0, 1], 'Zhen': [1, 0, 0],
    'Xun': [0, 1, 1], 'Kan': [0, 1, 0], 'Gen': [0, 0, 1], 'Kun': [0, 0, 0]
}

# 2. 洛书数解码字典 (数字 -> 卦象)
LUOSHU_DICT = {
    1: 'Kan', 2: 'Kun', 3: 'Zhen', 4: 'Xun', 5: 'Kun',
    6: 'Qian', 7: 'Dui', 8: 'Gen', 9: 'Li', 0: 'Gen'
}

# 3. 干支解码字典 (干支字符 -> 卦象)
GANZHI_REVERSE_DICT = {
    'Kan': ['癸', '子'],
    'Kun': ['己', '庚', '未'],
    'Zhen': ['甲', '卯'],
    'Xun': ['乙', '辰', '巳'],
    'Qian': ['壬', '戌', '亥'],
    'Dui': ['辛', '酉'],
    'Gen': ['戊', '丑', '寅'],
    'Li': ['丙', '丁', '午']
}
# 为了方便查表，反转一下，变成 字符 -> 卦象
GANZHI_DICT = {}
for gua, chars in GANZHI_REVERSE_DICT.items():
    for char in chars:
        GANZHI_DICT[char] = gua

# 4. 卦象中文显示名
GUA_NAMES = {
    'Qian': '乾 ☰', 'Dui': '兑 ☱', 'Li': '离 ☲', 'Zhen': '震 ☳',
    'Xun': '巽 ☴', 'Kan': '坎 ☵', 'Gen': '艮 ☶', 'Kun': '坤 ☷'
}

# 5. 爻位名称 (初爻 -> 上爻，对应序列的第1~6位)
YAO_NAMES = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻']

# 6. 时间周期与爻位的时间轴映射
PERIOD_PHASE_MAP = {
    "一天": {
        "unit": "日内",
        "phases": ["开盘", "上午盘中", "午间", "下午盘中", "尾盘前段", "收盘"],
    },
    "一周": {
        "unit": "本周",
        "phases": ["周一", "周二", "周三", "周四", "周五上半场", "周五下半场"],
    },
    "一个月": {
        "unit": "本月",
        "phases": ["月初", "上旬末", "中旬初", "中旬末", "下旬初", "月末"],
    },
    "三个月": {
        "unit": "本季度",
        "phases": ["首月初", "首月末", "次月初", "次月末", "末月初", "末月末"],
    },
}


# ==========================================
# 三、 核心推演引擎 (cyber_deduction_engine)
# ==========================================
def get_gua_by_char(char):
    # 如果找不到对应干支，默认给个坤卦（平稳）
    return GANZHI_DICT.get(char, 'Kun')

def cyber_deduction_engine(stock_code, input_date, period="一个月"):
    """
    纯代码数学推演引擎 (6步逻辑)
    基于《洛书》数理与时空干支动态同频映射，完全离线运算。
    """
    # 确保 stock_code 足够长，处理非标准输入
    code_str = str(stock_code).strip()
    if len(code_str) < 6:
        code_str = code_str.zfill(6)

    # --- Step 1: 股票后天卦 (梅花易数·数字起卦) ---
    try:
        # 前3位求和 -> 外卦（上卦）
        front_sum = sum(int(digit) for digit in code_str[:3])
        front_rem = front_sum % 10
        outer_gua = LUOSHU_DICT[front_rem]

        # 后3位求和 -> 内卦（下卦）
        back_sum = sum(int(digit) for digit in code_str[-3:])
        back_rem = back_sum % 10
        inner_gua = LUOSHU_DICT[back_rem]
    except ValueError:
        # 处理包含字母的代码
        outer_gua = 'Qian'
        inner_gua = 'Kun'

    # 拼接为 6 位数组：先内卦（下卦），再外卦（上卦）—— 自下而上
    stock_hex = BAGUA_DICT[inner_gua] + BAGUA_DICT[outer_gua]

    # --- Step 2: 时间卦 (年、月、日干支配卦) ---
    # 使用 borax 将 input_date 转为农历
    lunar = LunarDate.from_solar_date(input_date.year, input_date.month, input_date.day)

    # 提取干支字符 (如 '甲子')
    year_gz = lunar.gz_year
    month_gz = lunar.gz_month
    day_gz = lunar.gz_day

    # 天干=外卦, 地支=内卦。自下而上拼接：先地支（内卦），再天干（外卦）
    year_hex = BAGUA_DICT[get_gua_by_char(year_gz[1])] + BAGUA_DICT[get_gua_by_char(year_gz[0])]
    month_hex = BAGUA_DICT[get_gua_by_char(month_gz[1])] + BAGUA_DICT[get_gua_by_char(month_gz[0])]
    day_hex = BAGUA_DICT[get_gua_by_char(day_gz[1])] + BAGUA_DICT[get_gua_by_char(day_gz[0])]

    # --- Step 3: 年月大环境动能序列 (异或门逻辑) ---
    # 同位阴阳相同 -> 0 (沉寂)；不同 -> 1 (激荡)
    env_seq = [0 if year_hex[i] == month_hex[i] else 1 for i in range(6)]

    # --- Step 4: 初级共振与空亡 ---
    # 股票卦与年月环境序列逐位比对：不同=有效信号(保留股票侧)，相同=空亡(Null)
    primary_seq = [stock_hex[i] if stock_hex[i] != env_seq[i] else None for i in range(6)]

    # --- Step 5: 日建引动与填实空亡 ---
    final_seq = []
    for i in range(6):
        if primary_seq[i] is None:
            # 空亡位：引入日时间卦进行二次校验
            if day_hex[i] == 1 and stock_hex[i] == 1:
                final_seq.append(1)    # 同阳 -> 阳气填实，做多动能
            elif day_hex[i] == 0 and stock_hex[i] == 0:
                final_seq.append(0)    # 同阴 -> 阴气填实，做空动能
            else:
                final_seq.append(None) # 阴阳不同 -> 引动失败，维持空亡
        else:
            final_seq.append(primary_seq[i])

    # ===================================================================
    # Step 6: 定性与定量分析 (生成完整推演报告)
    # ===================================================================
    phase_info = PERIOD_PHASE_MAP.get(period, PERIOD_PHASE_MAP["一个月"])
    phases = phase_info["phases"]

    # ------ 6.1 基础多空判定 ------
    yang_count = final_seq.count(1)
    yin_count = final_seq.count(0)
    null_count = final_seq.count(None)

    if yang_count > yin_count:
        overall_tag = "偏多"
        overall_desc = f"阳气主导（阳×{yang_count} : 阴×{yin_count}），做多动能占优，整体看涨"
    elif yin_count > yang_count:
        overall_tag = "偏空"
        overall_desc = f"阴气偏重（阴×{yin_count} : 阳×{yang_count}），做空动能占优，整体看跌"
    else:
        overall_tag = "震荡"
        overall_desc = f"阴阳均势（阳×{yang_count} : 阴×{yin_count}），多空交织，整体震荡"
    if null_count > 0:
        overall_desc += f"（另有 {null_count} 处空亡位，增加不确定性）"

    # ------ 6.2 特殊形态检测（停滞位 & 物极必反） ------
    # 逐段扫描连续同属性爻（None 打断连续性）
    consecutive_patterns = []
    ci = 0
    while ci < 6:
        cv = final_seq[ci]
        if cv is None:
            ci += 1
            continue
        cj = ci + 1
        while cj < 6 and final_seq[cj] == cv:
            cj += 1
        crun = cj - ci
        if crun >= 2:
            consecutive_patterns.append({
                'start': ci, 'end': cj - 1,
                'value': cv, 'length': crun
            })
        ci = cj

    pattern_warnings = []
    for cp in consecutive_patterns:
        yao_range = '、'.join(YAO_NAMES[cp['start']:cp['end'] + 1])
        if cp['length'] >= 3:
            # 物极必反
            if cp['value'] == 0:
                pattern_warnings.append(
                    f"🚨 **物极必反（极阴生阳）**：{yao_range} 出现连续 {cp['length']} 阴，"
                    f"行情走至极端——**先出清深跌探底，随后强力触底反弹收涨**，切勿恐慌割肉！"
                )
            else:
                pattern_warnings.append(
                    f"🚨 **物极必反（极阳生阴）**：{yao_range} 出现连续 {cp['length']} 阳，"
                    f"行情走至极端——**先急涨拉升冲顶，随后见顶暴跌回落**，切勿盲目追高！"
                )
        else:  # length == 2 -> 停滞位
            if cp['value'] == 0:
                pattern_warnings.append(
                    f"🔍 **停滞位（阴滞）**：{yao_range} 连续 2 阴，"
                    f"空方力量僵持但跌幅有限，该阶段呈筑底震荡、多空拉锯态势。"
                )
            else:
                pattern_warnings.append(
                    f"🔍 **停滞位（阳滞）**：{yao_range} 连续 2 阳，"
                    f"多方力量钝化上攻受阻，该阶段呈高位整理、涨势放缓态势。"
                )

    # ------ 6.3 时间轴逐段走势叙述 ------
    narrative_parts = []
    ni = 0
    nstep = 1
    while ni < 6:
        nv = final_seq[ni]

        # 情形A：空亡位
        if nv is None:
            narrative_parts.append(
                f"{nstep}. **{phases[ni]}**（{YAO_NAMES[ni]}空亡）："
                f"方向不明，处于无序震荡过渡期，多空双方均缺乏有效引导信号。"
            )
            ni += 1
            nstep += 1
            continue

        # 情形B：有值——检测连续同属性
        nj = ni + 1
        while nj < 6 and final_seq[nj] == nv:
            nj += 1
        nrun = nj - ni

        time_label = phases[ni] if nrun == 1 else f"{phases[ni]}～{phases[nj - 1]}"
        yao_label = YAO_NAMES[ni] if nrun == 1 else '、'.join(YAO_NAMES[ni:nj])

        if nrun >= 3:
            # 物极必反
            if nv == 0:
                narrative_parts.append(
                    f"{nstep}. **{time_label}**（{yao_label} 连续 {nrun} 阴）："
                    f"陷入持续下行通道，空方主导。但连续 {nrun} 阴触发 **物极必反** 机制，"
                    f"预判先历经深度杀跌后将迎来强势反弹拉升。"
                )
            else:
                narrative_parts.append(
                    f"{nstep}. **{time_label}**（{yao_label} 连续 {nrun} 阳）："
                    f"进入强势上攻行情，多方主导。但连续 {nrun} 阳触发 **物极必反** 机制，"
                    f"预判先经历急速冲高后将面临重力回调下跌。"
                )
        elif nrun == 2:
            # 停滞位
            if nv == 0:
                narrative_parts.append(
                    f"{nstep}. **{time_label}**（{yao_label} 连续 2 阴）："
                    f"走势偏弱，形成 **停滞位**。下方存在支撑，跌幅有限，"
                    f"多空拉锯呈筑底震荡格局。"
                )
            else:
                narrative_parts.append(
                    f"{nstep}. **{time_label}**（{yao_label} 连续 2 阳）："
                    f"走势偏强，形成 **停滞位**。上方存在压力，涨势放缓，"
                    f"呈高位整理蓄势态势。"
                )
        else:
            # 单爻
            if nv == 1:
                narrative_parts.append(
                    f"{nstep}. **{phases[ni]}**（{YAO_NAMES[ni]}阳）："
                    f"受做多动能驱动，走势偏向上涨，资金入场意愿明确。"
                )
            else:
                narrative_parts.append(
                    f"{nstep}. **{phases[ni]}**（{YAO_NAMES[ni]}阴）："
                    f"受做空动能压制，走势偏向下跌，承压回调风险增大。"
                )

        ni = nj
        nstep += 1

    # ------ 6.4 综合推演结论 ------
    conclusion = f"综合推演，标的 **{code_str}** 在{phase_info['unit']}周期内"
    if overall_tag == "偏多":
        conclusion += "整体受阳气（做多动能）主导，大方向偏向上涨。"
    elif overall_tag == "偏空":
        conclusion += "整体受阴气（做空动能）压制，大方向偏向下跌。"
    else:
        conclusion += "阴阳均势拉扯，大方向处于多空博弈的震荡格局。"

    has_reversal = any(cp['length'] >= 3 for cp in consecutive_patterns)
    has_stagnation = any(cp['length'] == 2 for cp in consecutive_patterns)
    if has_reversal:
        conclusion += "需特别警惕 **物极必反** 节点，行情可能出现剧烈反转，切勿盲目追涨杀跌。"
    if has_stagnation:
        conclusion += "部分阶段存在 **停滞位**，行情钝化期间宜耐心观望，等待方向明朗。"
    if null_count > 0:
        conclusion += f"另有 {null_count} 处空亡位，代表对应时段缺乏有效引导，不确定性较高，需结合盘面实时判断。"

    # ===================================================================
    # 构建完整报告 (Markdown 格式)
    # ===================================================================
    def _fmt(seq):
        """格式化序列，含 Null 显示"""
        return ', '.join('Null' if v is None else str(v) for v in seq)

    report = f"### 🔮 《天机推演纪要：{code_str}》\n\n"
    report += f"**推演基准历法**：农历 {lunar.year}年 {lunar.month}月 {lunar.day}日 "
    report += f"（{year_gz}年 {month_gz}月 {day_gz}日）\n\n"
    report += f"**推演周期**：{period}\n\n"
    report += "---\n\n"

    # 核心矩阵解析表
    report += "#### 📊 核心矩阵解析\n\n"
    report += "| 解码层级 | 内卦（下卦） | 外卦（上卦） |\n"
    report += "|:--------:|:----------:|:----------:|\n"
    report += f"| 标的卦位 | {GUA_NAMES[inner_gua]} | {GUA_NAMES[outer_gua]} |\n"
    report += f"| 年时间卦 | {GUA_NAMES[get_gua_by_char(year_gz[1])]} | {GUA_NAMES[get_gua_by_char(year_gz[0])]} |\n"
    report += f"| 月时间卦 | {GUA_NAMES[get_gua_by_char(month_gz[1])]} | {GUA_NAMES[get_gua_by_char(month_gz[0])]} |\n"
    report += f"| 日时间卦 | {GUA_NAMES[get_gua_by_char(day_gz[1])]} | {GUA_NAMES[get_gua_by_char(day_gz[0])]} |\n\n"

    # 各级序列展示
    report += f"- **股票后天卦序列**：`[{', '.join(map(str, stock_hex))}]`\n"
    report += f"- **年月动能序列**：`[{', '.join(map(str, env_seq))}]`\n"
    report += f"- **初级共振序列**：`[{_fmt(primary_seq)}]`\n"
    report += f"- **终极过滤序列**：`[{_fmt(final_seq)}]`\n\n"
    report += "---\n\n"

    # 整体多空研判
    report += "#### ⚖️ 整体多空研判\n\n"
    report += f"**磁场定性**：【{overall_tag}】{overall_desc}\n\n"

    # 特殊形态预警
    if pattern_warnings:
        report += "---\n\n"
        report += "#### 🚨 特殊形态预警\n\n"
        for pw in pattern_warnings:
            report += f"- {pw}\n"
        report += "\n"

    # 阶段走势推演
    report += "---\n\n"
    report += f"#### 📈 阶段走势推演（{phase_info['unit']}时间轴）\n\n"
    report += (f"> 终极序列从初爻（第1位）至上爻（第6位），严格对应"
               f"{phase_info['unit']}周期的时间流逝过程。\n\n")
    for part in narrative_parts:
        report += f"{part}\n\n"

    # 综合结论
    report += "---\n\n"
    report += "#### 💡 综合推演结论\n\n"
    report += conclusion + "\n\n"
    report += "---\n\n"
    report += ("*批注：推演序列基于《洛书》数理与时空干支动态同频映射生成，"
               "纯代码离线运算闭环。天机不可泄露殆尽，仅供参考。*\n")

    return report

# ==========================================
# 四、 登录/注册页
# ==========================================
def render_login_page():
    st.markdown("<h1 style='text-align: center; margin-bottom: 50px;'>☯️ 纯血玄学股票推演系统</h1>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("""
            <div class="taichi-container">
                <div class="taichi"></div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("""
            <p style='text-align: center; color: #888; font-size: 16px; margin-top: 20px;'>
                🌌 本土易经内核 | 📈 洛书数理模型 | ⚛️ 告别外部API依赖
            </p>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("### 欢迎进入系统")
        tab_login, tab_register = st.tabs(["🔑 登录", "📝 注册"])
        
        with tab_login:
            st.text_input("邮箱/账号", placeholder="admin@mystic.com")
            st.text_input("密码", type="password", placeholder="请输入密码")
            if st.button("登录", use_container_width=True, type="primary"):
                st.session_state.logged_in = True
                st.session_state.current_page = "main"
                st.rerun()
                
        with tab_register:
            st.text_input("注册邮箱", placeholder="请输入常用邮箱")
            st.text_input("设置密码", type="password")
            st.text_input("确认密码", type="password")
            if st.button("注册", use_container_width=True):
                st.success("注册功能已开放，请直接登录测试。")

# ==========================================
# 五、 主控制台页面
# ==========================================
def render_main_page():
    # 顶部导航栏
    nav_col1, nav_col2, nav_col3, nav_spacer, nav_power, nav_logout = st.columns([1, 1, 1, 3, 2, 1])
    with nav_col1: st.markdown("<div style='padding-top:10px;'>🏠 首页</div>", unsafe_allow_html=True)
    with nav_col2: st.markdown("<div style='padding-top:10px;'>📊 数据回测</div>", unsafe_allow_html=True)
    with nav_col3: st.markdown("<div style='padding-top:10px;'>⚙️ 回测控制台</div>", unsafe_allow_html=True)
    
    with nav_power:
        st.markdown(f"<div style='text-align: right; padding-top: 10px; font-size: 18px; font-weight: bold; color: #00FFCC;'>✨ 剩余灵力：{st.session_state.spiritual_power}</div>", unsafe_allow_html=True)
        
    with nav_logout:
        if st.button("退出", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
            
    st.divider()

    st.markdown("<h2 style='text-align: center;'>🤖 纯血代码数学推演引擎</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #777;'>⚠️ 免责声明：本引擎基于洛书及干支历法完全离线推演，不依赖任何外部行情API。</p>", unsafe_allow_html=True)
    st.write("")

    st.markdown("#### ⏳ 推演时间跨度")
    period_options = ["一天", "一周", "一个月", "三个月"]
    default_idx = period_options.index(st.session_state.selected_period) if st.session_state.selected_period in period_options else 2
    
    selected = st.radio(
        "选择时间跨度",
        period_options,
        index=default_idx,
        horizontal=True,
        label_visibility="collapsed"
    )
    st.session_state.selected_period = selected
    st.write("---")

    st.markdown("#### 🔮 核心推演控制区")
    card_col1, card_col2, card_col3, card_col4 = st.columns(4)
    with card_col1: st.info("🛡️ 风险管理模型")
    with card_col2: st.success("📈 交易策略生成")
    with card_col3: st.warning("📊 技术分析指标")
    with card_col4: st.error("💰 资金仓位管理")
    
    st.write("")
    
    input_col1, input_col2 = st.columns(2)
    with input_col1:
        target_date = st.date_input("基准日期", datetime.date.today())
    with input_col2:
        symbol_input = st.text_input("标的代码 (支持数字字母)", placeholder="如：600519 或 AAPL", value="")
        
    st.write("")
    
    # 纯血引擎推演逻辑
    if st.button("🚀 开始推演", type="primary", use_container_width=True):
        if not symbol_input:
            st.warning("⚠️ 请输入标的代码！")
            return
            
        if st.session_state.spiritual_power >= 1:
            with st.spinner("起卦中... 正在剥离表象，洞察时空干支共振..."):
                time.sleep(1.5) # 模拟深邃的推演过程
                
                # 调用纯血离线引擎，传入用户选择的推演周期
                report_text = cyber_deduction_engine(
                    symbol_input, target_date, st.session_state.selected_period
                )
                
                # 扣除灵力
                st.session_state.spiritual_power -= 1
                
                # 保存上下文数据
                st.session_state.deduction_data = {
                    "symbol": symbol_input,
                    "date": target_date,
                    "report": report_text
                }
                # 跳转结果页
                st.session_state.current_page = "result"
                st.rerun()
        else:
            st.error("❌ 灵力不足，请充值！")

# ==========================================
# 六、 纯文本解盘结果页 (render_result_page)
# ==========================================
def render_result_page():
    # 顶部操作区
    top_col1, top_col2 = st.columns([1, 1])
    with top_col1:
        if st.button("⬅️ 返回重新推演", use_container_width=False):
            st.session_state.current_page = "main"
            st.rerun()
    with top_col2:
        st.markdown(f"<div style='text-align: right; padding-top: 5px; font-size: 18px; font-weight: bold; color: #00FFCC;'>✨ 剩余灵力：{st.session_state.spiritual_power}</div>", unsafe_allow_html=True)
        
    st.divider()
    
    data = st.session_state.deduction_data
    symbol = data.get("symbol", "未知标的")
    report = data.get("report", "天机被蒙蔽，未获得有效报告。")
    
    st.markdown(f"<h1 style='text-align: center; color: #ff4b4b; margin-bottom: 40px;'>标的 {symbol} 勘验录</h1>", unsafe_allow_html=True)
    
    # 使用优雅的卡片包裹报告
    st.success("天机已破译，解盘报告如下：")
    
    # 直接使用 st.markdown 渲染报告（正确处理 Markdown 语法）
    st.markdown(report)
    
    st.write("")
    st.info("注：上述结果完全由代码数学模型离线推演生成。如需对比其他时间线，请返回重新推演。")

# ==========================================
# 七、 主路由控制
# ==========================================
if __name__ == "__main__":
    if not st.session_state.logged_in:
        render_login_page()
    else:
        if st.session_state.current_page == "main":
            render_main_page()
        elif st.session_state.current_page == "result":
            render_result_page()
        else:
            st.session_state.current_page = "main"
            st.rerun()
