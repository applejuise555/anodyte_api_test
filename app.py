import streamlit as st
from supabase import create_client

# 1. การตั้งค่าหน้าจอ
st.set_page_config(page_title="Production Layout", layout="wide")

# 2. การเชื่อมต่อ Supabase
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"Error connecting to Supabase: {e}")
    st.stop()

# 3. Mapping: เชื่อมชื่อบน UI กับ Database
# แก้ไขค่าฝั่งขวาให้ตรงกับชื่อในตาราง 'tanks' ของคุณ
TANK_MAPPING = {
    "5 Black": "5Black", "2 Red": "2Red", "3 Violet": "3Violet", 
    "8 Green": "8Green", "17 Black": "17Black", "15 Gold": "15Gold", 
    "9 Orange": "9Orange", "10 Light Blue": "10LightBlue", "16 Blue": "16Blue",
    "6 Banana leaf Green": "6BananaLeafGreen", "4 Dark Blue": "4DarkBlue",
    "20 Black": "20Black", "1 Dark Red": "1DarkRed", "7 Pink": "7Pink", 
    "Hot Seal (H-60)": "HotSealH60", "11 Gold": "11Gold", "19 Copper": "19Copper", 
    "12 Titanium": "12Titanium", "14 Rose Gold": "14RoseGold",
    "RO 1": "RO1", "RO 2": "RO2", "RO 3": "RO3", "RO 4": "RO4", 
    "RO 5": "RO5", "RO 6": "RO6", "RO 7": "RO7", "RO 8": "RO8", "RO 9": "RO9"
}

# 4. ฟังก์ชันดึงข้อมูลจาก DB
@st.cache_data(ttl=60)
def get_tanks_data():
    try:
        response = supabase.table("tanks").select("tank_id, tank_name, tank_type").execute()
        return {item['tank_name']: {"id": item['tank_id'], "type": item['tank_type']} for item in response.data}
    except: return {}

# 5. ฟังก์ชันวาดปุ่ม
def draw_tank(tanks_data, label):
    db_name = TANK_MAPPING.get(label, label)
    if db_name in tanks_data:
        info = tanks_data[db_name]
        if st.button(label, key=f"btn_{db_name}", use_container_width=True):
            st.session_state['sel_id'] = info['id']
            st.session_state['sel_name'] = label
            st.session_state['sel_type'] = info['type']
            st.rerun()
    else:
        st.button(f"{label} (N/A)", disabled=True, use_container_width=True)

# --- ส่วนของการจัด Layout (อ้างอิงตาม image_c3447e.png) ---
data = get_tanks_data()

if 'sel_id' not in st.session_state:
    st.title("🏭 ผังบ่อสีและอโนไดซ์")
    
    # แถวที่ 1
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    with col1: draw_tank(data, "5 Black")
    with col2: draw_tank(data, "2 Red"); draw_tank(data, "3 Violet"); draw_tank(data, "RO 1")
    with col3: draw_tank(data, "8 Green"); draw_tank(data, "17 Black")
    with col4: draw_tank(data, "15 Gold"); draw_tank(data, "9 Orange"); draw_tank(data, "RO 2")
    with col5: draw_tank(data, "10 Light Blue"); draw_tank(data, "6 Banana leaf Green")
    with col6: draw_tank(data, "16 Blue"); draw_tank(data, "4 Dark Blue"); draw_tank(data, "RO 4")
    with col7: st.info("🧪 Sodium Bicarbonate")

    st.divider()

    # แถวที่ 2
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    with col1: st.info("🧪 Almite Sealer")
    with col2: draw_tank(data, "20 Black"); draw_tank(data, "1 Dark Red")
    with col3: draw_tank(data, "7 Pink"); draw_tank(data, "RO 3")
    with col4: draw_tank(data, "Hot Seal (H-60)"); draw_tank(data, "11 Gold"); draw_tank(data, "RO 5")
    with col5: draw_tank(data, "19 Copper"); draw_tank(data, "12 Titanium"); draw_tank(data, "14 Rose Gold")
    with col6: 
        draw_tank(data, "RO 6"); draw_tank(data, "RO 7"); draw_tank(data, "RO 8"); draw_tank(data, "RO 9")
    with col7: st.info("🏗️ Anodized Aluminum"); st.info("🧪 Nitric Acid 68")

else:
    # หน้าบันทึกข้อมูล
    st.subheader(f"บันทึกข้อมูล: {st.session_state['sel_name']}")
    if st.button("⬅️ กลับหน้าหลัก"):
        del st.session_state['sel_id']
        st.rerun()
    
    with st.form("input_form"):
        ph = st.number_input("pH", step=0.1)
        temp = st.number_input("Temp", step=0.1)
        # ตรวจสอบประเภทเพื่อบันทึก
        is_anodize = st.session_state['sel_type'] == "Anodize"
        density = st.number_input("Density", step=0.001) if is_anodize else None
        
        if st.form_submit_button("บันทึก"):
            table = "anodize_tank_logs" if is_anodize else "color_tank_logs"
            rec = {"tank_id": st.session_state['sel_id'], "ph_value": ph, "temperature": temp}
            if is_anodize: rec["density"] = density
            supabase.table(table).insert(rec).execute()
            st.success("บันทึกสำเร็จ!")
