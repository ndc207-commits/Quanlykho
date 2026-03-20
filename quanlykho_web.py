import streamlit as st
import pandas as pd
from datetime import datetime
import os
from sqlalchemy import create_engine, text

# ================= CONFIG =================
DB_URL = "postgresql://postgres:Nhutren9989@db.dgrdlmsnttkkvuyphfur.supabase.co:5432/postgres"
engine = create_engine(DB_URL, pool_pre_ping=True)

# ================= DB HELPERS =================
def run_query(query, params={}):
    with engine.connect() as conn:
        return conn.execute(text(query), params)

def run_commit(query, params={}):
    with engine.begin() as conn:
        conn.execute(text(query), params)

# ================= INIT TABLE =================
run_commit("""
CREATE TABLE IF NOT EXISTS products(
    id SERIAL PRIMARY KEY,
    sku TEXT UNIQUE,
    name TEXT,
    created_at TEXT,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS users(
    id SERIAL PRIMARY KEY,
    username TEXT,
    password TEXT,
    role TEXT,
    store TEXT
);

CREATE TABLE IF NOT EXISTS stores(
    id SERIAL PRIMARY KEY,
    name TEXT
);

CREATE TABLE IF NOT EXISTS inventory(
    id SERIAL PRIMARY KEY,
    sku TEXT,
    warehouse TEXT,
    quantity INTEGER
);

CREATE TABLE IF NOT EXISTS history(
    id SERIAL PRIMARY KEY,
    sku TEXT,
    type TEXT,
    quantity INTEGER,
    date TEXT,
    warehouse TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS warehouses(
    id SERIAL PRIMARY KEY,
    name TEXT
);
""")

# ================= INIT DATA =================
if run_query("SELECT COUNT(*) FROM warehouses").fetchone()[0] == 0:
    run_commit("""
    INSERT INTO warehouses(name) VALUES
    ('Kho La Pagode'),
    ('Kho Muse'),
    ('Kho Metz Ville'),
    ('Kho Nancy')
    """)

if run_query("SELECT COUNT(*) FROM stores").fetchone()[0] == 0:
    run_commit("""
    INSERT INTO stores(name) VALUES
    ('Muse'), ('Metz Ville'), ('Nancy')
    """)

if run_query("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
    run_commit("""
    INSERT INTO users(username,password,role,store) VALUES
    ('admin','admin123','admin','ALL'),
    ('muse','123','staff','Muse'),
    ('metz','123','staff','Metz Ville'),
    ('nancy','123','staff','Nancy')
    """)

# ================= HELPERS =================
def get_products():
    return pd.read_sql("SELECT * FROM products WHERE is_active=1", engine)

def get_stock():
    return pd.read_sql("""
    SELECT p.sku,p.name,
    COALESCE(i.warehouse,'Chưa có kho') as warehouse,
    COALESCE(i.quantity,0) as quantity
    FROM products p
    LEFT JOIN inventory i ON p.sku=i.sku
    WHERE p.is_active=1
    """, engine)

def get_warehouses():
    return [x[0] for x in run_query("SELECT name FROM warehouses")]

def get_stores():
    return [x[0] for x in run_query("SELECT name FROM stores")]

def safe_get_sku(df, display):
    row = df[df["display"] == display]
    return None if row.empty else row.iloc[0]["sku"]

# ================= LOGIN =================
def login(u,p):
    return run_query(
        "SELECT * FROM users WHERE username=:u AND password=:p",
        {"u":u,"p":p}
    ).fetchone()

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
    "Dashboard","Tồn kho","Thêm sản phẩm","Sửa / Xóa sản phẩm",
    "Nhập / Xuất","Chuyển kho","Báo cáo","Lịch sử","Xuất Excel"
])

# ================= DASHBOARD =================
if menu == "Dashboard":

    df_stock = get_stock()
    df_hist = pd.read_sql("SELECT * FROM history", engine)

    kho = df_stock.groupby("warehouse")["quantity"].sum().reset_index()
    kho.columns = ["Kho","Số lượng"]

    st.dataframe(kho)
    st.bar_chart(kho.set_index("Kho"))

