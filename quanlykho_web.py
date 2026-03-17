import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ================= CONFIG =================
DB_NAME = "inventory_production.db"

# ================= DB =================
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

# ================= TABLE =================
cursor.executescript("""
CREATE TABLE IF NOT EXISTS products(
id INTEGER PRIMARY KEY AUTOINCREMENT,
sku TEXT UNIQUE,
name TEXT,
created_at TEXT
);

CREATE TABLE IF NOT EXISTS inventory(
id INTEGER PRIMARY KEY AUTOINCREMENT,
sku TEXT,
warehouse TEXT,
quantity INTEGER
);

CREATE TABLE IF NOT EXISTS history(
id INTEGER PRIMARY KEY AUTOINCREMENT,
sku TEXT,
type TEXT,
quantity INTEGER,
date TEXT,
warehouse TEXT,
note TEXT
);

CREATE TABLE IF NOT EXISTS warehouses(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT
);
""")

conn.commit()

# ================= INIT DATA =================
cursor.execute("SELECT COUNT(*) FROM warehouses")
if cursor.fetchone()[0] == 0:
    cursor.executemany(
        "INSERT INTO warehouses(name) VALUES (?)",
        [
            ("Kho La Pagode",),
            ("Kho Muse",),
            ("Kho Metz Ville",),
            ("Kho Nancy",)
        ]
    )
    conn.commit()

# ================= HELPERS =================
def get_products():
    return pd.read_sql("SELECT * FROM products", conn)

def get_stock():
    return pd.read_sql("""
    SELECT p.sku,p.name,
    COALESCE(i.warehouse,'Chưa có kho') as warehouse,
    COALESCE(i.quantity,0) as quantity
    FROM products p
    LEFT JOIN inventory i ON p.sku=i.sku
    """, conn)

def get_warehouses():
    return [x[0] for x in cursor.execute("SELECT name FROM warehouses")]

def safe_get_sku(df, display):
    row = df[df["display"] == display]
    if row.empty:
        return None
    return row.iloc[0]["sku"]

# ================= UI =================
st.sidebar.title("📦 QUẢN LÝ KHO PRODUCTION")

menu = st.sidebar.radio("Menu",[
    "Dashboard",
    "Tồn kho",
    "Thêm sản phẩm",
    "Nhập / Xuất",
    "Chuyển kho",
    "Báo cáo",
    "Lịch sử",
    "Xuất Excel"
])

# ================= DASHBOARD =================
if menu == "Dashboard":

    st.header("📊 Dashboard tổng hợp")

    df_stock = get_stock()
    df_hist = pd.read_sql("SELECT * FROM history", conn)

    # ===== THEO KHO =====
    st.subheader("📦 Tồn kho theo kho")

    kho = df_stock.groupby("warehouse")["quantity"].sum().reset_index()
    kho.columns = ["Kho", "Số lượng"]

    st.dataframe(kho)
    st.bar_chart(kho.set_index("Kho"))

    # ===== THEO NGÀY =====
    if not df_hist.empty:
        df_hist["date"] = pd.to_datetime(df_hist["date"])

        df_hist["day"] = df_hist["date"].dt.date
        daily = df_hist.groupby(["day","type"])["quantity"].sum().unstack().fillna(0)

        st.subheader("📅 Theo ngày")
        st.line_chart(daily)

        # ===== THEO THÁNG =====
        df_hist["month"] = df_hist["date"].dt.to_period("M").astype(str)
        monthly = df_hist.groupby(["month","type"])["quantity"].sum().unstack().fillna(0)

        st.subheader("📆 Theo tháng")
        st.bar_chart(monthly)

# ================= TỒN KHO =================
elif menu == "Tồn kho":

    st.header("📦 Tồn kho")

    df = get_stock()

    search = st.text_input("🔎 Tìm SKU hoặc tên")

    if search:
        df = df[
            df["sku"].str.contains(search,case=False) |
            df["name"].str.contains(search,case=False)
        ]

    df.columns = ["SKU","Tên sản phẩm","Kho","Số lượng"]

    st.dataframe(df, use_container_width=True)

# ================= THÊM =================
elif menu == "Thêm sản phẩm":

    st.header("➕ Thêm sản phẩm")

    sku = st.text_input("SKU")
    name = st.text_input("Tên sản phẩm")

    if st.button("Thêm"):
        if not sku or not name:
            st.warning("Nhập đủ thông tin")
            st.stop()

        try:
            cursor.execute(
                "INSERT INTO products(sku,name,created_at) VALUES (?,?,?)",
                (sku,name,datetime.now())
            )
            conn.commit()
            st.success("Thêm thành công")
            st.rerun()
        except:
            st.error("SKU đã tồn tại")

