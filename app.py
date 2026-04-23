import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta

# --- การตั้งค่าเชื่อมต่อ ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ Supabase: {e}")

st.set_page_config(page_title="Production Log System", layout="wide")

# --- Mapping: ชื่อบน UI -> ชื่อใน Database ---
TANK_MAPPING = {
    "5 Black": "5Black", "2 Red": "2Red", "3 Violet": "3Violet",
    "8 Green": "8Green", "17 Black": "17Black", "15 Gold": "15Gold",
    "9 Orange": "18Orange", "10 Light Blue": "10LightBlue", 
    "6 Banana leaf Green": "6BananaLeafGreen", "16 Blue": "16Blue", 
    "4 Dark Blue": "4DarkBlue", "20 Black": "20Black", 
    "1 Dark Red": "1DarkRed", "19 Copper": "19Copper", 
    "12 Titanium": "12Titanium", "14 Rose Gold": "14RoseGold",
    "RO 1": "RO1", "RO 2": "RO2", "RO 4": "RO4", "7 Pink": "7Pink",
    "Hot Seal (H-60)": "HotSealH60", "11 Gold": "11Gold"
}

# --- Functions ---
def get_options():
    try:
        # ดึงข้อมูลจากตาราง tanks
        response = supabase.table("tanks").select("tank_id, tank_name, tank_type").execute()
        return {item['tank_name']: {"id": item['tank_id'], "type": item['tank_type']} for item in response.data}
    except Exception as e:
        st.error(f"Error loading tanks: {e}")
        return {}

# --- Main Logic ---
all_tanks = get_options()

if 'selected_tank_id' not in st.session_state:
    # (ส่วนผังบ่อ - ใช้โค้ดเดิมของคุณได้เลย)
    st.subheader("📍 ผังบ่อสีและอโนไดซ์")
    # ... ใส่โค้ดส่วน layout ปุ่มบ่อของคุณที่นี่ ...

else:
    # --- ส่วนกรอกข้อมูลที่แก้ไขแล้ว ---
    st.info(f"บันทึกข้อมูล: **{st.session_state['selected_tank_name']}** (Type: {st.session_state['active_type']})")
    
    if st.button("⬅️ กลับไปหน้าหลัก"):
        del st.session_state['selected_tank_id']
        st.rerun()
    
    with st.form("input_form"):
        ph = st.number_input("ค่า pH", step=0.1)
        temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
        
        # แสดงช่องกรอก Density เฉพาะบ่อที่เป็น Anodize
        is_anodize = st.session_state['active_type'] == "Anodize"
        density = None
        if is_anodize:
            density = st.number_input("ความหนาแน่น", step=0.001, format="%.3f")
        
        if st.form_submit_button("บันทึกข้อมูล"):
            try:
                # 1. เลือกตารางตาม type ที่ได้จาก DB
                if is_anodize:
                    table_name = "anodize_tank_logs"
                    data = {
                        "tank_id": st.session_state['selected_tank_id'],
                        "ph_value": ph,
                        "temperature": temp,
                        "density": density
                    }
                else:
                    table_name = "color_tank_logs"
                    data = {
                        "tank_id": st.session_state['selected_tank_id'],
                        "ph_value": ph,
                        "temperature": temp
                    }
                
                # 2. บันทึกลง Supabase
                supabase.table(table_name).insert(data).execute()
                st.success(f"บันทึกข้อมูล {table_name} สำเร็จ!")
                
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการบันทึก: {e}")
