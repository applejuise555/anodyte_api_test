import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta

# 1. ตั้งค่า Timezone (UTC +7)
ICT = timezone(timedelta(hours=7))

# --- ตั้งค่าสี (Color Mapping) ---
COLOR_HEX_MAP = {
    "Black": "#000000", "Red": "#FF0000", "Dark Red": "#8B0000", 
    "Violet": "#9400D3", "Green": "#008000", "Banana leaf Green": "#90EE90", 
    "Gold": "#FFD700", "Orange": "#FFA500", "Light Blue": "#ADD8E6", 
    "Blue": "#0000FF", "Dark Blue": "#00008B", "Pink": "#FFC0CB", 
    "Copper": "#B87333", "Titanium": "#808080", "Dark Titanium": "#4A4E69", 
    "Rose Gold": "#B76E79"
}

def get_hex_from_name(name):
    sorted_colors = sorted(COLOR_HEX_MAP.keys(), key=len, reverse=True)
    name_lower = str(name).lower()
    for color_name in sorted_colors:
        if color_name.lower() in name_lower:
            return COLOR_HEX_MAP[color_name]
    return "#CCCCCC"

def render_color_bar(name):
    hex_code = get_hex_from_name(name)
    st.markdown(f"""
        <div style="
            background-color:{hex_code}; 
            width:100%; 
            height:20px; 
            border-radius:5px; 
            border: 1px solid #ccc;
            margin-bottom: 10px;
        "></div>
    """, unsafe_allow_html=True)

# --- การตั้งค่าเชื่อมต่อ ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ Supabase: {e}")

st.set_page_config(page_title="Production Log System", layout="wide")
st.title("ระบบบันทึกข้อมูลการผลิต")

def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    try:
        query = supabase.table(table).select(f"{id_col}, {name_col}")
        if filter_col and filter_val:
            query = query.eq(filter_col, filter_val)
        response = query.execute()
        return {item[name_col]: item[id_col] for item in response.data}
    except:
        return {}

# --- โครงสร้าง Tabs ---
tab1, tab2, tab3 = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig)"])

