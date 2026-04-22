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
st.title("ระบบบันทึกข้อมูลการผลิต (Final Consolidated Version)")

# --- ฟังก์ชันตัวช่วย ---
def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    """ดึงข้อมูลจากตารางมาแสดงเป็น Dropdown"""
    try:
        query = supabase.table(table).select(f"{id_col}, {name_col}")
        if filter_col and filter_val:
            query = query.eq(filter_col, filter_val)
        response = query.execute()
        return {item[name_col]: item[id_col] for item in response.data}
    except:
        return {}

def get_daily_total(jig_id):
    """คำนวณยอดรวมรายจิ๊กของวันนี้"""
    try:
        today = str(datetime.date.today())
        response = supabase.table("jig_usage_log") \
            .select("total_pieces") \
            .eq("jig_id", jig_id) \
            .eq("recorded_date", today) \
            .execute()
        return sum(item['total_pieces'] for item in response.data if item['total_pieces'])
    except:
        return 0

# --- ส่วนของ Tabs ---
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
                supabase.table("color_tank_logs").insert({"tank_id": color_tanks[selected_tank], "ph_value": ph, "temperature": temp}).execute()
                st.success("บันทึกข้อมูลสำเร็จ!")

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
                supabase.table("anodize_tank_logs").insert({"tank_id": anodize_tanks[selected_tank], "ph_value": ph, "temperature": temp, "density": density}).execute()
                st.success("บันทึกข้อมูลสำเร็จ!")

# --- TAB 3: งานจิ๊ก ---
with tab3:
    sub_prod, sub_jig, sub_log = st.tabs(["1. ลงทะเบียนชิ้นงาน", "2. ลงทะเบียนจิ๊ก", "3. บันทึกผลผลิต"])

   with sub_prod:
        with st.form("new_product_form", clear_on_submit=True):
            st.subheader("รายละเอียดชิ้นงาน")
            p_code = st.text_input("รหัสสินค้า (Product Code)")
            p_name = st.text_input("ชื่อชิ้นงาน (Product Name)")
            
            # แบ่งคอลัมน์เพื่อให้หน้า UI ดูเรียบร้อยขึ้น
            col1, col2 = st.columns(2)
            with col1:
                h = st.number_input("Height", min_value=0.0, format="%.2f")
                w = st.number_input("Width", min_value=0.0, format="%.2f")
                t = st.number_input("Thickness", min_value=0.0, format="%.2f")
            with col2:
                d = st.number_input("Depth", min_value=0.0, format="%.2f")
                od = st.number_input("Outer Diameter", min_value=0.0, format="%.2f")
                id_val = st.number_input("Inner Diameter", min_value=0.0, format="%.2f")
            
            if st.form_submit_button("บันทึกสินค้า"):
                try:
                    # ข้อมูลที่ตรงกับคอลัมน์ในตาราง products จากภาพ image_366406.png
                    product_data = {
                        "product_code": p_code,
                        "product_name": p_name,
                        "height": h,
                        "width": w,
                        "thickness": t,
                        "depth": d,
                        "outer_diameter": od,
                        "inner_diameter": id_val
                    }
                    supabase.table("products").insert(product_data).execute()
                    st.success(f"ลงทะเบียนสินค้า {p_code} สำเร็จ!")
                except Exception as e:
                    st.error(f"ไม่สามารถบันทึกสินค้าได้: {e}")

    with sub_jig:
        with st.form("new_jig_form", clear_on_submit=True):
            jig_code = st.text_input("รหัสจิ๊ก")
            if st.form_submit_button("บันทึกจิ๊ก"):
                supabase.table("jigs").insert({"jig_model_code": jig_code}).execute()
                st.success("สำเร็จ!")

    with sub_log:
        prods = get_options("products", "product_id", "product_code")
        jigs = get_options("jigs", "jig_id", "jig_model_code")
        
        # สมมติชื่อสีในระบบ (ถ้ามีตารางสีแยกต่างหาก ให้เปลี่ยนเป็น get_options("colors", ...))
        color_list = ["Red", "Blue", "Black", "Gold", "Silver"] 

        if prods and jigs:
            sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))
            sel_j = st.selectbox("เลือกจิ๊ก", list(jigs.keys()))
            
            jig_id = jigs[sel_j]
            product_id = prods[sel_p]
            
            # โชว์ยอดรวมสะสมวันนี้ (เพื่อช่วยให้พนักงานเห็นภาพรวม)
            st.metric("ยอดผลิตรวมของจิ๊กนี้ (วันนี้)", value=f"{get_daily_total(jig_id)} ชิ้น")

            with st.form("log_prod_form", clear_on_submit=True):
                sel_c = st.selectbox("เลือกสี", color_list)
                pcs_row = st.number_input("จำนวนต่อแถว (pcs_per_row)", min_value=0, step=1)
                pcs_jig = st.number_input("จำนวนต่อจิ๊ก (pcs_per_jig)", min_value=0, step=1)
                total_pcs = st.number_input("จำนวนรวม (total_pieces)", min_value=0, step=1)
                
                if st.form_submit_button("บันทึกการผลิต"):
                    # ข้อมูลที่ส่งเข้า Database (ต้องตรงกับชื่อ Column ใน Supabase เป๊ะๆ)
                    insert_data = {
                        "product_id": product_id,
                        "jig_id": jig_id,
                        "color": sel_c,
                        "pcs_per_row": int(pcs_row),
                        "pcs_per_jig": int(pcs_jig),
                        "total_pieces": int(total_pcs),
                        "recorded_date": str(datetime.date.today())
                    }
                    
                    try:
                        supabase.table("jig_usage_log").insert(insert_data).execute()
                        st.success("บันทึกข้อมูลสำเร็จ!")
                        st.rerun() # รีเฟรชหน้าจอเพื่ออัปเดตยอดรวม
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาดในการบันทึก: {e}")
