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
        return {}

# --- สร้าง Tabs หลัก ---
tab1, tab2, tab3 = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig)"])

# --- TAB 1: บ่อสี ---
with tab1:
    st.header("บันทึกข้อมูลบ่อสี")
    # ... (โค้ดส่วนบ่อสีเดิมของคุณ)

# --- TAB 2: บ่ออโนไดซ์ ---
with tab2:
    st.header("บันทึกข้อมูลบ่ออโนไดซ์")
    # ... (โค้ดส่วนบ่ออโนไดซ์เดิมของคุณ)

# --- TAB 3: งานจิ๊ก ---
with tab3:
    # 1. ต้องประกาศ Tabs ก่อนใช้งาน
    sub_prod_reg, sub_jig_reg, sub_log = st.tabs(["1. ลงทะเบียนชิ้นงานใหม่", "2. ลงทะเบียนจิ๊กใหม่", "3. บันทึกผลผลิตรายวัน"])

    # 2. ส่วนลงทะเบียนชิ้นงาน
    with sub_prod_reg:
        st.subheader("เพิ่มฐานข้อมูลชิ้นงานใหม่")
        with st.form("register_product_form"):
            col1, col2 = st.columns(2)
            with col1:
                p_code = st.text_input("รหัสสินค้า (จำเป็น)")
                p_name = st.text_input("ชื่อชิ้นงาน (จำเป็น)")
                height = st.number_input("สูง (Height)", step=0.01)
                width = st.number_input("กว้าง (Width)", step=0.01)
                thickness = st.number_input("หนา (Thickness)", step=0.01)
            with col2:
                depth = st.number_input("ลึก (Depth)", step=0.01)
                surface_area = st.text_input("พื้นที่ผิว")
                outer_dia = st.number_input("เส้นผ่านศูนย์กลางนอก", step=0.01)
                inner_dia = st.number_input("เส้นผ่านศูนย์กลางใน", step=0.01)
            
            # ปุ่มบันทึกพร้อมระบบเช็คค่าว่าง
            if st.form_submit_button("บันทึกฐานข้อมูลสินค้า"):
                if not p_code or not p_name:
                    st.error("กรุณากรอก รหัสสินค้า และ ชื่อชิ้นงาน ให้ครบถ้วน")
                else:
                    data = {
                        "product_code": p_code, "product_name": p_name, "height": height, 
                        "width": width, "thickness": thickness, "depth": depth, 
                        "surface_area": surface_area, "outer_diameter": outer_dia, 
                        "inner_diameter": inner_dia
                    }
                    supabase.table("product_specifications").insert(data).execute()
                    st.success(f"บันทึกสินค้า {p_code} เรียบร้อย!")

    # 3. ส่วนลงทะเบียนจิ๊ก
    with sub_jig_reg:
        st.subheader("เพิ่มข้อมูลจิ๊กใหม่")
        with st.form("new_jig_form"):
            new_jig_code = st.text_input("ตั้งรหัสจิ๊กใหม่ (จำเป็น)")
            if st.form_submit_button("บันทึกจิ๊กใหม่"):
                if not new_jig_code:
                    st.error("กรุณาระบุรหัสจิ๊กใหม่")
                else:
                    supabase.table("jigs").insert({"jig_model_code": new_jig_code}).execute()
                    st.success(f"บันทึกจิ๊ก {new_jig_code} เรียบร้อย!")

    # 4. ส่วนบันทึกผลผลิตรายวัน
    with sub_log:
        st.subheader("บันทึกข้อมูลการผลิตรายวัน")
        product_list = get_dropdown_options("product_specifications", "product_code", "product_code")
        jig_list = get_dropdown_options("jigs", "jig_id", "jig_model_code")
        
        if product_list and jig_list:
            with st.form("daily_production_form"):
                sel_product = st.selectbox("เลือกรหัสสินค้า", list(product_list.keys()))
                sel_color = st.text_input("สี (จำเป็น)")
                selected_jig_name = st.selectbox("เลือกจิ๊กที่ใช้", list(jig_list.keys()))
                
                col_a, col_b = st.columns(2)
                pcs_jig = col_a.number_input("จำนวนชิ้นต่อจิ๊ก (จำเป็น)", step=1)
                pcs_row = col_b.number_input("จำนวนชิ้นต่อแถว", step=1)
                total_pieces = st.number_input("จำนวนชิ้นงานรวมทั้งหมด (จำเป็น)", step=1)
                
                if st.form_submit_button("บันทึกผลผลิต"):
                    # ตรวจสอบว่าข้อมูลห้ามว่าง
                    if not sel_color or pcs_jig <= 0 or total_pieces <= 0:
                        st.error("กรุณากรอกข้อมูล สี, จำนวนต่อจิ๊ก และ ยอดรวม ให้ครบถ้วนและมากกว่า 0")
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
                        st.success(f"บันทึกการผลิตจิ๊ก {selected_jig_name} สำเร็จ!")
        else:
            st.warning("โปรดตรวจสอบว่ามีการลงทะเบียน สินค้า หรือ จิ๊ก ในระบบแล้ว")
