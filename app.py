import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timezone, timedelta
from streamlit_autorefresh import st_autorefresh

# ================== TIMEZONE ==================
ICT = timezone(timedelta(hours=7))

# ================== CONFIG ==================
COLOR_HEX_MAP = {
    "Black": "#000000", "Red": "#FF0000", "Dark Red": "#8B0000",
    "Violet": "#9400D3", "Green": "#008000", "Banana leaf Green": "#90EE90",
    "Gold": "#FFD700", "Orange": "#FFA500", "Light Blue": "#ADD8E6",
    "Blue": "#0000FF", "Dark Blue": "#00008B", "Pink": "#FFC0CB",
    "Copper": "#B87333", "Titanium": "#808080", "Dark Titanium": "#4A4E69",
    "Rose Gold": "#B76E79"
}

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

# ================== PAGE ==================
st.set_page_config(page_title="Production Log System", layout="wide")

# ================== DB ==================
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# ================== HELPER ==================
def get_hex_from_name(name):
    for k in COLOR_HEX_MAP:
        if k.lower() in str(name).lower():
            return COLOR_HEX_MAP[k]
    return "#CCCCCC"

def render_color_bar(name):
    hex_code = get_hex_from_name(name)
    st.markdown(
        f"<div style='background:{hex_code};height:20px;border-radius:5px'></div>",
        unsafe_allow_html=True
    )

def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    query = supabase.table(table).select(f"{id_col}, {name_col}")
    if filter_col and filter_val:
        query = query.eq(filter_col, filter_val)
    res = query.execute()
    return {i[name_col]: i[id_col] for i in res.data}

# ================== MENU ==================
st.sidebar.title("เมนูระบบ")
menu = st.sidebar.radio("เลือกหน้า", ["Dashboard", "บันทึกข้อมูลการผลิต"])

# ================== DASHBOARD ==================
if menu == "Dashboard":
    st.title("📊 Production Dashboard")

    today = datetime.now(ICT).strftime("%Y-%m-%d")

    col1, col2, col3 = st.columns(3)

    active_jigs = supabase.table("jig_status") \
        .select("jig_id") \
        .eq("status_type", "In-Process") \
        .execute()

    col1.metric("🟢 จิ๊กที่กำลังผลิต", len(active_jigs.data))

    today_logs = supabase.table("jig_usage_log") \
        .select("total_pieces") \
        .gte("recorded_date", f"{today}T00:00:00") \
        .execute()

    col2.metric("📦 ผลิตวันนี้", sum(x['total_pieces'] for x in today_logs.data))

    tanks_today = supabase.table("color_tank_logs") \
        .select("tank_id") \
        .gte("recorded_at", f"{today}T00:00:00") \
        .execute()

    col3.metric("🧪 บ่อที่ใช้", len(set(x['tank_id'] for x in tanks_today.data)))

    st.markdown("---")

    st.subheader("🎨 Color Bath")
    logs = supabase.table("color_tank_logs") \
        .select("*") \
        .order("recorded_at", desc=True) \
        .limit(200) \
        .execute()

    if logs.data:
        df = pd.DataFrame(logs.data)
        df['recorded_at'] = pd.to_datetime(df['recorded_at'])

        tank_map = get_options("tanks", "tank_id", "tank_name")
        inv = {v: k for k, v in tank_map.items()}
        df['tank_name'] = df['tank_id'].map(inv)

        latest = df.drop_duplicates("tank_id")

        c1, c2 = st.columns(2)
        c1.bar_chart(latest.set_index('tank_name')['ph_value'])
        c2.bar_chart(latest.set_index('tank_name')['temperature'])

        tank = st.selectbox("เลือกบ่อ", df['tank_name'].unique())
        dff = df[df['tank_name'] == tank]

        st.line_chart(dff.set_index('recorded_at')[['ph_value', 'temperature']])

    st.markdown("---")
    st.subheader("⚙️ Anodize")

    logs_a = supabase.table("anodize_tank_logs") \
        .select("*") \
        .order("recorded_at", desc=True) \
        .limit(200) \
        .execute()

    if logs_a.data:
        df = pd.DataFrame(logs_a.data)
        df['recorded_at'] = pd.to_datetime(df['recorded_at'])

        tank_map = get_options("tanks", "tank_id", "tank_name")
        inv = {v: k for k, v in tank_map.items()}
        df['tank_name'] = df['tank_id'].map(inv)

        latest = df.drop_duplicates("tank_id")

        c1, c2, c3 = st.columns(3)
        c1.bar_chart(latest.set_index('tank_name')['ph_value'])
        c2.bar_chart(latest.set_index('tank_name')['temperature'])
        c3.bar_chart(latest.set_index('tank_name')['density'])

    st_autorefresh(interval=10000, key="refresh")

# ================== RECORD ==================
else:
    st.title("📥 บันทึกข้อมูล")

    tab1, tab2, tab3 = st.tabs(["บ่อสี", "บ่ออโนไดซ์", "งานจิ๊ก"])

    # COLOR
    with tab1:
        tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")
        name = st.selectbox("เลือกบ่อสี", list(tanks.keys()))

        color = TANK_COLOR_MAP.get(name, "Black")
        render_color_bar(color)

        with st.form("f1"):
            ph = st.number_input("pH")
            temp = st.number_input("Temp")

            if st.form_submit_button("บันทึก"):
                supabase.table("color_tank_logs").insert({
                    "tank_id": tanks[name],
                    "ph_value": ph,
                    "temperature": temp,
                    "recorded_at": datetime.now(ICT).isoformat()
                }).execute()
                st.success("บันทึกแล้ว")

    # ANODIZE
    with tab2:
        tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Anodize")
        name = st.selectbox("เลือกบ่อ", list(tanks.keys()))

        with st.form("f2"):
            ph = st.number_input("pH")
            temp = st.number_input("Temp")
            den = st.number_input("Density")

            if st.form_submit_button("บันทึก"):
                supabase.table("anodize_tank_logs").insert({
                    "tank_id": tanks[name],
                    "ph_value": ph,
                    "temperature": temp,
                    "density": den,
                    "recorded_at": datetime.now(ICT).isoformat()
                }).execute()
                st.success("บันทึกแล้ว")

    # JIG
    with tab3:
        sub_prod, sub_jig, sub_log = st.tabs([
            "1. ลงทะเบียนชิ้นงาน",
            "2. ลงทะเบียนจิ๊ก",
            "3. บันทึกผลผลิต"
        ])

        with sub_prod:
            st.write("เพิ่มสินค้า...")

        with sub_jig:
            st.write("เพิ่มจิ๊ก...")

        # ✅ FIXED ตรงนี้
        with sub_log:
            st.subheader("📊 ระบบจิ๊ก")

            prods = get_options("products", "product_id", "product_code")

            jigs = supabase.table("jigs") \
                .select("jig_id, jig_model_code") \
                .execute().data

            if not jigs:
                st.warning("ไม่มีข้อมูลจิ๊ก")
                st.stop()

            jig_map = {j['jig_model_code']: j['jig_id'] for j in jigs}

            sel_j = st.selectbox("เลือกจิ๊ก", list(jig_map.keys()))
            sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))

            st.success("ระบบพร้อมใช้งาน")