# ================= NHẬP XUẤT =================
elif menu == "Nhập / Xuất":

    st.header("📥📤 Nhập / Xuất")

    df = get_products()

    if df.empty:
        st.warning("Chưa có sản phẩm")
        st.stop()

    df["display"] = df["sku"] + " - " + df["name"]

    selected = st.selectbox("Chọn sản phẩm", df["display"])

    sku = safe_get_sku(df, selected)

    wh = st.selectbox("Kho", get_warehouses())
    qty = st.number_input("Số lượng", min_value=1)
    type_tx = st.radio("Loại", ["Nhập","Xuất"])

    if st.button("Xác nhận"):

        cursor.execute("SELECT quantity FROM inventory WHERE sku=? AND warehouse=?", (sku,wh))
        res = cursor.fetchone()
        current = res[0] if res else 0

        new = current + qty if type_tx=="Nhập" else current - qty

        if type_tx=="Xuất" and qty > current:
            st.error("Không đủ hàng")
            st.stop()

        if res:
            cursor.execute("UPDATE inventory SET quantity=? WHERE sku=? AND warehouse=?", (new,sku,wh))
        else:
            cursor.execute("INSERT INTO inventory(sku,warehouse,quantity) VALUES (?,?,?)", (sku,wh,new))

        cursor.execute("INSERT INTO history(sku,type,quantity,date,warehouse,note) VALUES (?,?,?,?,?,?)",
                       (sku,type_tx,qty,datetime.now(),wh,""))

        conn.commit()
        st.success("Thành công")
        st.rerun()

# ================= CHUYỂN KHO =================
elif menu == "Chuyển kho":

    st.header("🔄 Chuyển kho")

    df = get_products()

    df["display"] = df["sku"] + " - " + df["name"]
    selected = st.selectbox("Chọn sản phẩm", df["display"])

    sku = safe_get_sku(df, selected)

    from_wh = st.selectbox("Từ kho", get_warehouses())
    to_wh = st.selectbox("Đến kho", get_warehouses())
    qty = st.number_input("Số lượng", min_value=1)

    if st.button("Chuyển"):

        if from_wh == to_wh:
            st.error("Không thể cùng kho")
            st.stop()

        cursor.execute("SELECT quantity FROM inventory WHERE sku=? AND warehouse=?", (sku,from_wh))
        res = cursor.fetchone()
        current = res[0] if res else 0

        if qty > current:
            st.error("Kho nguồn không đủ hàng")
            st.stop()

        # trừ
        cursor.execute("UPDATE inventory SET quantity=? WHERE sku=? AND warehouse=?", (current-qty,sku,from_wh))

        # cộng
        cursor.execute("SELECT quantity FROM inventory WHERE sku=? AND warehouse=?", (sku,to_wh))
        res2 = cursor.fetchone()

        if res2:
            cursor.execute("UPDATE inventory SET quantity=? WHERE sku=? AND warehouse=?", (res2[0]+qty,sku,to_wh))
        else:
            cursor.execute("INSERT INTO inventory(sku,warehouse,quantity) VALUES (?,?,?)", (sku,to_wh,qty))

        cursor.execute("INSERT INTO history(sku,type,quantity,date,warehouse,note) VALUES (?,?,?,?,?,?)",
                       (sku,"Chuyển",qty,datetime.now(),from_wh,f"→ {to_wh}"))

        conn.commit()
        st.success("Chuyển thành công")
        st.rerun()

# ================= BÁO CÁO =================
elif menu == "Báo cáo":

    st.header("⚠️ Hàng sắp hết")

    df = get_stock()

    limit = st.number_input("Ngưỡng", value=5)

    low = df[df["quantity"] < limit]
    low.columns = ["SKU","Tên","Kho","Số lượng"]

    st.dataframe(low)

# ================= LỊCH SỬ =================
elif menu == "Lịch sử":

    st.header("📜 Lịch sử")

    df = pd.read_sql("SELECT * FROM history ORDER BY date DESC", conn)

    df.columns = ["ID","SKU","Loại","Số lượng","Thời gian","Kho","Ghi chú"]

    st.dataframe(df)

# ================= EXCEL =================
elif menu == "Xuất Excel":

    st.header("📄 Xuất Excel")

    df = get_stock()

    file = "ton_kho.xlsx"
    df.to_excel(file,index=False)

    with open(file,"rb") as f:
        st.download_button("⬇️ Tải file", f, file_name=file)
