import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# ===== DB =====
conn = sqlite3.connect("inventory_pro.db", check_same_thread=False)
cursor = conn.cursor()

# ===== TABLE =====
cursor.execute("""
CREATE TABLE IF NOT EXISTS products(
id INTEGER PRIMARY KEY AUTOINCREMENT,
sku TEXT UNIQUE,
name TEXT,
created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS inventory(
id INTEGER PRIMARY KEY AUTOINCREMENT,
sku TEXT,
warehouse TEXT,
quantity INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS history(
id INTEGER PRIMARY KEY AUTOINCREMENT,
sku TEXT,
type TEXT,
quantity INTEGER,
date TEXT,
warehouse TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS warehouses(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT
)
""")

conn.commit()

# ===== DEFAULT DATA =====
cursor.execute("SELECT COUNT(*) FROM warehouses")
if cursor.fetchone()[0] == 0:
    cursor.executemany(
        "INSERT INTO warehouses(name) VALUES (?)",
        [("Kho A",), ("Kho B",), ("Kho C",)]
    )
    conn.commit()

# ===== FUNCTIONS =====
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
    return [x[0] for x in cursor.execute("SELECT name FROM warehouses").fetchall()]

# ===== UI =====
st.sidebar.title("🚀 INVENTORY PRO")

menu = st.sidebar.radio("Menu",[
    "Dashboard",
    "Kho hàng",
    "Thêm sản phẩm",
    "Nhập/Xuất",
    "Lịch sử",
    "Xuất Excel"
])

# ===== DASHBOARD =====
if menu == "Dashboard":

    st.header("📊 Dashboard")

    df = get_stock()

    total = df["quantity"].sum()
    low = df[df["quantity"] < 5].shape[0]

    col1,col2 = st.columns(2)

    col1.metric("Tổng tồn kho", total)
    col2.metric("Sản phẩm sắp hết", low)

# ===== KHO =====
elif menu == "Kho hàng":

    st.header("📦 Tồn kho")

    df = get_stock()

    search = st.text_input("🔎 Tìm SKU hoặc tên")

    if search:
        df = df[
            df["sku"].str.contains(search,case=False) |
            df["name"].str.contains(search,case=False)
        ]

    st.dataframe(df,use_container_width=True)

# ===== ADD =====
elif menu == "Thêm sản phẩm":

    st.header("➕ Thêm sản phẩm")

    sku = st.text_input("SKU")
    name = st.text_input("Tên")

    if st.button("Thêm"):
        try:
            cursor.execute(
                "INSERT INTO products(sku,name,created_at) VALUES (?,?,?)",
                (sku,name,datetime.now())
            )
            conn.commit()
            st.success("Thêm thành công")
            st.rerun()
        except:
            st.error("SKU tồn tại")

# ===== IMPORT EXPORT =====
elif menu == "Nhập/Xuất":

    st.header("📥📤 Nhập/Xuất")

    df = get_products()

    product = st.selectbox("Chọn", df["name"])

    sku = df[df["name"]==product]["sku"].values[0]

    warehouses = get_warehouses()

    wh = st.selectbox("Kho", warehouses)

    qty = st.number_input("Số lượng",min_value=1)

    type_tx = st.radio("Loại",["Nhập","Xuất"])

    if st.button("Xác nhận"):

        cursor.execute(
            "SELECT quantity FROM inventory WHERE sku=? AND warehouse=?",
            (sku,wh)
        )

        res = cursor.fetchone()
        current = res[0] if res else 0

        if type_tx=="Nhập":
            new = current + qty
        else:
            if qty > current:
                st.error("Không đủ hàng")
                st.stop()
            new = current - qty

        if res:
            cursor.execute(
                "UPDATE inventory SET quantity=? WHERE sku=? AND warehouse=?",
                (new,sku,wh)
            )
        else:
            cursor.execute(
                "INSERT INTO inventory(sku,warehouse,quantity) VALUES (?,?,?)",
                (sku,wh,new)
            )

        cursor.execute(
            "INSERT INTO history(sku,type,quantity,date,warehouse) VALUES (?,?,?,?,?)",
            (sku,type_tx,qty,datetime.now(),wh)
        )

        conn.commit()
        st.success("OK")
        st.rerun()

# ===== HISTORY =====
elif menu == "Lịch sử":

    st.header("📜 Lịch sử")

    df = pd.read_sql("SELECT * FROM history ORDER BY date DESC", conn)

    st.dataframe(df)

# ===== EXPORT =====
elif menu == "Xuất Excel":

    st.header("📄 Xuất Excel")

    df = get_stock()

    file = "inventory.xlsx"

    df.to_excel(file,index=False)

    with open(file,"rb") as f:
        st.download_button("Download",f,file_name=file)
