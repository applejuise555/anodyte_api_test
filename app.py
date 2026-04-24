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
        selected_tank_name = st.selectbox("เลือกบ่อสี", list(color_tanks.keys()), key="tank_select_t1")
        detected_color = TANK_COLOR_MAP.get(selected_tank_name, "Black")
        
        st.write(f"ระบบตรวจพบสี: **{detected_color}**")
        render_color_bar(detected_color)
        
        with st.form("color_log_form", clear_on_submit=True):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            if st.form_submit_button("บันทึกค่ามาตรฐาน"):
                if ph == 0 or temp == 0:
                    st.error("กรุณากรอกค่า pH และอุณหภูมิให้ถูกต้อง")
                else:
                    supabase.table("color_tank_logs").insert({
                        "tank_id": color_tanks[selected_tank_name], 
                        "ph_value": ph, 
                        "temperature": temp,
                        "recorded_at": datetime.now(ICT).isoformat()
                    }).execute()
                    st.success("บันทึกข้อมูลมาตรฐานสำเร็จ!")

        with st.expander("บันทึกอุณหภูมิความถี่สูง (High Frequency)"):
            with st.form("color_temp_frequent_form", clear_on_submit=True):
                target_temp = st.number_input("อุณหภูมิเป้าหมาย (°C)", step=0.1)
                actual_temp = st.number_input("อุณหภูมิที่วัดได้จริง (°C)", step=0.1)
                if st.form_submit_button("บันทึกข้อมูลความถี่สูง"):
                    if target_temp == 0 or actual_temp == 0:
                        st.error("กรุณากรอกอุณหภูมิให้ครบถ้วน")
                    else:
                        supabase.table("temp_frequent_logs").insert({
                            "tank_id": color_tanks[selected_tank_name], 
                            "temp_target": target_temp, 
                            "temp_actual": actual_temp,
                            "recorded_at": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("บันทึกค่าความถี่สูงสำเร็จ!")
    else:
        st.warning("ไม่พบข้อมูลบ่อสีในระบบ")

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
                if ph == 0 or temp == 0 or density == 0:
                    st.error("กรุณากรอกข้อมูล pH, อุณหภูมิ และความหนาแน่น ให้ครบถ้วน")
                else:
                    supabase.table("anodize_tank_logs").insert({
                        "tank_id": anodize_tanks[selected_tank], "ph_value": ph, "temperature": temp, 
                        "density": density, "recorded_at": datetime.now(ICT).isoformat()
                    }).execute()
                    st.success("บันทึกข้อมูลมาตรฐานสำเร็จ!")
        
        with st.expander("บันทึกอุณหภูมิความถี่สูง (High Frequency)"):
            with st.form("anodize_temp_frequent_form", clear_on_submit=True):
                target_temp = st.number_input("อุณหภูมิเป้าหมาย (°C)", step=0.1)
                actual_temp = st.number_input("อุณหภูมิที่วัดได้จริง (°C)", step=0.1)
                if st.form_submit_button("บันทึกข้อมูลความถี่สูง"):
                    if target_temp == 0 or actual_temp == 0:
                        st.error("กรุณากรอกอุณหภูมิให้ครบถ้วน")
                    else:
                        supabase.table("temp_frequent_logs").insert({
                            "tank_id": anodize_tanks[selected_tank], "temp_target": target_temp, "temp_actual": actual_temp,
                            "recorded_at": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("บันทึกค่าความถี่สูงสำเร็จ!")

# --- TAB 3: งานจิ๊ก ---
with tab3:
    sub_prod, sub_jig, sub_log = st.tabs(["1. ลงทะเบียนชิ้นงาน", "2. ลงทะเบียนจิ๊ก", "3. บันทึกผลผลิต"])
    
    with sub_prod:
        with st.form("add_prod_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                p_code = st.text_input("รหัสสินค้า (Product Code)")
                p_name = st.text_input("ชื่อ/รายละเอียดสินค้า")
                height = st.number_input("ความสูง (Height)", step=0.01)
                width = st.number_input("ความกว้าง (Width)", step=0.01)
                thickness = st.number_input("ความหนา (Thickness)", step=0.01)
            with col2:
                depth = st.number_input("ความลึก (Depth)", step=0.01)
                outer_d = st.number_input("Outer Diameter", step=0.01)
                inner_d = st.number_input("Inner Diameter", step=0.01)
                s_finish = st.text_input("พื้นผิว (Surface Finish)")
                
            if st.form_submit_button("ลงทะเบียนชิ้นงาน"):
                if not p_code or not p_name:
                    st.error("กรุณากรอก รหัสสินค้า และ ชื่อสินค้า ให้ครบถ้วน")
                else:
                    data = {
                        "product_code": p_code, "product_name": p_name,
                        "height": height, "width": width, "thickness": thickness,
                        "depth": depth, "outer_diameter": outer_d, 
                        "inner_diameter": inner_d, "surface_finish": s_finish
                    }
                    supabase.table("products").insert(data).execute()
                    st.success("ลงทะเบียนชิ้นงานสำเร็จ")

    with sub_jig:
        with st.form("add_jig_form", clear_on_submit=True):
            j_code = st.text_input("รหัสจิ๊ก (Jig Model Code)")
            if st.form_submit_button("ลงทะเบียนจิ๊ก"):
                if not j_code:
                    st.error("กรุณากรอกรหัสจิ๊ก")
                else:
                    try:
                        supabase.table("jigs").insert({"jig_model_code": j_code}).execute()
                        st.success("ลงทะเบียนจิ๊กสำเร็จ")
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาดจากฐานข้อมูล: {e}")

# --- 3. บันทึกผลผลิต (ส่วนที่แก้ไขให้กรองเฉพาะจิ๊กที่ใช้งานได้) ---
with sub_log:
    prods = get_options("products", "product_id", "product_code")
    
    # 1. ดึงข้อมูลจิ๊กทั้งหมดพร้อมสถานะ
    # เลือก jig_id, code และสถานะ
    response = supabase.table("jigs").select("jig_id, jig_model_code, jig_status(status_type)").execute()
    all_jigs_data = response.data
    
    # 2. ทำการกรอง (Filter) เฉพาะจิ๊กที่ไม่ได้อยู่ในสถานะ 'Finished'
    available_jigs = []
    for j in all_jigs_data:
        # ดึงสถานะ (ถ้าไม่มีสถานะ ให้ถือว่าเป็น 'Available')
        status_list = j.get('jig_status', [])
        current_status = status_list[0]['status_type'] if status_list else "Available"
        
        # กรองเอาเฉพาะจิ๊กที่ "ไม่เท่ากับ" Finished
        if current_status != "Finished":
            available_jigs.append(j)
            
    # สร้าง Dictionary สำหรับแสดงใน Dropdown
    jig_map = {j['jig_model_code']: j['jig_id'] for j in available_jigs}
    
    if prods and available_jigs:
        # เลือกจิ๊กและสินค้า
        sel_j = st.selectbox("เลือกจิ๊กที่ใช้งานได้", list(jig_map.keys()))
        jig_id = jig_map[sel_j]
        sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))
        
        # ตรวจสอบสถานะปัจจุบันของจิ๊กตัวที่เลือก
        status_res = supabase.table("jig_status").select("status_type").eq("jig_id", jig_id).maybe_single().execute()
        status = status_res.data['status_type'] if status_res.data else "Available"

        # แสดงสถานะปัจจุบัน
        st.info(f"จิ๊กนี้กำลังอยู่ในสถานะ: {status}")

        # --- Logic จัดการสถานะ ---
        if status == "In-Process":
            st.warning("จิ๊กนี้กำลังถูกใช้งานอยู่")
            if st.button("เสร็จสิ้นงาน / ปลดล็อกจิ๊ก (Release Jig)"):
                # ใส่โค้ดของคุณที่นี่ เช่น:
                # supabase.table("jig_status").update({"status_type": "Finished"}).eq("jig_id", jig_id).execute()
                st.success("ปลดล็อกสำเร็จ!")
                st.rerun()
        else:
            st.success("จิ๊กนี้ว่างอยู่")
            if st.button("เริ่มรอบการผลิตใหม่"):
                # ใส่โค้ดของคุณที่นี่ เช่น:
                # supabase.table("jig_status").insert({"jig_id": jig_id, "status_type": "In-Process"}).execute()
                st.success("เริ่มผลิตแล้ว!")
                st.rerun()
             
    else:
        st.warning("ไม่มีจิ๊กที่พร้อมใช้งาน (จิ๊กทั้งหมดอาจอยู่ในสถานะ Finished หรือยังไม่ได้ลงทะเบียน)")
        
