import streamlit as st
from supabase import create_client
import datetime

# --- 1. การตั้งค่าเชื่อมต่อ ---
# ตรวจสอบให้แน่ใจว่าใน st.secrets มี SUPABASE_URL และ SUPABASE_KEY
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ Supabase: {e}")

st.set_page_config(page_title="Production Log System", layout="wide")
st.title("ระบบบันทึกข้อมูลการผลิต (Complete System)")

# ฟังก์ชันดึงข้อมูลมาทำ Dropdown
def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    try:
        query = supabase.table(table).select(f"{id_col}, {name_col}")
        if filter_col and filter_val:
            query = query.eq(filter_col, filter_val)
        response = query.execute()
        return {item[name_col]: item[id_col] for item in response.data}
    except Exception as e:
        return {}

# --- 2. โครงสร้าง Tabs หลัก ---
tab1, tab2, tab3 = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig)"])

# --- TAB 1: บ่อสี ---
with tab1:
    st.header("บันทึกข้อมูลบ่อสี")
    color_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")
    if color_tanks:
        selected_tank = st.selectbox("เลือกบ่อสี", list(color_tanks.keys()), key="tank_color_log")
        with st.form("color_log_form", clear_on_submit=True):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            if st.form_submit_button("บันทึก"):
                if ph <= 0 or temp <= 0:
                    st.error("กรุณากรอกค่า pH และอุณหภูมิ")
                else:
                    try:
                        supabase.table("color_tank_logs").insert({"tank_id": color_tanks[selected_tank], "ph_value": ph, "temperature": temp}).execute()
                        st.success("บันทึกข้อมูลบ่อสีสำเร็จ!")
                    except Exception as e:
                        st.error(f"Error: {e}")

# --- TAB 2: บ่ออโนไดซ์ ---
with tab2:
    st.header("บันทึกข้อมูลบ่ออโนไดซ์")
    anodize_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Anodize")
    if anodize_tanks:
        selected_tank = st.selectbox("เลือกบ่ออโนไดซ์", list(anodize_tanks.keys()), key="tank_anodize_log")
        with st.form("anodize_log_form", clear_on_submit=True):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            density = st.number_input("ความหนาแน่น (Density)", step=0.001, format="%.3f")
            if st.form_submit_button("บันทึก"):
                try:
                    supabase.table("anodize_tank_logs").insert({"tank_id": anodize_tanks[selected_tank], "ph_value": ph, "temperature": temp, "density": density}).execute()
                    st.success("บันทึกข้อมูลสำเร็จ!")
                except Exception as e:
                    st.error(f"Error: {e}")

# --- TAB 3: งานจิ๊ก ---
with tab3:
    sub_prod, sub_jig, sub_log = st.tabs(["1. ลงทะเบียนชิ้นงาน", "2. ลงทะเบียนจิ๊ก", "3. บันทึกผลผลิต"])

    with sub_prod:
        with st.form("new_product_form", clear_on_submit=True):
            p_code = st.text_input("รหัสสินค้า (Unique)")
            p_name = st.text_input("ชื่อชิ้นงาน")
            if st.form_submit_button("บันทึกสินค้า"):
                supabase.table("products").insert({"product_code": p_code, "product_name": p_name}).execute()
                st.success("ลงทะเบียนสินค้าสำเร็จ")

    with sub_jig:
        with st.form("new_jig_form", clear_on_submit=True):
            jig_code = st.text_input("รหัสจิ๊ก")
            if st.form_submit_button("บันทึกจิ๊ก"):
                supabase.table("jigs").insert({"jig_model_code": jig_code}).execute()
                st.success("บันทึกจิ๊กสำเร็จ")

    with sub_log:
        prods = get_options("products", "product_id", "product_code")
        jigs = get_options("jigs", "jig_id", "jig_model_code")
        tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")

        if prods and jigs and tanks:
            with st.form("log_prod_form", clear_on_submit=True):
                sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))
                sel_j = st.selectbox("เลือกจิ๊ก", list(jigs.keys()))
                
                # เลือกบ่อ
                sel_t = st.selectbox("เลือกบ่อสี", list(tanks.keys()))
                tank_id = tanks[sel_t]

                # ดึงสีที่ผูกกับบ่อนี้จากตาราง tank_color_mapping
                try:
                    response = supabase.table("tank_color_mapping") \
                        .select("color_id, colors(color_name)") \
                        .eq("tank_id", tank_id).execute()
                    
                    # สร้าง Dict ของสีที่ถูกต้อง
                    valid_colors = {item['colors']['color_name']: item['color_id'] for item in response.data}
                except:
                    valid_colors = {}

                if valid_colors:
                    sel_c = st.selectbox("เลือกสี (ตามบ่อ)", list(valid_colors.keys()))
                    color_id = valid_colors[sel_c]
                else:
                    st.warning(f"บ่อ {sel_t} นี้ยังไม่มีการตั้งค่าสี (กรุณาเช็คตาราง mapping)")
                    color_id = None

                pcs_jig = st.number_input("จำนวนต่อจิ๊ก", min_value=1)
                total = st.number_input("จำนวนรวม", min_value=1)
                
                if st.form_submit_button("บันทึกการผลิต"):
                    if not color_id:
                        st.error("ไม่สามารถบันทึกได้เนื่องจากยังไม่มีการแมปสีกับบ่อนี้")
                    else:
                        supabase.table("jig_usage_log").insert({
                            "product_id": prods[sel_p],
                            "jig_id": jigs[sel_j],
                            "color_id": color_id,
                            "tank_id": tank_id,
                            "pcs_per_jig": pcs_jig,
                            "total_pieces": total,
                            "recorded_date": str(datetime.date.today())
                        }).execute()
                        st.success("บันทึกผลผลิตสำเร็จ!")
        else:
            st.warning("กรุณาลงทะเบียน สินค้า, จิ๊ก และ บ่อ ให้ครบก่อน")