# --- TAB 1: บ่อสี ---
with tab1:
    st.header("บันทึกข้อมูลบ่อสี")
    
    TANK_COLOR_MAP = {
        "4DarkBlue": "Dark Blue", "16Blue": "Blue", "1DarkRedA": "Dark Red",
        "1DarkRedB": "Dark Red", "19Copper": "Copper", "12Titanium": "Titanium",
        "13DarkTitanium": "Dark Titanium", "14RoseGold": "Rose Gold",
        "6BananaLeafGreen": "Banana leaf Green", "10LightBlue": "Light Blue",
        "18OrangeOil": "Orange", "9Orange": "Orange", "15Gold": "Gold",
        "11Gold": "Gold", "17Black": "Black", "21Black": "Black",
        "5Black": "Black", "20Black": "Black", "7Pink": "Pink",
        "8Green": "Green", "3Violet": "Violet", "2Red": "Red",
        "HotSealH60": "Black"
    }
    
    color_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")
    
    if color_tanks:
        selected_tank_name = st.selectbox("เลือกบ่อสี", list(color_tanks.keys()), key="tank_select_t1")
        detected_color = TANK_COLOR_MAP.get(selected_tank_name, "Black")
        
        st.write(f"ระบบตรวจพบสี: **{detected_color}**")
        render_color_bar(detected_color)
        
        with st.form("color_log_form", clear_on_submit=True):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            if st.form_submit_button("บันทึกค่ามาตรฐาน"):
                if ph == 0 or temp == 0:
                    st.error("กรุณากรอกค่า pH และอุณหภูมิให้ถูกต้อง")
                else:
                    supabase.table("color_tank_logs").insert({
                        "tank_id": color_tanks[selected_tank_name], 
                        "ph_value": ph, 
                        "temperature": temp,
                        "recorded_at": datetime.now(ICT).isoformat()
                    }).execute()
                    st.success("บันทึกข้อมูลมาตรฐานสำเร็จ!")

        with st.expander("บันทึกอุณหภูมิความถี่สูง (High Frequency)"):
            with st.form("color_temp_frequent_form", clear_on_submit=True):
                target_temp = st.number_input("อุณหภูมิเป้าหมาย (°C)", step=0.1)
                actual_temp = st.number_input("อุณหภูมิที่วัดได้จริง (°C)", step=0.1)
                if st.form_submit_button("บันทึกข้อมูลความถี่สูง"):
                    if target_temp == 0 or actual_temp == 0:
                        st.error("กรุณากรอกอุณหภูมิให้ครบถ้วน")
                    else:
                        supabase.table("temp_frequent_logs").insert({
                            "tank_id": color_tanks[selected_tank_name], 
                            "temp_target": target_temp, 
                            "temp_actual": actual_temp,
                            "recorded_at": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("บันทึกค่าความถี่สูงสำเร็จ!")
    else:
        st.warning("ไม่พบข้อมูลบ่อสีในระบบ")

# --- TAB 2: บ่ออโนไดซ์ ---
with tab2:
    st.header("บันทึกข้อมูลบ่ออโนไดซ์")
    anodize_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Anodize")
    if anodize_tanks:
        selected_tank = st.selectbox("เลือกบ่ออโนไดซ์", list(anodize_tanks.keys()))
        
        with st.form("anodize_log_form", clear_on_submit=True):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            density = st.number_input("ความหนาแน่น (Density)", step=0.001, format="%.3f")
            if st.form_submit_button("บันทึก"):
                if ph == 0 or temp == 0 or density == 0:
                    st.error("กรุณากรอกข้อมูล pH, อุณหภูมิ และความหนาแน่น ให้ครบถ้วน")
                else:
                    supabase.table("anodize_tank_logs").insert({
                        "tank_id": anodize_tanks[selected_tank], "ph_value": ph, "temperature": temp, 
                        "density": density, "recorded_at": datetime.now(ICT).isoformat()
                    }).execute()
                    st.success("บันทึกข้อมูลมาตรฐานสำเร็จ!")
        
        with st.expander("บันทึกอุณหภูมิความถี่สูง (High Frequency)"):
            with st.form("anodize_temp_frequent_form", clear_on_submit=True):
                target_temp = st.number_input("อุณหภูมิเป้าหมาย (°C)", step=0.1)
                actual_temp = st.number_input("อุณหภูมิที่วัดได้จริง (°C)", step=0.1)
                if st.form_submit_button("บันทึกข้อมูลความถี่สูง"):
                    if target_temp == 0 or actual_temp == 0:
                        st.error("กรุณากรอกอุณหภูมิให้ครบถ้วน")
                    else:
                        supabase.table("temp_frequent_logs").insert({
                            "tank_id": anodize_tanks[selected_tank], "temp_target": target_temp, "temp_actual": actual_temp,
                            "recorded_at": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("บันทึกค่าความถี่สูงสำเร็จ!")

# 3. บันทึกผลผลิต (ส่วนที่ปรับปรุงให้ปลอดภัยและจัดการสถานะ Finished)
    with sub_log:
        prods = get_options("products", "product_id", "product_code")
        
        # ดึงรายชื่อจิ๊กทั้งหมดพร้อมสถานะจากตาราง jig_status
        # เราดึงข้อมูลจากตาราง jig_status โดยตรงเพื่อให้แน่ใจว่าสถานะเป็นปัจจุบันที่สุด
        jig_list_res = supabase.table("jigs") \
            .select("jig_id, jig_model_code, jig_status(status_type)") \
            .execute().data
        
        # กรองจิ๊กที่สถานะยังไม่เป็น 'Finished' หรือยังไม่มีสถานะในระบบ (ถือว่าว่าง)
        available_jigs = []
        for j in jig_list_res:
            status_data = j.get('jig_status')
            # ตรวจสอบสถานะ: ถ้ามีข้อมูลสถานะและเป็น 'Finished' ให้ข้ามจิ๊กนี้ไป
            if status_data and isinstance(status_data, list) and len(status_data) > 0:
                current_status = status_data[0].get('status_type', 'Available')
                if current_status == "Finished":
                    continue # ข้ามจิ๊กนี้ไปเลย ไม่ต้องเอาใส่ list
            
            # ถ้าไม่ใช่ Finished (หรือยังไม่มีสถานะ) ให้เพิ่มเข้าในรายการใช้งาน
            available_jigs.append(j)
        
        # สร้าง Mapping สำหรับ Selectbox
        jig_map = {j['jig_model_code']: j['jig_id'] for j in available_jigs}
        color_tanks_all = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")
        
        if prods and available_jigs and color_tanks_all:
            sel_j = st.selectbox("เลือกจิ๊กที่ใช้งานได้", list(jig_map.keys()))
            jig_id = jig_map[sel_j]
            sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))
            
            # --- ดึงสถานะปัจจุบันของจิ๊กตัวที่เลือกเพื่อแสดง UI ---
            status_res = supabase.table("jig_status").select("status_type").eq("jig_id", jig_id).maybe_single().execute()
            status = status_res.data['status_type'] if status_res and status_res.data else "Available"
            
            # --- CASE 1: จิ๊กกำลังผลิต (In-Process) ---
            if status == "In-Process":
                last_log = supabase.table("jig_usage_log").select("color, tank_id").eq("jig_id", jig_id).order("recorded_date", desc=True).limit(1).execute()
                current_color = last_log.data[0]['color'] if last_log.data else "ไม่ระบุ"
                
                st.warning(f"⚠️ จิ๊กนี้กำลังอยู่ในรอบการผลิต | สีที่ใช้: **{current_color}**")
                
                with st.form("add_more_batch_form", clear_on_submit=True):
                    st.subheader("เพิ่ม Batch งาน")
                    pcs = st.number_input("จำนวนต่อแถว", min_value=0)
                    rows = st.number_input("แถวที่เต็ม", min_value=0)
                    partial = st.number_input("เศษชิ้นงาน", min_value=0)
                    
                    if st.form_submit_button("บันทึก Batch งานเพิ่ม"):
                        tank_id = last_log.data[0]['tank_id']
                        supabase.table("jig_usage_log").insert({
                            "product_id": prods[sel_p], "jig_id": jig_id, "color": current_color,
                            "tank_id": tank_id, "pcs_per_row": pcs, "rows_filled": rows, 
                            "partial_pieces": partial, "total_pieces": (rows * pcs) + partial,
                            "recorded_date": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("บันทึกข้อมูลเพิ่มสำเร็จ!")
                        st.rerun()

                if st.button("🏁 เสร็จสิ้นงาน (Finish - จิ๊กนี้จะไม่สามารถใช้งานได้อีก)"):
                    # อัปเดตสถานะเป็น Finished
                    supabase.table("jig_status").upsert({
                        "jig_id": jig_id, 
                        "status_type": "Finished",
                        "updated_at": datetime.now(ICT).isoformat()
                    }).execute()
                    st.success("จิ๊กถูกปิดการใช้งานเรียบร้อยแล้ว!")
                    st.rerun()

            # --- CASE 2: จิ๊กว่าง (Available) ---
            else:
                st.info("✅ จิ๊กว่างอยู่ - เริ่มรอบการผลิตใหม่")
                unique_colors = list(set(TANK_COLOR_MAP.values()))
                sel_c_new = st.selectbox("เลือกสีสำหรับรอบนี้", options=sorted(unique_colors))
                render_color_bar(sel_c_new)
                
                filtered_tanks = {name: id for name, id in color_tanks_all.items() if TANK_COLOR_MAP.get(name) == sel_c_new}
                
                if filtered_tanks:
                    sel_tank_name = st.selectbox("เลือกบ่อสี", list(filtered_tanks.keys()))
                    sel_tank_id = filtered_tanks[sel_tank_name]
                    
                    with st.form("new_cycle_form", clear_on_submit=True):
                        st.subheader("บันทึกงาน Batch แรก")
                        pcs = st.number_input("จำนวนต่อแถว", min_value=0)
                        rows = st.number_input("แถวที่เต็ม", min_value=0)
                        partial = st.number_input("เศษชิ้นงาน", min_value=0)
                        
                        if st.form_submit_button("เริ่มการผลิต (Start Production)"):
                            # บันทึก log การผลิต
                            supabase.table("jig_usage_log").insert({
                                "product_id": prods[sel_p], "jig_id": jig_id, "color": sel_c_new,
                                "tank_id": sel_tank_id, "pcs_per_row": pcs, "rows_filled": rows, 
                                "partial_pieces": partial, "total_pieces": (rows * pcs) + partial,
                                "recorded_date": datetime.now(ICT).isoformat()
                            }).execute()
                            
                            # อัปเดตสถานะจิ๊กเป็น In-Process
                            supabase.table("jig_status").upsert({
                                "jig_id": jig_id, "status_type": "In-Process", 
                                "updated_at": datetime.now(ICT).isoformat()
                            }).execute()
                            st.success("เริ่มการผลิตสำเร็จ!")
                            st.rerun()
        else:
            st.warning("ไม่พบจิ๊กที่ว่างสำหรับการใช้งาน หรือข้อมูลไม่ครบถ้วน")
                            supabase.table("jig_status").upsert({
                                "jig_id": jig_id, "status_type": "In-Process", 
                                "updated_at": datetime.now(ICT).isoformat()
                            }).execute()
                            st.success("เริ่มการผลิตสำเร็จ!")
                            st.rerun()
        else:
            st.warning("ไม่พบจิ๊กที่ว่างสำหรับการใช้งาน หรือข้อมูลไม่ครบถ้วน กรุณาไปที่ 'ลงทะเบียนจิ๊ก' เพื่อเพิ่มจิ๊กใหม่")
