import streamlit as st
from supabase import create_client
from datetime import datetime

# --- 1. ตั้งค่าเชื่อมต่อ ---
# ตั้งค่า secrets ในหน้า Manage App > Settings > Secrets
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ Supabase: {e}")
    st.stop()

st.set_page_config(page_title="Production Log System", layout="wide")

# --- 2. การ Mapping ชื่อ (UI -> Database) ---
# ต้องแก้ฝั่งขวาให้ตรงกับชื่อในตาราง tanks ของคุณ
TANK_MAPPING = {
    "5 Black": "5Black", "2 Red": "2Red", "3 Violet": "3Violet",
    "8 Green": "8Green", "17 Black": "17Black", "15 Gold": "15Gold",
    "9 Orange": "9Orange", "18 Orange": "18Orange", "10 Light Blue": "10LightBlue",
    "6 Banana leaf Green": "6BananaLeafGreen", "16 Blue": "16Blue",
    "4 Dark Blue": "4DarkBlue", "20 Black": "20Black",
    "1 Dark Red": "1DarkRed", "19 Copper": "19Copper",
    "12 Titanium": "12Titanium", "14 Rose Gold": "14RoseGold",
    "RO 1": "RO1", "RO 2": "RO2", "RO 3": "RO3", "RO 4": "RO4", "RO 5": "RO5", "RO 6": "RO6",
    "7 Pink": "7Pink", "Hot Seal (H-60)": "HotSealH60", "11 Gold": "11Gold",
    "13 Dark Titanium": "13DarkTitanium", "21 Black": "21Black"
}

# --- 3. ฟังก์ชันดึงข้อมูล ---
@st.cache_data(ttl=60)
def get_tanks_from_db():
    try:
        response = supabase.table("tanks").select("tank_id, tank_name, tank_type").execute()
        return {item['tank_name']: {"id": item['tank_id'], "type": item['tank_type']} for item in response.data}
    except Exception as e:
        st.error(f"Error: {e}")
        return {}

# --- 4. ฟังก์ชันวาดปุ่ม ---
def draw_tank(tanks, ui_name):
    db_name = TANK_MAPPING.get(ui_name, ui_name)
    if db_name in tanks:
        info = tanks[db_name]
        # เปลี่ยนสีปุ่มถ้าเป็น RO
        btn_type = "primary" if "RO" in ui_name else "secondary"
        if st.button(ui_name, key=f"btn_{db_name}", use_container_width=True, type=btn_type):
            st.session_state['selected_tank_id'] = info['id']
            st.session_state['selected_tank_name'] = ui_name
            st.session_state['active_type'] = info['type']
            st.rerun()
    else:
        st.button(f"{ui_name}\n(N/A)", disabled=True, use_container_width=True)

# --- 5. Main UI ---
all_tanks = get_tanks_from_db()

if 'selected_tank_id' not in st.session_state:
    st.title("🏭 ระบบจัดการบ่ออโนไดซ์และสี")
    
    # วาด Layout ตามรูปผัง
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    
    with col1: draw_tank(all_tanks, "5 Black")
    with col2: draw_tank(all_tanks, "2 Red"); draw_tank(all_tanks, "3 Violet"); draw_tank(all_tanks, "RO 1")
    with col3: draw_tank(all_tanks, "8 Green"); draw_tank(all_tanks, "17 Black")
    with col4: draw_tank(all_tanks, "15 Gold"); draw_tank(all_tanks, "9 Orange"); draw_tank(all_tanks, "RO 2")
    with col5: draw_tank(all_tanks, "10 Light Blue"); draw_tank(all_tanks, "6 Banana leaf Green")
    with col6: draw_tank(all_tanks, "16 Blue"); draw_tank(all_tanks, "4 Dark Blue"); draw_tank(all_tanks, "RO 4")
    with col7: st.info("🧪 Sodium Bicarbonate")

    st.divider()

    col8, col9, col10, col11, col12, col13, col14 = st.columns(7)
    with col8: st.info("🧪 Almite Sealer")
    with col9: draw_tank(all_tanks, "20 Black"); draw_tank(all_tanks, "1 Dark Red")
    with col10: draw_tank(all_tanks, "7 Pink"); draw_tank(all_tanks, "RO 3")
    with col11: draw_tank(all_tanks, "Hot Seal (H-60)"); draw_tank(all_tanks, "11 Gold"); draw_tank(all_tanks, "RO 5")
    with col12: draw_tank(all_tanks, "19 Copper"); draw_tank(all_tanks, "12 Titanium"); draw_tank(all_tanks, "14 Rose Gold")
    with col13: st.info("🧪 Nitric Acid 68")
    with col14: st.info("🏗️ Anodized Aluminum")

else:
    # --- หน้ากรอกข้อมูล ---
    st.subheader(f"บันทึกข้อมูล: {st.session_state['selected_tank_name']}")
    
    if st.button("⬅️ กลับหน้าหลัก"):
        del st.session_state['selected_tank_id']
        st.rerun()

    with st.form("data_entry"):
        ph = st.number_input("ค่า pH", step=0.1)
        temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
        
        # แสดงช่อง Density เฉพาะบ่อที่เป็น Anodize
        is_anodize = st.session_state['active_type'] == "Anodize"
        density = None
        if is_anodize:
            density = st.number_input("ความหนาแน่น (Density)", step=0.001, format="%.3f")
        
        if st.form_submit_button("บันทึกข้อมูล"):
            try:
                table = "anodize_tank_logs" if is_anodize else "color_tank_logs"
                data = {
                    "tank_id": st.session_state['selected_tank_id'],
                    "ph_value": ph,
                    "temperature": temp
                }
                if is_anodize:
                    data["density"] = density
                
                supabase.table(table).insert(data).execute()
                st.success("บันทึกข้อมูลสำเร็จ!")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
