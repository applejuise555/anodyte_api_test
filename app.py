import streamlit as st
from supabase import create_client

# --- 1. การตั้งค่าเชื่อมต่อ ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ Supabase: {e}")
    st.stop()

st.set_page_config(page_title="Production Log System", layout="wide")

# --- 2. CSS สำหรับตกแต่งบ่อ ---
st.markdown("""
<style>
    div.stButton > button { width: 100%; height: 50px; font-weight: bold; border-radius: 5px; }
    .ro-button { background-color: #ff4b4b !important; color: white !important; }
    .chem-box { background-color: #e1f5fe; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; height: 50px; display: flex; align-items: center; justify-content: center; }
</style>
""", unsafe_allow_html=True)

# --- 3. Mapping: เชื่อมชื่อ UI กับ Database ---
# แก้ไขฝั่งขวาให้ตรงกับชื่อในตาราง tanks ของคุณ
TANK_MAPPING = {
    "5 Black": "5Black", "2 Red": "2Red", "3 Violet": "3Violet", "8 Green": "8Green", 
    "17 Black": "17Black", "15 Gold": "15Gold", "9 Orange": "9Orange", 
    "10 Light Blue": "10LightBlue", "6 Banana leaf Green": "6BananaLeafGreen", 
    "16 Blue": "16Blue", "4 Dark Blue": "4DarkBlue", "20 Black": "20Black", 
    "1 Dark Red": "1DarkRed", "19 Copper": "19Copper", "12 Titanium": "12Titanium", 
    "14 Rose Gold": "14RoseGold", "7 Pink": "7Pink", "Hot Seal (H-60)": "HotSealH60", 
    "11 Gold": "11Gold", "13 Dark Titanium": "13DarkTitanium", 
    "RO 1": "RO1", "RO 2": "RO2", "RO 3": "RO3", "RO 4": "RO4", "RO 5": "RO5"
}

# --- 4. ฟังก์ชันการทำงาน ---
@st.cache_data(ttl=60)
def get_tanks_from_db():
    try:
        response = supabase.table("tanks").select("tank_id, tank_name, tank_type").execute()
        return {item['tank_name']: {"id": item['tank_id'], "type": item['tank_type']} for item in response.data}
    except: return {}

def draw_tank(tanks, ui_name):
    db_name = TANK_MAPPING.get(ui_name, ui_name)
    if db_name in tanks:
        info = tanks[db_name]
        # ถ้าเป็น RO ให้ใส่ class พิเศษ
        is_ro = "RO" in ui_name
        if st.button(ui_name, key=f"btn_{db_name}", use_container_width=True):
            st.session_state['selected_tank_id'] = info['id']
            st.session_state['selected_tank_name'] = ui_name
            st.session_state['active_type'] = info['type']
            st.rerun()
    else:
        st.button(f"{ui_name}\n(ไม่พบ)", disabled=True, use_container_width=True)

# --- 5. Main UI Layout ---
all_tanks = get_tanks_from_db()

if 'selected_tank_id' not in st.session_state:
    st.title("🏭 ระบบจัดการบ่ออโนไดซ์และสี")
    
    # --- แถวบน ---
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1: draw_tank(all_tanks, "5 Black")
    with c2: draw_tank(all_tanks, "2 Red"); draw_tank(all_tanks, "3 Violet"); draw_tank(all_tanks, "RO 1")
    with c3: draw_tank(all_tanks, "8 Green"); draw_tank(all_tanks, "17 Black")
    with c4: draw_tank(all_tanks, "15 Gold"); draw_tank(all_tanks, "9 Orange"); draw_tank(all_tanks, "RO 2")
    with c5: draw_tank(all_tanks, "10 Light Blue"); draw_tank(all_tanks, "6 Banana leaf Green")
    with c6: draw_tank(all_tanks, "16 Blue"); draw_tank(all_tanks, "4 Dark Blue"); draw_tank(all_tanks, "RO 4")
    with c7: st.markdown('<div class="chem-box">Sodium Bicarbonate</div>', unsafe_allow_html=True)

    st.divider()

    # --- แถวล่าง ---
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1: st.markdown('<div class="chem-box">Almite Sealer</div>', unsafe_allow_html=True)
    with c2: draw_tank(all_tanks, "20 Black"); draw_tank(all_tanks, "1 Dark Red")
    with c3: draw_tank(all_tanks, "7 Pink"); draw_tank(all_tanks, "RO 3")
    with c4: draw_tank(all_tanks, "Hot Seal (H-60)"); draw_tank(all_tanks, "11 Gold"); draw_tank(all_tanks, "RO 5")
    with c5: draw_tank(all_tanks, "19 Copper"); draw_tank(all_tanks, "12 Titanium"); draw_tank(all_tanks, "14 Rose Gold")
    with c6: st.markdown('<div class="chem-box">Nitric Acid 68</div>', unsafe_allow_html=True)
    with c7: st.markdown('<div class="chem-box">Anodized Aluminum</div>', unsafe_allow_html=True)

else:
    # --- หน้าบันทึกข้อมูล ---
    st.subheader(f"บันทึกข้อมูล: {st.session_state['selected_tank_name']}")
    if st.button("⬅️ กลับไปหน้าหลัก"):
        del st.session_state['selected_tank_id']
        st.rerun()
    
    with st.form("data_form"):
        ph = st.number_input("ค่า pH", step=0.1)
        temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
        # ตรวจสอบประเภทเพื่อดูว่าจะถามหา Density ไหม
        is_anodize = st.session_state['active_type'] == "Anodize"
        density = None
        if is_anodize:
            density = st.number_input("ความหนาแน่น", step=0.001)
        
        if st.form_submit_button("บันทึกข้อมูล"):
            try:
                table = "anodize_tank_logs" if is_anodize else "color_tank_logs"
                data = {"tank_id": st.session_state['selected_tank_id'], "ph_value": ph, "temperature": temp}
                if is_anodize: data["density"] = density
                
                supabase.table(table).insert(data).execute()
                st.success("บันทึกสำเร็จ!")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
