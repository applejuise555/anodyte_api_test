import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timezone, timedelta
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
import math
from plotly.subplots import make_subplots
import time
import numpy as np

# 1. ตั้งค่า Timezone (UTC +7)
ICT = timezone(timedelta(hours=7))
st.set_page_config(page_title="Gissco Production Line and Dashboard", layout="wide")

# ================= CONFIG & MAPS =================
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

# ================= DB CONNECTION =================
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error connecting to Supabase: {e}")
        return None

supabase = init_connection()

# ================= HELPER FUNCTIONS =================
def validate_color_input(ph, temp):
    if ph < 0 or ph > 14:
        st.error("❌ ค่า pH ต้องอยู่ระหว่าง 0-14")
        return False
    if temp < 0 or temp > 100:
        st.error("❌ ค่าอุณหภูมิผิดปกติ (ต้องอยู่ระหว่าง 0-100°C)")
        return False
    return True

def validate_ano_input(ph, temp, den):
    if ph < 0 or ph > 5:
        st.error("❌ ค่า pH Anodize ผิดช่วงปกติ")
        return False
    if den < 0:
        st.error("❌ ค่า Density ห้ามติดลบ")
        return False
    return True

def add_trend(df, col):
    if len(df) < 3: return df
    try:
        df = df.sort_values("recorded_at")
        x = np.arange(len(df))
        coef = np.polyfit(x, df[col].astype(float), 1)
        df[col+"_trend"] = np.poly1d(coef)(x)
    except:
        df[col+"_trend"] = df[col]
    return df

def insight(df, col, name):
    if len(df) < 5: return
    diff = df[col].diff().mean()
    if diff > 0.05:
        st.warning(f"📈 Insight: แนวโน้ม {name} กำลังเพิ่มขึ้น")
    elif diff < -0.05:
        st.info(f"📉 Insight: แนวโน้ม {name} กำลังลดลง")

def get_hex_from_name(name):
    sorted_colors = sorted(COLOR_HEX_MAP.keys(), key=len, reverse=True)
    name_lower = str(name).lower()
    for color_name in sorted_colors:
        if color_name.lower() in name_lower:
            return COLOR_HEX_MAP[color_name]
    return "#CCCCCC"

def render_color_bar(name):
    hex_code = get_hex_from_name(name)
    st.markdown(f'<div style="background-color:{hex_code}; width:100%; height:20px; border-radius:5px; border: 1px solid #ccc; margin-bottom: 10px;"></div>', unsafe_allow_html=True)

def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    if not supabase: return {}
    try:
        query = supabase.table(table).select(f"{id_col}, {name_col}")
        if filter_col and filter_val:
            query = query.eq(filter_col, filter_val)
        response = query.execute()
        return {item[name_col]: item[id_col] for item in response.data}
    except:
        return {}

def get_status_icon(value, min_val, max_val, warn_margin=0.1):
    if value is None: return "⚪"
    if value < min_val or value > max_val: return "🔴"
    elif value < (min_val + warn_margin) or value > (max_val - warn_margin): return "🟡"
    return "🟢"

# ================= MENU =================
menu = st.sidebar.radio("เมนูหลัก", ["Dashboard", "บันทึกข้อมูลการผลิต"])

