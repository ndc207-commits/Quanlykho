import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

# ================= CONFIG =================
DB_URL = "postgresql://postgres.acwzgbfrlqykqlhanfdi:Nhutren9989@aws-1-eu-central-1.pooler.supabase.com:5432/postgres"
engine = create_engine(DB_URL, pool_size=5, max_overflow=10, pool_pre_ping=True)

# ================= DB HELPERS =================
def run_query(q, p={}):
    with engine.connect() as conn:
        return conn.execute(text(q), p)

def run_commit(q, p={}):
    with engine.begin() as conn:
        conn.execute(text(q), p)

def refresh():
    st.cache_data.clear()
    st.rerun()

# ================= INIT TABLES =================
run_commit("""
CREATE TABLE IF NOT EXISTS stores(
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS products(
    id SERIAL PRIMARY KEY,
    sku TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS warehouses(
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS inventory(
    id SERIAL PRIMARY KEY,
    sku TEXT NOT NULL,
    warehouse_id INTEGER,
    quantity INTEGER DEFAULT 0,
    UNIQUE(sku, warehouse_id)
);

CREATE TABLE IF NOT EXISTS store_inventory(
    id SERIAL PRIMARY KEY,
    sku TEXT NOT NULL,
    store_id INTEGER,
    quantity INTEGER DEFAULT 0,
    UNIQUE(sku, store_id)
);

CREATE TABLE IF NOT EXISTS users(
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT NOT NULL,
    role TEXT,
    store_id INTEGER
);

CREATE TABLE IF NOT EXISTS history(
    id SERIAL PRIMARY KEY,
    sku TEXT NOT NULL,
    type TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    warehouse_id INTEGER,
    note TEXT,
    created_at TIMESTAMP DEFAULT now()
);
""")

# ================= INIT DATA =================
if run_query("SELECT COUNT(*) FROM warehouses").fetchone()[0]==0:
    run_commit("""
    INSERT INTO warehouses(name) VALUES
    ('Kho La Pagode'), ('Kho Muse'), ('Kho Metz Ville'), ('Kho Nancy')
    """)

if run_query("SELECT COUNT(*) FROM stores").fetchone()[0]==0:
    run_commit("""
    INSERT INTO stores(name) VALUES
    ('Muse'), ('Metz Ville'), ('Nancy')
    """)

if run_query("SELECT COUNT(*) FROM users").fetchone()[0]==0:
    stores = {row[1]: row[0] for row in run_query("SELECT * FROM stores")}
    run_commit("""
    INSERT INTO users(username,password,role,store_id) VALUES
    (:admin,'admin123','admin',NULL),
    (:muse,'123','staff',:muse_id),
    (:metz,'123','staff',:metz_id),
    (:nancy,'123','staff',:nancy_id)
    """, {
        "admin":"admin","muse":"muse","metz":"metz","nancy":"nancy",
        "muse_id":stores["Muse"], "metz_id":stores["Metz Ville"], "nancy_id":stores["Nancy"]
    })

# ================= CACHE HELPERS =================
@st.cache_data(ttl=10)
def get_products():
    return pd.read_sql("SELECT * FROM products WHERE is_active=TRUE", engine)

@st.cache_data(ttl=10)
def get_stock():
    return pd.read_sql("""
    SELECT p.sku,p.name,COALESCE(w.name,'Chưa có kho') warehouse,COALESCE(i.quantity,0) quantity
    FROM products p
    LEFT JOIN inventory i ON p.sku=i.sku
    LEFT JOIN warehouses w ON i.warehouse_id=w.id
    WHERE p.is_active=TRUE
    """, engine)

@st.cache_data(ttl=10)
def get_store_stock():
    return pd.read_sql("""
    SELECT p.sku,p.name,s.name store,COALESCE(si.quantity,0) quantity
    FROM products p
    LEFT JOIN store_inventory si ON p.sku=si.sku
    LEFT JOIN stores s ON si.store_id=s.id
    WHERE p.is_active=TRUE
    """, engine)

@st.cache_data(ttl=60)
def get_warehouses():
    return pd.read_sql("SELECT * FROM warehouses", engine)

@st.cache_data(ttl=60)
def get_stores():
    return pd.read_sql("SELECT * FROM stores", engine)

# ================= LOGIN =================
def login(u,p):
    return run_query(
        "SELECT * FROM users WHERE username=:u AND password=:p",
        {"u":u,"p":p}
    ).fetchone()

if "user" not in st.session_state:
    st.session_state.user=None

if not st.session_state.user:
    st.title("🔐 Login")
    u=st.text_input("Username")
    p=st.text_input("Password",type="password")
    if st.button("Login"):
        user=login(u,p)
        if user:
            st.session_state.user=user
            st.rerun()
        else:
            st.error("Sai tài khoản")
    st.stop()

user=st.session_state.user
role=user[3]
store_user_id=user[4]

# ================= MENU =================
st.sidebar.title("📦 QUẢN LÝ KHO")
menu = st.sidebar.radio("Menu", [
    "Dashboard","Kho tổng","Kho cửa hàng","Thêm sản phẩm",
    "Sửa / Xóa sản phẩm","Nhập / Xuất","Lịch sử","Xuất Excel"
])

# ================= DASHBOARD =================
if menu=="Dashboard":
    df_stock=get_stock()
    st.subheader("Kho tổng")
    st.bar_chart(df_stock.groupby("warehouse")["quantity"].sum())
    
    df_store=get_store_stock()
    st.subheader("Kho cửa hàng")
    st.bar_chart(df_store.groupby("store")["quantity"].sum())

# ================= KHO TỔNG =================
elif menu=="Kho tổng":
    st.dataframe(get_stock())

