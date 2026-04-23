import streamlit as st
from supabase import create_client

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="Production Layout", layout="wide")

# เชื่อมต่อ Supabase
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except:
    st.error("ตรวจสอบการตั้งค่า Supabase ใน Secrets")
    st.stop()

@st.cache_data(ttl=10)
def get_tanks_data():
    try:
        res = supabase.table("tanks").select("tank_id, tank_name, tank_type").execute()
        return {i['tank_name']: i for i in res.data}
    except: return {}

# ฟังก์ชันสร้างปุ่มที่ระบุ Key เฉพาะตัว (แก้ปัญหากดไม่ได้)
def draw_tank(tanks_data, label, db_name):
    data = tanks_data.get(db_name)
    is_exists = data is not None
    # Key ต้องไม่ซ้ำกันเด็ดขาด
    if st.button(label, key=f"btn_{db_name}", disabled=not is_exists, use_container_width=True):
        st.session_state['sel_id'] = data['tank_id']
        st.session_state['sel_name'] = label
        st.session_state['sel_type'] = data['tank_type']
        st.rerun()

tanks = get_tanks_data()

# --- หน้าหลัก ---
if 'sel_id' not in st.session_state:
    st.title("🏭 ระบบจัดการบ่ออโนไดซ์และสี")
    
    # แบ่ง 7 คอลัมน์ตามโครงสร้างผัง
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)

    # --- ส่วนบน ---
    with col1: draw_tank(tanks, "5 Black", "5Black")
    with col2: 
        draw_tank(tanks, "2 Red", "2Red")
        draw_tank(tanks, "3 Violet", "3Violet")
        draw_tank(tanks, "RO 1", "RO1")
    with col3: 
        draw_tank(tanks, "8 Green", "8Green")
        draw_tank(tanks, "17 Black", "17Black")
    with col4: 
        draw_tank(tanks, "15 Gold", "15Gold")
        draw_tank(tanks, "9 Orange", "9Orange")
        draw_tank(tanks, "RO 2", "RO2")
    with col5: 
        draw_tank(tanks, "10 Light Blue", "10LightBlue")
        draw_tank(tanks, "6 BananaLeafGreen", "6BananaLeafGreen")
    with col6: 
        draw_tank(tanks, "16 Blue", "16Blue")
        draw_tank(tanks, "4 Dark Blue", "4DarkBlue")
        draw_tank(tanks, "RO 4", "RO4")
    with col7: st.info("🧪 Sodium Bicarbonate")

    st.divider()

    # --- ส่วนล่าง ---
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    with col1: st.info("🧪 Almite Sealer")
    with col2: 
        draw_tank(tanks, "20 Black", "20Black")
        draw_tank(tanks, "1 Dark Red (A)", "1DarkRedA")
    with col3: 
        draw_tank(tanks, "7 Pink", "7Pink")
        draw_tank(tanks, "RO 3", "RO3")
    with col4: 
        draw_tank(tanks, "Hot Seal", "HotSeal")
        draw_tank(tanks, "11 Gold", "11Gold")
        draw_tank(tanks, "RO 5", "RO5")
    with col5: 
        draw_tank(tanks, "1 Dark Red (B)", "1DarkRedB")
        draw_tank(tanks, "19 Copper", "19Copper")
        draw_tank(tanks, "12 Titanium", "12Titanium")
        draw_tank(tanks, "14 Rose Gold", "14RoseGold")
    with col6: 
        draw_tank(tanks, "RO 6", "RO6")
        draw_tank(tanks, "RO 7", "RO7")
        draw_tank(tanks, "RO 8", "RO8")
        draw_tank(tanks, "RO 9", "RO9")
    with col7: 
        st.info("🧪 Nitric Acid 68")
     with col8:
        st.info("🏗️ Anodized")

else:
    # หน้าบันทึกข้อมูล
    if st.button("⬅️ กลับ"): del st.session_state['sel_id']; st.rerun()
    st.subheader(f"บันทึกข้อมูล: {st.session_state['sel_name']}")
    with st.form("entry_form"):
        ph = st.number_input("pH")
        temp = st.number_input("Temp")
        if st.form_submit_button("บันทึก"):
            st.success("บันทึกสำเร็จ")
