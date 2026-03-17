import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

# ================= DATABASE =================
conn = sqlite3.connect("inventory.db", check_same_thread=False)
cursor = conn.cursor()

# ================= TABLES =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS products(
id INTEGER PRIMARY KEY AUTOINCREMENT,
sku TEXT UNIQUE,
name TEXT,
created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS warehouses(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS stock_by_warehouse(
id INTEGER PRIMARY KEY AUTOINCREMENT,
product_id INTEGER,
warehouse TEXT,
quantity INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS history(
id INTEGER PRIMARY KEY AUTOINCREMENT,
product_id INTEGER,
type TEXT,
quantity INTEGER,
date TEXT,
warehouse TEXT
)
""")

conn.commit()

# ================= DEFAULT WAREHOUSES =================
cursor.execute("SELECT COUNT(*) FROM warehouses")
if cursor.fetchone()[0] == 0:

    wh = [
        ("Kho La Pagode",),
        ("Kho Muse",),
        ("Kho Metz Ville",),
        ("Kho Nancy",)
    ]

    cursor.executemany("INSERT INTO warehouses(name) VALUES (?)", wh)
    conn.commit()

# ================= FUNCTIONS =================

def refresh_products():

    cursor.execute("SELECT * FROM products")

    rows = cursor.fetchall()

    return pd.DataFrame(
        rows,
        columns=["ID","SKU","Tên sản phẩm","Ngày tạo"]
    )


def refresh_stock():

    cursor.execute("""
    SELECT
    p.id,
    p.sku,
    p.name,
    w.name,
    IFNULL(s.quantity,0)
    FROM products p
    CROSS JOIN warehouses w
    LEFT JOIN stock_by_warehouse s
    ON p.id=s.product_id AND s.warehouse=w.name
    """)

    rows = cursor.fetchall()

    return pd.DataFrame(
        rows,
        columns=["ID","SKU","Tên sản phẩm","Kho","Số lượng"]
    )


# ================= SIDEBAR =================

st.sidebar.title("📦 QUẢN LÝ KHO")

menu = st.sidebar.radio(
    "Menu",
    [
        "Kho hàng",
        "Thêm sản phẩm",
        "Cập nhật/Xóa",
        "Nhập/Xuất",
        "Báo cáo hàng sắp hết",
        "Lịch sử giao dịch",
        "Xuất Excel"
    ]
)

# ================= VIEW STOCK =================

if menu == "Kho hàng":

    st.header("📦 Tồn kho")

    df = refresh_stock()

    search = st.text_input(
        "🔎 Tìm sản phẩm (SKU hoặc tên)"
    )

    if search != "":

        df = df[
            df["SKU"].str.contains(search,case=False) |
            df["Tên sản phẩm"].str.contains(search,case=False)
        ]

    st.dataframe(
        df.style.applymap(
            lambda x:'background-color:#ffcccc'
            if isinstance(x,int) and x<5 else '',
            subset=["Số lượng"]
        ),
        use_container_width=True
    )

# ================= ADD PRODUCT =================

elif menu == "Thêm sản phẩm":

    st.header("➕ Thêm sản phẩm")

    sku = st.text_input("SKU")
    name = st.text_input("Tên sản phẩm")

    cursor.execute("SELECT name FROM warehouses")
    warehouses = [x[0] for x in cursor.fetchall()]

    qty = {}

    for w in warehouses:

        qty[w] = st.number_input(
            f"Số lượng {w}",
            min_value=0,
            step=1
        )

    if st.button("Thêm sản phẩm"):

        try:

            cursor.execute(
                "INSERT INTO products(sku,name,created_at) VALUES (?,?,?)",
                (sku,name,datetime.now().strftime("%Y-%m-%d"))
            )

            pid = cursor.lastrowid

            for w,q in qty.items():

                if q>0:

                    cursor.execute(
                        "INSERT INTO stock_by_warehouse(product_id,warehouse,quantity) VALUES (?,?,?)",
                        (pid,w,q)
                    )

            conn.commit()

            st.success("Đã thêm sản phẩm")

            st.rerun()

        except:

            st.error("SKU đã tồn tại")

# ================= UPDATE / DELETE =================

elif menu == "Cập nhật/Xóa":

    st.header("✏️ Cập nhật sản phẩm")

    df = refresh_products()

    if df.empty:

        st.warning("Chưa có sản phẩm")

    else:

        product = st.selectbox(
            "Chọn sản phẩm",
            df["Tên sản phẩm"]
        )

        pid = df[df["Tên sản phẩm"]==product]["ID"].values[0]

        new_name = st.text_input("Tên mới",product)

        new_sku = st.text_input(
            "SKU mới",
            df[df["Tên sản phẩm"]==product]["SKU"].values[0]
        )

        cursor.execute("SELECT name FROM warehouses")

        warehouses = [x[0] for x in cursor.fetchall()]

        qty = {}

        for w in warehouses:

            cursor.execute(
                "SELECT IFNULL(quantity,0) FROM stock_by_warehouse WHERE product_id=? AND warehouse=?",
                (pid,w)
            )

            q = cursor.fetchone()

            qty[w] = st.number_input(
                f"{w}",
                value=q[0] if q else 0,
                min_value=0
            )

        col1,col2 = st.columns(2)

        with col1:

            if st.button("Cập nhật"):

                cursor.execute(
                    "UPDATE products SET name=?,sku=? WHERE id=?",
                    (new_name,new_sku,pid)
                )

                for w,q in qty.items():

                    cursor.execute(
                        "SELECT id FROM stock_by_warehouse WHERE product_id=? AND warehouse=?",
                        (pid,w)
                    )

                    res = cursor.fetchone()

                    if res:

                        cursor.execute(
                            "UPDATE stock_by_warehouse SET quantity=? WHERE product_id=? AND warehouse=?",
                            (q,pid,w)
                        )

                    else:

                        cursor.execute(
                            "INSERT INTO stock_by_warehouse(product_id,warehouse,quantity) VALUES (?,?,?)",
                            (pid,w,q)
                        )

                conn.commit()

                st.success("Cập nhật thành công")

                st.rerun()

        with col2:

            if st.button("Xóa sản phẩm"):

                cursor.execute(
                    "DELETE FROM stock_by_warehouse WHERE product_id=?",
                    (pid,)
                )

                cursor.execute(
                    "DELETE FROM products WHERE id=?",
                    (pid,)
                )

                conn.commit()

                st.success("Đã xóa")

                st.rerun()

# ================= IMPORT EXPORT =================

elif menu == "Nhập/Xuất":

    st.header("📥📤 Nhập / Xuất kho")

    df = refresh_products()

    product = st.selectbox(
        "Sản phẩm",
        df["Tên sản phẩm"]
    )

    pid = df[df["Tên sản phẩm"]==product]["ID"].values[0]

    cursor.execute("SELECT name FROM warehouses")

    warehouses = [x[0] for x in cursor.fetchall()]

    qty = {}

    for w in warehouses:

        qty[w] = st.number_input(
            f"{w}",
            min_value=0,
            step=1
        )

    type_tx = st.radio(
        "Loại giao dịch",
        ["Nhập","Xuất"]
    )

    if st.button("Xác nhận"):

        for w,q in qty.items():

            cursor.execute(
                "SELECT IFNULL(quantity,0) FROM stock_by_warehouse WHERE product_id=? AND warehouse=?",
                (pid,w)
            )

            res = cursor.fetchone()

            current = res[0] if res else 0

            if type_tx == "Nhập":

                new = current + q

            else:

                if q > current:

                    st.error(f"{w} không đủ hàng")

                    st.stop()

                new = current - q

            cursor.execute(
                "UPDATE stock_by_warehouse SET quantity=? WHERE product_id=? AND warehouse=?",
                (new,pid,w)
            )

            cursor.execute(
                "INSERT INTO history(product_id,type,quantity,date,warehouse) VALUES (?,?,?,?,?)",
                (pid,type_tx,q,datetime.now(),w)
            )

        conn.commit()

        st.success("Giao dịch thành công")

        st.rerun()

# ================= LOW STOCK REPORT =================

elif menu == "Báo cáo hàng sắp hết":

    st.header("⚠️ Hàng sắp hết")

    qty_limit = st.number_input("Ngưỡng tồn",value=5)

    days_limit = st.number_input("Số ngày tồn",value=180)

    date_limit = (
        datetime.now()-timedelta(days=days_limit)
    ).strftime("%Y-%m-%d")

    cursor.execute("""
    SELECT
    p.id,
    p.sku,
    p.name,
    IFNULL(SUM(s.quantity),0),
    p.created_at
    FROM products p
    LEFT JOIN stock_by_warehouse s
    ON p.id=s.product_id
    GROUP BY p.id
    HAVING SUM(s.quantity) < ? OR p.created_at < ?
    """,(qty_limit,date_limit))

    rows = cursor.fetchall()

    df = pd.DataFrame(
        rows,
        columns=["ID","SKU","Tên sản phẩm","Tồn kho","Ngày tạo"]
    )

    st.dataframe(df)

# ================= HISTORY =================

elif menu == "Lịch sử giao dịch":

    st.header("📜 Lịch sử giao dịch")

    cursor.execute("""
    SELECT
    h.id,
    p.name,
    h.type,
    h.quantity,
    h.date,
    h.warehouse
    FROM history h
    LEFT JOIN products p
    ON p.id=h.product_id
    ORDER BY h.date DESC
    """)

    rows = cursor.fetchall()

    df = pd.DataFrame(
        rows,
        columns=[
            "ID",
            "Sản phẩm",
            "Loại",
            "Số lượng",
            "Ngày",
            "Kho"
        ]
    )

    st.dataframe(df)

# ================= EXPORT =================

elif menu == "Xuất Excel":

    st.header("📄 Xuất Excel")

    df = refresh_stock()

    file = "inventory_export.xlsx"

    df.to_excel(file,index=False)

    st.download_button(
        "Tải file Excel",
        data=open(file,"rb"),
        file_name=file
    )
