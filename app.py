import streamlit as st
from supabase import create_client
import datetime

# เชื่อมต่อ Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("ระบบบันทึกข้อมูลการผลิต (Anodize & Color)")

# สร้างฟังก์ชันดึงข้อมูลมาทำ Dropdown
def get_dropdown_options(table_name, id_col, name_col):
    try:
        response = supabase.table(table_name).select(f"{id_col}, {name_col}").execute()
        # ส่งค่ากลับเป็น Dictionary {ชื่อ: ID}
        return {item[name_col]: item[id_col] for item in response.data}
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลด {table_name}: {e}")
        return {}

tab1, tab2, tab3 = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig)"])

# --- TAB 1: บ่อสี ---
with tab1:
    st.header("บันทึกข้อมูลบ่อสี")
    # ดึงข้อมูลจากตาราง color_bath
    bath_options = get_dropdown_options("color_bath", "color_bath_id", "tank_name")
    
    if bath_options:
        selected_name = st.selectbox("เลือกบ่อสี", list(bath_options.keys()))
        with st.form("color_bath_form"):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            if st.form_submit_button("บันทึกข้อมูล"):
                data = {
                    "color_bath_id": bath_options[selected_name], # ใช้ ID ที่ตรงกับชื่อ
                    "ph": ph,
                    "temperature": temp,
                    "recorded_at": datetime.datetime.now().isoformat()
                }
                supabase.table("color_bath_log").insert(data).execute()
                st.success(f"บันทึกข้อมูล {selected_name} สำเร็จ!")
    else:
        st.warning("ยังไม่มีข้อมูลบ่อสีในฐานข้อมูล โปรดเพิ่มข้อมูลบ่อสี 1-12 ในตาราง color_bath ก่อน")

# --- TAB 2: บ่ออนไดซ์ ---
# --- TAB 2: บ่ออโนไดซ์ ---
with tab2:
    st.header("บันทึกข้อมูลบ่ออโนไดซ์")
    
    # 1. ดึงรายการบ่ออโนไดซ์
    anodize_options = get_dropdown_options("anodize_tank", "anodize_id", "tank_name")
    # 2. ดึงรายการสินค้าทั้งหมด (เพื่อให้เลือกได้ว่างานไหนเข้าบ่อ)
    product_options = get_dropdown_options("jig_product", "jig_product_id", "product_name")
    
    if anodize_options and product_options:
        with st.form("anodize_form"):
            selected_tank = st.selectbox("เลือกบ่ออโนไดซ์", list(anodize_options.keys()))
            selected_product = st.selectbox("เลือกสินค้าที่จะลงบ่อ", list(product_options.keys()))
            
            ph = st.number_input("ค่า pH", step=0.1)
            density = st.number_input("ค่าความหนาแน่น (Density)", step=0.001, format="%.3f")
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            
            if st.form_submit_button("บันทึกข้อมูล"):
                try:
                    # ขั้นตอนที่ 1: บันทึกลง anodize_log
                    log_data = {
                        "anodize_id": anodize_options[selected_tank],
                        "ph": ph,
                        "density": density,
                        "temperature": temp,
                        "recorded_at": datetime.datetime.now().isoformat()
                    }
                    # ใส่พารามิเตอร์ returning='representation' เพื่อให้ได้ข้อมูลที่ insert เข้าไปกลับมา
                    response = supabase.table("anodize_log").insert(log_data).execute()
                    
                    # ดึง log_id ของรายการที่เพิ่งสร้าง
                    new_log_id = response.data[0]['log_id'] 
                    
                    # ขั้นตอนที่ 2: บันทึกลง anodize_log_product เพื่อเชื่อมโยงสินค้า
                    link_data = {
                        "log_id": new_log_id,
                        "jig_product_id": product_options[selected_product]
                    }
                    supabase.table("anodize_log_product").insert(link_data).execute()
                    
                    st.success(f"บันทึกข้อมูล {selected_tank} และเชื่อมโยงสินค้า {selected_product} เรียบร้อยแล้ว!")
                    
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดในการบันทึก: {e}")
    else:
        st.warning("ต้องมีข้อมูลทั้ง 'บ่ออโนไดซ์' และ 'สินค้า' ในระบบก่อนถึงจะบันทึกได้")
# --- TAB 3: งานจิ๊ก ---
with tab3:
    st.header("จัดการข้อมูลงานจิ๊ก")
    
    # แบ่งเป็น 3 ส่วนย่อย
    sub1, sub2, sub3 = st.tabs(["1. ลงทะเบียนจิ๊กใหม่", "2. เพิ่มสินค้าลงจิ๊ก", "3. บันทึกการใช้งาน"])

    # 1. ลงทะเบียนจิ๊กใหม่
    with sub1:
        st.subheader("สร้างรหัสจิ๊กใหม่")
        with st.form("new_jig_form"):
            today_str = datetime.datetime.now().strftime("%Y%m%d")
            jig_code = st.text_input("รหัสจิ๊ก (Jig Code)", value=f"{today_str}001", help="รูปแบบ: ปีเดือนวัน+ลำดับ เช่น 20260421001")
            if st.form_submit_button("สร้างจิ๊ก"):
                try:
                    supabase.table("jig").insert({"jig_code": jig_code}).execute()
                    st.success(f"สร้างจิ๊ก {jig_code} สำเร็จ!")
                except Exception as e:
                    st.error(f"สร้างไม่สำเร็จ (อาจมีรหัสนี้อยู่แล้ว): {e}")

    # 2. เพิ่มสินค้าลงจิ๊ก
   # 2. เพิ่มสินค้าลงจิ๊ก
    with sub2:
        st.subheader("ลงทะเบียนสินค้าในจิ๊ก")
        # ดึงรายชื่อจิ๊กที่มีอยู่มาให้เลือก
        jig_list_resp = supabase.table("jig").select("id, jig_code").execute()
        jig_map = {item['jig_code']: item['id'] for item in jig_list_resp.data}
        
        if jig_map:
            with st.form("product_to_jig_form"):
                selected_jig_code = st.selectbox("เลือกจิ๊ก", list(jig_map.keys()))
                
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
                
                if st.form_submit_button("เพิ่มสินค้า"):
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
    # 3. บันทึกการใช้งาน (ใช้ Code เดิมของคุณแต่ปรับปรุงเล็กน้อย)
    with sub3:
        st.subheader("บันทึกการใช้งานจริง")
        jig_options = get_dropdown_options("jig_product", "jig_product_id", "product_name")
        
        if jig_options:
            selected_name = st.selectbox("เลือกสินค้าในจิ๊ก", list(jig_options.keys()))
            with st.form("jig_usage_form"):
                actual_piece = st.number_input("จำนวนชิ้นงาน (Actual Piece)", min_value=0, step=1)
                if st.form_submit_button("บันทึกข้อมูลการผลิต"):
                    data = {
                        "jig_product_id": jig_options[selected_name],
                        "actual_piece": actual_piece,
                        "recorded_at": datetime.datetime.now().isoformat()
                    }
                    supabase.table("jig_usage_log").insert(data).execute()
                    st.success(f"บันทึกข้อมูล {selected_name} สำเร็จ!")
        else:
            st.warning("ยังไม่มีข้อมูลสินค้าในตาราง jig_product")