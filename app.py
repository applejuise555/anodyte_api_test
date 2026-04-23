import streamlit as st
from supabase import create_client

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="Production Layout", layout="wide")

# เชื่อมต่อ Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

@st.cache_data(ttl=60)
def get_tanks_data():
    res = supabase.table("tanks").select("tank_id, tank_name, tank_type").execute()
    # สร้าง Dictionary เพื่อให้หาชื่อได้ง่าย
    return {i['tank_name']: {"id": i['tank_id'], "type": i['tank_type']} for i in res.data}

# ฟังก์ชันวาดปุ่ม
def draw_tank(data, label, db_name):
    if db_name in data:
        info = data[db_name]
        if st.button(label, key=f"btn_{db_name}", use_container_width=True):
            st.session_state['sel_id'] = info['id']
            st.session_state['sel_name'] = label
            st.session_state['sel_type'] = info['type']
            st.rerun()
    else:
        st.button(f"{label} (N/A)", disabled=True, use_container_width=True)

data = get_tanks_data()

# --- หน้าหลัก ---
if 'sel_id' not in st.session_state:
    st.title("🏭 ระบบจัดการบ่ออโนไดซ์และสี")
    
    # ROW 1: ส่วนบนของผัง
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    
    with col1: draw_tank(data, "5 Black", "5Black")
    with col2: draw_tank(data, "2 Red", "2Red"); draw_tank(data, "3 Violet", "3Violet"); draw_tank(data, "RO 1", "RO1")
    with col3: draw_tank(data, "8 Green", "8Green"); draw_tank(data, "17 Black", "17Black")
    with col4: draw_tank(data, "15 Gold", "15Gold"); draw_tank(data, "9 Orange", "9Orange"); draw_tank(data, "RO 2", "RO2")
    with col5: draw_tank(data, "10 Light Blue", "10LightBlue"); draw_tank(data, "6 Banana Green", "6BananaLeafGreen")
    with col6: draw_tank(data, "16 Blue", "16Blue"); draw_tank(data, "4 Dark Blue", "4DarkBlue"); draw_tank(data, "RO 4", "RO4")
    with col7: st.info("🧪 Sodium Bicarbonate")

    st.divider()

    # ROW 2: ส่วนล่างของผัง
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    
    with col1: st.info("🧪 Almite Sealer")
    with col2: draw_tank(data, "20 Black", "20Black"); draw_tank(data, "1 Dark Red", "1DarkRed_A")
    with col3: draw_tank(data, "7 Pink", "7Pink"); draw_tank(data, "RO 3", "RO3")
    with col4: draw_tank(data, "Hot Seal", "HotSealH60"); draw_tank(data, "11 Gold", "11Gold"); draw_tank(data, "RO 5", "RO5")
    with col5: 
        draw_tank(data, "1 Dark Red", "1DarkRed_B")
        draw_tank(data, "19 Copper", "19Copper")
        draw_tank(data, "12 Titanium", "12Titanium")
        draw_tank(data, "14 Rose Gold", "14RoseGold")
    with col6: 
        draw_tank(data, "RO 6", "RO6"); draw_tank(data, "RO 7", "RO7")
        draw_tank(data, "RO 8", "RO8"); draw_tank(data, "RO 9", "RO9")
    with col7: st.info("🧪 Nitric Acid 68"); st.info("🏗️ Anodized Alum.")

else:
    # หน้าบันทึกข้อมูล
    if st.button("⬅️ กลับ"): del st.session_state['sel_id']; st.rerun()
    st.subheader(f"บันทึกข้อมูล: {st.session_state['sel_name']}")
    with st.form("input"):
        ph = st.number_input("pH")
        temp = st.number_input("Temp")
        if st.form_submit_button("บันทึก"):
            st.success("บันทึกสำเร็จ")
