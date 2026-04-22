import streamlit as st
from supabase import create_client
import datetime

# --- 1. การตั้งค่าเริ่มต้น ---
# ตรวจสอบให้แน่ใจว่าใน Streamlit Secrets มีค่า SUPABASE_URL และ SUPABASE_KEY
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ Supabase: {e}")

st.set_page_config(page_title="Production Log System", layout="wide")
st.title("ระบบบันทึกข้อมูลการผลิต (Anodize & Color)")

# ฟังก์ชันดึงข้อมูล Dropdown
def get_dropdown_options(table_name, id_col, name_col, filter_col=None, filter_val=None):
    try:
        query = supabase.table(table_name).select(f"{id_col}, {name_col}")
        if filter_col and filter_val:
            query = query.eq(filter_col, filter_val)
        response = query.execute()
        return {item[name_col]: item[id_col] for item in response.data}
    except Exception as e:
        return {}

# --- 2. โครงสร้าง Tabs หลัก (ประกาศตัวแปรให้ถูกที่) ---
tab1, tab2, tab3 = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig)"])

# --- TAB 1: บ่อสี ---
with tab1:
    st.header("บันทึกข้อมูลบ่อสี")
    color_tanks = get_dropdown_options("tanks", "tank_id", "tank_name", "tank_type", "Color")
    if color_tanks:
        selected_tank = st.selectbox("เลือกบ่อสี", list(color_tanks.keys()))
        with st.form("color_log_form", clear_on_submit=True):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            
            if st.form_submit_button("บันทึกข้อมูลบ่อสี"):
                # VALIDATION: ห้ามค่าว่าง
                if ph <= 0 or temp <= 0:
                    st.error("กรุณากรอกค่า pH และ อุณหภูมิ ให้มากกว่า 0")
                else:
                    try:
                        supabase.table("color_tank_logs").insert({
                            "tank_id": color_tanks[selected_tank], "ph_value": ph, "temperature": temp
                        }).execute()
                        st.success("บันทึกข้อมูลสำเร็จ!")
                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        st.warning("ยังไม่มีข้อมูลบ่อสี")

# --- TAB 2: บ่ออโนไดซ์ ---
with tab2:
    st.header("บันทึกข้อมูลบ่ออโนไดซ์")
    anodize_tanks = get_dropdown_options("tanks", "tank_id", "tank_name", "tank_type", "Anodize")
    if anodize_tanks:
        selected_tank = st.selectbox("เลือกบ่ออโนไดซ์", list(anodize_tanks.keys()))
        with st.form("anodize_log_form", clear_on_submit=True):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            density = st.number_input("ความหนาแน่น (Density)", step=0.001, format="%.3f")
            
            if st.form_submit_button("บันทึกข้อมูลบ่ออโนไดซ์"):
                # VALIDATION
                if ph <= 0 or temp <= 0 or density <= 0:
                    st.error("กรุณากรอกข้อมูลให้ครบถ้วนและถูกต้อง")
                else:
                    try:
                        supabase.table("anodize_tank_logs").insert({
                            "tank_id": anodize_tanks[selected_tank], "ph_value": ph, "temperature": temp, "density": density
                        }).execute()
                        st.success("บันทึกข้อมูลสำเร็จ!")
                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        st.warning("ยังไม่มีข้อมูลบ่ออโนไดซ์")

# --- TAB 3: งานจิ๊ก (แก้ไขการซ้อน Tabs) ---
with tab3:
    # ประกาศ Sub-tabs ไว้ที่นี่ (เพื่อให้ Scope ถูกต้อง)
    sub_prod_reg, sub_jig_reg, sub_log = st.tabs(["1. ลงทะเบียนชิ้นงาน", "2. ลงทะเบียนจิ๊ก", "3. บันทึกผลผลิต"])

    # 1. ลงทะเบียนสินค้า
    with sub_prod_reg:
        with st.form("register_product_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                p_code = st.text_input("รหัสสินค้า (จำเป็น)")
                p_name = st.text_input("ชื่อชิ้นงาน (จำเป็น)")
            with col2:
                height = st.number_input("สูง", step=0.1)
                width = st.number_input("กว้าง", step=0.1)
            
            if st.form_submit_button("บันทึกฐานข้อมูลสินค้า"):
                if not p_code or not p_name:
                    st.error("รหัสสินค้าและชื่อชิ้นงานห้ามว่าง")
                else:
                    supabase.table("product_specifications").insert({
                        "product_code": p_code, "product_name": p_name, "height": height, "width": width
                    }).execute()
                    st.success("บันทึกสินค้าเรียบร้อย!")

    # 2. ลงทะเบียนจิ๊ก
    with sub_jig_reg:
        with st.form("new_jig_form", clear_on_submit=True):
            new_jig_code = st.text_input("ตั้งรหัสจิ๊กใหม่ (จำเป็น)")
            if st.form_submit_button("บันทึกจิ๊กใหม่"):
                if not new_jig_code:
                    st.error("กรุณาระบุรหัสจิ๊ก")
                else:
                    supabase.table("jigs").insert({"jig_model_code": new_jig_code}).execute()
                    st.success("บันทึกจิ๊กเรียบร้อย!")

    # 3. บันทึกผลผลิตรายวัน
    with sub_log:
        product_list = get_dropdown_options("product_specifications", "product_code", "product_code")
        jig_list = get_dropdown_options("jigs", "jig_id", "jig_model_code")
        
        if product_list and jig_list:
            with st.form("daily_production_form", clear_on_submit=True):
                sel_product = st.selectbox("เลือกรหัสสินค้า", list(product_list.keys()))
                sel_color = st.text_input("สี (จำเป็น)")
                selected_jig_name = st.selectbox("เลือกจิ๊ก", list(jig_list.keys()))
                pcs_jig = st.number_input("จำนวนต่อจิ๊ก", step=1)
                total = st.number_input("จำนวนรวมทั้งหมด", step=1)
                
                if st.form_submit_button("บันทึกผลผลิต"):
                    # VALIDATION
                    if not sel_color or pcs_jig <= 0 or total <= 0:
                        st.error("กรุณากรอก สี, จำนวนต่อจิ๊ก และ ยอดรวม ให้ครบถ้วน")
                    else:
                        try:
                            supabase.table("jig_usage_log").insert({
                                "product_code": sel_product,
                                "color": sel_color,
                                "jig_id": jig_list[selected_jig_name],
                                "pcs_per_jig": pcs_jig,
                                "total_pieces": total,
                                "recorded_date": str(datetime.date.today())
                            }).execute()
                            st.success("บันทึกข้อมูลสำเร็จ!")
                        except Exception as e:
                            st.error(f"Error: {e}")
        else:
            st.warning("กรุณาลงทะเบียนสินค้าและจิ๊กก่อนบันทึกข้อมูล")
