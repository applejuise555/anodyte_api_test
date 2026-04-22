import streamlit as st
from supabase import create_client
import datetime

# --- 1. การตั้งค่าเริ่มต้น ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ Supabase: {e}")

st.set_page_config(page_title="Production Log System", layout="wide")
st.title("ระบบบันทึกข้อมูลการผลิต (New Schema)")

# ฟังก์ชันดึงข้อมูลมาทำ Dropdown (ส่งกลับเป็น Dict {name: id})
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
        selected_tank = st.selectbox("เลือกบ่อสี", list(color_tanks.keys()))
        with st.form("color_log_form", clear_on_submit=True):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            if st.form_submit_button("บันทึก"):
                if ph <= 0 or temp <= 0:
                    st.error("กรุณากรอกค่า pH และอุณหภูมิ")
                else:
                    try:
                        supabase.table("color_tank_logs").insert({
                            "tank_id": color_tanks[selected_tank], "ph_value": ph, "temperature": temp
                        }).execute()
                        st.success("บันทึกข้อมูลบ่อสีสำเร็จ!")
                    except Exception as e:
                        st.error(f"Error: {e}")

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
                if ph <= 0 or temp <= 0 or density <= 0:
                    st.error("กรุณากรอกข้อมูลให้ครบถ้วน")
                else:
                    try:
                        supabase.table("anodize_tank_logs").insert({
                            "tank_id": anodize_tanks[selected_tank], "ph_value": ph, "temperature": temp, "density": density
                        }).execute()
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
            c1, c2 = st.columns(2)
            height = c1.number_input("สูง", 0.0)
            width = c2.number_input("กว้าง", 0.0)
            c3, c4 = st.columns(2)
            thick = c3.number_input("หนา", 0.0)
            depth = c4.number_input("ลึก", 0.0)
            c5, c6 = st.columns(2)
            out_d = c5.number_input("เส้นผ่านศูนย์กลางภายนอก", 0.0)
            in_d = c6.number_input("เส้นผ่านศูนย์กลางภายใน", 0.0)
            
            if st.form_submit_button("บันทึกสินค้า"):
                if not p_code or not p_name:
                    st.error("กรุณากรอกรหัสและชื่อ")
                else:
                    try:
                        supabase.table("products").insert({
                            "product_code": p_code, "product_name": p_name, "height": height, 
                            "width": width, "thickness": thick, "depth": depth,
                            "outer_diameter": out_d, "inner_diameter": in_d
                        }).execute()
                        st.success("ลงทะเบียนสินค้าสำเร็จ")
                    except Exception as e:
                        st.error(f"Error: {e}")

    with sub_jig:
        with st.form("new_jig_form", clear_on_submit=True):
            jig_code = st.text_input("รหัสจิ๊ก")
            if st.form_submit_button("บันทึกจิ๊ก"):
                if not jig_code: st.error("ระบุรหัสจิ๊ก")
                else:
                    supabase.table("jigs").insert({"jig_model_code": jig_code}).execute()
                    st.success("บันทึกจิ๊กสำเร็จ")

    with sub_log:
        # ดึง ID มาทั้งหมด
        prods = get_options("products", "product_id", "product_code")
        jigs = get_options("jigs", "jig_id", "jig_model_code")
        cols = get_options("colors", "color_id", "color_name")
        tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")

        if prods and jigs and cols and tanks:
            with st.form("log_prod_form", clear_on_submit=True):
                sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))
                sel_j = st.selectbox("เลือกจิ๊ก", list(jigs.keys()))
                sel_c = st.selectbox("เลือกสี", list(cols.keys()))
                sel_t = st.selectbox("เลือกบ่อสี", list(tanks.keys()))
                pcs_jig = st.number_input("จำนวนต่อจิ๊ก", min_value=1)
                total = st.number_input("จำนวนรวม", min_value=1)
                
                if st.form_submit_button("บันทึกการผลิต"):
                    try:
                        supabase.table("jig_usage_log").insert({
                            "product_id": prods[sel_p],
                            "jig_id": jigs[sel_j],
                            "color_id": cols[sel_c],
                            "tank_id": tanks[sel_t],
                            "pcs_per_jig": pcs_jig,
                            "total_pieces": total,
                            "recorded_date": str(datetime.date.today())
                        }).execute()
                        st.success("บันทึกผลผลิตสำเร็จ!")
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.warning("กรุณาลงทะเบียน สินค้า, จิ๊ก, สี และ บ่อ ให้ครบก่อนบันทึกข้อมูล")
