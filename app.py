import streamlit as st
from supabase import create_client
from datetime import datetime

# --- การตั้งค่าเชื่อมต่อ ---
# ตรวจสอบว่าในไฟล์ .streamlit/secrets.toml มี SUPABASE_URL และ SUPABASE_KEY แล้ว
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ Supabase: {e}")

st.set_page_config(page_title="Production Log System", layout="wide")

# --- Mapping: ชื่อบน UI -> ชื่อใน Database (ต้องตรงกับตาราง tanks) ---
# แก้ไขฝั่งขวาให้ตรงกับข้อมูลในคอลัมน์ tank_name ของคุณ
TANK_MAPPING = {
    "5 Black": "5Black", "2 Red": "2Red", "3 Violet": "3Violet",
    "8 Green": "8Green", "17 Black": "17Black", "15 Gold": "15Gold",
    "9 Orange": "9Orange", "18 Orange": "18Orange", "10 Light Blue": "10LightBlue", 
    "6 Banana leaf Green": "6BananaLeafGreen", "16 Blue": "16Blue", 
    "4 Dark Blue": "4DarkBlue", "20 Black": "20Black", 
    "1 Dark Red": "1DarkRed", "19 Copper": "19Copper", 
    "12 Titanium": "12Titanium", "14 Rose Gold": "14RoseGold",
    "RO 1": "RO1", "RO 2": "RO2", "RO 4": "RO4", "RO 3": "RO3", "RO 5": "RO5", "RO 6": "RO6",
    "7 Pink": "7Pink", "Hot Seal (H-60)": "HotSealH60", "11 Gold": "11Gold",
    "Dark Titanium": "13DarkTitanium"
}

# --- Functions ---
@st.cache_data(ttl=60) # Cache ข้อมูลไว้ 60 วินาที
def get_tanks_from_db():
    try:
        response = supabase.table("tanks").select("tank_id, tank_name, tank_type").execute()
        return {item['tank_name']: {"id": item['tank_id'], "type": item['tank_type']} for item in response.data}
    except Exception as e:
        st.error(f"Error: {e}")
        return {}

def draw_tank_btn(tanks, ui_name):
    db_name = TANK_MAPPING.get(ui_name, ui_name)
    if db_name in tanks:
        info = tanks[db_name]
        if st.button(ui_name, key=f"btn_{db_name}", use_container_width=True):
            st.session_state['selected_tank_id'] = info['id']
            st.session_state['selected_tank_name'] = ui_name
            st.session_state['active_type'] = info['type']
            st.rerun()
    else:
        st.button(f"{ui_name}\n(N/A)", disabled=True, use_container_width=True)

# --- Layout ---
all_tanks = get_tanks_from_db()

if 'selected_tank_id' not in st.session_state:
    st.title("🏭 ระบบจัดการบ่ออโนไดซ์และสี")
    st.subheader("📍 ผังบ่อ (กรุณาเลือกบ่อ)")
    
    # Grid Layout
    cols = st.columns(7)
    with cols[0]: draw_tank_btn(all_tanks, "5 Black")
    with cols[1]: draw_tank_btn(all_tanks, "2 Red"); draw_tank_btn(all_tanks, "3 Violet")
    with cols[2]: draw_tank_btn(all_tanks, "8 Green"); draw_tank_btn(all_tanks, "17 Black")
    with cols[3]: draw_tank_btn(all_tanks, "15 Gold"); draw_tank_btn(all_tanks, "9 Orange")
    with cols[4]: draw_tank_btn(all_tanks, "10 Light Blue"); draw_tank_btn(all_tanks, "6 Banana leaf Green")
    with cols[5]: draw_tank_btn(all_tanks, "16 Blue"); draw_tank_btn(all_tanks, "4 Dark Blue")
    with cols[6]: st.info("🧪 Sodium Bicarbonate")

    st.divider()

    cols2 = st.columns(7)
    with cols2[0]: st.info("🧪 Almite Sealer")
    with cols2[1]: draw_tank_btn(all_tanks, "20 Black"); draw_tank_btn(all_tanks, "1 Dark Red")
    with cols2[2]: draw_tank_btn(all_tanks, "7 Pink")
    with cols2[3]: draw_tank_btn(all_tanks, "Hot Seal (H-60)"); draw_tank_btn(all_tanks, "11 Gold")
    with cols2[4]: draw_tank_btn(all_tanks, "19 Copper"); draw_tank_btn(all_tanks, "12 Titanium"); draw_tank_btn(all_tanks, "14 Rose Gold")
    with cols2[5]: st.info("🧪 Nitric Acid 68")
    with cols2[6]: st.info("🏗️ Anodized Aluminum")

else:
    # --- หน้าบันทึกข้อมูล ---
    st.title(f"บันทึกข้อมูล: {st.session_state['selected_tank_name']}")
    if st.button("⬅️ กลับหน้าหลัก"):
        del st.session_state['selected_tank_id']
        st.rerun()

    with st.form("data_entry_form"):
        ph = st.number_input("ค่า pH", min_value=0.0, max_value=14.0, step=0.1)
        temp = st.number_input("อุณหภูมิ (°C)", min_value=0.0, step=0.1)
        
        # ตรรกะ: ถ้า type เป็น Anodize ให้ถามหา Density
        is_anodize = st.session_state['active_type'] == "Anodize"
        density = None
        if is_anodize:
            density = st.number_input("ความหนาแน่น (Density)", min_value=0.0, step=0.001, format="%.3f")
        
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
                st.success("บันทึกข้อมูลเรียบร้อย!")
            except Exception as e:
                st.error(f"Error: {e}")
