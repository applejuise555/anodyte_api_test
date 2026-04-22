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
st.title("ระบบบันทึกข้อมูลการผลิต (Full Corrected)")

# --- Helper Functions ---
def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    try:
        query = supabase.table(table).select(f"{id_col}, {name_col}")
        if filter_col and filter_val:
            query = query.eq(filter_col, filter_val)
        response = query.execute()
        return {item[name_col]: item[id_col] for item in response.data}
    except:
        return {}

def get_daily_total(jig_id):
    """ฟังก์ชันคำนวณยอดรวมรายจิ๊กของวันนี้"""
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

def get_standard_capacity(product_id, jig_id):
    """ดึงค่ามาตรฐาน (สมมติคุณมีตาราง jig_standard หรือดึงจาก products)"""
    # ถ้ายังไม่มีตารางมาตรฐาน ให้ return 0 หรือค่า default
    return 0 

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["บ่อสี", "บ่ออโนไดซ์", "งานจิ๊ก"])

# --- TAB 3: งานจิ๊ก (ที่แก้ไข) ---
with tab3:
    sub_prod, sub_jig, sub_log = st.tabs(["1. ลงทะเบียนชิ้นงาน", "2. ลงทะเบียนจิ๊ก", "3. บันทึกผลผลิต"])

    with sub_log:
        prods = get_options("products", "product_id", "product_code")
        jigs = get_options("jigs", "jig_id", "jig_model_code")
        all_colors = get_options("colors", "color_id", "color_name") 

        if prods and jigs:
            sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))
            sel_j = st.selectbox("เลือกจิ๊ก", list(jigs.keys()))
            
            jig_id = jigs[sel_j]
            
            # โชว์ยอดรวมของจิ๊กนี้ในวันนี้ (แบบ Real-time)
            current_total = get_daily_total(jig_id)
            st.metric("ยอดรวมสะสมของจิ๊กนี้ (วันนี้)", value=f"{current_total} ชิ้น")

            with st.form("log_prod_form", clear_on_submit=True):
                sel_c = st.selectbox("เลือกสี", list(all_colors.keys()))
                
                # Input ค่าจริงที่ผลิตได้
                actual_qty = st.number_input("จำนวนที่ผลิตได้ในรอบนี้ (pcs)", min_value=0, step=1)
                
                # ฟิลด์เสริม (ถ้าจำเป็นต้องมีตาม DB)
                pcs_row = st.number_input("จำนวนต่อแถว (ระบุ 0 ถ้าไม่ทราบ)", min_value=0, step=1)
                
                if st.form_submit_button("บันทึกผลผลิต"):
                    try:
                        # สร้าง Dictionary (ตรวจสอบชื่อคอลัมน์ให้ตรง DB)
                        insert_data = {
                            "product_id": prods[sel_p],
                            "jig_id": jig_id,
                            "color": sel_c,            # ชื่อต้องตรงกับ DB (color)
                            "total_pieces": actual_qty,
                            "pcs_per_row": pcs_row,
                            "recorded_date": str(datetime.date.today())
                        }
                        
                        supabase.table("jig_usage_log").insert(insert_data).execute()
                        st.success("บันทึกสำเร็จ!")
                        st.rerun() # รีเฟรชเพื่ออัปเดตยอดรวม
                    except Exception as e:
                        st.error(f"Error: {e}")
                        st.write("คำแนะนำ: หาก Error ว่า Column ไม่พบ ให้เช็คชื่อคอลัมน์ใน DB อีกครั้ง")
