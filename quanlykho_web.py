import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

# ================= CONFIG =================
DB_URL = "postgresql://postgres:Nhutren9989@db.acwzgbfrlqykqlhanfdi.supabase.co:5432/postgres"
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
CREATE TABLE IF NOT EXISTS stores(
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS products(
    id SERIAL PRIMARY KEY,
    sku TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS users(
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT,
    store_id INTEGER REFERENCES stores(id)
);

CREATE TABLE IF NOT EXISTS warehouses(
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory(
    id SERIAL PRIMARY KEY,
    sku TEXT NOT NULL,
    warehouse_id INTEGER REFERENCES warehouses(id),
    quantity INTEGER NOT NULL DEFAULT 0,
    UNIQUE(sku, warehouse_id)
);

CREATE TABLE IF NOT EXISTS history(
    id SERIAL PRIMARY KEY,
    sku TEXT NOT NULL,
    type TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    warehouse_id INTEGER REFERENCES warehouses(id),
    note TEXT
);
""")

# ================= INIT DATA =================
if run_query("SELECT COUNT(*) FROM warehouses").fetchone()[0] == 0:
    run_commit("""
    INSERT INTO warehouses(name) VALUES
    ('Kho La Pagode'), ('Kho Muse'), ('Kho Metz Ville'), ('Kho Nancy')
    """)

if run_query("SELECT COUNT(*) FROM stores").fetchone()[0] == 0:
    run_commit("""
    INSERT INTO stores(name) VALUES
    ('Muse'), ('Metz Ville'), ('Nancy')
    """)

if run_query("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
    # Lấy store_id cho từng store
    stores = {row[1]: row[0] for row in run_query("SELECT * FROM stores")}
    run_commit("""
    INSERT INTO users(username,password,role,store_id) VALUES
    (:admin, 'admin123', 'admin', NULL),
    (:muse, '123', 'staff', :muse_id),
    (:metz, '123', 'staff', :metz_id),
    (:nancy, '123', 'staff', :nancy_id)
    """, {
        "admin": "admin",
        "muse": "muse",
        "metz": "metz",
        "nancy": "nancy",
        "muse_id": stores["Muse"],
        "metz_id": stores["Metz Ville"],
        "nancy_id": stores["Nancy"]
    })

# ================= HELPERS =================
def get_products():
    return pd.read_sql("SELECT * FROM products WHERE is_active=TRUE", engine)

def get_stock():
    return pd.read_sql("""
    SELECT 
        p.sku,
        p.name,
        COALESCE(w.name, 'Chưa có kho') AS warehouse,
        COALESCE(i.quantity, 0) AS quantity
    FROM products p
    LEFT JOIN inventory i ON p.sku = i.sku
    LEFT JOIN warehouses w ON i.warehouse_id = w.id
    WHERE p.is_active = TRUE
    """, engine)

def get_warehouses():
    return [x[0] for x in run_query("SELECT name FROM warehouses")]

def get_stores():
    return [x[0] for x in run_query("SELECT name FROM stores")]

def safe_get_sku(df, display):
    row = df[df["display"] == display]
    return None if row.empty else row.iloc[0]["sku"]

def get_warehouse_id(name):
    row = run_query("SELECT id FROM warehouses WHERE name=:name", {"name": name}).fetchone()
    return row[0] if row else None

def get_store_id(name):
    row = run_query("SELECT id FROM stores WHERE name=:name", {"name": name}).fetchone()
    return row[0] if row else None

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
store_user_id = user[4]

# ================= UI =================
st.sidebar.title("📦 QUẢN LÝ KHO AMME THE")

menu = st.sidebar.radio("DANH MUC",[
    "Dashboard","Tồn kho","Thêm sản phẩm","Sửa / Xóa sản phẩm",
    "Nhập / Xuất","Chuyển kho","Báo cáo","Lịch sử","Xuất Excel"
])

# ================= DASHBOARD =================
if menu == "Dashboard":
    df_stock = get_stock()
    kho = df_stock.groupby("warehouse")["quantity"].sum().reset_index()
    kho.columns = ["Kho","Số lượng"]
    st.dataframe(kho)
    st.bar_chart(kho.set_index("Kho"))

# ================= TỒN KHO =================
elif menu == "Tồn kho":
    df = get_stock()
    search = st.text_input("🔎 Tìm")
    if search:
        df = df[df["sku"].str.contains(search, case=False) | df["name"].str.contains(search, case=False)]
    df.columns = ["SKU","Tên","Kho","Số lượng"]
    st.dataframe(df, use_container_width=True)

# ================= THÊM SẢN PHẨM =================
elif menu == "Thêm sản phẩm":
    sku = st.text_input("SKU")
    name = st.text_input("Tên")
    if st.button("Thêm"):
        run_commit(
            "INSERT INTO products(sku,name,created_at) VALUES (:sku,:name,:t)",
            {"sku": sku, "name": name, "t": datetime.now()}
        )
        st.success("Đã thêm sản phẩm")
        st.rerun()

# ================= NHẬP / XUẤT =================
elif menu == "Nhập / Xuất":
    df = get_products()
    df["display"] = df["sku"] + " - " + df["name"]
    selected = st.selectbox("Sản phẩm", df["display"])
    sku = safe_get_sku(df, selected)

    wh_name = st.selectbox("Kho", get_warehouses())
    wh_id = get_warehouse_id(wh_name)
    qty = st.number_input("Số lượng", min_value=1)
    type_tx = st.radio("Loại", ["Nhập","Xuất"])

    destination = ""
    if type_tx == "Xuất":
        if role == "admin":
            store_name = st.selectbox("Cửa hàng", get_stores())
            destination = store_name
        else:
            destination = run_query("SELECT name FROM stores WHERE id=:id", {"id": store_user_id}).fetchone()[0]

    if st.button("Xác nhận"):
        res = run_query(
            "SELECT quantity FROM inventory WHERE sku=:sku AND warehouse_id=:wh",
            {"sku": sku, "wh": wh_id}
        ).fetchone()
        current = res[0] if res else 0
        if type_tx=="Xuất" and qty>current:
            st.error("Không đủ hàng")
            st.stop()
        new_qty = current + qty if type_tx=="Nhập" else current - qty
        if res:
            run_commit(
                "UPDATE inventory SET quantity=:q WHERE sku=:sku AND warehouse_id=:wh",
                {"q": new_qty, "sku": sku, "wh": wh_id}
            )
        else:
            run_commit(
                "INSERT INTO inventory(sku, warehouse_id, quantity) VALUES (:sku,:wh,:q)",
                {"sku": sku, "wh": wh_id, "q": new_qty}
            )
        run_commit(
            "INSERT INTO history(sku,type,quantity,created_at,warehouse_id,note) VALUES "
            "(:sku,:type,:qty,:date,:wh,:note)",
            {
                "sku": sku,
                "type": type_tx,
                "qty": qty,
                "date": datetime.now(),
                "wh": wh_id,
                "note": destination
            }
        )
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
    SELECT h.id, h.sku, p.name, h.type, h.quantity, h.created_at, w.name AS warehouse, h.note
    FROM history h
    LEFT JOIN products p ON h.sku=p.sku
    LEFT JOIN warehouses w ON h.warehouse_id=w.id
    ORDER BY h.created_at DESC
    """, engine)
    df.columns = ["ID","SKU","Tên","Loại","Số lượng","Thời gian","Kho","Ghi chú"]
    if role != "admin":
        df = df[df["Ghi chú"] == destination]
    st.dataframe(df)

# ================= XUẤT EXCEL =================
elif menu == "Xuất Excel":
    df = pd.read_sql("SELECT * FROM history", engine)
    if st.button("Download"):
        file = "export.xlsx"
        df.to_excel(file,index=False)
        with open(file,"rb") as f:
            st.download_button("Download",f,file_name=file)
