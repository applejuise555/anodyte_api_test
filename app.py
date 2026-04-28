import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timezone, timedelta
import time

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

# ===== Threshold (ปรับได้ตามโรงงาน) =====
PH_MIN, PH_MAX = 5.5, 6.5
TEMP_MIN, TEMP_MAX = 20, 25

st.set_page_config(page_title="Production Log System", layout="wide")

# ================== DB ==================
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# ================== HELPER ==================
def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    query = supabase.table(table).select(f"{id_col}, {name_col}")
    if filter_col and filter_val:
        query = query.eq(filter_col, filter_val)
    response = query.execute()
    return {item[name_col]: item[id_col] for item in response.data}

def get_hex_from_name(name):
    for k in COLOR_HEX_MAP:
        if k.lower() in name.lower():
            return COLOR_HEX_MAP[k]
    return "#CCCCCC"

def render_color_bar(name):
    hex_code = get_hex_from_name(name)
    st.markdown(f"""
    <div style="background:{hex_code};height:20px;border-radius:5px"></div>
    """, unsafe_allow_html=True)

def check_status(ph, temp):
    if PH_MIN <= ph <= PH_MAX and TEMP_MIN <= temp <= TEMP_MAX:
        return "OK"
    return "ALERT"

# ================== MENU ==================
st.sidebar.title("เมนูระบบ")
menu = st.sidebar.radio("เลือกหน้า", ["Dashboard", "บันทึกข้อมูลการผลิต"])

# ================== DASHBOARD ==================
if menu == "Dashboard":
    st.title("📊 Production Dashboard (Real-Time)")

    today = datetime.now(ICT).strftime("%Y-%m-%d")

    # ===== KPI =====
    col1, col2, col3 = st.columns(3)

    active_jigs = supabase.table("jig_status")\
        .select("jig_id")\
        .eq("status_type", "In-Process")\
        .execute()

    col1.metric("🟢 จิ๊กที่กำลังผลิต", len(active_jigs.data))

    today_logs = supabase.table("jig_usage_log")\
        .select("total_pieces")\
        .gte("recorded_date", f"{today}T00:00:00")\
        .execute()

    total_today = sum(x['total_pieces'] for x in today_logs.data)
    col2.metric("📦 ผลิตได้วันนี้", total_today)

    active_tanks = supabase.table("color_tank_logs")\
        .select("tank_id")\
        .gte("recorded_at", f"{today}T00:00:00")\
        .execute()

    unique_tanks = len(set(x['tank_id'] for x in active_tanks.data))
    col3.metric("🧪 บ่อที่ใช้งานวันนี้", unique_tanks)

    st.markdown("---")

    # ================= COLOR DASHBOARD =================
    st.subheader("🎨 บ่อสี (Color Bath)")

    logs = supabase.table("color_tank_logs")\
        .select("*")\
        .order("recorded_at", desc=True)\
        .limit(200)\
        .execute()

    if logs.data:
        df = pd.DataFrame(logs.data)
        df['recorded_at'] = pd.to_datetime(df['recorded_at'])

        tanks_map = get_options("tanks", "tank_id", "tank_name")
        inv_map = {v:k for k,v in tanks_map.items()}
        df['tank_name'] = df['tank_id'].map(inv_map)

        latest = df.drop_duplicates("tank_id")
        latest['status'] = latest.apply(lambda x: check_status(x['ph_value'], x['temperature']), axis=1)

        # ALERT
        alert = latest[latest['status']=="ALERT"]
        if not alert.empty:
            st.error("⚠️ พบค่าผิดปกติ")
            st.dataframe(alert[['tank_name','ph_value','temperature']])

        c1, c2 = st.columns(2)
        with c1:
            st.bar_chart(latest.set_index('tank_name')['ph_value'])
        with c2:
            st.bar_chart(latest.set_index('tank_name')['temperature'])

        # Trend
        st.markdown("### 📈 แนวโน้ม")
        tank = st.selectbox("เลือกบ่อสี", df['tank_name'].unique())
        hours = st.selectbox("ช่วงเวลา", [1,6,24])

        cutoff = datetime.now(ICT) - timedelta(hours=hours)
        dff = df[(df['tank_name']==tank) & (df['recorded_at']>=cutoff)]

        st.line_chart(dff.set_index('recorded_at')[['ph_value','temperature']])

    # ================= ANODIZE DASHBOARD =================
    st.markdown("---")
    st.subheader("⚙️ บ่ออโนไดซ์ (Anodize)")

    logs_a = supabase.table("anodize_tank_logs")\
        .select("*")\
        .order("recorded_at", desc=True)\
        .limit(200)\
        .execute()

    if logs_a.data:
        df_a = pd.DataFrame(logs_a.data)
        df_a['recorded_at'] = pd.to_datetime(df_a['recorded_at'])

        tanks_map = get_options("tanks", "tank_id", "tank_name")
        inv_map = {v:k for k,v in tanks_map.items()}
        df_a['tank_name'] = df_a['tank_id'].map(inv_map)

        latest_a = df_a.drop_duplicates("tank_id")

        c3, c4, c5 = st.columns(3)
        with c3:
            st.bar_chart(latest_a.set_index('tank_name')['ph_value'])
        with c4:
            st.bar_chart(latest_a.set_index('tank_name')['temperature'])
        with c5:
            st.bar_chart(latest_a.set_index('tank_name')['density'])

        st.markdown("### 📈 แนวโน้มอโนไดซ์")
        tank_a = st.selectbox("เลือกบ่ออโนไดซ์", df_a['tank_name'].unique())
        dff_a = df_a[df_a['tank_name']==tank_a]

        st.line_chart(dff_a.set_index('recorded_at')[['ph_value','temperature','density']])

    # AUTO REFRESH
    time.sleep(10)
    st.rerun()