# ================= KHO CỬA HÀNG =================
elif menu=="Kho cửa hàng":
    st.dataframe(get_store_stock())

# ================= THÊM SẢN PHẨM =================
elif menu=="Thêm sản phẩm":
    sku=st.text_input("SKU")
    name=st.text_input("Tên")
    if st.button("Thêm"):
        run_commit("INSERT INTO products(sku,name) VALUES (:s,:n)",{"s":sku,"n":name})
        st.success("Đã thêm sản phẩm")
        refresh()

# ================= SỬA / XÓA / PHỤC HỒI =================
elif menu=="Sửa / Xóa sản phẩm":
    df=get_products()
    if df.empty:
        st.info("Chưa có sản phẩm nào.")
        st.stop()
    df["display"]=df["sku"]+" - "+df["name"]
    selected = st.selectbox("Chọn sản phẩm", df["display"])
    sku=df[df["display"]==selected]["sku"].values[0]
    current_name=df[df["sku"]==sku]["name"].values[0]

    new_name=st.text_input("Tên mới",value=current_name)
    if st.button("Cập nhật tên"):
        run_commit("UPDATE products SET name=:n WHERE sku=:s",{"n":new_name,"s":sku})
        st.success("Đã cập nhật tên")
        refresh()

    if st.button("Xóa sản phẩm"):
        run_commit("UPDATE products SET is_active=FALSE WHERE sku=:s",{"s":sku})
        st.success("Đã xóa sản phẩm (có thể phục hồi)")
        refresh()

    # Phục hồi
    deleted_df=pd.read_sql("SELECT * FROM products WHERE is_active=FALSE",engine)
    if not deleted_df.empty:
        deleted_df["display"]=deleted_df["sku"]+" - "+deleted_df["name"]
        recover=st.selectbox("Phục hồi sản phẩm đã xóa",deleted_df["display"])
        recover_sku=deleted_df[deleted_df["display"]==recover]["sku"].values[0]
        if st.button("Phục hồi"):
            run_commit("UPDATE products SET is_active=TRUE WHERE sku=:s",{"s":recover_sku})
            st.success("Đã phục hồi sản phẩm")
            refresh()

# ================= NHẬP / XUẤT =================
elif menu=="Nhập / Xuất":
    products=get_products()
    wh=get_warehouses()
    stores=get_stores()

    products["d"]=products["sku"]+"-"+products["name"]
    sel=st.selectbox("Sản phẩm",products["d"])
    sku=products[products["d"]==sel]["sku"].values[0]

    wh_name=st.selectbox("Kho",wh["name"])
    wh_id=wh[wh["name"]==wh_name]["id"].values[0]

    qty=st.number_input("Số lượng",min_value=1)
    type_tx=st.radio("Loại",["Nhập","Xuất"])

    store_name=None
    if type_tx=="Xuất":
        if role=="admin":
            store_name=st.selectbox("Cửa hàng",stores["name"])
        else:
            store_name=run_query("SELECT name FROM stores WHERE id=:id",{"id":store_user_id}).fetchone()[0]

    if st.button("Xác nhận"):
        with engine.begin() as conn:
            res=conn.execute(text("SELECT quantity FROM inventory WHERE sku=:s AND warehouse_id=:w FOR UPDATE"),{"s":sku,"w":wh_id}).fetchone()
            current=res[0] if res else 0
            if type_tx=="Xuất" and qty>current:
                st.error("Không đủ hàng")
                st.stop()
            new_qty=current+qty if type_tx=="Nhập" else current-qty
            if res:
                conn.execute(text("UPDATE inventory SET quantity=:q WHERE sku=:s AND warehouse_id=:w"),{"q":new_qty,"s":sku,"w":wh_id})
            else:
                conn.execute(text("INSERT INTO inventory(sku,warehouse_id,quantity) VALUES (:s,:w,:q)"),{"s":sku,"w":wh_id,"q":new_qty})

            # Cập nhật kho cửa hàng
            if type_tx=="Xuất":
                sid=run_query("SELECT id FROM stores WHERE name=:n",{"n":store_name}).fetchone()[0]
                res2=conn.execute(text("SELECT quantity FROM store_inventory WHERE sku=:s AND store_id=:sid FOR UPDATE"),{"s":sku,"sid":sid}).fetchone()
                cur2=res2[0] if res2 else 0
                new2=cur2+qty
                if res2:
                    conn.execute(text("UPDATE store_inventory SET quantity=:q WHERE sku=:s AND store_id=:sid"),{"q":new2,"s":sku,"sid":sid})
                else:
                    conn.execute(text("INSERT INTO store_inventory(sku,store_id,quantity) VALUES (:s,:sid,:q)"),{"s":sku,"sid":sid,"q":new2})

            # Lưu lịch sử
            conn.execute(text("INSERT INTO history(sku,type,quantity,warehouse_id,note) VALUES (:s,:t,:q,:w,:n)"),{"s":sku,"t":type_tx,"q":qty,"w":wh_id,"n":store_name})
        st.success("OK")
        refresh()

# ================= LỊCH SỬ =================
elif menu=="Lịch sử":
    df=pd.read_sql("SELECT * FROM history ORDER BY created_at DESC LIMIT 200",engine)
    st.dataframe(df)

# ================= XUẤT EXCEL =================
elif menu=="Xuất Excel":
    df=pd.read_sql("SELECT * FROM history ORDER BY created_at DESC LIMIT 1000",engine)
    if st.button("Download"):
        df.to_excel("export.xlsx",index=False)
        with open("export.xlsx","rb") as f:
            st.download_button("Download",f,file_name="export.xlsx")
