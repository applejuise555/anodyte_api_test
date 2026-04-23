import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta

# --- ตั้งค่าพื้นฐาน ---
ICT = timezone(timedelta(hours=7))
st.set_page_config(page_title="Production Log System", layout="wide")

# เชื่อมต่อ Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- ข้อมูลสี (ใส่เพิ่มเข้าไป) ---
color_hex_map = {
    "5 Black": "#000000", "2 Red": "#FF0000", "3 Violet": "#9400D3", 
    "8 Green": "#008000", "6 Banana leaf Green": "#90EE90", "15 Gold": "#FFD700", 
    "9 Orange": "#FFA500", "10 Lt.Blue": "#ADD8E6", "16 Blue": "#0000FF", 
    "4 Dk.Blue": "#00008B", "Dark Titanium": "#4A4E69", "17 Black": "#333333",
    "7 Pink": "#FFC0CB", "19 Copper": "#B87333", "12 Ti": "#808080", "14 Rose G.": "#B76E79",
    "RO 1": "#78909c", "RO 2": "#78909c", "RO 3": "#78909c", "RO 4": "#78909c", 
    "RO 5": "#78909c", "RO 6": "#78909c", "RO 7": "#78909c", "RO 8": "#78909c", "RO 9": "#78909c"
}

# ฟังก์ชันสำหรับฉีด CSS เพื่อเปลี่ยนสีปุ่ม
def inject_button_style(key, color):
    # CSS ตัวนี้จะไปหาปุ่มที่มี key นั้นๆ แล้วเปลี่ยนสีพื้นหลังและสีตัวอักษร
    st.markdown(f"""
    <style>
    div[data-testid="stButton"] button[key="{key}"] {{
        background-color: {color} !important;
        color: white !important;
        border: 1px solid #ffffff !important;
        width: 100%;
        height: 50px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- จัดการ State สำหรับระบบคลิกเลือกบ่อ ---
if "selected_tank" not in st.session_state:
    st.session_state.selected_tank = None

# --- หน้าแสดงผลแผนที่บ่อ ---
def render_tank_map(tab_name):
    st.subheader(f"ผังบ่อ {tab_name}")
    
    tanks_data = supabase.table("tanks").select("tank_id, tank_name, tank_type").eq("tank_type", tab_name).execute()
    
    # สร้าง Grid (6 บ่อต่อแถว)
    cols = st.columns(6) 
    for i, tank in enumerate(tanks_data.data):
        tank_name = tank['tank_name']
        btn_key = f"btn_{tank['tank_id']}"
        
        # ใส่สีให้ปุ่ม
        color = color_hex_map.get(tank_name, "#cccccc") # ถ้าไม่มีสีใน map ให้ใช้สีเทา
        inject_button_style(btn_key, color)
        
        if cols[i % 6].button(tank_name, key=btn_key):
            st.session_state.selected_tank = tank
            st.rerun()

# --- หน้าฟอร์มบันทึกข้อมูล ---
def render_log_form():
    tank = st.session_state.selected_tank
    st.subheader(f"บันทึกข้อมูล: {tank['tank_name']}")
    
    if st.button("⬅️ กลับไปหน้าแผนที่"):
        st.session_state.selected_tank = None
        st.rerun()

    with st.form("log_form"):
        ph = st.number_input("ค่า pH", step=0.1)
        temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
        
        density = None
        if tank['tank_type'] == "Anodize":
            density = st.number_input("ความหนาแน่น (Density)", step=0.001, format="%.3f")
            
        if st.form_submit_button("บันทึกข้อมูล"):
            try:
                table_name = "anodize_tank_logs" if tank['tank_type'] == "Anodize" else "color_tank_logs"
                data_to_insert = {"tank_id": tank['tank_id'], "ph_value": ph, "temperature": temp}
                if density: data_to_insert["density"] = density
                
                supabase.table(table_name).insert(data_to_insert).execute()
                st.success("บันทึกข้อมูลสำเร็จ!")
            except Exception as e:
                st.error(f"Error: {e}")

# --- โครงสร้างหลัก ---
tab1, tab2, tab3 = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig)"])

with tab1:
    if st.session_state.selected_tank is None:
        render_tank_map("Color")
    else:
        render_log_form()

with tab2:
    if st.session_state.selected_tank is None:
        render_tank_map("Anodize")
    else:
        render_log_form()
# --- TAB 3: งานจิ๊ก ---
with tab3:
    # 1. ประกาศ Tab ก่อนเสมอ เพื่อไม่ให้เกิด NameError
    sub_prod, sub_jig, sub_log = st.tabs(["1. ลงทะเบียนชิ้นงาน", "2. ลงทะเบียนจิ๊ก", "3. บันทึกผลผลิต"])
    
    with sub_prod:
        with st.form("new_product_form", clear_on_submit=True):
            p_code = st.text_input("รหัสสินค้า *")
            p_name = st.text_input("ชื่อชิ้นงาน *")
            surface_finish = st.text_input("ลักษณะพื้นผิว (Surface Finish) *")
            
            col1, col2 = st.columns(2)
            with col1:
                h = st.number_input("Height", 0.0, format="%.2f")
                w = st.number_input("Width", 0.0, format="%.2f")
                t = st.number_input("Thickness", 0.0, format="%.2f")
            with col2:
                d = st.number_input("Depth", 0.0, format="%.2f")
                od = st.number_input("Outer Diameter", 0.0, format="%.2f")
                id_val = st.number_input("Inner Diameter", 0.0, format="%.2f")
            
            if st.form_submit_button("บันทึกสินค้า"):
                # เช็คซ้ำใน Database
                check_dup = supabase.table("products").select("product_code").eq("product_code", p_code).execute()
                if check_dup.data:
                    st.error(f"รหัสสินค้า '{p_code}' มีอยู่ในระบบแล้ว!")
                else:
                    try:
                        supabase.table("products").insert({
                            "product_code": p_code, "product_name": p_name,
                            "surface_finish": surface_finish,
                            "height": h, "width": w, "thickness": t, 
                            "depth": d, "outer_diameter": od, "inner_diameter": id_val
                        }).execute()
                        st.success("บันทึกสินค้าสำเร็จ!")
                    except Exception as e:
                        st.error(f"Error Database: {e}") # ดู Error จริงที่นี่

    with sub_jig:
        with st.form("new_jig_form", clear_on_submit=True):
            jig_code = st.text_input("รหัสจิ๊ก")
            if st.form_submit_button("บันทึกจิ๊ก"):
                # เช็คซ้ำใน Database
                check_dup = supabase.table("jigs").select("jig_model_code").eq("jig_model_code", jig_code).execute()
                if check_dup.data:
                    st.error(f"รหัสจิ๊ก '{jig_code}' มีอยู่ในระบบแล้ว!")
                else:
                    try:
                        supabase.table("jigs").insert({"jig_model_code": jig_code}).execute()
                        st.success("บันทึกจิ๊กสำเร็จ!")
                    except Exception as e:
                        st.error(f"Error Database: {e}")

    with sub_log:
        prods = get_options("products", "product_id", "product_code")
        jigs = get_options("jigs", "jig_id", "jig_model_code")
        all_colors = get_options("colors", "color_id", "color_name") 

        if prods and jigs:
            sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))
            sel_j = st.selectbox("เลือกจิ๊ก", list(jigs.keys()))
            
            jig_id = jigs[sel_j]
            first_color = None
            
            # ดึงสีแรกที่เคยใช้
            try:
                hist = supabase.table("jig_usage_log").select("color").eq("jig_id", jig_id).order("recorded_date", desc=False).limit(1).execute()
                if hist.data: first_color = hist.data[0]['color']
            except: pass
            
            # ล็อกสีถ้าเคยมีประวัติ
            if first_color:
                st.warning(f"จิ๊กนี้ถูกกำหนดสีไว้แล้ว: {first_color}")
                sel_c = st.selectbox("เลือกสี", [first_color], disabled=True)
            else:
                sel_c = st.selectbox("เลือกสี", list(all_colors.keys()))
            
            # แสดงกล่องสี
            if sel_c in color_hex_map:
                st.markdown(f'<div style="background-color:{color_hex_map[sel_c]}; width:100%; height:30px; border-radius:5px;"></div>', unsafe_allow_html=True)
            
            with st.form("log_prod_form", clear_on_submit=True):
                pcs_per_row = st.number_input("จำนวนต่อแถว", min_value=0, step=1)
                rows_filled = st.number_input("จำนวนแถวที่เต็ม", min_value=0, step=1)
                partial_pieces = st.number_input("เศษชิ้นงาน", min_value=0, step=1)
                
                if st.form_submit_button("บันทึกการผลิต"):
                    try:
                        supabase.table("jig_usage_log").insert({
                            "product_id": prods[sel_p],
                            "jig_id": jig_id,
                            "color": sel_c,
                            "pcs_per_row": pcs_per_row,
                            "rows_filled": rows_filled,
                            "partial_pieces": partial_pieces,
                            "total_pieces": (rows_filled * pcs_per_row) + partial_pieces,
                            "recorded_date": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("บันทึกสำเร็จ!")
                    except Exception as e:
                        st.error(f"Error: {e}")