# ================= DASHBOARD =================
if menu == "Dashboard":
    st.title("📊 Production Dashboard & Analytics")

    # STANDARDS
    PH_MIN, PH_MAX = 5.0, 6.0
    TEMP_COLOR_MIN, TEMP_COLOR_MAX = 30, 40
    PH_ANO_MIN, PH_ANO_MAX = 1, 1.5
    TEMP_ANO_MIN, TEMP_ANO_MAX = 18, 22
    DEN_ANO_MIN, DEN_ANO_MAX = 0.5, 1.5

    @st.cache_data(ttl=10)
    def load_color_logs():
        return supabase.table("color_tank_logs").select("*").order("recorded_at", desc=True).limit(200).execute().data

    @st.cache_data(ttl=10)
    def load_anodize_logs():
        return supabase.table("anodize_tank_logs").select("*").order("recorded_at", desc=True).limit(200).execute().data

    # --- KPI SECTION ---
    col1, col2, col3 = st.columns(3)
    active_jigs_res = supabase.table("jig_status").select("jig_id").eq("status_type", "In-Process").execute()
    col1.metric("🟢 กำลังผลิต (จิ๊ก)", len(active_jigs_res.data) if active_jigs_res.data else 0)
    
    color_data = load_color_logs()
    if color_data:
        df_c = pd.DataFrame(color_data)
        out_spec = df_c[(df_c["ph_value"] < PH_MIN) | (df_c["ph_value"] > PH_MAX)]
        col2.metric("% pH นอก Spec (บ่อสี)", f"{(len(out_spec)/len(df_c))*100:.1f}%")
    st.markdown("---")

    # --- Color Tank Analysis ---
    st.subheader("🎨 วิเคราะห์ข้อมูลบ่อสี (Color Tanks)")
    if color_data:
        df_color = pd.DataFrame(color_data)
        df_color["recorded_at"] = pd.to_datetime(df_color["recorded_at"])
        
        tank_map = get_options("tanks", "tank_id", "tank_name")
        inv_map = {v: k for k, v in tank_map.items()}
        df_color["tank_name"] = df_color["tank_id"].map(inv_map)

        # Individual Analysis with Trend
        selected_tank = st.selectbox("เลือกบ่อสีเพื่อดูแนวโน้มและ Insight", sorted(df_color["tank_name"].dropna().unique()))
        tank_df = df_color[df_color["tank_name"] == selected_tank].sort_values("recorded_at")
        
        if not tank_df.empty:
            tank_df = add_trend(tank_df, "ph_value")
            
            c1, c2 = st.columns([2, 1])
            with c1:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=tank_df["recorded_at"], y=tank_df["ph_value"], name="ค่าจริง", mode="lines+markers"))
                fig.add_trace(go.Scatter(x=tank_df["recorded_at"], y=tank_df["ph_value_trend"], name="แนวโน้ม (Trend)", line=dict(dash='dash')))
                fig.add_hrect(y0=PH_MIN, y1=PH_MAX, fillcolor="green", opacity=0.1)
                fig.update_layout(title=f"แนวโน้มค่า pH: {selected_tank}", height=400)
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.write("🔍 **Analytics Insight**")
                insight(tank_df, "ph_value", "ค่า pH")
                latest_ph = tank_df.iloc[-1]["ph_value"]
                st.metric("ค่าล่าสุด", f"{latest_ph:.2f}", f"{latest_ph - tank_df.iloc[-2]['ph_value']:.2f}" if len(tank_df)>1 else None)

    # --- Anodize Tank Analysis ---
    st.markdown("---")
    st.subheader("🧪 วิเคราะห์ข้อมูลบ่ออโนไดซ์ (Anodize)")
    ano_data = load_anodize_logs()
    if ano_data:
        df_a = pd.DataFrame(ano_data)
        df_a["recorded_at"] = pd.to_datetime(df_a["recorded_at"])
        # (ส่วนแสดงผลกราฟและตารางอโนไดซ์คงเดิมจากโค้ดชุดที่ 2)
        latest_ano = df_a.sort_values("recorded_at").groupby("tank_id").tail(1)
        st.dataframe(latest_ano[["recorded_at", "ph_value", "temperature", "density"]], use_container_width=True)

    try:
        st_autorefresh(interval=30000, key="refresh")
    except: pass

