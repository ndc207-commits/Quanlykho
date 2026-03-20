import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

# ================= CONFIG =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "inventory_production.db")

# ================= DB =================
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

# ================= CREATE TABLES (FIXED) =================
cursor.executescript("""
CREATE TABLE IF NOT EXISTS products(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE,
    name TEXT,
    created_at TEXT,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    role TEXT,
    store TEXT
);

CREATE TABLE IF NOT EXISTS stores(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
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

# ================= SAFE MIGRATION =================
try:
    cursor.execute("PRAGMA table_info(products)")
    columns = [column[1] for column in cursor.fetchall()]

    if "is_active" not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN is_active INTEGER DEFAULT 1")
        conn.commit()
except:
    pass

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

# ===== STORES =====
cursor.execute("SELECT COUNT(*) FROM stores")
if cursor.fetchone()[0] == 0:
    cursor.executemany(
        "INSERT INTO stores(name) VALUES (?)",
        [("Muse",), ("Metz Ville",), ("Nancy",)]
    )

# ===== USERS =====
cursor.execute("SELECT COUNT(*) FROM users")
if cursor.fetchone()[0] == 0:
    cursor.executemany(
        "INSERT INTO users(username,password,role,store) VALUES (?,?,?,?)",
        [
            ("admin","admin123","admin","ALL"),
            ("muse","123","staff","Muse"),
            ("metz","123","staff","Metz Ville"),
            ("nancy","123","staff","Nancy")
        ]
    )

conn.commit()

# ================= HELPERS =================
def get_products():
    return pd.read_sql("SELECT * FROM products WHERE is_active=1", conn)

def get_stock():
    return pd.read_sql("""
    SELECT p.sku,p.name,
    COALESCE(i.warehouse,'Chưa có kho') as warehouse,
    COALESCE(i.quantity,0) as quantity
    FROM products p
    LEFT JOIN inventory i ON p.sku=i.sku
    WHERE p.is_active=1
    """, conn)

def get_warehouses():
    return [x[0] for x in cursor.execute("SELECT name FROM warehouses")]

def safe_get_sku(df, display):
    row = df[df["display"] == display]
    if row.empty:
        return None
    return row.iloc[0]["sku"]


# ================= LOGIN =================
def login(u,p):
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
    return cursor.fetchone()

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login(u,p)
        if user:
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Sai tài khoản")
    st.stop()

user = st.session_state.user
role = user[3]
store_user = user[4]

# ================= UI =================
st.sidebar.title("📦 QUẢN LÝ KHO AMME THE")

menu = st.sidebar.radio("DANH MUC",[
    "Dashboard",
    "Tồn kho",
    "Thêm sản phẩm",
    "Sửa / Xóa sản phẩm",
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

    st.subheader("📦 Tồn kho theo kho")

    kho = df_stock.groupby("warehouse")["quantity"].sum().reset_index()
    kho.columns = ["Kho", "Số lượng"]

    st.dataframe(kho)
    st.bar_chart(kho.set_index("Kho"))

    if not df_hist.empty:
        df_hist["date"] = pd.to_datetime(df_hist["date"])

        df_hist["day"] = df_hist["date"].dt.date
        daily = df_hist.groupby(["day","type"])["quantity"].sum().unstack().fillna(0)

        st.subheader("📅 Theo ngày")
        st.line_chart(daily)

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

# ================= SỬA / XÓA =================
elif menu == "Sửa / Xóa sản phẩm":

    st.header("✏️ Sửa / Xóa sản phẩm")

    df_products = get_products()

    if df_products.empty:
        st.warning("Chưa có sản phẩm")
        st.stop()

    df_products["display"] = df_products["sku"] + " - " + df_products["name"]

    selected = st.selectbox("Chọn sản phẩm", df_products["display"])

    sku = safe_get_sku(df_products, selected)

    product = df_products[df_products["sku"] == sku].iloc[0]

    new_name = st.text_input("Tên mới", value=product["name"])

    if st.button("Cập nhật"):
        cursor.execute("UPDATE products SET name=? WHERE sku=?", (new_name, sku))
        conn.commit()
        st.success("Đã cập nhật")
        st.rerun()

    st.divider()

    new_sku = st.text_input("SKU mới", value=sku)

    if st.button("Đổi SKU"):
        cursor.execute("SELECT 1 FROM products WHERE sku=?", (new_sku,))
        if cursor.fetchone():
            st.error("SKU đã tồn tại")
            st.stop()

        cursor.execute("UPDATE products SET sku=? WHERE sku=?", (new_sku, sku))
        cursor.execute("UPDATE inventory SET sku=? WHERE sku=?", (new_sku, sku))
        cursor.execute("UPDATE history SET sku=? WHERE sku=?", (new_sku, sku))
        conn.commit()
        st.success("Đổi SKU thành công")
        st.rerun()

    st.divider()

    confirm = st.checkbox("Xác nhận xóa")

    if st.button("Xóa"):
        if not confirm:
            st.warning("Hãy xác nhận trước")
            st.stop()

        cursor.execute("UPDATE products SET is_active=0 WHERE sku=?", (sku,))
        conn.commit()
        st.success("Đã xóa")
        st.rerun()

# ================= NHẬP XUẤT =================
elif menu == "Nhập / Xuất":

    st.header("📥📤 Nhập / Xuất")

    df = get_products()

    df["display"] = df["sku"] + " - " + df["name"]

    selected = st.selectbox("Chọn sản phẩm", df["display"])

    sku = safe_get_sku(df, selected)

    wh = st.selectbox("Kho", get_warehouses())
    qty = st.number_input("Số lượng", min_value=1)

    type_tx = st.radio("Loại", ["Nhập", "Xuất"])

   # 👇 THÊM
    def get_stores():
        return [x[0] for x in cursor.execute("SELECT name FROM stores")]

    destination = ""

    if type_tx == "Xuất":
        if role == "admin":
            destination = st.selectbox("Xuất đến", get_stores())
        else:
            destination = store_user
            st.info(f"Xuất cho: {destination}")
    
        

    if st.button("Xác nhận"):

        cursor.execute("SELECT quantity FROM inventory WHERE sku=? AND warehouse=?", (sku, wh))
        res = cursor.fetchone()
        current = res[0] if res else 0

        if type_tx == "Xuất" and qty > current:
            st.error("Không đủ hàng")
            st.stop()

        new = current + qty if type_tx == "Nhập" else current - qty

        if res:
            cursor.execute("UPDATE inventory SET quantity=? WHERE sku=? AND warehouse=?", (new, sku, wh))
        else:
            cursor.execute("INSERT INTO inventory(sku,warehouse,quantity) VALUES (?,?,?)", (sku, wh, new))

        cursor.execute("INSERT INTO history(sku,type,quantity,date,warehouse,note) VALUES (?,?,?,?,?,?)",
                       (sku, type_tx, qty, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), wh, destination))

        conn.commit()

        st.success("Thành công")
        st.rerun()

# ================= CHUYỂN =================
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

        cursor.execute("UPDATE inventory SET quantity=? WHERE sku=? AND warehouse=?", (current-qty,sku,from_wh))

        cursor.execute("SELECT quantity FROM inventory WHERE sku=? AND warehouse=?", (sku,to_wh))
        res2 = cursor.fetchone()

        if res2:
            cursor.execute("UPDATE inventory SET quantity=? WHERE sku=? AND warehouse=?", (res2[0]+qty,sku,to_wh))
        else:
            cursor.execute("INSERT INTO inventory(sku,warehouse,quantity) VALUES (?,?,?)", (sku,to_wh,qty))

        # xác định shop
        store = store_user if role != "admin" else "Chuyển kho"

        cursor.execute(
            "INSERT INTO history(sku,type,quantity,date,warehouse,note) VALUES (?,?,?,?,?,?)",
            (sku,"Chuyển",qty,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
         from_wh,
         f"{store} → {to_wh}")
)

        conn.commit()
        st.success("Chuyển thành công")
        st.rerun()

elif menu == "Báo cáo":

    st.header("⚠️ Hàng sắp hết")

    df = get_stock()

    limit = st.number_input("Ngưỡng", value=5)

    df.columns = ["SKU","Tên","Kho","Số lượng"]

    # ===== HIGHLIGHT =====
    def highlight_low(row):
        if row["Số lượng"] < limit:
            return ['background-color: #ff4d4d'] * len(row)  # đỏ
        elif row["Số lượng"] < limit * 2:
            return ['background-color: #fff3cd'] * len(row)  # vàng
        else:
            return [''] * len(row)

    styled_df = df.style.apply(highlight_low, axis=1)

    st.dataframe(styled_df, use_container_width=True)

# ================= LỊCH SỬ =================
elif menu == "Lịch sử":

    st.header("📜 Lịch sử")

    df = pd.read_sql("""
    SELECT h.id,
           h.sku,
           p.name,
           h.type,
           h.quantity,
           h.date,
           h.warehouse,
           h.note
    FROM history h
    LEFT JOIN products p ON h.sku = p.sku
    ORDER BY h.date DESC
    """, conn)

    df.columns = ["ID","SKU","Tên sản phẩm","Loại","Số lượng","Thời gian","Kho","Ghi chú"]

    df["Thời gian"] = pd.to_datetime(df["Thời gian"], errors="coerce")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Từ ngày", value=None)
    with col2:
        end_date = st.date_input("Đến ngày", value=None)

    if start_date and end_date:
        df = df[
            (df["Thời gian"] >= pd.to_datetime(start_date)) &
            (df["Thời gian"] <= pd.to_datetime(end_date))
        ]

    if role != "admin":
        df = df[df["Ghi chú"] == store_user]
    st.dataframe(df, use_container_width=True)

    df_xuat = df[df["Loại"] == "Xuất"]

    if not df_xuat.empty:
        summary = df_xuat.groupby("Ghi chú")["Số lượng"].sum().reset_index()
        summary.columns = ["Cửa hàng","Tổng xuất"]

        st.dataframe(summary)
        st.bar_chart(summary.set_index("Cửa hàng"))
    

# ================= EXPORT =================
elif menu == "Xuất Excel":

    st.header("📤 Xuất Excel")

    df = pd.read_sql("SELECT * FROM history", conn)

    if st.button("Tải file"):
        file = "export.xlsx"
        df.to_excel(file, index=False)

        with open(file, "rb") as f:
            st.download_button("Download", f, file_name=file)
