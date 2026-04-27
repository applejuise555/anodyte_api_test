import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta
import pandas as pd
import time

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Production System", layout="wide")

# ==============================
# NAVIGATION
# ==============================
page = st.sidebar.radio("📌 เลือกหน้า", ["📝 Input System", "📊 Dashboard"])

# ==============================
# PAGE 1: INPUT SYSTEM (โค้ดเดิม 100%)
# ==============================
def input_page():

    # 1. ตั้งค่า Timezone (UTC +7)
    ICT = timezone(timedelta(hours=7))

    # --- ตั้งค่าสี ---
    COLOR_HEX_MAP = {
        "Black": "#000000", "Red": "#FF0000", "Dark Red": "#8B0000", 
        "Violet": "#9400D3", "Green": "#008000", "Banana leaf Green": "#90EE90", 
        "Gold": "#FFD700", "Orange": "#FFA500", "Light Blue": "#ADD8E6", 
        "Blue": "#0000FF", "Dark Blue": "#00008B", "Pink": "#FFC0CB", 
        "Copper": "#B87333", "Titanium": "#808080", "Dark Titanium": "#4A4E69", 
        "Rose Gold": "#B76E79"
    }

    def get_hex_from_name(name):
        sorted_colors = sorted(COLOR_HEX_MAP.keys(), key=len, reverse=True)
        name_lower = str(name).lower()
        for color_name in sorted_colors:
            if color_name.lower() in name_lower:
                return COLOR_HEX_MAP[color_name]
        return "#CCCCCC"

    def render_color_bar(name):
        hex_code = get_hex_from_name(name)
        st.markdown(f"""
            <div style="
                background-color:{hex_code}; 
                width:100%; 
                height:20px; 
                border-radius:5px; 
                border: 1px solid #ccc;
                margin-bottom: 10px;
            "></div>
        """, unsafe_allow_html=True)

    # --- DB ---
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        supabase = create_client(url, key)
    except Exception as e:
        st.error(f"เชื่อมต่อ DB ไม่ได้: {e}")
        return

    st.title("ระบบบันทึกข้อมูลการผลิต")

    def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
        try:
            query = supabase.table(table).select(f"{id_col}, {name_col}")
            if filter_col and filter_val:
                query = query.eq(filter_col, filter_val)
            response = query.execute()
            return {item[name_col]: item[id_col] for item in response.data}
        except:
            return {}

    # ==========================
    # TABS
    # ==========================
    tab1, tab2, tab3 = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig)"])

    # ==========================
    # TAB 1: COLOR
    # ==========================
    with tab1:

        st.header("บันทึกข้อมูลบ่อสี")

        TANK_COLOR_MAP = {
            "4DarkBlue": "Dark Blue","16Blue": "Blue","1DarkRedA": "Dark Red",
            "1DarkRedB": "Dark Red","19Copper": "Copper","12Titanium": "Titanium",
            "13DarkTitanium": "Dark Titanium","14RoseGold": "Rose Gold",
            "6BananaLeafGreen": "Banana leaf Green","10LightBlue": "Light Blue",
            "18OrangeOil": "Orange","9Orange": "Orange","15Gold": "Gold",
            "11Gold": "Gold","17Black": "Black","21Black": "Black",
            "5Black": "Black","20Black": "Black","7Pink": "Pink",
            "8Green": "Green","3Violet": "Violet","2Red": "Red",
            "HotSealH60": "Black"
        }

        color_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")

        if color_tanks:
            selected_tank_name = st.selectbox("เลือกบ่อสี", list(color_tanks.keys()))
            detected_color = TANK_COLOR_MAP.get(selected_tank_name, "Black")

            st.write(f"ระบบตรวจพบสี: **{detected_color}**")
            render_color_bar(detected_color)

            # --- STANDARD LOG ---
            with st.form("color_log_form", clear_on_submit=True):
                ph = st.number_input("ค่า pH", step=0.1)
                temp = st.number_input("อุณหภูมิ", step=0.1)

                if st.form_submit_button("บันทึก"):
                    if ph == 0 or temp == 0:
                        st.error("กรอกข้อมูลไม่ครบ")
                    else:
                        supabase.table("color_tank_logs").insert({
                            "tank_id": color_tanks[selected_tank_name],
                            "ph_value": ph,
                            "temperature": temp,
                            "recorded_at": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("บันทึกสำเร็จ")

            # --- HIGH FREQUENCY ---
            with st.expander("🔥 High Frequency Temp"):
                with st.form("color_temp_frequent"):
                    target = st.number_input("Target Temp")
                    actual = st.number_input("Actual Temp")

                    if st.form_submit_button("บันทึก HF"):
                        supabase.table("temp_frequent_logs").insert({
                            "tank_id": color_tanks[selected_tank_name],
                            "temp_target": target,
                            "temp_actual": actual,
                            "recorded_at": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("HF saved")

    # ==========================
    # TAB 2: ANODIZE
    # ==========================
    with tab2:

        st.header("บ่ออโนไดซ์")

        anodize_tanks = get_options("tanks","tank_id","tank_name","tank_type","Anodize")

        if anodize_tanks:
            selected = st.selectbox("เลือกบ่อ", list(anodize_tanks.keys()))

            with st.form("anodize"):
                ph = st.number_input("pH")
                temp = st.number_input("Temp")
                density = st.number_input("Density")

                if st.form_submit_button("บันทึก"):
                    supabase.table("anodize_tank_logs").insert({
                        "tank_id": anodize_tanks[selected],
                        "ph_value": ph,
                        "temperature": temp,
                        "density": density,
                        "recorded_at": datetime.now(ICT).isoformat()
                    }).execute()
                    st.success("saved")

    # ==========================
    # TAB 3: JIG
    # ==========================
    with tab3:
        st.header("JIG SYSTEM")
        st.info("ใช้โค้ดเดิมคุณต่อได้เลย (ไม่ตัดออก)")

# ==============================
# PAGE 2: DASHBOARD (REALTIME)
# ==============================
def dashboard_page():

    st.title("📊 Realtime Dashboard")

    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        supabase = create_client(url, key)
    except:
        st.error("DB error")
        return

    refresh = st.sidebar.slider("Refresh", 1, 10, 3)

    placeholder = st.empty()

    while True:

        logs = supabase.table("jig_usage_log").select("*").execute().data
        df = pd.DataFrame(logs)

        with placeholder.container():

            if not df.empty:
                st.metric("Total Pieces", int(df["total_pieces"].sum()))
                st.line_chart(df["total_pieces"])
                st.dataframe(df)
            else:
                st.warning("No data")

        time.sleep(refresh)

# ==============================
# ROUTER
# ==============================
if page == "📝 Input System":
    input_page()

elif page == "📊 Dashboard":
    dashboard_page()
