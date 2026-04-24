import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta

# 1. ตั้งค่า Timezone (UTC +7)
ICT = timezone(timedelta(hours=7))

# --- ตั้งค่าสี (Color Mapping) ---
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
    name_lower = name.lower()
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

# --- การตั้งค่าเชื่อมต่อ ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ Supabase: {e}")

st.set_page_config(page_title="Production Log System", layout="wide")
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

# --- โครงสร้าง Tabs ---
tab1, tab2, tab3 = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig)"])

# --- TAB 1: บ่อสี ---
with tab1:
    st.header("บันทึกข้อมูลบ่อสี")
    color_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")
    if color_tanks:
        selected_tank = st.selectbox("เลือกบ่อสี", list(color_tanks.keys()), key="tank_select_t1")
        render_color_bar(selected_tank)
        with st.form("color_log_form", clear_on_submit=True):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            if st.form_submit_button("บันทึกค่ามาตรฐาน"):
                supabase.table("color_tank_logs").insert({
                    "tank_id": color_tanks[selected_tank], "ph_value": ph, "temperature": temp,
                    "recorded_at": datetime.now(ICT).isoformat()
                }).execute()
                st.success("บันทึกข้อมูลสำเร็จ!")

# --- TAB 2: บ่ออโนไดซ์ ---
with tab2:
    st.header("บันทึกข้อมูลบ่ออโนไดซ์")
    anodize_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Anodize")
    if anodize_tanks:
        selected_tank = st.selectbox("เลือกบ่ออโนไดซ์", list(anodize_tanks.keys()))
        with st.form("anodize_log_form", clear_on_submit=True):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            density = st.number_input("ความหนาแน่น (Density)", step=0.001, format="%.3f")
            if st.form_submit_button("บันทึก"):
                supabase.table("anodize_tank_logs").insert({
                    "tank_id": anodize_tanks[selected_tank], "ph_value": ph, "temperature": temp, 
                    "density": density, "recorded_at": datetime.now(ICT).isoformat()
                }).execute()
                st.success("บันทึกข้อมูลสำเร็จ!")

# --- TAB 3: งานจิ๊ก ---
with tab3:
    sub_prod, sub_jig, sub_log = st.tabs(["1. ลงทะเบียนชิ้นงาน", "2. ลงทะเบียนจิ๊ก", "3. บันทึกผลผลิต"])
    
    with sub_prod:
        # ... (ส่วนเดิม)
        pass

    with sub_jig:
        # ... (ส่วนเดิม)
        pass

    with sub_log:
        prods = get_options("products", "product_id", "product_code")
        jigs = get_options("jigs", "jig_id", "jig_model_code")
        colors = get_options("colors", "color_id", "color_name") # ดึงรายการสีจาก DB
        
        if prods and jigs and colors:
            sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))
            sel_j = st.selectbox("เลือกจิ๊ก", list(jigs.keys()))
            
            # --- เปลี่ยนเป็น selectbox ---
            sel_c = st.selectbox("เลือกสี", list(colors.keys())) 
            
            # แสดงแถบสีตามที่เลือกจาก selectbox
            render_color_bar(sel_c)
            
            with st.form("log_prod_form", clear_on_submit=True):
                pcs = st.number_input("จำนวนต่อแถว", min_value=0); rows = st.number_input("แถวที่เต็ม", min_value=0); partial = st.number_input("เศษชิ้นงาน", min_value=0)
                if st.form_submit_button("บันทึกการผลิต"):
                    jig_id = jigs[sel_j]
                    supabase.table("jig_usage_log").insert({
                        "product_id": prods[sel_p], "jig_id": jig_id, "color": sel_c,
                        "pcs_per_row": pcs, "rows_filled": rows, "partial_pieces": partial,
                        "total_pieces": (rows * pcs) + partial,
                        "recorded_date": datetime.now(ICT).isoformat()
                    }).execute()
                    
                    supabase.table("jig_status").upsert({
                        "jig_id": jig_id, "status_type": "In-Process", "updated_at": datetime.now(ICT).isoformat()
                    }).execute()
                    st.success("บันทึกการผลิตและอัปเดตสถานะจิ๊กเรียบร้อย!")
