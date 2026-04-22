import streamlit as st
from supabase import create_client
import datetime

# --- การตั้งค่าเริ่มต้น ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Production Log System", layout="wide")
st.title("ระบบบันทึกข้อมูลการผลิต (Anodize & Color)")

# ฟังก์ชันดึงข้อมูลมาทำ Dropdown
def get_dropdown_options(table_name, id_col, name_col, filter_col=None, filter_val=None):
    try:
        query = supabase.table(table_name).select(f"{id_col}, {name_col}")
        if filter_col and filter_val:
            query = query.eq(filter_col, filter_val)
        response = query.execute()
        return {item[name_col]: item[id_col] for item in response.data}
    except Exception as e:
        st.error(f"Error loading {table_name}: {e}")
        return {}

# --- สร้าง Tabs หลัก ---
tab1, tab2, tab3 = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig)"])

# --- TAB 1: บ่อสี ---
with tab1:
    st.header("บันทึกข้อมูลบ่อสี")
    color_tanks = get_dropdown_options("tanks", "tank_id", "tank_name", "tank_type", "Color")
    if color_tanks:
        selected_tank = st.selectbox("เลือกบ่อสี", list(color_tanks.keys()))
        with st.form("color_log_form"):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            if st.form_submit_button("บันทึกข้อมูลบ่อสี"):
                if ph == 0 or temp == 0:
                    st.error("กรุณากรอกค่า pH และอุณหภูมิให้ครบถ้วน")
                else:
                    data = {"tank_id": color_tanks[selected_tank], "ph_value": ph, "temperature": temp}
                    supabase.table("color_tank_logs").insert(data).execute()
                    st.success("บันทึกสำเร็จ!")
    else:
        st.warning("ยังไม่มีข้อมูลบ่อสีในระบบ")

# --- TAB 2: บ่ออโนไดซ์ ---
with tab2:
    st.header("บันทึกข้อมูลบ่ออโนไดซ์")
    anodize_tanks = get_dropdown_options("tanks", "tank_id", "tank_name", "tank_type", "Anodize")
    if anodize_tanks:
        selected_tank = st.selectbox("เลือกบ่ออโนไดซ์", list(anodize_tanks.keys()))
        with st.form("anodize_log_form"):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            density = st.number_input("ความหนาแน่น (Density)", step=0.001, format="%.3f")
            if st.form_submit_button("บันทึกข้อมูลบ่ออโนไดซ์"):
                if ph == 0 or temp == 0 or density == 0:
                    st.error("กรุณากรอกข้อมูลบ่ออโนไดซ์ให้ครบถ้วน")
                else:
                    data = {"tank_id": anodize_tanks[selected_tank], "ph_value": ph, "temperature": temp, "density": density}
                    supabase.table("anodize_tank_logs").insert(data).execute()
                    st.success("บันทึกสำเร็จ!")
    else:
        st.warning("ยังไม่มีข้อมูลบ่ออโนไดซ์ในระบบ")

# --- TAB 3: งานจิ๊ก ---
with tab3:
    sub_prod_reg, sub_jig_reg, sub_log = st.tabs(["1. ลงทะเบียนชิ้นงานใหม่", "2. ลงทะเบียนจิ๊กใหม่", "3. บันทึกผลผลิตรายวัน"])

    # ส่วนที่ 1: ลงทะเบียนสินค้า
    with sub_prod_reg:
        st.subheader("เพิ่มฐานข้อมูลชิ้นงานใหม่")
        with st.form("register_product_form"):
            col1, col2 = st.columns(2)
            with col1:
                p_code = st.text_input("รหัสสินค้า (ใช้ค้นหา)")
                p_name = st.text_input("ชื่อชิ้นงาน")
            with col2:
                height = st.number_input("สูง (Height)")
                width = st.number_input("กว้าง (Width)")
            
            if st.form_submit_button("บันทึกฐานข้อมูลสินค้า"):
                if not p_code or not p_name:
                    st.error("กรุณากรอก รหัสสินค้า และ ชื่อชิ้นงาน ให้ครบ")
                else:
                    data = {"product_code": p_code, "product_name": p_name, "height": height, "width": width}
                    supabase.table("product_specifications").insert(data).execute()
                    st.success(f"บันทึกสินค้า {p_code} เรียบร้อย!")

    # ส่วนที่ 2: ลงทะเบียนจิ๊กใหม่
    with sub_jig_reg:
        st.subheader("เพิ่มข้อมูลจิ๊กใหม่")
        with st.form("new_jig_form"):
            new_jig_code = st.text_input("ตั้งรหัสจิ๊กใหม่ (Jig Model Code)")
            if st.form_submit_button("บันทึกจิ๊กใหม่"):
                if not new_jig_code:
                    st.error("กรุณาระบุรหัสจิ๊กใหม่")
                else:
                    supabase.table("jigs").insert({"jig_model_code": new_jig_code}).execute()
                    st.success(f"บันทึกจิ๊ก {new_jig_code} เรียบร้อย!")

    # ส่วนที่ 3: บันทึกการผลิต
    with sub_log:
        st.subheader("บันทึกข้อมูลการผลิตรายวัน")
        product_list = get_dropdown_options("product_specifications", "product_code", "product_code")
        jig_list = get_dropdown_options("jigs", "jig_id", "jig_model_code")
        
        if product_list and jig_list:
            with st.form("daily_production_form"):
                sel_product = st.selectbox("เลือกรหัสสินค้า", list(product_list.keys()))
                sel_color = st.text_input("สี (Color ที่ผลิตในล็อตนี้)")
                selected_jig_name = st.selectbox("เลือกจิ๊กที่ใช้", list(jig_list.keys()))
                
                col_a, col_b = st.columns(2)
                with col_a:
                    pcs_jig = st.number_input("จำนวนชิ้นต่อจิ๊ก", step=1)
                with col_b:
                    pcs_row = st.number_input("จำนวนชิ้นต่อแถว", step=1)
                
                total_pieces = st.number_input("จำนวนชิ้นงานรวมทั้งหมด", step=1)
                
                if st.form_submit_button("บันทึกผลผลิต"):
                    # Validate ว่าข้อมูลห้ามว่าง
                    if not sel_color or total_pieces == 0 or pcs_jig == 0:
                        st.error("กรุณากรอก สี, จำนวนชิ้นต่อจิ๊ก และ ยอดรวม ให้ครบถ้วน")
                    else:
                        target_jig_id = jig_list[selected_jig_name]
                        data = {
                            "product_code": sel_product,
                            "color": sel_color,
                            "jig_id": target_jig_id,
                            "pcs_per_jig": pcs_jig,
                            "pcs_per_row": pcs_row,
                            "total_pieces": total_pieces,
                            "recorded_date": str(datetime.date.today())
                        }
                        supabase.table("jig_usage_log").insert(data).execute()
                        st.success(f"บันทึกยอดการผลิตสำหรับจิ๊ก {selected_jig_name} สำเร็จ!")
        else:
            st.warning("โปรดตรวจสอบว่ามีการลงทะเบียน สินค้า หรือ จิ๊ก ในระบบแล้ว")
