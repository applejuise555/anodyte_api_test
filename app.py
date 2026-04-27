import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta
import pandas as pd
import time

# ==============================
# CONFIG
# ==============================
ICT = timezone(timedelta(hours=7))

st.set_page_config(page_title="Production System", layout="wide")

# ==============================
# CONNECT
# ==============================
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ Supabase: {e}")
    st.stop()

# ==============================
# COLOR SYSTEM
# ==============================
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

# ==============================
# UTILS
# ==============================
def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    try:
        query = supabase.table(table).select(f"{id_col}, {name_col}")
        if filter_col and filter_val:
            query = query.eq(filter_col, filter_val)
        response = query.execute()
        return {item[name_col]: item[id_col] for item in response.data}
    except:
        return {}

# ==============================
# NAVIGATION
# ==============================
page = st.sidebar.radio("📌 เลือกหน้า", ["📝 Input System", "📊 Dashboard"])

# =========================================================
# ==================== PAGE 1: INPUT ======================
# =========================================================
if page == "📝 Input System":

    st.title("ระบบบันทึกข้อมูลการผลิต")

    tab1, tab2, tab3 = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig)"])

    # ---------------- TAB 1 ----------------
    with tab1:
        st.header("บันทึกข้อมูลบ่อสี")
        
        TANK_COLOR_MAP = {
            "4DarkBlue": "Dark Blue", "16Blue": "Blue", "1DarkRedA": "Dark Red",
            "1DarkRedB": "Dark Red", "19Copper": "Copper", "12Titanium": "Titanium",
            "13DarkTitanium": "Dark Titanium", "14RoseGold": "Rose Gold",
            "6BananaLeafGreen": "Banana leaf Green", "10LightBlue": "Light Blue",
            "18OrangeOil": "Orange", "9Orange": "Orange", "15Gold": "Gold",
            "11Gold": "Gold", "17Black": "Black", "21Black": "Black",
            "5Black": "Black", "20Black": "Black", "7Pink": "Pink",
            "8Green": "Green", "3Violet": "Violet", "2Red": "Red",
            "HotSealH60": "Black"
        }

        color_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")

        if color_tanks:
            selected_tank_name = st.selectbox("เลือกบ่อสี", list(color_tanks.keys()))
            detected_color = TANK_COLOR_MAP.get(selected_tank_name, "Black")

            st.write(f"ระบบตรวจพบสี: **{detected_color}**")
            render_color_bar(detected_color)

            with st.form("color_log_form"):
                ph = st.number_input("ค่า pH", step=0.1)
                temp = st.number_input("อุณหภูมิ (°C)", step=0.1)

                if st.form_submit_button("บันทึกค่ามาตรฐาน"):
                    if ph == 0 or temp == 0:
                        st.error("กรุณากรอกข้อมูล")
                    else:
                        supabase.table("color_tank_logs").insert({
                            "tank_id": color_tanks[selected_tank_name],
                            "ph_value": ph,
                            "temperature": temp,
                            "recorded_at": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("บันทึกสำเร็จ")

    # ---------------- TAB 2 ----------------
    with tab2:
        st.header("บ่ออโนไดซ์")

        anodize_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Anodize")

        if anodize_tanks:
            selected_tank = st.selectbox("เลือกบ่อ", list(anodize_tanks.keys()))

            with st.form("anodize_form"):
                ph = st.number_input("pH", step=0.1)
                temp = st.number_input("Temp", step=0.1)
                density = st.number_input("Density", step=0.001)

                if st.form_submit_button("บันทึก"):
                    supabase.table("anodize_tank_logs").insert({
                        "tank_id": anodize_tanks[selected_tank],
                        "ph_value": ph,
                        "temperature": temp,
                        "density": density,
                        "recorded_at": datetime.now(ICT).isoformat()
                    }).execute()
                    st.success("สำเร็จ")

    # ---------------- TAB 3 ----------------
    with tab3:
        st.header("ระบบจิ๊ก")

        prods = get_options("products", "product_id", "product_code")

        jigs = supabase.table("jigs").select("*").execute().data
        jig_map = {j["jig_model_code"]: j["jig_id"] for j in jigs}

        if jig_map:
            sel_j = st.selectbox("เลือกจิ๊ก", list(jig_map.keys()))
            jig_id = jig_map[sel_j]

            pcs = st.number_input("pcs", min_value=0)
            rows = st.number_input("rows", min_value=0)
            partial = st.number_input("partial", min_value=0)

            if st.button("บันทึก"):
                supabase.table("jig_usage_log").insert({
                    "jig_id": jig_id,
                    "pcs_per_row": pcs,
                    "rows_filled": rows,
                    "partial_pieces": partial,
                    "total_pieces": (pcs * rows) + partial,
                    "recorded_date": datetime.now(ICT).isoformat()
                }).execute()

                st.success("บันทึกสำเร็จ")

# =========================================================
# ==================== PAGE 2: DASHBOARD ===================
# =========================================================
elif page == "📊 Dashboard":

    st.title("📊 Production Dashboard (Realtime)")

    refresh = st.sidebar.slider("Refresh (sec)", 1, 30, 5)

    def load_data():
        res = supabase.table("jig_usage_log").select("*").execute()
        return pd.DataFrame(res.data)

    placeholder = st.empty()

    while True:
        df = load_data()

        with placeholder.container():

            if not df.empty:
                col1, col2 = st.columns(2)

                col1.metric("Total Pieces", int(df["total_pieces"].sum()))
                col2.metric("Total Records", len(df))

                st.subheader("Production Trend")
                st.line_chart(df["total_pieces"])

                st.subheader("Raw Data")
                st.dataframe(df)
            else:
                st.warning("ยังไม่มีข้อมูล")

        time.sleep(refresh)
