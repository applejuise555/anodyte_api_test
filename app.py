import streamlit as st
from supabase import create_client
import datetime

# เชื่อมต่อ Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("ระบบบันทึกข้อมูลการผลิต (Anodize & Color)")

def get_dropdown_options(table_name, id_col, name_col):
    try:
        response = supabase.table(table_name).select(f"{id_col}, {name_col}").execute()
        return {item[name_col]: item[id_col] for item in response.data}
    except Exception as e:
        return {}

tab1, tab2, tab3 = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig)"])

# --- TAB 1: บ่อสี ---
with tab1:
    st.header("บันทึกข้อมูลบ่อสี")
    bath_options = get_dropdown_options("color_bath", "color_bath_id", "tank_name")
    if bath_options:
        selected_name = st.selectbox("เลือกบ่อสี", list(bath_options.keys()))
        with st.form("color_bath_form"):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            if st.form_submit_button("บันทึกข้อมูล"):
                data = {"color_bath_id": bath_options[selected_name], "ph": ph, "temperature": temp, "recorded_at": datetime.datetime.now().isoformat()}
                supabase.table("color_bath_log").insert(data).execute()
                st.success("บันทึกสำเร็จ!")

# --- TAB 2: บ่ออโนไดซ์ (เลือกสินค้าหรือไม่ก็ได้) ---
with tab2:
    st.header("บันทึกข้อมูลบ่ออโนไดซ์")
    anodize_options = get_dropdown_options("anodize_tank", "anodize_id", "tank_name")
    product_options = get_dropdown_options("jig_product", "jig_product_id", "product_name")
    
    if anodize_options:
        with st.form("anodize_form"):
            selected_tank = st.selectbox("เลือกบ่ออโนไดซ์", list(anodize_options.keys()))
            # ตัวเลือกสินค้าแบบ optional
            selected_product = st.selectbox("เลือกสินค้า (ไม่จำเป็น)", ["- ไม่มีสินค้า -"] + list(product_options.keys()))
            
            ph = st.number_input("ค่า pH", step=0.1)
            density = st.number_input("ค่าความหนาแน่น (Density)", step=0.001, format="%.3f")
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            
            if st.form_submit_button("บันทึกข้อมูล"):
                log_data = {
                    "anodize_id": anodize_options[selected_tank],
                    "ph": ph, "density": density, "temperature": temp,
                    "recorded_at": datetime.datetime.now().isoformat()
                }
                resp = supabase.table("anodize_log").insert(log_data).execute()
                
                # ถ้าเลือกสินค้า ถึงจะบันทึกในตารางเชื่อม
                if selected_product != "- ไม่มีสินค้า -":
                    new_log_id = resp.data[0]['log_id']
                    link_data = {"log_id": new_log_id, "jig_product_id": product_options[selected_product]}
                    supabase.table("anodize_log_product").insert(link_data).execute()
                
                st.success("บันทึกข้อมูลเรียบร้อย!")

