import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta

# 1. ตั้งค่า Timezone
ICT = timezone(timedelta(hours=7))

# --- การตั้งค่าเชื่อมต่อ ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ Supabase: {e}")

st.set_page_config(page_title="Production Log System", layout="wide")
st.title("ระบบบันทึกข้อมูลการผลิต")

# ฟังก์ชันดึง Options
def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    try:
        query = supabase.table(table).select(f"{id_col}, {name_col}")
        if filter_col and filter_val:
            query = query.eq(filter_col, filter_val)
        response = query.execute()
        return {item[name_col]: item[id_col] for item in response.data}
    except:
        return {}

# สร้างรายการสีและ Hex Code
color_hex_map = {
    "Black": "#000000", "Red": "#FF0000", "Violet": "#9400D3", 
    "Green": "#008000", "Banana leaf Green": "#90EE90", "Gold": "#FFD700", 
    "Orange": "#FFA500", "Light Blue": "#ADD8E6", "Blue": "#0000FF", 
    "Dark Blue": "#00008B", "Dark Titanium": "#4A4E69", "Dark Red": "#8B0000", 
    "Pink": "#FFC0CB", "Copper": "#B87333", "Titanium": "#808080", "Rose Gold": "#B76E79"
}

# --- โครงสร้าง Tabs ---
tab1, tab2, tab3 = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig)"])

with tab1:
    st.header("บันทึกข้อมูลบ่อสี")
    tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")
    if tanks:
        selected_tank = st.selectbox("เลือกบ่อสี", list(tanks.keys()), key="tank_color")
        with st.form("color_log_form", clear_on_submit=True):
            ph_value = st.number_input("ค่า pH", step=0.1)
            temperature = st.number_input("อุณหภูมิ (°C)", step=0.1)
            if st.form_submit_button("บันทึกข้อมูลบ่อสี"):
                # ใส่ข้อมูลตาม Schema: tank_id, ph_value, temperature
                supabase.table("color_tank_logs").insert({
                    "tank_id": tanks[selected_tank], 
                    "ph_value": ph_value, 
                    "temperature": temperature
                }).execute()
                st.success("บันทึกสำเร็จ!")

with tab2:
    st.header("บันทึกข้อมูลบ่ออโนไดซ์")
    tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Anodize")
    if tanks:
        selected_tank = st.selectbox("เลือกบ่ออโนไดซ์", list(tanks.keys()), key="tank_anodize")
        with st.form("anodize_log_form", clear_on_submit=True):
            ph_value = st.number_input("ค่า pH", step=0.1)
            temperature = st.number_input("อุณหภูมิ (°C)", step=0.1)
            density = st.number_input("ความหนาแน่น (Density)", step=0.001, format="%.3f")
            if st.form_submit_button("บันทึกข้อมูลบ่ออโนไดซ์"):
                # ใส่ข้อมูลตาม Schema: tank_id, ph_value, temperature, density
                supabase.table("anodize_tank_logs").insert({
                    "tank_id": tanks[selected_tank], 
                    "ph_value": ph_value, 
                    "temperature": temperature, 
                    "density": density
                }).execute()
                st.success("บันทึกสำเร็จ!")

with tab3:
    sub_prod, sub_jig, sub_log = st.tabs(["1. ลงทะเบียนชิ้นงาน", "2. ลงทะเบียนจิ๊ก", "3. บันทึกผลผลิต"])
    
    with sub_prod:
        with st.form("new_product_form", clear_on_submit=True):
            p_code = st.text_input("รหัสสินค้า")
            p_name = st.text_input("ชื่อชิ้นงาน")
            surf = st.text_input("ลักษณะพื้นผิว (Surface Finish)")
            
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
                # ใส่ข้อมูลตาม Schema: product_code, product_name, surface_finish, height, width, thickness, depth, outer_diameter, inner_diameter
                supabase.table("products").insert({
                    "product_code": p_code, 
                    "product_name": p_name, 
                    "surface_finish": surf,
                    "height": h, "width": w, "thickness": t, 
                    "depth": d, "outer_diameter": od, "inner_diameter": id_val
                }).execute()
                st.success("บันทึกสินค้าเรียบร้อย")

    with sub_jig:
        with st.form("new_jig_form", clear_on_submit=True):
            jig_code = st.text_input("รหัสจิ๊ก")
            if st.form_submit_button("บันทึกจิ๊ก"):
                supabase.table("jigs").insert({"jig_model_code": jig_code}).execute()
                st.success("บันทึกจิ๊กสำเร็จ!")

    with sub_log:
        prods = get_options("products", "product_id", "product_code")
        jigs = get_options("jigs", "jig_id", "jig_model_code")

        if prods and jigs:
            sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))
            sel_j = st.selectbox("เลือกจิ๊ก", list(jigs.keys()))
            
            last_color = None
            try:
                hist = supabase.table("jig_usage_log").select("color").eq("jig_id", jigs[sel_j]).order("recorded_date", desc=True).limit(1).execute()
                if hist.data: last_color = hist.data[0]['color']
            except: pass

            sel_c = st.pills("เลือกสี", list(color_hex_map.keys()), selection_mode="single", default=last_color if last_color else None)
            
            with st.form("log_prod_form", clear_on_submit=True):
                pcs_per_row = st.number_input("จำนวนต่อแถว (pcs_per_row)", min_value=0, step=1)
                rows_filled = st.number_input("จำนวนแถวที่เต็ม (Rows Filled)", min_value=0, step=1)
                partial = st.number_input("เศษชิ้นงาน (Partial Pieces)", min_value=0, step=1)
                
                if st.form_submit_button("บันทึกการผลิต"):
                    if not sel_c:
                        st.error("กรุณาเลือกสีก่อน!")
                    else:
                        total = (rows_filled * pcs_per_row) + partial
                        # ใส่ข้อมูลตาม Schema: product_id, jig_id, color, pcs_per_row, rows_filled, partial_pieces, total_pieces, recorded_date
                        data = {
                            "product_id": prods[sel_p],
                            "jig_id": jigs[sel_j],
