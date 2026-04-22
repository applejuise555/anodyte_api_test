import streamlit as st
from supabase import create_client
import datetime
from datetime import datetime, timezone, timedelta

# 1. สร้างตัวแปร Timezone สำหรับประเทศไทย (UTC +7)
ICT = timezone(timedelta(hours=7))
# --- 1. การตั้งค่าเชื่อมต่อ ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ Supabase: {e}")

st.set_page_config(page_title="Production Log System", layout="wide")
st.title("ระบบบันทึกข้อมูลการผลิต")

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
    sub_prod, sub_jig, sub_log = st.tabs(["1. ลงทะเบียนชิ้นงาน", "2. ลงทะเบียนจิ๊ก", "3. บันทึกผลผลิต"])
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

# --- วางไว้ข้างนอกฟอร์ม เพื่อให้แสดงผลทันที ---
sel_c = st.pills("เลือกสี", list(color_hex_map.keys()), selection_mode="single")

if sel_c:
    st.markdown(
        f"""<div style="display: flex; align-items: center; margin-bottom: 10px;">
            <div style="width: 20px; height: 20px; background-color: {color_hex_map[sel_c]}; border-radius: 4px; margin-right: 10px;"></div>
            <span>เลือกสี: <b>{sel_c}</b></span>
        </div>""", unsafe_allow_html=True
    )

# --- ส่วนของฟอร์ม (ไว้ข้างล่าง) ---
with st.form("log_prod_form", clear_on_submit=True):
    # ช่องกรอกข้อมูลต่างๆ
    pcs_per_row = st.number_input("จำนวนต่อแถว", min_value=0, step=1)
    rows_filled = st.number_input("จำนวนแถวที่เต็ม", min_value=0, step=1)
    partial_pieces = st.number_input("เศษชิ้นงาน", min_value=0, step=1)
    
    if st.form_submit_button("บันทึกการผลิต"):
        # ตรวจสอบว่าเลือกสีแล้วหรือยัง
        if not sel_c:
            st.error("กรุณาเลือกสีก่อนกดบันทึก!")
        else:
            # ใช้ sel_c จากด้านบนได้เลย เพราะมันค้างอยู่ในตัวแปรแล้ว
            total_pieces = (rows_filled * pcs_per_row) + partial_pieces
            try:
                insert_data = {
                    "product_id": prods[sel_p],
                    "jig_id": jig_id,
                    "color": sel_c,  # ใช้ตัวแปร sel_c ที่เลือกไว้ด้านบน
                    "pcs_per_row": pcs_per_row,
                    "rows_filled": rows_filled,
                    "partial_pieces": partial_pieces,
                    "total_pieces": total_pieces,
                    "recorded_date": datetime.now(ICT).isoformat()
                }
                supabase.table("jig_usage_log").insert(insert_data).execute()
                st.success(f"บันทึกข้อมูลสำเร็จ! ({total_pieces} ชิ้น)")
            except Exception as e:
                st.error(f"Error: {e}")
