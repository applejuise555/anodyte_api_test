import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta
import pandas as pd

ICT = timezone(timedelta(hours=7))

# ตั้งค่าการเชื่อมต่อ (คัดลอกส่วนนี้มาไว้ในหน้านี้ด้วย)
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ Supabase: {e}")

st.set_page_config(page_title="Dashboard", layout="wide")
st.header("📊 แดชบอร์ดการผลิต (Real-time Overview)")

# 1. ปุ่มรีเฟรชข้อมูล
if st.button("🔄 อัปเดตข้อมูลล่าสุด"):
    st.rerun()

# 2. ดึงข้อมูลและสร้าง Metrics
col1, col2, col3 = st.columns(3)

# ดึงงานที่กำลังผลิต
active_jigs = supabase.table("jig_status").select("*").eq("status_type", "In-Process").execute().data

# ดึงยอดผลิตวันนี้
today_str = datetime.now(ICT).strftime("%Y-%m-%d")
production_logs = supabase.table("jig_usage_log").select("total_pieces, recorded_date").gte("recorded_date", today_str).execute().data

total_pieces = sum([item['total_pieces'] for item in production_logs])

col1.metric("จิ๊กที่กำลังผลิต", len(active_jigs), delta_color="normal")
col2.metric("จำนวนชิ้นงานผลิตวันนี้", total_pieces)
col3.metric("สถานะระบบ", "Online ✅")

st.divider()

# 3. แสดงกราฟแนวโน้มอุณหภูมิ
st.subheader("แนวโน้มอุณหภูมิ (High Frequency Temp)")
temp_data = supabase.table("temp_frequent_logs").select("recorded_at, temp_actual, temp_target").order("recorded_at", desc=True).limit(50).execute().data

if temp_data:
    df_temp = pd.DataFrame(temp_data)
    df_temp['recorded_at'] = pd.to_datetime(df_temp['recorded_at'])
    df_temp = df_temp.set_index('recorded_at')
    st.line_chart(df_temp[['temp_actual', 'temp_target']])
else:
    st.info("ไม่มีข้อมูลอุณหภูมิในขณะนี้")

# 4. แสดงปริมาณการผลิตแยกตามสินค้า
st.subheader("ปริมาณการผลิตแยกตามสินค้า")
prod_logs = supabase.table("jig_usage_log").select("total_pieces, products(product_code)").execute().data

if prod_logs:
    df_prod = pd.DataFrame(prod_logs)
    df_prod['product_code'] = df_prod['products'].apply(lambda x: x['product_code'] if x else "N/A")
    df_prod = df_prod.groupby('product_code')['total_pieces'].sum()
    st.bar_chart(df_prod)
else:
    st.info("ยังไม่มีข้อมูลการผลิต")