# ================== RECORD ==================
elif menu == "บันทึกข้อมูลการผลิต":
    st.title("📥 ระบบบันทึกข้อมูล (กรอกข้อมูลง่ายขึ้น)")

    tab1, tab2, tab3 = st.tabs(["บ่อสี", "บ่ออโนไดซ์", "งานจิ๊ก"])

    # ===== COLOR =====
    with tab1:
        st.header("🎨 บันทึกค่าบ่อสี")

        tanks = get_options("tanks","tank_id","tank_name","tank_type","Color")
        name = st.selectbox("เลือกชื่อบ่อ", list(tanks.keys()))

        color = TANK_COLOR_MAP.get(name,"Black")
        st.write(f"สีที่ระบบตรวจจับ: {color}")
        render_color_bar(color)

        with st.form("f1"):
            ph = st.number_input("ค่า pH (ควรอยู่ ~5.5 - 6.5)")
            temp = st.number_input("อุณหภูมิ °C (ควรอยู่ ~20-25)")

            if st.form_submit_button("💾 บันทึก"):
                supabase.table("color_tank_logs").insert({
                    "tank_id":tanks[name],
                    "ph_value":ph,
                    "temperature":temp,
                    "recorded_at":datetime.now(ICT).isoformat()
                }).execute()
                st.success("บันทึกสำเร็จ")

    # ===== ANODIZE =====
    with tab2:
        st.header("⚙️ บันทึกค่าบ่ออโนไดซ์")

        tanks = get_options("tanks","tank_id","tank_name","tank_type","Anodize")
        name = st.selectbox("เลือกชื่อบ่ออโนไดซ์", list(tanks.keys()))

        with st.form("f2"):
            ph = st.number_input("ค่า pH")
            temp = st.number_input("อุณหภูมิ °C")
            den = st.number_input("ความหนาแน่น (Density)")

            if st.form_submit_button("💾 บันทึก"):
                supabase.table("anodize_tank_logs").insert({
                    "tank_id":tanks[name],
                    "ph_value":ph,
                    "temperature":temp,
                    "density":den,
                    "recorded_at":datetime.now(ICT).isoformat()
                }).execute()
                st.success("บันทึกสำเร็จ")

    # ===== JIG (ห้ามแก้ logic) =====
    with tab3:
        sub1, sub2, sub3 = st.tabs(["เพิ่มสินค้า","เพิ่มจิ๊ก","บันทึกผลผลิต"])
    
    tab1, tab2, tab3 = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig)"])

    with tab1:
        st.header("บันทึกข้อมูลบ่อสี")
        color_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")
        if color_tanks:
            selected_tank_name = st.selectbox("เลือกบ่อสี", list(color_tanks.keys()), key="tank_select_t1")
            detected_color = TANK_COLOR_MAP.get(selected_tank_name, "Black")
            st.write(f"ระบบตรวจพบสี: **{detected_color}**")
            render_color_bar(detected_color)
            
            with st.form("color_log_form", clear_on_submit=True):
                ph = st.number_input("ค่า pH", step=0.1)
                temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
                if st.form_submit_button("บันทึกค่ามาตรฐาน"):
                    try:
                        supabase.table("color_tank_logs").insert({
                            "tank_id": color_tanks[selected_tank_name], 
                            "ph_value": ph, 
                            "temperature": temp, 
                            "recorded_at": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("บันทึกสำเร็จ")
                    except Exception as e:
                        st.error(f"Error: {e}")

    with tab2:
        st.header("บันทึกข้อมูลบ่ออโนไดซ์")
        anodize_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Anodize")
        if anodize_tanks:
            selected_tank_name = st.selectbox("เลือกบ่ออโนไดซ์", list(anodize_tanks.keys()))
            with st.form("anodize_log_form", clear_on_submit=True):
                ph = st.number_input("ค่า pH", step=0.1)
                temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
                density = st.number_input("ความหนาแน่น (Density)", step=0.001, format="%.3f")
                if st.form_submit_button("บันทึก"):
                    try:
                        supabase.table("anodize_tank_logs").insert({
                            "tank_id": anodize_tanks[selected_tank_name], 
                            "ph_value": ph, 
                            "temperature": temp, 
                            "density": density, 
                            "recorded_at": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("บันทึกสำเร็จ")
                    except Exception as e:
                        st.error(f"Error: {e}")

    with tab3:
        sub_prod, sub_jig, sub_log = st.tabs(["1. ลงทะเบียนชิ้นงาน", "2. ลงทะเบียนจิ๊ก", "3. บันทึกผลผลิต"])
        
        with sub_prod:
            with st.form("add_prod_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    p_code = st.text_input("รหัสสินค้า (Product Code)")
                    p_name = st.text_input("ชื่อ/รายละเอียดสินค้า")
                    height = st.number_input("ความสูง (Height)", step=0.01)
                    width = st.number_input("ความว้าง (Width)", step=0.01)
                    thickness = st.number_input("ความหนา (Thickness)", step=0.01)
                with col2:
                    depth = st.number_input("ความลึก (Depth)", step=0.01)
                    outer_d = st.number_input("Outer Diameter", step=0.01)
                    inner_d = st.number_input("Inner Diameter", step=0.01)
                    s_finish = st.text_input("พื้นผิว (Surface Finish)")
                
                if st.form_submit_button("ลงทะเบียนชิ้นงาน"):
                    if not p_code or not p_name: 
                        st.error("กรุณากรอกรหัสสินค้า และ ชื่อสินค้า")
                    else:
                        try:
                            supabase.table("products").insert({
                                "product_code": p_code, 
                                "product_name": p_name, 
                                "height": height, 
                                "width": width, 
                                "thickness": thickness, 
                                "depth": depth, 
                                "outer_diameter": outer_d, 
                                "inner_diameter": inner_d, 
                                "surface_finish": s_finish
                            }).execute()
                            st.success("บันทึกข้อมูลสินค้าสำเร็จ")
                        except Exception as e:
                            st.error(f"Error: {e}")

        with sub_jig:
            with st.form("add_jig_form", clear_on_submit=True):
                jig_m_code = st.text_input("Jig Model Code")
                if st.form_submit_button("ลงทะเบียนจิ๊ก"):
                    try:
                        # เพิ่มค่า total_pcs_in_jig เป็น 0 เพื่อแก้ error not-null constraint
                        supabase.table("jigs").insert({
                            "jig_model_code": jig_m_code,
                            "total_pcs_in_jig": 0 
                        }).execute()
                        st.success("ลงทะเบียนจิ๊กสำเร็จ")
                    except Exception as e:
                        st.error(f"Error: {e}")
