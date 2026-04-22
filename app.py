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
st.title("ระบบบันทึกข้อมูลการผลิต (Full System)")

# --- Helper Functions ---
def get_options(table, id_col, name_col):
    try:
        response = supabase.table(table).select(f"{id_col}, {name_col}").execute()
        return {item[name_col]: item[id_col] for item in response.data}
    except:
        return {}

# --- Tabs หลัก ---
tab1, tab2, tab3 = st.tabs(["บ่อสี", "บ่ออโนไดซ์", "งานจิ๊ก"])

# --- TAB 1: บ่อสี ---
with tab1:
    st.header("บันทึกข้อมูลบ่อสี (Color Tank)")
    with st.form("color_log_form", clear_on_submit=True):
        # ปรับเปลี่ยน key ใน dict ให้ตรงกับชื่อคอลัมน์ในตาราง color_tank_logs ของคุณ
        value_data = st.number_input("ค่าที่บันทึก (เช่น อุณหภูมิ/ความเข้มข้น)", format="%.2f")
        note = st.text_input("หมายเหตุ")
        
        if st.form_submit_button("บันทึกข้อมูลบ่อสี"):
            try:
                supabase.table("color_tank_logs").insert({
                    "value": value_data,
                    "note": note,
                    "created_at": str(datetime.datetime.now())
                }).execute()
                st.success("บันทึกข้อมูลบ่อสีสำเร็จ!")
            except Exception as e:
                st.error(f"Error: {e}")

# --- TAB 2: บ่ออโนไดซ์ ---
with tab2:
    st.header("บันทึกข้อมูลบ่ออโนไดซ์ (Anodize Tank)")
    with st.form("anodize_log_form", clear_on_submit=True):
        value_data = st.number_input("ค่าที่บันทึก", format="%.2f")
        note = st.text_input("หมายเหตุ")
        
        if st.form_submit_button("บันทึกข้อมูลบ่ออโนไดซ์"):
            try:
                supabase.table("anodize_tank_logs").insert({
                    "value": value_data,
                    "note": note,
                    "created_at": str(datetime.datetime.now())
                }).execute()
                st.success("บันทึกข้อมูลบ่ออโนไดซ์สำเร็จ!")
            except Exception as e:
                st.error(f"Error: {e}")

# --- TAB 3: งานจิ๊ก ---
with tab3:
    sub_prod, sub_jig, sub_log = st.tabs(["1. ลงทะเบียนชิ้นงาน", "2. ลงทะเบียนจิ๊ก", "3. บันทึกผลผลิต"])

    with sub_prod:
           with sub_prod:
        with st.form("new_product_form", clear_on_submit=True):
            p_code = st.text_input("รหัสสินค้า")
            p_name = st.text_input("ชื่อชิ้นงาน")
            h = st.number_input("Height", 0.0, format="%.2f")
            w = st.number_input("Width", 0.0, format="%.2f")
            t = st.number_input("Thickness", 0.0, format="%.2f")
            d = st.number_input("Depth", 0.0, format="%.2f")
            od = st.number_input("Outer Diameter", 0.0, format="%.2f")
            id_val = st.number_input("Inner Diameter", 0.0, format="%.2f")
            
            if st.form_submit_button("บันทึกสินค้า"):
                try:
                    supabase.table("products").insert({
                        "product_code": p_code, "product_name": p_name,
                        "height": h, "width": w, "thickness": t,
                        "depth": d, "outer_diameter": od, "inner_diameter": id_val
                    }).execute()
                    st.success("บันทึกสินค้าสำเร็จ!")
                except Exception as e:
                    st.error(f"Error: {e}")

        st.write("ฟอร์มลงทะเบียนชิ้นงาน")

    with sub_jig:
        with st.form("new_jig_form", clear_on_submit=True):
            jig_code = st.text_input("รหัสจิ๊ก")
            if st.form_submit_button("บันทึกจิ๊ก"):
                supabase.table("jigs").insert({"jig_model_code": jig_code}).execute()
                st.success("บันทึกจิ๊กสำเร็จ!")
        st.write("ฟอร์มลงทะเบียนจิ๊ก")

    with sub_log:
        prods = get_options("products", "product_id", "product_code")
        jigs = get_options("jigs", "jig_id", "jig_model_code")
        colors = get_options("colors", "color_id", "color_name")
        
        if prods and jigs and colors:
            sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))
            sel_j = st.selectbox("เลือกจิ๊ก", list(jigs.keys()))
            sel_c = st.selectbox("เลือกสี", list(colors.keys()))
            
            with st.form("log_prod_form", clear_on_submit=True):
                pcs_row = st.number_input("จำนวนต่อแถว", min_value=0, step=1)
                pcs_jig = st.number_input("จำนวนต่อจิ๊ก", min_value=0, step=1)
                total_pcs = st.number_input("จำนวนรวม", min_value=0, step=1)
                
                if st.form_submit_button("บันทึกการผลิต"):
                    try:
                        supabase.table("jig_usage_log").insert({
                            "product_id": prods[sel_p],
                            "jig_id": jigs[sel_j],
                            "color": sel_c,
                            "pcs_per_row": int(pcs_row),
                            "pcs_per_jig": int(pcs_jig),
                            "total_pieces": int(total_pcs),
                            "recorded_date": str(datetime.date.today())
                        }).execute()
                        st.success("บันทึกผลผลิตสำเร็จ!")
                    except Exception as e:
                        st.error(f"ไม่สามารถบันทึกได้: {e}")
