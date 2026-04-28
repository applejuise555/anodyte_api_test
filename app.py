import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timezone, timedelta

# 1. ตั้งค่า Timezone (UTC +7)
ICT = timezone(timedelta(hours=7))

# --- ตั้งค่า Configuration ---
COLOR_HEX_MAP = {
    "Black": "#000000", "Red": "#FF0000", "Dark Red": "#8B0000", 
    "Violet": "#9400D3", "Green": "#008000", "Banana leaf Green": "#90EE90", 
    "Gold": "#FFD700", "Orange": "#FFA500", "Light Blue": "#ADD8E6", 
    "Blue": "#0000FF", "Dark Blue": "#00008B", "Pink": "#FFC0CB", 
    "Copper": "#B87333", "Titanium": "#808080", "Dark Titanium": "#4A4E69", 
    "Rose Gold": "#B76E79"
}

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

st.set_page_config(page_title="Production Log System", layout="wide")

# --- เชื่อมต่อ Supabase ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ Supabase: {e}")

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
        <div style="background-color:{hex_code}; width:100%; height:20px; border-radius:5px; border: 1px solid #ccc; margin-bottom: 10px;"></div>
    """, unsafe_allow_html=True)

def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    try:
        query = supabase.table(table).select(f"{id_col}, {name_col}")
        if filter_col and filter_val:
            query = query.eq(filter_col, filter_val)
        response = query.execute()
        return {item[name_col]: item[id_col] for item in response.data}
    except Exception:
        return {}

st.title("ระบบบันทึกข้อมูลการผลิต")

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig)"])

# --- TAB 1: บ่อสี ---
with tab1:
    st.header("บันทึกข้อมูลบ่อสี")
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
                try:
                    supabase.table("color_tank_logs").insert({"tank_id": color_tanks[selected_tank_name], "ph_value": ph, "temperature": temp, "recorded_at": datetime.now(ICT).isoformat()}).execute()
                    st.success("บันทึกสำเร็จ")
                except Exception as e:
                    st.error(f"Error: {e}")

        with st.expander("บันทึกอุณหภูมิความถี่สูง (High Frequency)"):
            with st.form("color_temp_frequent_form", clear_on_submit=True):
                target_temp = st.number_input("อุณหภูมิเป้าหมาย (°C)", step=0.1)
                actual_temp = st.number_input("อุณหภูมิที่วัดได้จริง (°C)", step=0.1)
                if st.form_submit_button("บันทึกข้อมูลความถี่สูง"):
                    try:
                        supabase.table("temp_frequent_logs").insert({"tank_id": color_tanks[selected_tank_name], "temp_target": target_temp, "temp_actual": actual_temp, "color": detected_color, "recorded_at": datetime.now(ICT).isoformat()}).execute()
                        st.success("บันทึกสำเร็จ!")
                    except Exception as e:
                        st.error(f"Error: {e}")

# --- TAB 2: บ่ออโนไดซ์ ---
with tab2:
    st.header("บันทึกข้อมูลบ่ออโนไดซ์")
    anodize_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Anodize")
    if anodize_tanks:
        selected_tank_name = st.selectbox("เลือกบ่ออโนไดซ์", list(anodize_tanks.keys()))
        with st.form("anodize_log_form", clear_on_submit=True):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            density = st.number_input("ความหนาแน่น (Density)", step=0.001, format="%.3f")
            if st.form_submit_button("บันทึก"):
                try:
                    supabase.table("anodize_tank_logs").insert({"tank_id": anodize_tanks[selected_tank_name], "ph_value": ph, "temperature": temp, "density": density, "recorded_at": datetime.now(ICT).isoformat()}).execute()
                    st.success("บันทึกสำเร็จ")
                except Exception as e:
                    st.error(f"Error: {e}")

        with st.expander("บันทึกอุณหภูมิความถี่สูง"):
            with st.form("anodize_temp_frequent_form", clear_on_submit=True):
                unique_colors = sorted(list(set(TANK_COLOR_MAP.values())))
                sel_color = st.selectbox("เลือกสีที่ผลิต", options=unique_colors)
                sel_target = st.selectbox("อุณหภูมิเป้าหมาย", options=[18, 20, 22])
                actual_temp = st.number_input("อุณหภูมิที่วัดได้จริง", step=0.1)
                if st.form_submit_button("บันทึก"):
                    try:
                        supabase.table("temp_frequent_logs").insert({"tank_id": anodize_tanks[selected_tank_name], "temp_target": sel_target, "temp_actual": actual_temp, "color": sel_color, "recorded_at": datetime.now(ICT).isoformat()}).execute()
                        st.success("บันทึกข้อมูลสำเร็จ!")
                    except Exception as e:
                        st.error(f"Error: {e}")

# --- TAB 3: งานจิ๊ก ---
with tab3:
    sub_prod, sub_jig, sub_log = st.tabs(["1. ลงทะเบียนชิ้นงาน", "2. ลงทะเบียนจิ๊ก", "3. บันทึกผลผลิต"])
    
    with sub_prod:
        with st.form("add_prod_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                p_code = st.text_input("รหัสสินค้า (Product Code)")
                p_name = st.text_input("ชื่อ/รายละเอียดสินค้า")
                height = st.number_input("ความสูง (Height)", step=0.01)
                width = st.number_input("ความว้าง (Width)", step=0.01)
                thickness = st.number_input("ความหนา (Thickness)", step=0.01)
            with col2:
                depth = st.number_input("ความลึก (Depth)", step=0.01)
                outer_d = st.number_input("Outer Diameter", step=0.01)
                inner_d = st.number_input("Inner Diameter", step=0.01)
                s_finish = st.text_input("พื้นผิว (Surface Finish)")
                
            if st.form_submit_button("ลงทะเบียนชิ้นงาน"):
                if not p_code or not p_name:
                    st.error("กรุณากรอก รหัสสินค้า และ ชื่อสินค้า")
                else:
                    try:
                        supabase.table("products").insert({
                            "product_code": p_code, "product_name": p_name,
                            "height": height, "width": width, "thickness": thickness,
                            "depth": depth, "outer_diameter": outer_d, 
                            "inner_diameter": inner_d, "surface_finish": s_finish
                        }).execute()
                        st.success("ลงทะเบียนชิ้นงานสำเร็จ")
                    except Exception as e:
                        st.error(f"Error: {e}")

    with sub_jig:
        with st.form("add_jig_form", clear_on_submit=True):
            j_code = st.text_input("รหัสจิ๊ก")
            if st.form_submit_button("ลงทะเบียนจิ๊ก"):
                if not j_code:
                    st.error("กรุณากรอกรหัสจิ๊ก")
                else:
                    try:
                        supabase.table("jigs").insert({
                            "jig_model_code": j_code, 
                            "total_pcs_in_jig": 0
                        }).execute()
                        st.success("ลงทะเบียนจิ๊กสำเร็จ")
                    except Exception as e:
                        st.error(f"Error: {e}")

    with sub_log:
        # ดึงข้อมูลสินค้าไว้ต้น Block เพื่อป้องกัน error
        prods = get_options("products", "product_id", "product_code")
        
        jigs_data_res = supabase.table("jigs").select("jig_id, jig_model_code").execute()
        jigs_data = jigs_data_res.data
        available_jigs = []
        for j in jigs_data:
            status_res = supabase.table("jig_status").select("status_type").eq("jig_id", j["jig_id"]).order("updated_at", desc=True).limit(1).execute()
            latest_status = status_res.data[0].get("status_type", "Available") if (status_res.data and len(status_res.data) > 0) else "Available"
            if latest_status != "Finished":
                available_jigs.append(j)
        
        jig_map = {j['jig_model_code']: j['jig_id'] for j in available_jigs}
        color_tanks_all = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")

        if prods and jigs_data and color_tanks_all:
            sel_j = st.selectbox("เลือกจิ๊ก", list(jig_map.keys()))
            jig_id = jig_map[sel_j]
            sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))
            
            status_res = supabase.table("jig_status").select("status_type").eq("jig_id", jig_id).order("updated_at", desc=True).limit(1).execute()
            status = status_res.data[0].get("status_type", "Available") if (status_res.data and len(status_res.data) > 0) else "Available"

            if status == "In-Process":
                last_log = supabase.table("jig_usage_log").select("color, tank_id").eq("jig_id", jig_id).order("recorded_date", desc=True).limit(1).execute()
                current_color = last_log.data[0]['color'] if last_log.data else "ไม่ระบุ"
                st.warning(f"⚠️ กำลังผลิต | สี: **{current_color}**")
                
                with st.form("add_more_batch_form", clear_on_submit=True):
                    pcs = st.number_input("จำนวนต่อแถว", min_value=0)
                    rows = st.number_input("แถวที่เต็ม", min_value=0)
                    partial = st.number_input("เศษ", min_value=0)
                    if st.form_submit_button("บันทึกเพิ่ม"):
                        try:
                            supabase.table("jig_usage_log").insert({
                                "product_id": prods[sel_p], "jig_id": jig_id, "color": current_color, 
                                "tank_id": last_log.data[0]['tank_id'], "pcs_per_row": pcs, "rows_filled": rows, 
                                "partial_pieces": partial, "total_pieces": (rows * pcs) + partial, 
                                "recorded_date": datetime.now(ICT).isoformat()
                            }).execute()
                            st.success("บันทึกสำเร็จ!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                
                # ปุ่มจบงาน: แก้ไขให้ current_tank_id เป็น None (NULL)
                if st.button("🏁 เสร็จสิ้นงาน"):
                    try:
                        supabase.table("jig_status").upsert({
                            "jig_id": jig_id, 
                            "status_type": "Finished", 
                            "current_tank_id": None, 
                            "updated_at": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("ปิดงานสำเร็จ!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.info("✅ จิ๊กว่าง - เริ่มรอบใหม่")
                sel_c_new = st.selectbox("เลือกสี", options=sorted(list(set(TANK_COLOR_MAP.values()))))
                render_color_bar(sel_c_new)
                filtered_tanks = {name: id for name, id in color_tanks_all.items() if TANK_COLOR_MAP.get(name) == sel_c_new}
                
                if filtered_tanks:
                    sel_tank_name = st.selectbox("เลือกบ่อสี", list(filtered_tanks.keys()))
                    sel_tank_id = filtered_tanks[sel_tank_name]
                    
                    with st.form("new_cycle_form", clear_on_submit=True):
                        pcs = st.number_input("จำนวนต่อแถว", min_value=0)
                        rows = st.number_input("แถวที่เต็ม", min_value=0)
                        partial = st.number_input("เศษ", min_value=0)
                        
                        if st.form_submit_button("เริ่มผลิต"):
                            try:
                                # 1. บันทึก log
                                supabase.table("jig_usage_log").insert({
                                    "product_id": prods[sel_p], "jig_id": jig_id, "color": sel_c_new, 
                                    "tank_id": sel_tank_id, "pcs_per_row": pcs, "rows_filled": rows, 
                                    "partial_pieces": partial, "total_pieces": (rows * pcs) + partial, 
                                    "recorded_date": datetime.now(ICT).isoformat()
                                }).execute()

                                # 2. อัปเดตสถานะ
                                supabase.table("jig_status").upsert({
                                    "jig_id": jig_id, 
                                    "status_type": "In-Process", 
                                    "current_tank_id": sel_tank_id, 
                                    "updated_at": datetime.now(ICT).isoformat()
                                }).execute()

                                st.success("เริ่มสำเร็จ!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
