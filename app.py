import streamlit as st
from supabase import create_client
import datetime

# เชื่อมต่อ Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("ระบบบันทึกข้อมูลการผลิต (Anodize & Color)")

# ฟังก์ชันดึง Dropdown แบบระบุเงื่อนไข (เช่น เอาเฉพาะบ่อสี หรือ บ่ออโนไดซ์)
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
            if st.form_submit_button("บันทึก"):
                data = {
                    "tank_id": color_tanks[selected_tank],
                    "ph_value": ph,
                    "temperature": temp
                }
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
            if st.form_submit_button("บันทึก"):
                data = {
                    "tank_id": anodize_tanks[selected_tank],
                    "ph_value": ph,
                    "temperature": temp,
                    "density": density
                }
                supabase.table("anodize_tank_logs").insert(data).execute()
                st.success("บันทึกสำเร็จ!")
    else:
        st.warning("ยังไม่มีข้อมูลบ่ออโนไดซ์ในระบบ")

# --- TAB 3: การจัดการ (งานจิ๊ก + สินค้า) ---
# --- TAB 3: งานจิ๊ก ---
with tab3:
    # แยกเป็น 2 Sub-tab ชัดเจน
    sub_register, sub_log = st.tabs(["1. ลงทะเบียนชิ้นงานใหม่", "2. บันทึกผลผลิตรายวัน"])

    # ส่วนที่ 1: ลงทะเบียนสินค้า (Master Data)
    with sub_register:
        st.subheader("เพิ่มฐานข้อมูลชิ้นงานใหม่")
        with st.form("register_product_form"):
            col1, col2 = st.columns(2)
            with col1:
                p_code = st.text_input("รหัสสินค้า (ใช้ค้นหา)")
                p_name = st.text_input("ชื่อชิ้นงาน")
                p_color = st.text_input("สี")
                height = st.number_input("สูง (Height)")
                width = st.number_input("กว้าง (Width)")
            with col2:
                thickness = st.number_input("หนา (Thickness)")
                depth = st.number_input("ลึก (Depth)")
                surface_area = st.text_input("พื้นที่ผิว")
                outer_dia = st.number_input("เส้นผ่านศูนย์กลางนอก")
                inner_dia = st.number_input("เส้นผ่านศูนย์กลางใน")
            
            if st.form_submit_button("บันทึกฐานข้อมูลสินค้า"):
                data = {
                    "product_code": p_code, "product_name": p_name, "color": p_color,
                    "height": height, "width": width, "thickness": thickness,
                    "depth": depth, "surface_area": surface_area,
                    "outer_diameter": outer_dia, "inner_diameter": inner_dia
                }
                supabase.table("product_specifications").insert(data).execute()
                st.success(f"บันทึกสินค้า {p_code} เรียบร้อย!")

    # ส่วนที่ 2: บันทึกการผลิต (Transactional Data)
    with sub_log:
        st.subheader("บันทึกข้อมูลการผลิตรายวัน")
        
        # ดึงข้อมูลมาแสดงเป็นตัวเลือก
        product_list = get_dropdown_options("product_specifications", "product_code", "product_code")
        jig_list = get_dropdown_options("jigs", "jig_id", "jig_model_code")
        
        if product_list and jig_list:
            with st.form("daily_production_form"):
                sel_product = st.selectbox("เลือกรหัสสินค้า", list(product_list.keys()))
                sel_jig = st.selectbox("เลือกจิ๊กที่ใช้", list(jig_list.keys()))
                
                col_a, col_b = st.columns(2)
                with col_a:
                    pcs_jig = st.number_input("จำนวนชิ้นต่อจิ๊ก", step=1)
                with col_b:
                    pcs_row = st.number_input("จำนวนชิ้นต่อแถว", step=1)
                
                total_pieces = st.number_input("จำนวนชิ้นงานรวมทั้งหมด", step=1)
                
                if st.form_submit_button("บันทึกผลผลิต"):
                    data = {
                        "product_code": sel_product, # เก็บแค่ Code ไปอ้างอิง
                        "jig_id": jig_list[sel_jig],
                        "pcs_per_jig": pcs_jig,
                        "pcs_per_row": pcs_row,
                        "total_pieces": total_pieces,
                        "recorded_date": str(datetime.date.today())
                    }
                    supabase.table("jig_usage_log").insert(data).execute()
                    st.success("บันทึกยอดการผลิตสำเร็จ!")
        else:
            st.warning("ต้องลงทะเบียนสินค้าหรือจิ๊กก่อนเริ่มบันทึก")

    # 3. บันทึกผลผลิต (ลิงก์ จิ๊ก + สินค้า)
    with sub3:
        # ดึงรายชื่อจิ๊กและสินค้ามาทำ Dropdown
        jig_list = get_dropdown_options("jigs", "jig_id", "jig_model_code")
        prod_list = get_dropdown_options("products", "product_id", "product_code")
        
        if jig_list and prod_list:
            with st.form("production_form"):
                sel_jig = st.selectbox("เลือกจิ๊ก", list(jig_list.keys()))
                sel_prod = st.selectbox("เลือกสินค้าที่ผลิต", list(prod_list.keys()))
                total_workpieces = st.number_input("จำนวนชิ้นงานรวม", step=1)
                
                if st.form_submit_button("บันทึกยอด"):
                    # บันทึกลงตาราง production_summary โดยเก็บทั้ง jig_id และ product_id
                    data = {
                        "jig_id": jig_list[sel_jig],
                        "product_id": prod_list[sel_prod],
                        "total_workpieces": total_workpieces
                    }
                    supabase.table("production_summary").insert(data).execute()
                    st.success("บันทึกยอดการผลิตสำเร็จ!")
    # 3. สรุปผลผลิต
    with sub3:
        jig_list = get_dropdown_options("jigs", "jig_id", "jig_model_code")
        if jig_list:
            selected_jig = st.selectbox("เลือกจิ๊กสำหรับสรุปงาน", list(jig_list.keys()))
            with st.form("production_form"):
                total_workpieces = st.number_input("จำนวนชิ้นงานรวม", step=1)
                recorded_date = st.date_input("วันที่")
                if st.form_submit_button("บันทึกยอด"):
                    data = {
                        "jig_id": jig_list[selected_jig],
                        "total_workpieces": total_workpieces,
                        "recorded_date": str(recorded_date)
                    }
                    supabase.table("production_summary").insert(data).execute()
                    st.success("บันทึกยอดสำเร็จ!")
