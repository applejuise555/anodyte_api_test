import streamlit as st
from supabase import create_client
import datetime

# --- 1. การตั้งค่าเชื่อมต่อ ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ Supabase: {e}")

st.set_page_config(page_title="Production Log System", layout="wide")
st.title("ระบบบันทึกข้อมูลการผลิต (Updated System)")

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
        selected_tank = st.selectbox("เลือกบ่อสี", list(color_tanks.keys()))
        with st.form("color_log_form", clear_on_submit=True):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            if st.form_submit_button("บันทึก"):
                if ph <= 0 or temp <= 0:
                    st.warning("กรุณากรอกค่า pH และอุณหภูมิให้ถูกต้อง")
                else:
                    try:
                        supabase.table("color_tank_logs").insert({"tank_id": color_tanks[selected_tank], "ph_value": ph, "temperature": temp}).execute()
                        st.success("บันทึกข้อมูลสำเร็จ!")
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
                    st.warning("กรุณากรอกข้อมูลให้ครบถ้วน")
                else:
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
            st.subheader("ข้อมูลทั่วไป")
            p_code = st.text_input("รหัสสินค้า (Unique)")
            p_name = st.text_input("ชื่อชิ้นงาน")
            
            st.subheader("ขนาดและมิติ (Dimensions)")
            col1, col2 = st.columns(2)
            h = col1.number_input("ความสูง (height)", 0.0, format="%.2f")
            w = col2.number_input("ความกว้าง (width)", 0.0, format="%.2f")
            col3, col4 = st.columns(2)
            t = col3.number_input("ความหนา (thickness)", 0.0, format="%.2f")
            d = col4.number_input("ความลึก (depth)", 0.0, format="%.2f")
            col5, col6 = st.columns(2)
            od = col5.number_input("เส้นผ่านศูนย์กลางภายนอก (outer_diameter)", 0.0, format="%.2f")
            id_val = col6.number_input("เส้นผ่านศูนย์กลางภายใน (inner_diameter)", 0.0, format="%.2f")
            
            if st.form_submit_button("บันทึกสินค้า"):
                if not p_code or not p_name:
                    st.warning("กรุณากรอกรหัสและชื่อสินค้าให้ครบถ้วน")
                else:
                    try:
                        supabase.table("products").insert({
                            "product_code": p_code, "product_name": p_name,
                            "height": h, "width": w, "thickness": t,
                            "depth": d, "outer_diameter": od, "inner_diameter": id_val
                        }).execute()
                        st.success("ลงทะเบียนสินค้าสำเร็จ!")
                    except Exception as e:
                        st.error(f"Error: {e}")

    with sub_jig:
        with st.form("new_jig_form", clear_on_submit=True):
            jig_code = st.text_input("รหัสจิ๊ก")
            if st.form_submit_button("บันทึกจิ๊ก"):
                if not jig_code:
                    st.warning("กรุณากรอกรหัสจิ๊ก")
                else:
                    try:
                        supabase.table("jigs").insert({"jig_model_code": jig_code}).execute()
                        st.success("บันทึกจิ๊กสำเร็จ")
                    except Exception as e:
                        st.error(f"Error: {e}")

    with sub_log:
        prods = get_options("products", "product_id", "product_code")
        jigs = get_options("jigs", "jig_id", "jig_model_code")
        all_colors = get_options("colors", "color_id", "color_name")

        if prods and jigs and all_colors:
            # 1. เลือกสินค้าและจิ๊ก
            sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))
            sel_j = st.selectbox("เลือกจิ๊ก", list(jigs.keys()))
            
            # 2. Logic: หาสีล่าสุดจากจิ๊กที่เลือก
            jig_id = jigs[sel_j]
            default_color_idx = 0
            try:
                # ดึง log ล่าสุดของจิ๊กนี้
                hist = supabase.table("jig_usage_log").select("color_id").eq("jig_id", jig_id).order("recorded_date", desc=True).limit(1).execute()
                if hist.data:
                    last_color_id = hist.data[0]['color_id']
                    # หา index ของสีล่าสุดใน List เพื่อตั้งเป็นค่า Default
                    color_names = list(all_colors.keys())
                    # กลับค่าเพื่อหาชื่อจาก ID
                    rev_colors = {v: k for k, v in all_colors.items()}
                    if last_color_id in rev_colors:
                        last_color_name = rev_colors[last_color_id]
                        if last_color_name in color_names:
                            default_color_idx = color_names.index(last_color_name)
            except:
                pass

            with st.form("log_prod_form", clear_on_submit=True):
                # 3. เลือกสี (ตั้งค่า default ตามที่หามาได้)
                sel_c = st.selectbox("เลือกสี", list(all_colors.keys()), index=default_color_idx)
                pcs_jig = st.number_input("จำนวนต่อจิ๊ก", min_value=1)
                
                if st.form_submit_button("บันทึกการผลิต"):
                    try:
                        supabase.table("jig_usage_log").insert({
                            "product_id": prods[sel_p],
                            "jig_id": jig_id,
                            "color_id": all_colors[sel_c],
                            "pcs_per_jig": pcs_jig,
                            "recorded_date": str(datetime.date.today())
                        }).execute()
                        st.success("บันทึกผลผลิตสำเร็จ!")
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.warning("กรุณาลงทะเบียน สินค้า, จิ๊ก และเพิ่มรายชื่อสี ให้ครบก่อน")
