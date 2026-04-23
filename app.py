import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")

# ---------------- CSS ----------------
st.markdown("""
<style>
.canvas {
    position: relative;
    width: 100%;
    height: 700px;
    background: #f5f5f5;
    border: 1px solid #ccc;
}

/* กล่อง */
.box {
    position: absolute;
    width: 90px;
    height: 60px;
    border-radius: 6px;
    text-align: center;
    line-height: 60px;
    font-weight: bold;
    color: white;
}

/* สี */
.black { background:#000; }
.red { background:#ff2d2d; }
.violet { background:#6a00ff; }
.green { background:#2e6b00; }
.orange { background:#ff7a00; }
.blue { background:#2f55ff; }
.darkblue { background:#0b1c7a; }
.pink { background:#ff66cc; }
.gold { background:#f5a623; }
.gray { background:#777; }
.ro { background:#66d1d1; color:#000; }

.label {
    position:absolute;
    font-size:12px;
    font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SUPABASE ----------------
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except:
    st.warning("ยังไม่เชื่อม Supabase")

# ---------------- DRAW ----------------
st.title("🏭 Production Layout (Match Diagram)")

st.markdown("""
<div class="canvas">

<!-- แถวบน -->
<div class="box black" style="top:40px; left:40px;">5</div>

<div class="box red" style="top:40px; left:160px;">2</div>
<div class="box violet" style="top:40px; left:260px;">3</div>
<div class="box ro" style="top:110px; left:210px;">RO</div>

<div class="box green" style="top:40px; left:360px;">8</div>
<div class="box black" style="top:40px; left:460px;">17</div>

<div class="box gold" style="top:40px; left:560px;">15</div>
<div class="box orange" style="top:40px; left:660px;">9</div>
<div class="box ro" style="top:110px; left:610px;">RO</div>

<div class="box blue" style="top:40px; left:760px;">10</div>
<div class="box green" style="top:40px; left:860px;">6</div>

<div class="box blue" style="top:40px; left:960px;">16</div>
<div class="box darkblue" style="top:40px; left:1060px;">4</div>
<div class="box ro" style="top:110px; left:1010px;">RO</div>

<!-- ล่าง -->
<div class="box gray" style="top:260px; left:40px;">Sealer</div>

<div class="box black" style="top:260px; left:160px;">20</div>
<div class="box red" style="top:260px; left:260px;">1A</div>

<div class="box pink" style="top:260px; left:360px;">7</div>
<div class="box ro" style="top:330px; left:360px;">RO</div>

<div class="box gray" style="top:260px; left:460px;">Hot</div>
<div class="box gold" style="top:260px; left:560px;">11</div>
<div class="box ro" style="top:330px; left:510px;">RO</div>

<div class="box red" style="top:260px; left:660px;">1B</div>
<div class="box orange" style="top:260px; left:760px;">19</div>
<div class="box gray" style="top:260px; left:860px;">12</div>
<div class="box pink" style="top:260px; left:960px;">14</div>

<div class="box ro" style="top:260px; left:1060px;">RO</div>
<div class="box ro" style="top:330px; left:1060px;">RO</div>
<div class="box ro" style="top:400px; left:1060px;">RO</div>

<!-- เคมี -->
<div class="label" style="top:80px; left:1180px;">Sodium Bicarbonate</div>
<div class="label" style="top:300px; left:1180px;">Nitric Acid 68</div>

<!-- anodized -->
<div class="box gray" style="top:420px; left:900px; width:120px; height:120px;">Anodized</div>

</div>
""", unsafe_allow_html=True)