# --- TAB 3: งานจิ๊ก ---
with tab3:
    st.header("จัดการข้อมูลงานจิ๊ก")
    sub1, sub2, sub3 = st.tabs(["1. จิ๊ก", "2. เพิ่มสินค้า", "3. บันทึกการใช้งาน"])

    # 1. ลงทะเบียนจิ๊กใหม่
    with sub1:
        st.subheader("สร้างรหัสจิ๊ก")
        new_code = st.text_input("รหัสจิ๊กที่ต้องการสร้าง", value=f"{datetime.datetime.now().strftime('%Y%m%d')}001")
        if st.button("บันทึกรหัสจิ๊กใหม่"):
            supabase.table("jig").insert({"jig_code": new_code}).execute()
            st.success(f"สร้าง {new_code} แล้ว")

 
   # 2. เพิ่มสินค้าลงจิ๊ก
    with sub2:
        st.subheader("ลงทะเบียนสินค้าในจิ๊ก")
        # ดึงรายชื่อจิ๊กที่มีอยู่มาให้เลือก
        jig_list_resp = supabase.table("jig").select("id, jig_code").execute()
        jig_map = {item['jig_code']: item['id'] for item in jig_list_resp.data}
        
        if jig_map:
            with st.form("product_to_jig_form"):
                selected_jig_code = st.selectbox("เลือกจิ๊กที่ต้องการเพิ่มสินค้า", list(jig_map.keys()))
                
                # แบ่งคอลัมน์เพื่อให้ฟอร์มดูสะอาดตา
                col1, col2 = st.columns(2)
                
                with col1:
                    product_code = st.text_input("รหัสสินค้า (Product Code)")
                    product_name = st.text_input("ชื่อสินค้า (Product Name)")
                    color = st.text_input("สี (Color)")
                    surface_type = st.text_input("ประเภทพื้นผิว (Surface Type)")
                    planned_piece = st.number_input("จำนวนชิ้นงานตามแผน (Planned)", min_value=0, step=1)
                
                with col2:
                    width = st.number_input("ความกว้าง (Width)", step=0.01)
                    length = st.number_input("ความยาว (Length)", step=0.01)
                    height = st.number_input("ความสูง (Height)", step=0.01)
                    thickness = st.number_input("ความหนา (Thickness)", step=0.01)
                    depth = st.number_input("ความลึก (Depth)", step=0.01)
                    outer_diameter = st.number_input("เส้นผ่านศูนย์กลางนอก (Outer Diameter)", step=0.01)
                    inner_diameter = st.number_input("เส้นผ่านศูนย์กลางใน (Inner Diameter)", step=0.01)
                
                if st.form_submit_button("เพิ่มสินค้าลงในจิ๊ก"):
                    data = {
                        "jig_id": jig_map[selected_jig_code],
                        "product_code": product_code,
                        "product_name": product_name,
                        "color": color,
                        "width": width,
                        "length": length,
                        "height": height,
                        "thickness": thickness,
                        "depth": depth,
                        "outer_diameter": outer_diameter,
                        "inner_diameter": inner_diameter,
                        "surface_type": surface_type,
                        "planned_piece": planned_piece
                    }
                    try:
                        supabase.table("jig_product").insert(data).execute()
                        st.success(f"เพิ่มสินค้า {product_name} ลงในจิ๊ก {selected_jig_code} สำเร็จ!")
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาด: {e}")
        else:
            st.warning("ยังไม่มีข้อมูลจิ๊ก โปรดไปที่แท็บ '1. ลงทะเบียนจิ๊กใหม่' ก่อน")

    # 3. บันทึกการใช้งาน (คำนวณรวม)
    with sub3:
        st.subheader("บันทึกการใช้งานจริง")
        jig_list = supabase.table("jig").select("id, jig_code").execute().data
        jig_map = {item['jig_code']: item['id'] for item in jig_list}
        
        selected_jig = st.selectbox("เลือกจิ๊กที่ใช้", list(jig_map.keys()))
        
        # ดึงสินค้าทั้งหมดในจิ๊กนี้มาคำนวณ
        products_in_jig = supabase.table("jig_product").select("*").eq("jig_id", jig_map[selected_jig]).execute().data
        total_planned = sum([p['planned_piece'] for p in products_in_jig])
        
        st.info(f"จิ๊กนี้มีสินค้าทั้งหมด {len(products_in_jig)} รายการ รวมจำนวนตามแผน: {total_planned} ชิ้น")
        
        actual = st.number_input("จำนวนชิ้นงานที่ผลิตจริง", min_value=0)
        if st.button("บันทึกการผลิต"):
            supabase.table("jig_usage_log").insert({
                "jig_product_id": products_in_jig[0]['jig_product_id'] if products_in_jig else None,
                "actual_piece": actual,
                "recorded_at": datetime.datetime.now().isoformat()
            }).execute()
            st.success("บันทึกข้อมูลเรียบร้อย")
