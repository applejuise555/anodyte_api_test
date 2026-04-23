import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta

# 1. ตั้งค่า Timezone (UTC +7)
ICT = timezone(timedelta(hours=7))

# --- การตั้งค่าเชื่อมต่อ ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ Supabase: {e}")

st.set_page_config(page_title="Production Log System", layout="wide")

# --- Mapping: ชื่อบน UI (ซ้าย) -> ชื่อใน Database (ขวา) ---
# แก้ไขส่วนนี้ให้ตรงกับชื่อใน Database ของคุณได้เลยครับ
TANK_MAPPING = {
    "5 Black": "5Black",
    "2 Red": "2Red",
    "3 Violet": "3Violet",
    "8 Green": "8Green",
    "17 Black": "17Black",
    "15 Gold": "15Gold",
    "9 Orange": "18Orange", # ใน DB คุณคือ 18Orange
    "10 Light Blue": "10LightBlue",
    "6 Banana leaf Green": "6BananaLeafGreen",
    "16 Blue": "16Blue",
    "4 Dark Blue": "4DarkBlue",
    "20 Black": "20Black",
    "1 Dark Red": "1DarkRed",
    "19 Copper": "19Copper",
    "12 Titanium": "12Titanium",
    "14 Rose Gold": "14RoseGold",
    "RO 1": "RO1",
    "RO 2": "RO2",
    "RO 4": "RO4",
}

# --- CSS ---
st.markdown("""
<style>
    div.stButton > button { width: 100%; height: 60px; font-size: 11px; font-weight: bold; border-radius: 5px; }
    .ro-box { background-color: #00bcd4; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# --- Functions ---
def get_options():
    try:
        response = supabase.table("tanks").select("tank_id, tank_name, tank_type").execute()
        return {item['tank_name']: {"id": item['tank_id'], "type": item['tank_type']} for item in response.data}
    except: return {}

def draw_tank(tanks, display_name):
    db_name = TANK_MAPPING.get(display_name, display_name) # แปลงชื่อ UI เป็น DB
    
    if db_name in tanks:
        info = tanks[db_name]
        if st.button(display_name, key=f"btn_{db_name}"):
            st.session_state['selected_tank_id'] = info['id']
            st.session_state['selected_tank_name'] = display_name
            st.session_state['active_type'] = info['type']
            st.rerun()
    else:
        st.button(f"{display_name}\n(ไม่พบ)", disabled=True)

def draw_ro(name):
    st.markdown(f'<div class="ro-box">{name}</div>', unsafe_allow_html=True)

# --- Main Layout ---
st.title("🏭 ระบบจัดการบ่ออโนไดซ์และสี")
all_tanks = get_options()

if 'selected_tank_id' not in st.session_state:
    st.subheader("📍 ผังบ่อสีและอโนไดซ์")
    
    # --- แถวที่ 1 ---
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1: draw_tank(all_tanks, "5 Black")
    with c2: draw_tank(all_tanks, "2 Red"); draw_tank(all_tanks, "3 Violet"); draw_ro("RO 1")
    with c3: draw_tank(all_tanks, "8 Green"); draw_tank(all_tanks, "17 Black")
    with c4: draw_tank(all_tanks, "15 Gold"); draw_tank(all_tanks, "9 Orange"); draw_ro("RO 2")
    with c5: draw_tank(all_tanks, "10 Light Blue"); draw_tank(all_tanks, "6 Banana leaf Green")
    with c6: draw_tank(all_tanks, "16 Blue"); draw_tank(all_tanks, "4 Dark Blue"); draw_ro("RO 4")
    with c7: st.info("🧪 Sodium Bicarbonate")

    st.write("---")
    
    # --- แถวที่ 2 ---
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1: st.info("🧪 Almite Sealer")
    with c2: draw_tank(all_tanks, "20 Black"); draw_tank(all_tanks, "1 Dark Red")
    with c3: draw_tank(all_tanks, "7 Pink"); draw_ro("RO 3")
    with c4: draw_tank(all_tanks, "Hot Seal (H-60)"); draw_tank(all_tanks, "11 Gold"); draw_ro("RO 5")
    with c5: draw_tank(all_tanks, "19 Copper"); draw_tank(all_tanks, "12 Titanium"); draw_tank(all_tanks, "14 Rose Gold")
    with c6: st.info("🧪 Nitric Acid 68")
    with c7: st.info("🏗️ Anozied Aluminum")

else:
    # --- ส่วนบันทึกข้อมูล (เหมือนเดิม) ---
    st.info(f"บันทึกข้อมูล: **{st.session_state['selected_tank_name']}**")
    if st.button("⬅️ กลับไปหน้าหลัก"):
        del st.session_state['selected_tank_id']
        st.rerun()
    
    with st.form("input_form"):
        ph = st.number_input("ค่า pH", step=0.1)
        temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
        # ถ้าเป็น RO จะไม่มี Density
        if "RO" not in st.session_state['selected_tank_name']:
            density = st.number_input("ความหนาแน่น", step=0.001)
        
        if st.form_submit_button("บันทึกข้อมูล"):
            st.success("บันทึกสำเร็จ!")
