import streamlit as st
from supabase import create_client

# --- การตั้งค่าเชื่อมต่อ ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except:
    st.error("กรุณาตั้งค่า SUPABASE_URL และ SUPABASE_KEY ใน Secrets")
    st.stop()

st.set_page_config(page_title="Production Log", layout="wide")

# --- Mapping UI (ปุ่ม) -> DB (tank_name) ---
# ตรวจสอบชื่อใน Database ของคุณให้ตรงกับฝั่งขวา
TANK_MAPPING = {
    "5 Black": "5Black", "2 Red": "2Red", "3 Violet": "3Violet", 
    "8 Green": "8Green", "17 Black": "17Black", "Dark Titanium": "DarkTitanium",
    "15 Gold": "15Gold", "9 Orange": "9Orange", 
    "10 Light Blue": "10LightBlue", "6 Banana leaf Green": "6BananaLeafGreen", 
    "16 Blue": "16Blue", "4 Dark Blue": "4DarkBlue",
    "20 Black": "20Black", "1 Dark Red": "1DarkRed", 
    "7 Pink": "7Pink", "Hot Seal (H-60)": "HotSealH60", "11 Gold": "11Gold",
    "19 Copper": "19Copper", "12 Titanium": "12Titanium", "14 Rose Gold": "14RoseGold",
    "RO 1": "RO1", "RO 2": "RO2", "RO 3": "RO3", "RO 4": "RO4", 
    "RO 5": "RO5", "RO 6": "RO6", "RO 7": "RO7", "RO 8": "RO8", "RO 9": "RO9"
}

@st.cache_data(ttl=60)
def get_tanks():
    try:
        res = supabase.table("tanks").select("tank_id, tank_name, tank_type").execute()
        return {i['tank_name']: {"id": i['tank_id'], "type": i['tank_type']} for i in res.data}
    except: return {}

def draw_tank(tanks, label):
    key = TANK_MAPPING.get(label, label)
    if key in tanks:
        if st.button(label, key=f"btn_{key}", use_container_width=True):
            st.session_state['selected_id'] = tanks[key]['id']
            st.session_state['selected_name'] = label
            st.session_state['type'] = tanks[key]['type']
            st.rerun()
    else:
        st.button(f"{label}\n(N/A)", disabled=True, use_container_width=True)

all_tanks = get_tanks()

# --- หน้าหลัก ---
if 'selected_id' not in st.session_state:
    st.title("🏭 ระบบจัดการบ่ออโนไดซ์และสี")
    
    # --- แถวบน ---
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    with col1: draw_tank(all_tanks, "5 Black")
    with col2: draw_tank(all_tanks, "2 Red"); draw_tank(all_tanks, "3 Violet"); draw_tank(all_tanks, "RO 1")
    with col3: draw_tank(all_tanks, "8 Green"); draw_tank(all_tanks, "17 Black"); draw_tank(all_tanks, "Dark Titanium")
    with col4: draw_tank(all_tanks, "15 Gold"); draw_tank(all_tanks, "9 Orange"); draw_tank(all_tanks, "RO 2")
    with col5: draw_tank(all_tanks, "10 Light Blue"); draw_tank(all_tanks, "6 Banana leaf Green")
    with col6: draw_tank(all_tanks, "16 Blue"); draw_tank(all_tanks, "4 Dark Blue"); draw_tank(all_tanks, "RO 4")
    with col7: st.info("🧪 Sodium Bicarbonate")

    st.write("---")

    # --- แถวล่าง ---
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    with col1: st.info("🧪 Almite Sealer")
    with col2: draw_tank(all_tanks, "20 Black"); draw_tank(all_tanks, "1 Dark Red")
    with col3: draw_tank(all_tanks, "7 Pink"); draw_tank(all_tanks, "RO 3")
    with col4: draw_tank(all_tanks, "Hot Seal (H-60)"); draw_tank(all_tanks, "11 Gold"); draw_tank(all_tanks, "RO 5")
    with col5: draw_tank(all_tanks, "19 Copper"); draw_tank(all_tanks, "12 Titanium"); draw_tank(all_tanks, "14 Rose Gold")
    with col6: 
        draw_tank(all_tanks, "RO 6"); draw_tank(all_tanks, "RO 7"); draw_tank(all_tanks, "RO 8"); draw_tank(all_tanks, "RO 9")
        st.info("🧪 Nitric Acid 68")
    with col7: st.info("🏗️ Anodized Aluminum")

else:
    # --- หน้าบันทึก ---
    st.subheader(f"บันทึกข้อมูล: {st.session_state['selected_name']}")
    if st.button("⬅️ กลับ"):
        del st.session_state['selected_id']
        st.rerun()
    
    with st.form("entry"):
        ph = st.number_input("pH", step=0.1)
        temp = st.number_input("Temp", step=0.1)
        is_anodize = st.session_state['type'] == "Anodize"
        density = st.number_input("Density", step=0.001) if is_anodize else None
        
        if st.form_submit_button("บันทึก"):
            table = "anodize_tank_logs" if is_anodize else "color_tank_logs"
            data = {"tank_id": st.session_state['selected_id'], "ph_value": ph, "temperature": temp}
            if is_anodize: data["density"] = density
            supabase.table(table).insert(data).execute()
            st.success("บันทึกสำเร็จ")
