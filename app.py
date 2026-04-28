import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timezone, timedelta

# 1. ตั้งค่า Timezone (UTC +7)
ICT = timezone(timedelta(hours=7))

# --- Configuration ---
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

st.set_page_config(page_title="Production Log System", layout="wide")

# --- เชื่อมต่อ Supabase ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error connecting to Supabase: {e}")
        return None

supabase = init_connection()

# --- Helper Functions ---
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
        <div style="background-color:{hex_code}; width:100%; height:20px; border-radius:5px; border: 1px solid #ccc; margin-bottom: 10px;"></div>
    """, unsafe_allow_html=True)

def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    if not supabase: return {}
    try:
        query = supabase.table(table).select(f"{id_col}, {name_col}")
        if filter_col and filter_val:
            query = query.eq(filter_col, filter_val)
        response = query.execute()
        return {item[name_col]: item[id_col] for item in response.data}
    except Exception:
        return {}

def update_jig_total_pieces(jig_id):
    try:
        logs = supabase.table("jig_usage_log").select("total_pieces").eq("jig_id", jig_id).execute()
        total_sum = sum(item['total_pieces'] for item in logs.data)
        supabase.table("jigs").update({"total_pcs_in_jig": total_sum}).eq("jig_id", jig_id).execute()
    except Exception as e:
        st.error(f"Error updating total: {e}")

# --- Main App Navigation ---
st.sidebar.title("เมนูระบบ")
menu = st.sidebar.radio("เลือกหน้า", ["Dashboard", "บันทึกข้อมูลการผลิต"])

# --- DASHBOARD SECTION ---
if menu == "Dashboard":
    st.title("📊 Production Dashboard")
    
    # 1. Metrics
    col1, col2, col3 = st.columns(3)
    active_jigs = supabase.table("jig_status").select("jig_id").eq("status_type", "In-Process").execute()
    col1.metric("จิ๊กที่กำลังผลิต", len(active_jigs.data))
    
    today = datetime.now(ICT).strftime("%Y-%m-%d")
    today_logs = supabase.table("jig_usage_log").select("total_pieces").gte("recorded_date", f"{today}T00:00:00").execute()
    total_today = sum(x['total_pieces'] for x in today_logs.data)
    col2.metric("ผลิตได้วันนี้ (ชิ้น)", total_today)
    col3.metric("บ่อที่ใช้งานอยู่", len(active_jigs.data))
    
    st.markdown("---")
    
    # 2. Latest pH Values Chart
    st.subheader("💧 แนวโน้มค่า pH (ย้อนหลัง)")
    logs_res = supabase.table("color_tank_logs").select("tank_id, ph_value, recorded_at").order("recorded_at", desc=True).limit(50).execute()
    
    if logs_res.data:
        df_logs = pd.DataFrame(logs_res.data)
        df_logs['recorded_at'] = pd.to_datetime(df_logs['recorded_at'])
        
        # เลือกแสดงกราฟตามบ่อ
        tanks_map = get_options("tanks", "tank_id", "tank_name")
        inv_tanks_map = {v: k for k, v in tanks_map.items()}
        df_logs['tank_name'] = df_logs['tank_id'].map(inv_tanks_map)
        
        selected_tank = st.selectbox("เลือกบ่อที่ต้องการดูกราฟ", df_logs['tank_name'].unique())
        df_filtered = df_logs[df_logs['tank_name'] == selected_tank]
        
        if not df_filtered.empty:
            chart_data = df_filtered.set_index('recorded_at')[['ph_value']]
            st.line_chart(chart_data)
        else:
            st.write("ไม่พบข้อมูล")
    else:
        st.write("ไม่พบข้อมูลบันทึกบ่อสี")

# --- RECORDING SECTION ---
elif menu == "บันทึกข้อมูลการผลิต":
    st.title("ระบบบันทึกข้อมูลการผลิต")
    
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