# ================= RECORD PAGE =================
else:
    st.title("📝 ระบบบันทึกข้อมูลการผลิต")
    tab_main = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig System)"])

    # --- Tab 1: บ่อสี ---
    with tab_main[0]:
        st.header("🎨 บันทึกข้อมูลบ่อสี")
        color_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")
        if color_tanks:
            selected_tank_name = st.selectbox("เลือกบ่อสี", list(color_tanks.keys()))
            render_color_bar(TANK_COLOR_MAP.get(selected_tank_name, "Black"))
            
            with st.form("color_log_form", clear_on_submit=True):
                ph = st.number_input("ค่า pH", step=0.01, format="%.2f", min_value=0.0, max_value=14.0)
                temp = st.number_input("อุณหภูมิ (°C)", step=0.1, format="%.1f", min_value=0.0)
                
                if st.form_submit_button("💾 บันทึกค่าบ่อสี"):
                    if validate_color_input(ph, temp):
                        supabase.table("color_tank_logs").insert({
                            "tank_id": color_tanks[selected_tank_name], 
                            "ph_value": ph, "temperature": temp, 
                            "recorded_at": datetime.now(ICT).isoformat()
                        }).execute()
                        st.toast(f"✅ บันทึก {selected_tank_name} สำเร็จ", icon="🎨")
                        st.balloons()
                        time.sleep(1.5)
                        st.rerun()

    # --- Tab 2: บ่ออโนไดซ์ ---
    with tab_main[1]:
        st.header("🧪 บันทึกข้อมูลบ่ออโนไดซ์")
        ano_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Anodize")
        if ano_tanks:
            sel_ano = st.selectbox("เลือกบ่ออโนไดซ์", list(ano_tanks.keys()))
            with st.form("ano_form", clear_on_submit=True):
                ph_a = st.number_input("ค่า pH", step=0.01, format="%.2f")
                temp_a = st.number_input("อุณหภูมิ (°C)", step=0.1, format="%.1f")
                den_a = st.number_input("ความหนาแน่น (Density)", step=0.001, format="%.3f")
                
                if st.form_submit_button("💾 บันทึกข้อมูลอโนไดซ์"):
                    if validate_ano_input(ph_a, temp_a, den_a):
                        supabase.table("anodize_tank_logs").insert({
                            "tank_id": ano_tanks[sel_ano], "ph_value": ph_a,
                            "temperature": temp_a, "density": den_a,
                            "recorded_at": datetime.now(ICT).isoformat()
                        }).execute()
                        st.toast("✅ บันทึกข้อมูลอโนไดซ์สำเร็จ", icon="🧪")
                        time.sleep(1.5)
                        st.rerun()

    # --- Tab 3: ระบบงานจิ๊ก (Jig System) ---
    with tab_main[2]:
        sub_prod, sub_jig, sub_log = st.tabs(["📦 1. ลงทะเบียนสินค้า", "🛠️ 2. ลงทะเบียนจิ๊ก", "⚡ 3. บันทึกผลผลิต"])

        with sub_prod:
            st.subheader("เพิ่มสินค้าใหม่ลงระบบ")
            shape = st.selectbox("📐 เลือกรูปทรง", ["สี่เหลี่ยม", "ทรงกระบอกทึบ", "ทรงกระบอกกลวง"], key="shape_sel")
            with st.form("add_prod_form_fixed", clear_on_submit=True):
                c1, c2 = st.columns(2)
                p_code = c1.text_input("รหัสสินค้า *")
                p_name = c1.text_input("ชื่อสินค้า")
                s_finish = c1.text_input("พื้นผิว *", value="-")
                height = c2.number_input("ความยาว (H) [mm]", min_value=0.0)
                
                # Logic คำนวณปริมาตรจากโค้ดชุดที่ 2
                width, thickness, od, u_vol, id_inner = 0.0, 0.0, 0.0, 0.0, 0.0
                if shape == "สี่เหลี่ยม":
                    width = c2.number_input("กว้าง [mm]", min_value=0.0)
                    thickness = c2.number_input("สูง/หนา [mm]", min_value=0.0)
                    u_vol = height * width * thickness
                elif shape == "ทรงกระบอกทึบ":
                    od = c2.number_input("เส้นผ่านศูนย์กลาง (OD) [mm]", min_value=0.0)
                    u_vol = math.pi * ((od/2)**2) * height
                else:
                    od = c2.number_input("เส้นผ่านศูนย์กลาง (OD) [mm]", min_value=0.0)
                    thickness = c2.number_input("ความหนาของเนื้อชิ้นงาน [mm]", min_value=0.0)
                    id_inner = max(0.0, od - (2*thickness))
                    u_vol = math.pi * ((od/2)**2 - (id_inner/2)**2) * height

                if st.form_submit_button("➕ ลงทะเบียนสินค้า"):
                    if p_code:
                        payload = {
                            "product_code": p_code, "product_name": p_name, "surface_finish": s_finish, 
                            "unit_volume": u_vol, "shape": shape, "height": height, "width": width, 
                            "thickness": thickness, "outer_diameter": od, "inner_diameter": id_inner
                        }
                        supabase.table("products").insert(payload).execute()
                        st.toast(f"✅ ลงทะเบียนสินค้า {p_code} สำเร็จ")
                        time.sleep(1)
                        st.rerun()

        with sub_jig:
            st.subheader("เพิ่มรหัสจิ๊กใหม่")
            with st.form("add_jig_fixed", clear_on_submit=True):
                j_code = st.text_input("รหัสจิ๊ก (เช่น 20260501001)").strip()
                if st.form_submit_button("ลงทะเบียนจิ๊ก"):
                    if j_code:
                        supabase.table("jigs").insert({"jig_model_code": j_code, "total_pcs_in_jig": 0}).execute()
                        st.success(f"✅ ลงทะเบียนจิ๊ก {j_code} สำเร็จ")

        with sub_log:
            # ส่วนบันทึก Jig Usage Log (คงเดิมจากโค้ดชุดที่ 2)
            prods_res = supabase.table("products").select("product_id, product_code, product_name").execute().data
            jigs_data = supabase.table("jigs").select("jig_id, jig_model_code").execute().data
            
            if prods_res and jigs_data:
                jig_map = {j['jig_model_code']: j['jig_id'] for j in jigs_data}
                prod_display = {f"{p['product_code']} | {p['product_name']}": p['product_id'] for p in prods_res}
                
                sel_j = st.selectbox("เลือกจิ๊ก", list(jig_map.keys()))
                sel_p = st.selectbox("เลือกสินค้า", list(prod_display.keys()))
                action = st.radio("สถานะ", ["🔵 บันทึกงานต่อ", "🟢 เสร็จสิ้นงาน"])

                if action == "🔵 บันทึกงานต่อ":
                    with st.form("jig_action_form", clear_on_submit=True):
                        c1, c2 = st.columns(2)
                        pcs = c1.number_input("จำนวนต่อแถว", min_value=1)
                        rows = c1.number_input("แถวที่เต็ม", min_value=1)
                        total_pcs = pcs * rows
                        c2.metric("รวมจำนวน", total_pcs)
                        
                        if st.form_submit_button("💾 บันทึกการผลิต"):
                            # Logic การ insert ลง jig_usage_log และ upsert jig_status
                            j_id = jig_map[sel_j]
                            p_id = prod_display[sel_p]
                            supabase.table("jig_usage_log").insert({
                                "jig_id": j_id, "product_id": p_id, "total_pieces": total_pcs,
                                "recorded_date": datetime.now(ICT).isoformat()
                            }).execute()
                            supabase.table("jig_status").upsert({
                                "jig_id": j_id, "status_type": "In-Process", "updated_at": datetime.now(ICT).isoformat()
                            }).execute()
                            st.toast("บันทึกข้อมูลการผลิตเรียบร้อย")
                            time.sleep(1.2)
                            st.rerun()
                else:
                    if st.button("🏁 ยืนยันปิดงานจิ๊กนี้"):
                        supabase.table("jig_status").upsert({
                            "jig_id": jig_map[sel_j], "status_type": "Finished", "updated_at": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("ปิดงานจิ๊กเรียบร้อย")
                        st.rerun()
