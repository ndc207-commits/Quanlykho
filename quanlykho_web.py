# inventory_web_pro.py
import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

# ==== Database connection ====
conn = sqlite3.connect("inventory_web_pro.db", check_same_thread=False)
cursor = conn.cursor()

# ==== Create tables if not exists ====
cursor.execute("""
CREATE TABLE IF NOT EXISTS products(
id INTEGER PRIMARY KEY AUTOINCREMENT,
sku TEXT UNIQUE,
name TEXT,
quantity INTEGER,
created_at TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS history(
id INTEGER PRIMARY KEY AUTOINCREMENT,
product_id INTEGER,
type TEXT,
quantity INTEGER,
date TEXT,
employee TEXT,
warehouse TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS employees(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
role TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS warehouses(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
location TEXT
)
""")
conn.commit()

# ==== Sample data ====
cursor.execute("SELECT COUNT(*) FROM employees")
if cursor.fetchone()[0]==0:
    employees = [("Admin","Manager"), ("Hanh","Staff"), ("Linh","Staff")]
    cursor.executemany("INSERT INTO employees(name, role) VALUES (?,?)", employees)
    conn.commit()

cursor.execute("SELECT COUNT(*) FROM warehouses")
if cursor.fetchone()[0]==0:
    warehouses = [("Kho La Pagode","HN"), ("Kho Muse","HCM"), ("Kho Metz Vilee","DN"), ("Kho Nancy","HP")]
    cursor.executemany("INSERT INTO warehouses(name, location) VALUES (?,?)", warehouses)
    conn.commit()

# ==== Sidebar menu ====
st.sidebar.title("Quản lý Kho Online Pro")
menu = st.sidebar.radio("Điều hướng", ["Kho hàng","Nhập/Xuất","Báo cáo hàng sắp hết","Lịch sử giao dịch","Xuất Excel"])

# ==== Helper functions ====
def refresh_products():
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=["ID","SKU","Tên sản phẩm","Số lượng","Ngày tạo"])
    return df

def highlight_low(x):
    return ['background-color: #FFAAAA' if v<5 else '' for v in x["Số lượng"]]

def add_product(sku, name, qty):
    try:
        cursor.execute("INSERT INTO products(sku,name,quantity,created_at) VALUES (?,?,?,?)",
                       (sku,name,qty,datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
    except sqlite3.IntegrityError:
        st.error("SKU đã tồn tại!")

def update_quantity(pid, qty, type_tx, employees_list, warehouses_list):
    for emp in employees_list:
        for wh in warehouses_list:
            if type_tx=="Nhập":
                cursor.execute("UPDATE products SET quantity=quantity+? WHERE id=?",(qty,pid))
            else:
                cursor.execute("SELECT quantity FROM products WHERE id=?",(pid,))
                if cursor.fetchone()[0]<qty:
                    st.error("Không đủ hàng để xuất!")
                    return False
                cursor.execute("UPDATE products SET quantity=quantity-? WHERE id=?",(qty,pid))
            cursor.execute("INSERT INTO history(product_id,type,quantity,date,employee,warehouse) VALUES (?,?,?,?,?,?)",
                           (pid,type_tx,qty,datetime.now().strftime("%Y-%m-%d %H:%M:%S"),emp,wh))
    conn.commit()
    return True

# ==== Kho hàng ====
if menu=="Kho hàng":
    st.header("Danh sách sản phẩm")
    df = refresh_products()
    st.dataframe(df.style.apply(highlight_low, axis=None))

# ==== Nhập/Xuất ====
elif menu=="Nhập/Xuất":
    st.header("Nhập / Xuất kho")
    df = refresh_products()
    product = st.selectbox("Chọn sản phẩm", df["Tên sản phẩm"])
    pid = df[df["Tên sản phẩm"]==product]["ID"].values[0]
    type_tx = st.radio("Loại giao dịch", ["Nhập","Xuất"])
    qty = st.number_input("Số lượng", min_value=1, step=1)
    employees_list = st.multiselect("Nhân viên", [row[0] for row in cursor.execute("SELECT name FROM employees").fetchall()], default=["Hanh"])
    warehouses_list = st.multiselect("Kho", [row[0] for row in cursor.execute("SELECT name FROM warehouses").fetchall()], default=["Kho La Pagode"])
    if st.button("Xác nhận"):
        if update_quantity(pid, qty, type_tx, employees_list, warehouses_list):
            st.success(f"{type_tx} thành công {qty} sản phẩm {product} cho {len(employees_list)} nhân viên và {len(warehouses_list)} kho")

# ==== Báo cáo hàng sắp hết ====
elif menu=="Báo cáo hàng sắp hết":
    st.header("Hàng tồn sắp hết / tồn lâu")
    days_limit = st.number_input("Số ngày tồn tối đa", value=60)
    qty_limit = st.number_input("Số lượng tối thiểu", value=5)
    date_limit = (datetime.now()-timedelta(days=days_limit)).strftime("%Y-%m-%d")
    cursor.execute("SELECT * FROM products WHERE quantity<? OR created_at<?",(qty_limit,date_limit))
    rows = cursor.fetchall()
    df_low = pd.DataFrame(rows, columns=["ID","SKU","Tên sản phẩm","Số lượng","Ngày tạo"])
    st.dataframe(df_low.style.apply(highlight_low, axis=None))

# ==== Lịch sử giao dịch ====
elif menu=="Lịch sử giao dịch":
    st.header("Lịch sử nhập xuất")
    cursor.execute("SELECT * FROM history")
    rows = cursor.fetchall()
    df_hist = pd.DataFrame(rows, columns=["ID","ProductID","Loại","Số lượng","Ngày giờ","Nhân viên","Kho"])
    st.dataframe(df_hist)

# ==== Xuất Excel ====
elif menu=="Xuất Excel":
    st.header("Xuất Excel")
    df = refresh_products()
    file_name = f"inventory_pro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(file_name,index=False)
    st.success(f"Đã xuất Excel: {file_name}")
    st.download_button("Tải file Excel", data=open(file_name,"rb"), file_name=file_name)