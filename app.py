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
with tab3:
    sub1, sub2, sub3 = st.tabs(["1. จิ๊กใหม่", "2. สินค้าใหม่", "3. บันทึกผลผลิต"])

    # 1. ลงทะเบียนจิ๊ก (เหมือนเดิม)
    with sub1:
        with st.form("new_jig_form"):
            jig_code = st.text_input("รหัสจิ๊ก (ป/ด/ว/จิ๊กที่ เช่น 20260422001)")
            if st.form_submit_button("สร้างจิ๊ก"):
                supabase.table("jigs").insert({"jig_model_code": jig_code}).execute()
                st.success("สร้างจิ๊กสำเร็จ!")

    # 2. ลงทะเบียนสินค้าใหม่ (ย้ายข้อมูลที่ต้องการเก็บมาไว้ตรงนี้)
    with sub2:
        with st.form("new_product_form"):
            st.subheader("ลงทะเบียนสินค้า")
            col1, col2 = st.columns(2)
            with col1:
                p_code = st.text_input("รหัสสินค้า (ใช้ค้นหา)")
                p_name = st.text_input("ชื่อชิ้นงาน")
                p_color = st.text_input("สี")
                height = st.number_input("สูง")
                width = st.number_input("กว้าง")
            with col2:
                thickness = st.number_input("หนา")
                depth = st.number_input("ลึก")
                surface_area = st.text_input("ลักษณะผิว")
                outer_dia = st.number_input("เส้นผ่านศูนย์กลางนอก")
                inner_dia = st.number_input("เส้นผ่านศูนย์กลางใน")
            
            if st.form_submit_button("บันทึกสินค้า"):
                data = {
                    "product_code": p_code, "name": p_name, "color": p_color,
                    "height": height, "width": width, "thickness": thickness,
                    "depth": depth, "surface_area": surface_area,
                    "outer_diameter": outer_dia, "inner_diameter": inner_dia
                }
                supabase.table("products").insert(data).execute()
                st.success(f"บันทึกสินค้า {p_code} สำเร็จ!")

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