# ================= TỒN KHO =================
elif menu == "Tồn kho":

    df = get_stock()

    search = st.text_input("🔎 Tìm")

    if search:
        df = df[df["sku"].str.contains(search,case=False) | df["name"].str.contains(search,case=False)]

    df.columns = ["SKU","Tên","Kho","Số lượng"]
    st.dataframe(df, use_container_width=True)

# ================= THÊM =================
elif menu == "Thêm sản phẩm":

    sku = st.text_input("SKU")
    name = st.text_input("Tên")

    if st.button("Thêm"):
        run_commit(
            "INSERT INTO products(sku,name,created_at) VALUES (:sku,:name,:t)",
            {"sku":sku,"name":name,"t":datetime.now()}
        )
        st.success("OK")
        st.rerun()

# ================= NHẬP XUẤT =================
elif menu == "Nhập / Xuất":

    df = get_products()
    df["display"] = df["sku"] + " - " + df["name"]

    selected = st.selectbox("Sản phẩm", df["display"])
    sku = safe_get_sku(df, selected)

    wh = st.selectbox("Kho", get_warehouses())
    qty = st.number_input("Số lượng", min_value=1)
    type_tx = st.radio("Loại", ["Nhập","Xuất"])

    destination = ""
    if type_tx == "Xuất":
        destination = st.selectbox("Cửa hàng", get_stores()) if role=="admin" else store_user

    if st.button("Xác nhận"):

        res = run_query(
            "SELECT quantity FROM inventory WHERE sku=:sku AND warehouse=:wh",
            {"sku":sku,"wh":wh}
        ).fetchone()

        current = res[0] if res else 0

        if type_tx == "Xuất" and qty > current:
            st.error("Không đủ hàng")
            st.stop()

        new = current + qty if type_tx=="Nhập" else current - qty

        if res:
            run_commit(
                "UPDATE inventory SET quantity=:q WHERE sku=:sku AND warehouse=:wh",
                {"q":new,"sku":sku,"wh":wh}
            )
        else:
            run_commit(
                "INSERT INTO inventory(sku,warehouse,quantity) VALUES (:sku,:wh,:q)",
                {"sku":sku,"wh":wh,"q":new}
            )

        run_commit("""
        INSERT INTO history(sku,type,quantity,date,warehouse,note)
        VALUES (:sku,:type,:qty,:date,:wh,:note)
        """,{
            "sku":sku,
            "type":type_tx,
            "qty":qty,
            "date":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "wh":wh,
            "note":destination
        })

        st.success("OK")
        st.rerun()

# ================= BÁO CÁO =================
elif menu == "Báo cáo":

    df = get_stock()
    limit = st.number_input("Ngưỡng", value=5)

    df.columns = ["SKU","Tên","Kho","Số lượng"]

    def highlight(row):
        if row["Số lượng"] < limit:
            return ['background-color:#ff4d4d']*4
        elif row["Số lượng"] < limit*2:
            return ['background-color:#fff3cd']*4
        return ['']*4

    st.dataframe(df.style.apply(highlight, axis=1))

# ================= LỊCH SỬ =================
elif menu == "Lịch sử":

    df = pd.read_sql("""
    SELECT h.id,h.sku,p.name,h.type,h.quantity,h.date,h.warehouse,h.note
    FROM history h
    LEFT JOIN products p ON h.sku=p.sku
    ORDER BY h.date DESC
    """, engine)

    df.columns = ["ID","SKU","Tên","Loại","Số lượng","Thời gian","Kho","Ghi chú"]

    if role != "admin":
        df = df[df["Ghi chú"] == store_user]

    st.dataframe(df)

# ================= EXPORT =================
elif menu == "Xuất Excel":

    df = pd.read_sql("SELECT * FROM history", engine)

    if st.button("Download"):
        file = "export.xlsx"
        df.to_excel(file,index=False)
        with open(file,"rb") as f:
            st.download_button("Download",f,file_name=file)
