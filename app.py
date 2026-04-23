import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Production Layout", layout="wide")

# เชื่อมต่อ Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

@st.cache_data(ttl=60)
def get_tanks_data():
    res = supabase.table("tanks").select("tank_id, tank_name, tank_type").execute()
    # สร้าง Dictionary Map จากชื่อบ่อไปหาข้อมูล
    return {i['tank_name']: i for i in res.data}

# ฟังก์ชันสร้างปุ่มแบบมี Key ป้องกัน Error
def draw_button(data_dict, display_name, db_name):
    exists = db_name in data_dict
    # ถ้ามีข้อมูลใน DB ให้กดได้ ถ้าไม่มีให้กดไม่ได้
    if st.button(display_name, key=f"btn_{db_name}", disabled=not exists, use_container_width=True):
        if exists:
            st.session_state['sel_id'] = data_dict[db_name]['tank_id']
            st.session_state['sel_name'] = display_name
            st.rerun()

# ดึงข้อมูลมาใช้งาน
tanks_data = get_tanks_data()

st.title("🏭 ระบบจัดการบ่ออโนไดซ์และสี")

# --- โซนบน ---
col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2, 1, 2, 2, 2, 1])

with col1: draw_button(tanks_data, "5 Black", "5Black")
with col2: draw_button(tanks_data, "2 Red", "2Red"); draw_button(tanks_data, "3 Violet", "3Violet"); draw_button(tanks_data, "RO 1", "RO1")
with col3: draw_button(tanks_data, "8 Green", "8Green"); draw_button(tanks_data, "17 Black", "17Black")
with col4: draw_button(tanks_data, "15 Gold", "15Gold"); draw_button(tanks_data, "9 Orange", "9Orange"); draw_button(tanks_data, "RO 2", "RO2")
with col5: draw_button(tanks_data, "10 Light Blue", "10LightBlue"); draw_button(tanks_data, "6 Banana", "6Banana")
with col6: draw_button(tanks_data, "16 Blue", "16Blue"); draw_button(tanks_data, "4 Dark Blue", "4DarkBlue"); draw_button(tanks_data, "RO 4", "RO4")
with col7: st.info("🧪 Sodium Bicarbonate")

st.divider()

# --- โซนล่าง ---
col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2, 1, 2, 2, 1, 1])

with col1: st.info("🧪 Almite Sealer")
with col2: draw_button(tanks_data, "20 Black", "20Black"); draw_button(tanks_data, "1 Dark Red (A)", "1DarkRed_A")
with col3: draw_button(tanks_data, "7 Pink", "7Pink"); draw_button(tanks_data, "RO 3", "RO3")
with col4: draw_button(tanks_data, "Hot Seal", "HotSeal"); draw_button(tanks_data, "11 Gold", "11Gold"); draw_button(tanks_data, "RO 5", "RO5")
with col5: 
    draw_button(tanks_data, "1 Dark Red (B)", "1DarkRed_B")
    draw_button(tanks_data, "19 Copper", "19Copper")
    draw_button(tanks_data, "12 Titanium", "12Titanium")
    draw_button(tanks_data, "14 Rose Gold", "14RoseGold")
with col6: 
    draw_button(tanks_data, "RO 6", "RO6")
    draw_button(tanks_data, "RO 7", "RO7")
    draw_button(tanks_data, "RO 8", "RO8")
    draw_button(tanks_data, "RO 9", "RO9")
with col7: st.info("🧪 Nitric Acid 68"); st.info("🏗️ Anodized Alum")

# --- ส่วนจัดการ (เมื่อเลือกบ่อ) ---
if 'sel_id' in st.session_state:
    st.divider()
    if st.button("⬅️ กลับ"): del st.session_state['sel_id']; st.rerun()
    st.subheader(f"บันทึกข้อมูล: {st.session_state['sel_name']}")
    # ใส่ฟอร์มบันทึกข้อมูลของคุณตรงนี้
