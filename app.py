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
st.title("ระบบบันทึกข้อมูลการผลิต (Full Corrected Version)")

def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    try:
        query = supabase.table(table).select(f"{id_col}, {name_col}")
        if filter_col and filter_val:
            query = query.eq(filter_col, filter_val)
        response = query.execute()
        return {item[name_col]: item[id_col] for item in response.data}
    except Exception as e:
        return {}

# --- โครงสร้าง Tabs ---
tab1, tab2, tab3 = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig)"])

# --- TAB 1 & 2 ---
with tab1:
    st.header("บันทึกข้อมูลบ่อสี")
    color_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")
    if color_tanks:
        selected_tank = st.selectbox("เลือกบ่อสี", list(color_tanks.keys()))
        with st.form("color_log_form", clear_on_submit=True):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            if st.form_submit_button("บันทึก"):
                supabase.table("color_tank_logs").insert({"tank_id": color_tanks[selected_tank], "ph_value": ph, "temperature": temp}).execute()
                st.success("บันทึกข้อมูลสำเร็จ!")

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
                supabase.table("anodize_tank_logs").insert({"tank_id": anodize_tanks[selected_tank], "ph_value": ph, "temperature": temp, "density": density}).execute()
                st.success("บันทึกข้อมูลสำเร็จ!")

# --- TAB 3: งานจิ๊ก ---
with tab3:
    with sub_prod:
        with st.form("new_product_form", clear_on_submit=True):
            p_code = st.text_input("รหัสสินค้า")
            p_name = st.text_input("ชื่อชิ้นงาน")
            
            # --- เพิ่มฟิลด์ลักษณะพื้นผิวตรงนี้ ---
            surface_finish = st.text_input("ลักษณะพื้นผิว (Surface Finish)")
            # หรือถ้ามีรายการที่ใช้บ่อย ให้เปลี่ยนเป็น selectbox แบบนี้ครับ:
            # surface_finish = st.selectbox("ลักษณะพื้นผิว", ["Polished", "Matte", "Sandblasted", "Anodized"])
            
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
                try:
                    # เพิ่ม "surface_finish": surface_finish เข้าไปในนี้
                    supabase.table("products").insert({
                        "product_code": p_code, 
                        "product_name": p_name,
                        "surface_finish": surface_finish, # เพิ่มบรรทัดนี้
                        "height": h, 
                        "width": w, 
                        "thickness": t,
                        "depth": d, 
                        "outer_diameter": od, 
                        "inner_diameter": id_val
                    }).execute()
                    st.success("บันทึกสินค้าสำเร็จ!")
                except Exception as e:
                    st.error(f"Error: {e}")

    with sub_jig:
        with st.form("new_jig_form", clear_on_submit=True):
            jig_code = st.text_input("รหัสจิ๊ก")
            if st.form_submit_button("บันทึกจิ๊ก"):
                supabase.table("jigs").insert({"jig_model_code": jig_code}).execute()
                st.success("สำเร็จ!")

    with sub_log:
        prods = get_options("products", "product_id", "product_code")
        jigs = get_options("jigs", "jig_id", "jig_model_code")
        all_colors = get_options("colors", "color_id", "color_name") 

        if prods and jigs:
            sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))
            sel_j = st.selectbox("เลือกจิ๊ก", list(jigs.keys()))
            
            jig_id = jigs[sel_j]
            last_color = None
            try:
                # แก้ไขชื่อคอลัมน์เป็น "color" ให้ตรงกับ DB
                hist = supabase.table("jig_usage_log").select("color").eq("jig_id", jig_id).order("recorded_date", desc=True).limit(1).execute()
                if hist.data:
                    last_color = hist.data[0]['color']
            except:
                pass
            
            color_names = list(all_colors.keys())
            default_idx = color_names.index(last_color) if last_color in color_names else 0

            with st.form("log_prod_form", clear_on_submit=True):
                sel_c = st.selectbox("เลือกสี", color_names, index=default_idx)
                
                # Input สำหรับคอลัมน์ที่บังคับ (Not Null ตามฐานข้อมูล)
                pcs_per_row = st.number_input("จำนวนต่อแถว (pcs_per_row)", min_value=0, step=1)
                pcs_per_jig = st.number_input("จำนวนต่อจิ๊ก (pcs_per_jig)", min_value=0, step=1)
                total_pieces = st.number_input("จำนวนรวม (total_pieces)", min_value=0, step=1)
                
                if st.form_submit_button("บันทึกการผลิต"):
                    try:
                        # สร้าง Dictionary ให้ตรงชื่อคอลัมน์ในฐานข้อมูลเป๊ะๆ
                        insert_data = {
                            "product_id": prods[sel_p],
                            "jig_id": jig_id,
                            "color": sel_c,            # ชื่อคอลัมน์คือ 'color'
                            "pcs_per_row": pcs_per_row,
                            "pcs_per_jig": pcs_per_jig,
                            "total_pieces": total_pieces, # เพิ่มเพื่อให้ครบ Not-null
                            "recorded_date": str(datetime.date.today())
                        }
                        
                        supabase.table("jig_usage_log").insert(insert_data).execute()
                        st.success("บันทึกผลผลิตสำเร็จ!")
                    except Exception as e:
                        st.error(f"Error: {e}")
