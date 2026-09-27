# """
# Inventory Dashboard
# ====================
# A desktop dashboard (Tkinter) to manage inventory items with:
#   - Add / Update / Delete items
#   - Search & filter
#   - Charts: Stock levels, Customer ratings distribution, Trending items
#   - SQLite persistence (inventory.db is created next to this script)

# Run:
#     pip install matplotlib
#     python inventory_dashboard.py
# """

# import sqlite3
# import tkinter as tk
# from tkinter import ttk, messagebox
# import os

# from matplotlib.figure import Figure
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.db")


# # ----------------------------------------------------------------------------
# # Database layer
# # ----------------------------------------------------------------------------
# class Database:
#     def __init__(self, path=DB_PATH):
#         self.conn = sqlite3.connect(path)
#         self.conn.execute("PRAGMA foreign_keys = ON")
#         self._create_tables()
#         self._seed_if_empty()

#     def _create_tables(self):
#         self.conn.execute("""
#             CREATE TABLE IF NOT EXISTS items (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 name TEXT NOT NULL,
#                 category TEXT,
#                 price REAL NOT NULL DEFAULT 0,
#                 quantity INTEGER NOT NULL DEFAULT 0,
#                 rating REAL NOT NULL DEFAULT 0,       -- avg customer rating 0-5
#                 reviews_count INTEGER NOT NULL DEFAULT 0,
#                 units_sold INTEGER NOT NULL DEFAULT 0, -- used to compute trending
#                 trending INTEGER NOT NULL DEFAULT 0    -- manual trending flag (0/1)
#             )
#         """)
#         self.conn.commit()

#     def _seed_if_empty(self):
#         cur = self.conn.execute("SELECT COUNT(*) FROM items")
#         if cur.fetchone()[0] == 0:
#             sample = [
#                 ("Wireless Mouse", "Electronics", 19.99, 120, 4.3, 58, 340, 1),
#                 ("Mechanical Keyboard", "Electronics", 59.99, 45, 4.6, 92, 210, 1),
#                 ("Yoga Mat", "Fitness", 24.50, 80, 4.1, 34, 95, 0),
#                 ("Water Bottle", "Fitness", 12.00, 200, 4.7, 150, 480, 1),
#                 ("Desk Lamp", "Home", 22.75, 60, 3.9, 21, 60, 0),
#                 ("Notebook Set", "Stationery", 8.99, 300, 4.2, 40, 140, 0),
#                 ("Bluetooth Speaker", "Electronics", 45.00, 30, 4.0, 66, 175, 1),
#                 ("Office Chair", "Home", 129.99, 15, 4.4, 28, 50, 0),
#             ]
#             self.conn.executemany(
#                 """INSERT INTO items
#                    (name, category, price, quantity, rating, reviews_count, units_sold, trending)
#                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
#                 sample,
#             )
#             self.conn.commit()

#     def add_item(self, name, category, price, quantity, rating, reviews_count, units_sold, trending):
#         cur = self.conn.execute(
#             """INSERT INTO items
#                (name, category, price, quantity, rating, reviews_count, units_sold, trending)
#                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
#             (name, category, price, quantity, rating, reviews_count, units_sold, trending),
#         )
#         self.conn.commit()
#         return cur.lastrowid

#     def update_item(self, item_id, name, category, price, quantity, rating, reviews_count, units_sold, trending):
#         self.conn.execute(
#             """UPDATE items SET name=?, category=?, price=?, quantity=?, rating=?,
#                reviews_count=?, units_sold=?, trending=? WHERE id=?""",
#             (name, category, price, quantity, rating, reviews_count, units_sold, trending, item_id),
#         )
#         self.conn.commit()

#     def delete_item(self, item_id):
#         self.conn.execute("DELETE FROM items WHERE id=?", (item_id,))
#         self.conn.commit()

#     def get_all(self, search_term=""):
#         if search_term:
#             like = f"%{search_term}%"
#             cur = self.conn.execute(
#                 "SELECT * FROM items WHERE name LIKE ? OR category LIKE ? ORDER BY id",
#                 (like, like),
#             )
#         else:
#             cur = self.conn.execute("SELECT * FROM items ORDER BY id")
#         return cur.fetchall()

#     def get(self, item_id):
#         cur = self.conn.execute("SELECT * FROM items WHERE id=?", (item_id,))
#         return cur.fetchone()


# # ----------------------------------------------------------------------------
# # Main Application
# # ----------------------------------------------------------------------------
# COLUMNS = (
#     "id", "name", "category", "price", "quantity",
#     "rating", "reviews_count", "units_sold", "trending",
# )
# HEADINGS = (
#     "ID", "Name", "Category", "Price", "Qty",
#     "Rating", "Reviews", "Units Sold", "Trending",
# )


# class InventoryDashboard(tk.Tk):
#     def __init__(self):
#         super().__init__()
#         self.title("Inventory Dashboard")
#         self.geometry("1150x680")
#         self.minsize(950, 600)

#         self.db = Database()
#         self.selected_id = None

#         self._build_style()
#         self._build_layout()
#         self.refresh_table()
#         self.refresh_charts()

#     # ---------- styling ----------
#     def _build_style(self):
#         style = ttk.Style(self)
#         try:
#             style.theme_use("clam")
#         except tk.TclError:
#             pass
#         style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
#         style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
#         style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(14, 8))

#     # ---------- layout ----------
#     def _build_layout(self):
#         notebook = ttk.Notebook(self)
#         notebook.pack(fill="both", expand=True, padx=8, pady=8)

#         self.items_tab = ttk.Frame(notebook)
#         self.charts_tab = ttk.Frame(notebook)
#         notebook.add(self.items_tab, text="Items")
#         notebook.add(self.charts_tab, text="Dashboard / Charts")

#         self._build_items_tab(self.items_tab)
#         self._build_charts_tab(self.charts_tab)

#     # ------------------------------------------------------------------
#     # ITEMS TAB
#     # ------------------------------------------------------------------
#     def _build_items_tab(self, parent):
#         parent.columnconfigure(0, weight=1)
#         parent.rowconfigure(1, weight=1)

#         # --- top bar: search ---
#         top = ttk.Frame(parent)
#         top.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
#         ttk.Label(top, text="Search:").pack(side="left")
#         self.search_var = tk.StringVar()
#         search_entry = ttk.Entry(top, textvariable=self.search_var, width=30)
#         search_entry.pack(side="left", padx=6)
#         search_entry.bind("<KeyRelease>", lambda e: self.refresh_table())
#         ttk.Button(top, text="Clear", command=self._clear_search).pack(side="left")
#         ttk.Button(top, text="Refresh Charts", command=self.refresh_charts).pack(side="right")

#         # --- table ---
#         table_frame = ttk.Frame(parent)
#         table_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
#         table_frame.columnconfigure(0, weight=1)
#         table_frame.rowconfigure(0, weight=1)

#         self.tree = ttk.Treeview(table_frame, columns=COLUMNS, show="headings", selectmode="browse")
#         for col, head in zip(COLUMNS, HEADINGS):
#             self.tree.heading(col, text=head)
#             width = 70 if col in ("id", "qty", "trending") else 110
#             self.tree.column(col, width=width, anchor="center")
#         self.tree.column("name", width=160, anchor="w")
#         self.tree.column("category", width=110, anchor="w")

#         vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
#         self.tree.configure(yscrollcommand=vsb.set)
#         self.tree.grid(row=0, column=0, sticky="nsew")
#         vsb.grid(row=0, column=1, sticky="ns")
#         self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

#         # --- form ---
#         form = ttk.LabelFrame(parent, text="Item Details")
#         form.grid(row=2, column=0, sticky="ew", padx=6, pady=(0, 6))
#         for i in range(8):
#             form.columnconfigure(i, weight=1)

#         self.fields = {}
#         field_defs = [
#             ("name", "Name"), ("category", "Category"), ("price", "Price"),
#             ("quantity", "Quantity"), ("rating", "Rating (0-5)"),
#             ("reviews_count", "Reviews Count"), ("units_sold", "Units Sold"),
#         ]
#         for idx, (key, label) in enumerate(field_defs):
#             r, c = divmod(idx, 4)
#             ttk.Label(form, text=label + ":").grid(row=r * 2, column=c, sticky="w", padx=6, pady=(6, 0))
#             var = tk.StringVar()
#             ttk.Entry(form, textvariable=var).grid(row=r * 2 + 1, column=c, sticky="ew", padx=6, pady=(0, 6))
#             self.fields[key] = var

#         self.trending_var = tk.BooleanVar()
#         ttk.Checkbutton(form, text="Trending", variable=self.trending_var).grid(
#             row=2, column=3, sticky="w", padx=6, pady=6
#         )

#         # --- buttons ---
#         btns = ttk.Frame(parent)
#         btns.grid(row=3, column=0, sticky="ew", padx=6, pady=(0, 8))
#         ttk.Button(btns, text="Add Item", command=self.add_item).pack(side="left", padx=4)
#         ttk.Button(btns, text="Update Selected", command=self.update_item).pack(side="left", padx=4)
#         ttk.Button(btns, text="Delete Selected", command=self.delete_item).pack(side="left", padx=4)
#         ttk.Button(btns, text="Clear Form", command=self.clear_form).pack(side="left", padx=4)

#     def _clear_search(self):
#         self.search_var.set("")
#         self.refresh_table()

#     def refresh_table(self):
#         for row in self.tree.get_children():
#             self.tree.delete(row)
#         rows = self.db.get_all(self.search_var.get().strip())
#         for row in rows:
#             item_id, name, category, price, qty, rating, reviews, sold, trending = row
#             self.tree.insert(
#                 "", "end", iid=str(item_id),
#                 values=(item_id, name, category, f"{price:.2f}", qty,
#                         f"{rating:.1f}", reviews, sold, "Yes" if trending else "No"),
#             )

#     def _on_row_select(self, event=None):
#         sel = self.tree.selection()
#         if not sel:
#             return
#         item_id = int(sel[0])
#         row = self.db.get(item_id)
#         if not row:
#             return
#         self.selected_id = item_id
#         (_, name, category, price, qty, rating, reviews, sold, trending) = row
#         self.fields["name"].set(name)
#         self.fields["category"].set(category or "")
#         self.fields["price"].set(price)
#         self.fields["quantity"].set(qty)
#         self.fields["rating"].set(rating)
#         self.fields["reviews_count"].set(reviews)
#         self.fields["units_sold"].set(sold)
#         self.trending_var.set(bool(trending))

#     def clear_form(self):
#         self.selected_id = None
#         for var in self.fields.values():
#             var.set("")
#         self.trending_var.set(False)
#         self.tree.selection_remove(self.tree.selection())

#     def _read_form(self):
#         name = self.fields["name"].get().strip()
#         category = self.fields["category"].get().strip()
#         if not name:
#             raise ValueError("Name is required.")
#         try:
#             price = float(self.fields["price"].get() or 0)
#             quantity = int(float(self.fields["quantity"].get() or 0))
#             rating = float(self.fields["rating"].get() or 0)
#             reviews_count = int(float(self.fields["reviews_count"].get() or 0))
#             units_sold = int(float(self.fields["units_sold"].get() or 0))
#         except ValueError:
#             raise ValueError("Price/Quantity/Rating/Reviews/Units Sold must be numeric.")
#         if not (0 <= rating <= 5):
#             raise ValueError("Rating must be between 0 and 5.")
#         trending = 1 if self.trending_var.get() else 0
#         return name, category, price, quantity, rating, reviews_count, units_sold, trending

#     def add_item(self):
#         try:
#             data = self._read_form()
#         except ValueError as e:
#             messagebox.showerror("Invalid input", str(e))
#             return
#         self.db.add_item(*data)
#         self.clear_form()
#         self.refresh_table()
#         self.refresh_charts()

#     def update_item(self):
#         if self.selected_id is None:
#             messagebox.showwarning("No selection", "Select an item in the table first.")
#             return
#         try:
#             data = self._read_form()
#         except ValueError as e:
#             messagebox.showerror("Invalid input", str(e))
#             return
#         self.db.update_item(self.selected_id, *data)
#         self.clear_form()
#         self.refresh_table()
#         self.refresh_charts()

#     def delete_item(self):
#         if self.selected_id is None:
#             messagebox.showwarning("No selection", "Select an item in the table first.")
#             return
#         if messagebox.askyesno("Confirm delete", "Delete the selected item?"):
#             self.db.delete_item(self.selected_id)
#             self.clear_form()
#             self.refresh_table()
#             self.refresh_charts()

#     # ------------------------------------------------------------------
#     # CHARTS TAB
#     # ------------------------------------------------------------------
#     def _build_charts_tab(self, parent):
#         parent.columnconfigure(0, weight=1)
#         parent.columnconfigure(1, weight=1)
#         parent.rowconfigure(0, weight=1)
#         parent.rowconfigure(1, weight=1)

#         self.fig_stock = Figure(figsize=(5, 3.6), dpi=100)
#         self.ax_stock = self.fig_stock.add_subplot(111)
#         self.canvas_stock = FigureCanvasTkAgg(self.fig_stock, master=parent)
#         self.canvas_stock.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

#         self.fig_reviews = Figure(figsize=(5, 3.6), dpi=100)
#         self.ax_reviews = self.fig_reviews.add_subplot(111)
#         self.canvas_reviews = FigureCanvasTkAgg(self.fig_reviews, master=parent)
#         self.canvas_reviews.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

#         self.fig_trend = Figure(figsize=(10, 3.6), dpi=100)
#         self.ax_trend = self.fig_trend.add_subplot(111)
#         self.canvas_trend = FigureCanvasTkAgg(self.fig_trend, master=parent)
#         self.canvas_trend.get_tk_widget().grid(row=1, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)

#     def refresh_charts(self):
#         rows = self.db.get_all()

#         # --- Chart 1: Stock levels by item ---
#         self.ax_stock.clear()
#         if rows:
#             names = [r[1] for r in rows]
#             qtys = [r[4] for r in rows]
#             bars = self.ax_stock.bar(names, qtys, color="#4C72B0")
#             self.ax_stock.set_title("Stock Levels by Item")
#             self.ax_stock.set_ylabel("Quantity in stock")
#             self.ax_stock.tick_params(axis="x", rotation=45, labelsize=7)
#             for b in bars:
#                 h = b.get_height()
#                 self.ax_stock.annotate(str(int(h)), (b.get_x() + b.get_width() / 2, h),
#                                         ha="center", va="bottom", fontsize=7)
#         else:
#             self.ax_stock.set_title("Stock Levels by Item (no data)")
#         self.fig_stock.tight_layout()
#         self.canvas_stock.draw()

#         # --- Chart 2: Customer reviews / rating distribution ---
#         self.ax_reviews.clear()
#         if rows:
#             buckets = {"0-1": 0, "1-2": 0, "2-3": 0, "3-4": 0, "4-5": 0}
#             for r in rows:
#                 rating = r[5]
#                 reviews = r[6]
#                 if rating < 1:
#                     buckets["0-1"] += reviews
#                 elif rating < 2:
#                     buckets["1-2"] += reviews
#                 elif rating < 3:
#                     buckets["2-3"] += reviews
#                 elif rating < 4:
#                     buckets["3-4"] += reviews
#                 else:
#                     buckets["4-5"] += reviews
#             labels = list(buckets.keys())
#             values = list(buckets.values())
#             colors = ["#C44E52", "#DD8452", "#CCB974", "#55A868", "#4C72B0"]
#             if sum(values) > 0:
#                 self.ax_reviews.pie(
#                     values, labels=labels, autopct=lambda p: f"{p:.0f}%" if p > 0 else "",
#                     colors=colors, startangle=90,
#                 )
#             self.ax_reviews.set_title("Customer Reviews by Rating Band")
#         else:
#             self.ax_reviews.set_title("Customer Reviews (no data)")
#         self.fig_reviews.tight_layout()
#         self.canvas_reviews.draw()

#         # --- Chart 3: Trending items (by units sold, flagged trending highlighted) ---
#         self.ax_trend.clear()
#         if rows:
#             sorted_rows = sorted(rows, key=lambda r: r[7], reverse=True)[:8]  # top 8 by units_sold
#             names = [r[1] for r in sorted_rows]
#             sold = [r[7] for r in sorted_rows]
#             trending_flags = [r[8] for r in sorted_rows]
#             colors = ["#DD4C4C" if t else "#8C8C8C" for t in trending_flags]
#             bars = self.ax_trend.bar(names, sold, color=colors)
#             self.ax_trend.set_title("Trending Items (red = flagged trending) — by Units Sold")
#             self.ax_trend.set_ylabel("Units sold")
#             self.ax_trend.tick_params(axis="x", rotation=20, labelsize=8)
#             for b in bars:
#                 h = b.get_height()
#                 self.ax_trend.annotate(str(int(h)), (b.get_x() + b.get_width() / 2, h),
#                                         ha="center", va="bottom", fontsize=7)
#         else:
#             self.ax_trend.set_title("Trending Items (no data)")
#         self.fig_trend.tight_layout()
#         self.canvas_trend.draw()


# if __name__ == "__main__":
#     app = InventoryDashboard()
#     app.mainloop()



"""
================================================================================
 ADVANCED INVENTORY & SALES MANAGEMENT DASHBOARD
================================================================================
A real-world-style desktop application built with Tkinter + SQLite + Matplotlib.

Features
--------
- Login system with roles (admin / staff) and hashed passwords
- Full CRUD for Items, Categories, Suppliers, Customers
- Order / Sales processing that automatically updates stock and revenue
- Customer reviews system that recomputes each item's live rating
- Analytics dashboard: KPI cards + 5 live charts (stock, ratings, trending,
  sales-over-time, revenue-by-category)
- Low-stock alerts & highlighting
- CSV export/import for items, orders and reviews
- Database backup / restore
- Activity log (audit trail) of who did what and when
- Light / Dark theme toggle
- Configurable settings (currency symbol, low-stock threshold) persisted in DB

Run:
    pip install matplotlib
    python advanced_dashboard.py

Default login:
    username: admin
    password: admin123
================================================================================
"""

import os
import csv
import shutil
import sqlite3
import hashlib
import datetime as dt
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ==============================================================================
# CONSTANTS
# ==============================================================================
APP_TITLE = "Advanced Inventory & Sales Dashboard"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "advanced_inventory.db")
BACKUP_DIR = os.path.join(APP_DIR, "backups")

DATE_FMT = "%Y-%m-%d"
DATETIME_FMT = "%Y-%m-%d %H:%M:%S"

LIGHT_THEME = {
    "bg": "#F4F6F8",
    "fg": "#1B1F23",
    "panel": "#FFFFFF",
    "accent": "#2F6FED",
    "danger": "#D64545",
    "success": "#3AA655",
    "warning": "#E0952F",
    "muted": "#6B7280",
    "tree_bg": "#FFFFFF",
    "tree_alt": "#F0F3F7",
}

DARK_THEME = {
    "bg": "#1E2126",
    "fg": "#E8EAED",
    "panel": "#262A31",
    "accent": "#5B8DEF",
    "danger": "#E5716B",
    "success": "#5FC77E",
    "warning": "#F0B152",
    "muted": "#9CA3AF",
    "tree_bg": "#262A31",
    "tree_alt": "#2C313A",
}

CHART_PALETTE = ["#4C72B0", "#DD8452", "#55A868", "#C44E52",
                 "#8172B2", "#937860", "#DA8BC3", "#8C8C8C"]


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================
def hash_password(password, salt="dashboard_salt_v1"):
    """One-way hash for storing passwords (not reversible)."""
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def now_str():
    return dt.datetime.now().strftime(DATETIME_FMT)


def today_str():
    return dt.date.today().strftime(DATE_FMT)


def days_ago_str(days):
    return (dt.date.today() - dt.timedelta(days=days)).strftime(DATE_FMT)


def format_currency(value, symbol="$"):
    try:
        return f"{symbol}{float(value):,.2f}"
    except (TypeError, ValueError):
        return f"{symbol}0.00"


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def export_rows_to_csv(path, headers, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)


def import_rows_from_csv(path):
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return [], []
    return rows[0], rows[1:]


# ==============================================================================
# DATABASE LAYER
# ==============================================================================
class Database:
    """All persistence logic lives here. Tabs never touch SQL directly."""

    def __init__(self, path=DB_PATH):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._seed_if_empty()

    # ---------------------------------------------------------------- schema
    def _create_tables(self):
        c = self.conn
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'staff',
                created_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_person TEXT,
                email TEXT,
                phone TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                joined_date TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category_id INTEGER,
                supplier_id INTEGER,
                price REAL NOT NULL DEFAULT 0,
                quantity INTEGER NOT NULL DEFAULT 0,
                units_sold INTEGER NOT NULL DEFAULT 0,
                rating REAL NOT NULL DEFAULT 0,
                reviews_count INTEGER NOT NULL DEFAULT 0,
                trending INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total REAL NOT NULL,
                order_date TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                customer_id INTEGER,
                rating REAL NOT NULL,
                comment TEXT,
                review_date TEXT,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                action TEXT,
                timestamp TEXT
            )
        """)
        c.commit()

    def _seed_if_empty(self):
        c = self.conn
        if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            c.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                ("admin", hash_password("admin123"), "admin", now_str()),
            )
            c.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                ("staff", hash_password("staff123"), "staff", now_str()),
            )

        if c.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
            for name in ("Electronics", "Fitness", "Home", "Stationery"):
                c.execute("INSERT INTO categories (name) VALUES (?)", (name,))

        if c.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0] == 0:
            suppliers = [
                ("TechSource Ltd", "Rahul Mehta", "rahul@techsource.com", "9876543210"),
                ("HomeGoods Inc", "Priya Nair", "priya@homegoods.com", "9123456780"),
                ("FitLife Supplies", "Aman Gupta", "aman@fitlife.com", "9988776655"),
            ]
            c.executemany(
                "INSERT INTO suppliers (name, contact_person, email, phone) VALUES (?, ?, ?, ?)",
                suppliers,
            )

        if c.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:
            customers = [
                ("Ananya Sharma", "ananya@example.com", "9000011111", today_str()),
                ("Rohan Verma", "rohan@example.com", "9000022222", today_str()),
                ("Ishita Roy", "ishita@example.com", "9000033333", today_str()),
            ]
            c.executemany(
                "INSERT INTO customers (name, email, phone, joined_date) VALUES (?, ?, ?, ?)",
                customers,
            )

        if c.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 0:
            cats = {r["name"]: r["id"] for r in c.execute("SELECT id, name FROM categories")}
            sups = list(c.execute("SELECT id FROM suppliers"))
            sup_ids = [r["id"] for r in sups]
            items = [
                ("Wireless Mouse", cats["Electronics"], sup_ids[0], 19.99, 120, 340, 0),
                ("Mechanical Keyboard", cats["Electronics"], sup_ids[0], 59.99, 45, 210, 1),
                ("Bluetooth Speaker", cats["Electronics"], sup_ids[0], 45.00, 30, 175, 0),
                ("Yoga Mat", cats["Fitness"], sup_ids[2], 24.50, 80, 95, 0),
                ("Water Bottle", cats["Fitness"], sup_ids[2], 12.00, 200, 480, 1),
                ("Desk Lamp", cats["Home"], sup_ids[1], 22.75, 60, 60, 0),
                ("Office Chair", cats["Home"], sup_ids[1], 129.99, 15, 50, 0),
                ("Notebook Set", cats["Stationery"], sup_ids[1], 8.99, 300, 140, 1),
            ]
            for name, cat_id, sup_id, price, qty, sold, trend in items:
                c.execute(
                    """INSERT INTO items
                       (name, category_id, supplier_id, price, quantity, units_sold, trending)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (name, cat_id, sup_id, price, qty, sold, trend),
                )

        if c.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 0:
            item_ids = [r["id"] for r in c.execute("SELECT id FROM items")]
            cust_ids = [r["id"] for r in c.execute("SELECT id FROM customers")]
            sample_reviews = [
                (item_ids[0], cust_ids[0], 4.5, "Very smooth tracking, great value.", days_ago_str(5)),
                (item_ids[0], cust_ids[1], 4.0, "Good but a bit small for large hands.", days_ago_str(20)),
                (item_ids[1], cust_ids[2], 5.0, "Best keyboard I've used, love the clicky feel.", days_ago_str(2)),
                (item_ids[1], cust_ids[0], 4.5, "Sturdy build quality.", days_ago_str(15)),
                (item_ids[3], cust_ids[1], 3.5, "Decent grip, a little thin.", days_ago_str(9)),
                (item_ids[4], cust_ids[2], 5.0, "Keeps water cold all day!", days_ago_str(1)),
                (item_ids[4], cust_ids[0], 4.5, "Love the design.", days_ago_str(30)),
                (item_ids[7], cust_ids[1], 4.0, "Good paper quality.", days_ago_str(12)),
            ]
            for item_id, cust_id, rating, comment, rdate in sample_reviews:
                c.execute(
                    """INSERT INTO reviews (item_id, customer_id, rating, comment, review_date)
                       VALUES (?, ?, ?, ?, ?)""",
                    (item_id, cust_id, rating, comment, rdate),
                )
            for item_id in item_ids:
                self._recompute_item_rating(item_id, commit=False)

        if c.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
            item_rows = list(c.execute("SELECT id, price FROM items"))
            cust_ids = [r["id"] for r in c.execute("SELECT id FROM customers")]
            import random
            random.seed(42)
            for day_offset in range(30, -1, -1):
                if random.random() < 0.6:
                    for _ in range(random.randint(1, 3)):
                        item = random.choice(item_rows)
                        qty = random.randint(1, 5)
                        cust = random.choice(cust_ids)
                        odate = days_ago_str(day_offset)
                        total = round(qty * item["price"], 2)
                        c.execute(
                            """INSERT INTO orders
                               (customer_id, item_id, quantity, unit_price, total, order_date)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (cust, item["id"], qty, item["price"], total, odate),
                        )

        if c.execute("SELECT COUNT(*) FROM settings").fetchone()[0] == 0:
            c.execute("INSERT INTO settings (key, value) VALUES ('currency_symbol', '$')")
            c.execute("INSERT INTO settings (key, value) VALUES ('low_stock_threshold', '20')")
            c.execute("INSERT INTO settings (key, value) VALUES ('theme', 'light')")
        c.commit()

    # ---------------------------------------------------------------- users
    def verify_user(self, username, password):
        row = self.conn.execute(
            "SELECT * FROM users WHERE username=?", (username,)
        ).fetchone()
        if row is None:
            return None
        if row["password_hash"] == hash_password(password):
            return dict(row)
        return None

    def get_users(self):
        return [dict(r) for r in self.conn.execute("SELECT id, username, role, created_at FROM users ORDER BY id")]

    def add_user(self, username, password, role="staff"):
        self.conn.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), role, now_str()),
        )
        self.conn.commit()

    def change_password(self, username, new_password):
        self.conn.execute(
            "UPDATE users SET password_hash=? WHERE username=?",
            (hash_password(new_password), username),
        )
        self.conn.commit()

    # ---------------------------------------------------------------- categories
    def get_categories(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM categories ORDER BY name")]

    def add_category(self, name):
        try:
            self.conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_category(self, category_id):
        self.conn.execute("DELETE FROM categories WHERE id=?", (category_id,))
        self.conn.commit()

    # ---------------------------------------------------------------- suppliers
    def get_suppliers(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM suppliers ORDER BY name")]

    def add_supplier(self, name, contact_person, email, phone):
        self.conn.execute(
            "INSERT INTO suppliers (name, contact_person, email, phone) VALUES (?, ?, ?, ?)",
            (name, contact_person, email, phone),
        )
        self.conn.commit()

    def update_supplier(self, supplier_id, name, contact_person, email, phone):
        self.conn.execute(
            "UPDATE suppliers SET name=?, contact_person=?, email=?, phone=? WHERE id=?",
            (name, contact_person, email, phone, supplier_id),
        )
        self.conn.commit()

    def delete_supplier(self, supplier_id):
        self.conn.execute("DELETE FROM suppliers WHERE id=?", (supplier_id,))
        self.conn.commit()

    # ---------------------------------------------------------------- customers
    def get_customers(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM customers ORDER BY name")]

    def add_customer(self, name, email, phone):
        self.conn.execute(
            "INSERT INTO customers (name, email, phone, joined_date) VALUES (?, ?, ?, ?)",
            (name, email, phone, today_str()),
        )
        self.conn.commit()

    def update_customer(self, customer_id, name, email, phone):
        self.conn.execute(
            "UPDATE customers SET name=?, email=?, phone=? WHERE id=?",
            (name, email, phone, customer_id),
        )
        self.conn.commit()

    def delete_customer(self, customer_id):
        self.conn.execute("DELETE FROM customers WHERE id=?", (customer_id,))
        self.conn.commit()

    # ---------------------------------------------------------------- items
    ITEM_SELECT = """
        SELECT items.*, categories.name AS category_name, suppliers.name AS supplier_name
        FROM items
        LEFT JOIN categories ON items.category_id = categories.id
        LEFT JOIN suppliers ON items.supplier_id = suppliers.id
    """

    def get_items(self, search=""):
        query = self.ITEM_SELECT
        params = ()
        if search:
            query += " WHERE items.name LIKE ? OR categories.name LIKE ? OR suppliers.name LIKE ?"
            like = f"%{search}%"
            params = (like, like, like)
        query += " ORDER BY items.id"
        return [dict(r) for r in self.conn.execute(query, params)]

    def get_item(self, item_id):
        row = self.conn.execute(self.ITEM_SELECT + " WHERE items.id=?", (item_id,)).fetchone()
        return dict(row) if row else None

    def add_item(self, name, category_id, supplier_id, price, quantity, trending):
        cur = self.conn.execute(
            """INSERT INTO items (name, category_id, supplier_id, price, quantity, trending)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, category_id, supplier_id, price, quantity, trending),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_item(self, item_id, name, category_id, supplier_id, price, quantity, trending):
        self.conn.execute(
            """UPDATE items SET name=?, category_id=?, supplier_id=?, price=?, quantity=?, trending=?
               WHERE id=?""",
            (name, category_id, supplier_id, price, quantity, trending, item_id),
        )
        self.conn.commit()

    def delete_item(self, item_id):
        self.conn.execute("DELETE FROM items WHERE id=?", (item_id,))
        self.conn.commit()

    def adjust_stock(self, item_id, delta_quantity, delta_units_sold=0):
        self.conn.execute(
            "UPDATE items SET quantity = quantity + ?, units_sold = units_sold + ? WHERE id=?",
            (delta_quantity, delta_units_sold, item_id),
        )
        self.conn.commit()

    def low_stock_items(self, threshold):
        return [
            dict(r) for r in self.conn.execute(
                self.ITEM_SELECT + " WHERE items.quantity <= ? ORDER BY items.quantity", (threshold,)
            )
        ]

    def total_stock_value(self):
        row = self.conn.execute("SELECT SUM(price * quantity) AS total FROM items").fetchone()
        return row["total"] or 0.0

    def stock_value_by_category(self):
        rows = self.conn.execute("""
            SELECT COALESCE(categories.name, 'Uncategorized') AS category,
                   SUM(items.price * items.quantity) AS value
            FROM items
            LEFT JOIN categories ON items.category_id = categories.id
            GROUP BY category
            ORDER BY value DESC
        """).fetchall()
        return [(r["category"], r["value"] or 0.0) for r in rows]

    # ---------------------------------------------------------------- orders
    ORDER_SELECT = """
        SELECT orders.*, items.name AS item_name, customers.name AS customer_name
        FROM orders
        LEFT JOIN items ON orders.item_id = items.id
        LEFT JOIN customers ON orders.customer_id = customers.id
    """

    def create_order(self, customer_id, item_id, quantity, unit_price, order_date=None):
        order_date = order_date or today_str()
        total = round(quantity * unit_price, 2)
        cur = self.conn.execute(
            """INSERT INTO orders (customer_id, item_id, quantity, unit_price, total, order_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (customer_id, item_id, quantity, unit_price, total, order_date),
        )
        # selling reduces stock and increases the units_sold counter
        self.adjust_stock(item_id, delta_quantity=-quantity, delta_units_sold=quantity)
        self.conn.commit()
        return cur.lastrowid

    def delete_order(self, order_id):
        row = self.conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if row:
            # deleting an order restores the stock it had consumed
            self.adjust_stock(row["item_id"], delta_quantity=row["quantity"], delta_units_sold=-row["quantity"])
            self.conn.execute("DELETE FROM orders WHERE id=?", (order_id,))
            self.conn.commit()

    def get_orders(self, search=""):
        query = self.ORDER_SELECT
        params = ()
        if search:
            query += " WHERE items.name LIKE ? OR customers.name LIKE ?"
            like = f"%{search}%"
            params = (like, like)
        query += " ORDER BY orders.order_date DESC, orders.id DESC"
        return [dict(r) for r in self.conn.execute(query, params)]

    def sales_by_date(self, days=30):
        start = days_ago_str(days)
        rows = self.conn.execute(
            """SELECT order_date, SUM(total) AS revenue
               FROM orders WHERE order_date >= ?
               GROUP BY order_date ORDER BY order_date""",
            (start,),
        ).fetchall()
        return [(r["order_date"], r["revenue"] or 0.0) for r in rows]

    def total_revenue(self, days=None):
        if days is None:
            row = self.conn.execute("SELECT SUM(total) AS total FROM orders").fetchone()
        else:
            start = days_ago_str(days)
            row = self.conn.execute(
                "SELECT SUM(total) AS total FROM orders WHERE order_date >= ?", (start,)
            ).fetchone()
        return row["total"] or 0.0

    def top_selling_items(self, limit=8):
        rows = self.conn.execute("""
            SELECT items.id, items.name, items.units_sold, items.trending
            FROM items ORDER BY items.units_sold DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]

    def order_count(self):
        return self.conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]

    # ---------------------------------------------------------------- reviews
    REVIEW_SELECT = """
        SELECT reviews.*, items.name AS item_name, customers.name AS customer_name
        FROM reviews
        LEFT JOIN items ON reviews.item_id = items.id
        LEFT JOIN customers ON reviews.customer_id = customers.id
    """

    def add_review(self, item_id, customer_id, rating, comment, review_date=None):
        review_date = review_date or today_str()
        self.conn.execute(
            """INSERT INTO reviews (item_id, customer_id, rating, comment, review_date)
               VALUES (?, ?, ?, ?, ?)""",
            (item_id, customer_id, rating, comment, review_date),
        )
        self.conn.commit()
        self._recompute_item_rating(item_id)

    def delete_review(self, review_id):
        row = self.conn.execute("SELECT item_id FROM reviews WHERE id=?", (review_id,)).fetchone()
        self.conn.execute("DELETE FROM reviews WHERE id=?", (review_id,))
        self.conn.commit()
        if row:
            self._recompute_item_rating(row["item_id"])

    def get_reviews(self, item_id=None, search=""):
        query = self.REVIEW_SELECT
        clauses, params = [], []
        if item_id is not None:
            clauses.append("reviews.item_id = ?")
            params.append(item_id)
        if search:
            clauses.append("(items.name LIKE ? OR customers.name LIKE ? OR reviews.comment LIKE ?)")
            like = f"%{search}%"
            params.extend([like, like, like])
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY reviews.review_date DESC, reviews.id DESC"
        return [dict(r) for r in self.conn.execute(query, params)]

    def _recompute_item_rating(self, item_id, commit=True):
        row = self.conn.execute(
            "SELECT AVG(rating) AS avg_rating, COUNT(*) AS cnt FROM reviews WHERE item_id=?",
            (item_id,),
        ).fetchone()
        avg_rating = round(row["avg_rating"] or 0.0, 2)
        count = row["cnt"] or 0
        self.conn.execute(
            "UPDATE items SET rating=?, reviews_count=? WHERE id=?",
            (avg_rating, count, item_id),
        )
        if commit:
            self.conn.commit()

    def rating_distribution(self):
        buckets = {"0-1": 0, "1-2": 0, "2-3": 0, "3-4": 0, "4-5": 0}
        rows = self.conn.execute("SELECT rating FROM reviews").fetchall()
        for r in rows:
            rating = r["rating"]
            if rating < 1:
                buckets["0-1"] += 1
            elif rating < 2:
                buckets["1-2"] += 1
            elif rating < 3:
                buckets["2-3"] += 1
            elif rating < 4:
                buckets["3-4"] += 1
            else:
                buckets["4-5"] += 1
        return buckets

    def average_rating_overall(self):
        row = self.conn.execute("SELECT AVG(rating) AS avg_rating FROM reviews").fetchone()
        return round(row["avg_rating"] or 0.0, 2)

    # ---------------------------------------------------------------- settings
    def get_setting(self, key, default=None):
        row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        self.conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value)),
        )
        self.conn.commit()

    # ---------------------------------------------------------------- activity log
    def log_activity(self, username, action):
        self.conn.execute(
            "INSERT INTO activity_log (username, action, timestamp) VALUES (?, ?, ?)",
            (username, action, now_str()),
        )
        self.conn.commit()

    def get_recent_activity(self, limit=25):
        rows = self.conn.execute(
            "SELECT * FROM activity_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ---------------------------------------------------------------- backup / restore
    def backup(self, dest_path=None):
        self.conn.commit()
        os.makedirs(BACKUP_DIR, exist_ok=True)
        if dest_path is None:
            stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_path = os.path.join(BACKUP_DIR, f"backup_{stamp}.db")
        shutil.copyfile(self.path, dest_path)
        return dest_path

    def restore(self, src_path):
        self.conn.commit()
        self.conn.close()
        shutil.copyfile(src_path, self.path)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row

# ==============================================================================
# LOGIN DIALOG
# ==============================================================================
class LoginDialog(tk.Toplevel):
    """Modal dialog shown before the main app window opens."""

    def __init__(self, parent, db, on_success):
        super().__init__(parent)
        self.db = db
        self.on_success = on_success
        self.title(f"{APP_TITLE} — Login")
        self.geometry("360x260")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._quit_app)
        self.grab_set()

        container = ttk.Frame(self, padding=24)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text=APP_TITLE, font=("Segoe UI", 13, "bold")).pack(pady=(0, 4))
        ttk.Label(container, text="Please sign in to continue", foreground="#6B7280").pack(pady=(0, 16))

        ttk.Label(container, text="Username").pack(anchor="w")
        self.username_var = tk.StringVar(value="admin")
        entry_user = ttk.Entry(container, textvariable=self.username_var)
        entry_user.pack(fill="x", pady=(0, 10))

        ttk.Label(container, text="Password").pack(anchor="w")
        self.password_var = tk.StringVar(value="admin123")
        entry_pass = ttk.Entry(container, textvariable=self.password_var, show="*")
        entry_pass.pack(fill="x", pady=(0, 4))

        hint = ttk.Label(
            container,
            text="Default admin: admin / admin123\nDefault staff: staff / staff123",
            foreground="#9CA3AF", font=("Segoe UI", 8),
        )
        hint.pack(anchor="w", pady=(0, 12))

        btn_row = ttk.Frame(container)
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="Login", command=self._attempt_login).pack(side="right")
        ttk.Button(btn_row, text="Quit", command=self._quit_app).pack(side="right", padx=6)

        entry_pass.bind("<Return>", lambda e: self._attempt_login())
        entry_user.focus_set()

    def _attempt_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        user = self.db.verify_user(username, password)
        if user is None:
            messagebox.showerror("Login failed", "Incorrect username or password.", parent=self)
            return
        self.db.log_activity(username, "Logged in")
        self.destroy()
        self.on_success(user)

    def _quit_app(self):
        self.master.destroy()


# ==============================================================================
# SIMPLE DIALOG: generic add/edit form for small entities
# (suppliers, customers, categories) to avoid duplicating Toplevel boilerplate
# ==============================================================================
class EntityFormDialog(tk.Toplevel):
    """Generic modal form. `fields` is a list of (key, label) tuples."""

    def __init__(self, parent, title, fields, initial=None, on_submit=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()
        self.on_submit = on_submit
        self.vars = {}

        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)

        initial = initial or {}
        for key, label in fields:
            ttk.Label(container, text=label + ":").pack(anchor="w", pady=(6, 0))
            var = tk.StringVar(value=str(initial.get(key, "")))
            ttk.Entry(container, textvariable=var, width=36).pack(fill="x")
            self.vars[key] = var

        btn_row = ttk.Frame(container)
        btn_row.pack(fill="x", pady=(14, 0))
        ttk.Button(btn_row, text="Save", command=self._submit).pack(side="right")
        ttk.Button(btn_row, text="Cancel", command=self.destroy).pack(side="right", padx=6)

    def _submit(self):
        values = {k: v.get().strip() for k, v in self.vars.items()}
        if self.on_submit:
            ok = self.on_submit(values)
            if ok is not False:
                self.destroy()
        else:
            self.destroy()

# ==============================================================================
# MAIN APPLICATION
# ==============================================================================
class DashboardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()  # hide until logged in
        self.title(APP_TITLE)
        self.geometry("1300x760")
        self.minsize(1050, 650)

        self.db = Database()
        self.current_user = None
        self.theme = LIGHT_THEME if self.db.get_setting("theme", "light") == "light" else DARK_THEME

        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        LoginDialog(self, self.db, self._on_login_success)

    # ------------------------------------------------------------ login flow
    def _on_login_success(self, user):
        self.current_user = user
        self.deiconify()
        self._apply_theme()
        self._build_menu()
        self._build_layout()
        self._build_statusbar()
        self.refresh_everything()

    def is_admin(self):
        return self.current_user and self.current_user["role"] == "admin"

    # ------------------------------------------------------------ theming
    def _apply_theme(self):
        t = self.theme
        self.configure(bg=t["bg"])
        self.style.configure(".", background=t["bg"], foreground=t["fg"])
        self.style.configure("TFrame", background=t["bg"])
        self.style.configure("TLabelframe", background=t["bg"], foreground=t["fg"])
        self.style.configure("TLabelframe.Label", background=t["bg"], foreground=t["fg"])
        self.style.configure("TLabel", background=t["bg"], foreground=t["fg"])
        self.style.configure("TNotebook", background=t["bg"])
        self.style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(14, 8))
        self.style.configure("TButton", padding=6)
        self.style.configure("Treeview", rowheight=25, font=("Segoe UI", 10),
                              background=t["tree_bg"], fieldbackground=t["tree_bg"], foreground=t["fg"])
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self.style.map("Treeview", background=[("selected", t["accent"])])

        self.style.configure("KPI.TFrame", background=t["panel"])
        self.style.configure("KPI.TLabel", background=t["panel"], foreground=t["fg"])
        self.style.configure("KPITitle.TLabel", background=t["panel"], foreground=t["muted"],
                              font=("Segoe UI", 9))
        self.style.configure("KPIValue.TLabel", background=t["panel"], foreground=t["accent"],
                              font=("Segoe UI", 18, "bold"))

    def toggle_theme(self):
        self.theme = DARK_THEME if self.theme is LIGHT_THEME else LIGHT_THEME
        self.db.set_setting("theme", "dark" if self.theme is DARK_THEME else "light")
        self._apply_theme()
        # rebuild charts so matplotlib picks up new colors too
        self.refresh_everything()

    # ------------------------------------------------------------ menu bar
    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Backup Database", command=self._menu_backup)
        file_menu.add_command(label="Restore Database", command=self._menu_restore)
        file_menu.add_separator()
        file_menu.add_command(label="Export Items to CSV", command=self._menu_export_items)
        file_menu.add_command(label="Export Orders to CSV", command=self._menu_export_orders)
        file_menu.add_command(label="Import Items from CSV", command=self._menu_import_items)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Toggle Light / Dark Theme", command=self.toggle_theme)
        menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._menu_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _menu_backup(self):
        path = self.db.backup()
        messagebox.showinfo("Backup complete", f"Database backed up to:\n{path}")
        self.db.log_activity(self.current_user["username"], "Created a database backup")

    def _menu_restore(self):
        path = filedialog.askopenfilename(title="Select backup file", filetypes=[("SQLite DB", "*.db")])
        if not path:
            return
        if messagebox.askyesno("Confirm restore",
                                "This will replace all current data with the backup. Continue?"):
            self.db.restore(path)
            messagebox.showinfo("Restore complete", "Database restored. Refreshing dashboard.")
            self.refresh_everything()

    def _menu_export_items(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        items = self.db.get_items()
        headers = ["id", "name", "category_name", "supplier_name", "price", "quantity",
                   "units_sold", "rating", "reviews_count", "trending"]
        rows = [[it.get(h, "") for h in headers] for it in items]
        export_rows_to_csv(path, headers, rows)
        messagebox.showinfo("Export complete", f"{len(rows)} items exported to:\n{path}")

    def _menu_export_orders(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        orders = self.db.get_orders()
        headers = ["id", "customer_name", "item_name", "quantity", "unit_price", "total", "order_date"]
        rows = [[o.get(h, "") for h in headers] for o in orders]
        export_rows_to_csv(path, headers, rows)
        messagebox.showinfo("Export complete", f"{len(rows)} orders exported to:\n{path}")

    def _menu_import_items(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path:
            return
        headers, rows = import_rows_from_csv(path)
        try:
            name_i, price_i, qty_i = headers.index("name"), headers.index("price"), headers.index("quantity")
        except ValueError:
            messagebox.showerror("Import failed", "CSV must contain at least: name, price, quantity columns.")
            return
        count = 0
        for row in rows:
            try:
                name = row[name_i]
                price = safe_float(row[price_i])
                qty = safe_int(row[qty_i])
                if name:
                    self.db.add_item(name, None, None, price, qty, 0)
                    count += 1
            except IndexError:
                continue
        messagebox.showinfo("Import complete", f"{count} items imported.")
        self.refresh_everything()

    def _menu_about(self):
        messagebox.showinfo(
            "About",
            f"{APP_TITLE}\n\nBuilt with Python, Tkinter, SQLite and Matplotlib.\n"
            "Includes inventory, suppliers, customers, orders, reviews and analytics.",
        )

    # ------------------------------------------------------------ status bar
    def _build_statusbar(self):
        bar = ttk.Frame(self)
        bar.pack(side="bottom", fill="x")
        self.status_left = ttk.Label(bar, text="", anchor="w", padding=(8, 4))
        self.status_left.pack(side="left")
        self.status_right = ttk.Label(bar, text="", anchor="e", padding=(8, 4))
        self.status_right.pack(side="right")
        self._update_statusbar()

    def _update_statusbar(self):
        role = self.current_user["role"].capitalize()
        self.status_left.config(
            text=f"Logged in as {self.current_user['username']} ({role})"
        )
        item_count = len(self.db.get_items())
        order_count = self.db.order_count()
        self.status_right.config(text=f"Items: {item_count}   |   Orders: {order_count}   |   {now_str()}")

    def set_status_message(self, message):
        self.status_left.config(text=message)
        self.after(3000, self._update_statusbar)

    def refresh_everything(self):
        self.refresh_dashboard_tab()
        self.refresh_items_tab()
        self.refresh_suppliers_tab()
        self.refresh_customers_tab()
        self.refresh_orders_tab()
        self.refresh_reviews_tab()
        self.refresh_reports_tab()
        self._update_statusbar()

    # ------------------------------------------------------------ layout / tabs
    def _build_layout(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=(6, 0))

        self.tab_dashboard = ttk.Frame(self.notebook)
        self.tab_items = ttk.Frame(self.notebook)
        self.tab_suppliers = ttk.Frame(self.notebook)
        self.tab_customers = ttk.Frame(self.notebook)
        self.tab_orders = ttk.Frame(self.notebook)
        self.tab_reviews = ttk.Frame(self.notebook)
        self.tab_reports = ttk.Frame(self.notebook)
        self.tab_settings = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_dashboard, text="Dashboard")
        self.notebook.add(self.tab_items, text="Items")
        self.notebook.add(self.tab_suppliers, text="Suppliers")
        self.notebook.add(self.tab_customers, text="Customers")
        self.notebook.add(self.tab_orders, text="Orders / Sales")
        self.notebook.add(self.tab_reviews, text="Customer Reviews")
        self.notebook.add(self.tab_reports, text="Reports")
        self.notebook.add(self.tab_settings, text="Settings")

        self._build_dashboard_tab(self.tab_dashboard)
        self._build_items_tab(self.tab_items)
        self._build_suppliers_tab(self.tab_suppliers)
        self._build_customers_tab(self.tab_customers)
        self._build_orders_tab(self.tab_orders)
        self._build_reviews_tab(self.tab_reviews)
        self._build_reports_tab(self.tab_reports)
        self._build_settings_tab(self.tab_settings)

    # ==========================================================================
    # DASHBOARD TAB — KPI cards + 5 live charts
    # ==========================================================================
    def _build_dashboard_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        parent.rowconfigure(2, weight=1)

        # --- KPI cards row ---
        kpi_row = ttk.Frame(parent)
        kpi_row.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        for i in range(5):
            kpi_row.columnconfigure(i, weight=1)

        self.kpi_labels = {}
        kpi_defs = [
            ("total_items", "Total Items"),
            ("stock_value", "Stock Value"),
            ("low_stock", "Low Stock Alerts"),
            ("avg_rating", "Avg. Customer Rating"),
            ("revenue_30d", "Revenue (30 days)"),
        ]
        for idx, (key, title) in enumerate(kpi_defs):
            card = ttk.Frame(kpi_row, style="KPI.TFrame", padding=14)
            card.grid(row=0, column=idx, sticky="nsew", padx=4)
            ttk.Label(card, text=title, style="KPITitle.TLabel").pack(anchor="w")
            value_label = ttk.Label(card, text="—", style="KPIValue.TLabel")
            value_label.pack(anchor="w", pady=(6, 0))
            self.kpi_labels[key] = value_label

        ttk.Button(kpi_row, text="↻ Refresh", command=self.refresh_everything).grid(
            row=0, column=5, sticky="e", padx=(10, 0)
        )

        # --- charts grid ---
        charts_top = ttk.Frame(parent)
        charts_top.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 4))
        charts_top.columnconfigure(0, weight=1)
        charts_top.columnconfigure(1, weight=1)
        charts_top.rowconfigure(0, weight=1)

        charts_bottom = ttk.Frame(parent)
        charts_bottom.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        charts_bottom.columnconfigure(0, weight=1)
        charts_bottom.columnconfigure(1, weight=1)
        charts_bottom.rowconfigure(0, weight=1)

        self.fig_stock = Figure(figsize=(5, 3.2), dpi=100)
        self.ax_stock = self.fig_stock.add_subplot(111)
        self.canvas_stock = FigureCanvasTkAgg(self.fig_stock, master=charts_top)
        self.canvas_stock.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        self.fig_ratings = Figure(figsize=(5, 3.2), dpi=100)
        self.ax_ratings = self.fig_ratings.add_subplot(111)
        self.canvas_ratings = FigureCanvasTkAgg(self.fig_ratings, master=charts_top)
        self.canvas_ratings.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=4, pady=4)

        self.fig_trend = Figure(figsize=(5, 3.2), dpi=100)
        self.ax_trend = self.fig_trend.add_subplot(111)
        self.canvas_trend = FigureCanvasTkAgg(self.fig_trend, master=charts_bottom)
        self.canvas_trend.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        self.fig_sales = Figure(figsize=(5, 3.2), dpi=100)
        self.ax_sales = self.fig_sales.add_subplot(111)
        self.canvas_sales = FigureCanvasTkAgg(self.fig_sales, master=charts_bottom)
        self.canvas_sales.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=4, pady=4)

    def refresh_dashboard_tab(self):
        t = self.theme
        currency = self.db.get_setting("currency_symbol", "$")
        threshold = safe_int(self.db.get_setting("low_stock_threshold", 20), 20)

        items = self.db.get_items()
        low_stock = self.db.low_stock_items(threshold)
        stock_value = self.db.total_stock_value()
        avg_rating = self.db.average_rating_overall()
        revenue_30d = self.db.total_revenue(days=30)

        self.kpi_labels["total_items"].config(text=str(len(items)))
        self.kpi_labels["stock_value"].config(text=format_currency(stock_value, currency))
        self.kpi_labels["low_stock"].config(text=str(len(low_stock)))
        self.kpi_labels["avg_rating"].config(text=f"{avg_rating:.2f} / 5")
        self.kpi_labels["revenue_30d"].config(text=format_currency(revenue_30d, currency))

        # colour the low-stock KPI red if there are any alerts
        if low_stock:
            self.kpi_labels["low_stock"].config(foreground=t["danger"])
        else:
            self.kpi_labels["low_stock"].config(foreground=t["success"])

        self._draw_stock_chart(items, threshold, t)
        self._draw_ratings_chart(t)
        self._draw_trend_chart(t)
        self._draw_sales_chart(t)

    def _style_axes(self, ax, fig, theme):
        fig.patch.set_facecolor(theme["panel"])
        ax.set_facecolor(theme["panel"])
        ax.tick_params(colors=theme["fg"])
        ax.xaxis.label.set_color(theme["fg"])
        ax.yaxis.label.set_color(theme["fg"])
        ax.title.set_color(theme["fg"])
        for spine in ax.spines.values():
            spine.set_color(theme["muted"])

    def _draw_stock_chart(self, items, threshold, theme):
        self.ax_stock.clear()
        self._style_axes(self.ax_stock, self.fig_stock, theme)
        if items:
            names = [it["name"] for it in items]
            qtys = [it["quantity"] for it in items]
            colors = [theme["danger"] if q <= threshold else theme["accent"] for q in qtys]
            bars = self.ax_stock.bar(names, qtys, color=colors)
            self.ax_stock.axhline(threshold, color=theme["warning"], linestyle="--", linewidth=1)
            self.ax_stock.set_title("Stock Levels (red = low stock)")
            self.ax_stock.set_ylabel("Qty")
            self.ax_stock.tick_params(axis="x", rotation=45, labelsize=7)
            for b in bars:
                h = b.get_height()
                self.ax_stock.annotate(str(int(h)), (b.get_x() + b.get_width() / 2, h),
                                        ha="center", va="bottom", fontsize=7, color=theme["fg"])
        else:
            self.ax_stock.set_title("Stock Levels (no data)")
        self.fig_stock.tight_layout()
        self.canvas_stock.draw()

    def _draw_ratings_chart(self, theme):
        self.ax_ratings.clear()
        self._style_axes(self.ax_ratings, self.fig_ratings, theme)
        buckets = self.db.rating_distribution()
        labels = list(buckets.keys())
        values = list(buckets.values())
        if sum(values) > 0:
            wedges, _texts, autotexts = self.ax_ratings.pie(
                values, labels=labels, autopct=lambda p: f"{p:.0f}%" if p > 0 else "",
                colors=CHART_PALETTE, startangle=90,
                textprops={"color": theme["fg"], "fontsize": 8},
            )
        self.ax_ratings.set_title("Customer Reviews by Rating Band")
        self.fig_ratings.tight_layout()
        self.canvas_ratings.draw()

    def _draw_trend_chart(self, theme):
        self.ax_trend.clear()
        self._style_axes(self.ax_trend, self.fig_trend, theme)
        top_items = self.db.top_selling_items(limit=8)
        if top_items:
            names = [i["name"] for i in top_items]
            sold = [i["units_sold"] for i in top_items]
            colors = [theme["danger"] if i["trending"] else theme["muted"] for i in top_items]
            bars = self.ax_trend.bar(names, sold, color=colors)
            self.ax_trend.set_title("Trending Items (red = flagged) — Units Sold")
            self.ax_trend.set_ylabel("Units sold")
            self.ax_trend.tick_params(axis="x", rotation=20, labelsize=8)
            for b in bars:
                h = b.get_height()
                self.ax_trend.annotate(str(int(h)), (b.get_x() + b.get_width() / 2, h),
                                        ha="center", va="bottom", fontsize=7, color=theme["fg"])
        else:
            self.ax_trend.set_title("Trending Items (no data)")
        self.fig_trend.tight_layout()
        self.canvas_trend.draw()

    def _draw_sales_chart(self, theme):
        self.ax_sales.clear()
        self._style_axes(self.ax_sales, self.fig_sales, theme)
        data = self.db.sales_by_date(days=30)
        if data:
            dates = [d[0][5:] for d in data]  # trim year for compact labels (MM-DD)
            revenue = [d[1] for d in data]
            self.ax_sales.plot(dates, revenue, marker="o", color=theme["accent"], linewidth=2)
            self.ax_sales.fill_between(range(len(dates)), revenue, color=theme["accent"], alpha=0.15)
            self.ax_sales.set_title("Revenue — Last 30 Days")
            self.ax_sales.set_ylabel("Revenue")
            self.ax_sales.tick_params(axis="x", rotation=60, labelsize=6)
        else:
            self.ax_sales.set_title("Revenue — Last 30 Days (no data)")
        self.fig_sales.tight_layout()
        self.canvas_sales.draw()

    # ==========================================================================
    # ITEMS TAB
    # ==========================================================================
    ITEM_COLUMNS = ("id", "name", "category", "supplier", "price", "quantity",
                     "units_sold", "rating", "reviews", "trending")
    ITEM_HEADINGS = ("ID", "Name", "Category", "Supplier", "Price", "Qty",
                      "Sold", "Rating", "Reviews", "Trending")

    def _build_items_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        top = ttk.Frame(parent)
        top.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        ttk.Label(top, text="Search:").pack(side="left")
        self.item_search_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.item_search_var, width=28)
        entry.pack(side="left", padx=6)
        entry.bind("<KeyRelease>", lambda e: self.refresh_items_tab())
        ttk.Button(top, text="Clear", command=lambda: (self.item_search_var.set(""), self.refresh_items_tab())).pack(side="left")

        table_frame = ttk.Frame(parent)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=6)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        self.item_tree = ttk.Treeview(table_frame, columns=self.ITEM_COLUMNS, show="headings")
        for col, head in zip(self.ITEM_COLUMNS, self.ITEM_HEADINGS):
            self.item_tree.heading(col, text=head, command=lambda c=col: self._sort_item_tree(c))
            width = 60 if col in ("id", "qty", "sold", "rating", "reviews", "trending") else 120
            self.item_tree.column(col, width=width, anchor="center")
        self.item_tree.column("name", width=150, anchor="w")
        self.item_tree.column("category", width=100, anchor="w")
        self.item_tree.column("supplier", width=120, anchor="w")
        self.item_tree.tag_configure("low_stock", foreground="#D64545")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.item_tree.yview)
        self.item_tree.configure(yscrollcommand=vsb.set)
        self.item_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self.item_tree.bind("<<TreeviewSelect>>", self._on_item_select)

        form = ttk.LabelFrame(parent, text="Item Details")
        form.grid(row=2, column=0, sticky="ew", padx=6, pady=6)
        for i in range(4):
            form.columnconfigure(i, weight=1)

        ttk.Label(form, text="Name:").grid(row=0, column=0, sticky="w", padx=6, pady=(6, 0))
        self.item_name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.item_name_var).grid(row=1, column=0, sticky="ew", padx=6)

        ttk.Label(form, text="Category:").grid(row=0, column=1, sticky="w", padx=6, pady=(6, 0))
        self.item_category_var = tk.StringVar()
        self.item_category_combo = ttk.Combobox(form, textvariable=self.item_category_var, state="readonly")
        self.item_category_combo.grid(row=1, column=1, sticky="ew", padx=6)

        ttk.Label(form, text="Supplier:").grid(row=0, column=2, sticky="w", padx=6, pady=(6, 0))
        self.item_supplier_var = tk.StringVar()
        self.item_supplier_combo = ttk.Combobox(form, textvariable=self.item_supplier_var, state="readonly")
        self.item_supplier_combo.grid(row=1, column=2, sticky="ew", padx=6)

        self.item_trending_var = tk.BooleanVar()
        ttk.Checkbutton(form, text="Trending", variable=self.item_trending_var).grid(
            row=1, column=3, sticky="w", padx=6
        )

        ttk.Label(form, text="Price:").grid(row=2, column=0, sticky="w", padx=6, pady=(6, 0))
        self.item_price_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.item_price_var).grid(row=3, column=0, sticky="ew", padx=6, pady=(0, 8))

        ttk.Label(form, text="Quantity:").grid(row=2, column=1, sticky="w", padx=6, pady=(6, 0))
        self.item_quantity_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.item_quantity_var).grid(row=3, column=1, sticky="ew", padx=6, pady=(0, 8))

        btns = ttk.Frame(parent)
        btns.grid(row=3, column=0, sticky="ew", padx=6, pady=(0, 8))
        ttk.Button(btns, text="Add Item", command=self._add_item).pack(side="left", padx=4)
        ttk.Button(btns, text="Update Selected", command=self._update_item).pack(side="left", padx=4)
        self.item_delete_btn = ttk.Button(btns, text="Delete Selected", command=self._delete_item)
        self.item_delete_btn.pack(side="left", padx=4)
        ttk.Button(btns, text="Clear Form", command=self._clear_item_form).pack(side="left", padx=4)

        self.selected_item_id = None

    def _category_choices(self):
        cats = self.db.get_categories()
        return {c["name"]: c["id"] for c in cats}

    def _supplier_choices(self):
        sups = self.db.get_suppliers()
        return {s["name"]: s["id"] for s in sups}

    def refresh_items_tab(self):
        cat_map = self._category_choices()
        sup_map = self._supplier_choices()
        self.item_category_combo["values"] = list(cat_map.keys())
        self.item_supplier_combo["values"] = list(sup_map.keys())
        self._item_cat_map, self._item_sup_map = cat_map, sup_map

        for row in self.item_tree.get_children():
            self.item_tree.delete(row)

        threshold = safe_int(self.db.get_setting("low_stock_threshold", 20), 20)
        currency = self.db.get_setting("currency_symbol", "$")
        items = self.db.get_items(self.item_search_var.get().strip() if hasattr(self, "item_search_var") else "")
        for it in items:
            tags = ("low_stock",) if it["quantity"] <= threshold else ()
            self.item_tree.insert(
                "", "end", iid=str(it["id"]), tags=tags,
                values=(it["id"], it["name"], it["category_name"] or "—", it["supplier_name"] or "—",
                        format_currency(it["price"], currency), it["quantity"], it["units_sold"],
                        f"{it['rating']:.1f}", it["reviews_count"], "Yes" if it["trending"] else "No"),
            )

        # keep delete button admin-only
        if hasattr(self, "item_delete_btn"):
            self.item_delete_btn.config(state="normal" if self.is_admin() else "disabled")

    def _sort_item_tree(self, col):
        data = [(self.item_tree.set(k, col), k) for k in self.item_tree.get_children("")]
        try:
            data.sort(key=lambda t: float(str(t[0]).replace(",", "").replace("$", "").replace("₹", "")))
        except ValueError:
            data.sort(key=lambda t: t[0])
        for index, (_, k) in enumerate(data):
            self.item_tree.move(k, "", index)

    def _on_item_select(self, event=None):
        sel = self.item_tree.selection()
        if not sel:
            return
        item_id = int(sel[0])
        it = self.db.get_item(item_id)
        if not it:
            return
        self.selected_item_id = item_id
        self.item_name_var.set(it["name"])
        self.item_category_var.set(it["category_name"] or "")
        self.item_supplier_var.set(it["supplier_name"] or "")
        self.item_price_var.set(it["price"])
        self.item_quantity_var.set(it["quantity"])
        self.item_trending_var.set(bool(it["trending"]))

    def _clear_item_form(self):
        self.selected_item_id = None
        self.item_name_var.set("")
        self.item_category_var.set("")
        self.item_supplier_var.set("")
        self.item_price_var.set("")
        self.item_quantity_var.set("")
        self.item_trending_var.set(False)
        self.item_tree.selection_remove(self.item_tree.selection())

    def _read_item_form(self):
        name = self.item_name_var.get().strip()
        if not name:
            raise ValueError("Name is required.")
        price = safe_float(self.item_price_var.get())
        quantity = safe_int(self.item_quantity_var.get())
        if price < 0 or quantity < 0:
            raise ValueError("Price and quantity cannot be negative.")
        category_id = self._item_cat_map.get(self.item_category_var.get())
        supplier_id = self._item_sup_map.get(self.item_supplier_var.get())
        trending = 1 if self.item_trending_var.get() else 0
        return name, category_id, supplier_id, price, quantity, trending

    def _add_item(self):
        try:
            data = self._read_item_form()
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))
            return
        self.db.add_item(*data)
        self.db.log_activity(self.current_user["username"], f"Added item '{data[0]}'")
        self._clear_item_form()
        self.refresh_items_tab()
        self.refresh_dashboard_tab()
        self.refresh_reports_tab()
        self.refresh_orders_tab()
        self.refresh_reviews_tab()

    def _update_item(self):
        if self.selected_item_id is None:
            messagebox.showwarning("No selection", "Select an item first.")
            return
        try:
            data = self._read_item_form()
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))
            return
        self.db.update_item(self.selected_item_id, *data)
        self.db.log_activity(self.current_user["username"], f"Updated item '{data[0]}'")
        self._clear_item_form()
        self.refresh_items_tab()
        self.refresh_dashboard_tab()
        self.refresh_reports_tab()
        self.refresh_orders_tab()
        self.refresh_reviews_tab()

    def _delete_item(self):
        if not self.is_admin():
            messagebox.showwarning("Permission denied", "Only admins can delete items.")
            return
        if self.selected_item_id is None:
            messagebox.showwarning("No selection", "Select an item first.")
            return
        if messagebox.askyesno("Confirm delete", "Delete this item? This also removes its orders and reviews."):
            self.db.delete_item(self.selected_item_id)
            self.db.log_activity(self.current_user["username"], f"Deleted item id={self.selected_item_id}")
            self._clear_item_form()
            self.refresh_everything()

    # ==========================================================================
    # SUPPLIERS TAB
    # ==========================================================================
    def _build_suppliers_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        table_frame = ttk.Frame(parent)
        table_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        cols = ("id", "name", "contact_person", "email", "phone")
        heads = ("ID", "Name", "Contact Person", "Email", "Phone")
        self.supplier_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c, h in zip(cols, heads):
            self.supplier_tree.heading(c, text=h)
            self.supplier_tree.column(c, width=140 if c != "id" else 50, anchor="w" if c != "id" else "center")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.supplier_tree.yview)
        self.supplier_tree.configure(yscrollcommand=vsb.set)
        self.supplier_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        btns = ttk.Frame(parent)
        btns.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 8))
        ttk.Button(btns, text="Add Supplier", command=self._add_supplier_dialog).pack(side="left", padx=4)
        ttk.Button(btns, text="Edit Selected", command=self._edit_supplier_dialog).pack(side="left", padx=4)
        ttk.Button(btns, text="Delete Selected", command=self._delete_supplier).pack(side="left", padx=4)

    def refresh_suppliers_tab(self):
        for row in self.supplier_tree.get_children():
            self.supplier_tree.delete(row)
        for s in self.db.get_suppliers():
            self.supplier_tree.insert("", "end", iid=str(s["id"]),
                                       values=(s["id"], s["name"], s["contact_person"] or "",
                                               s["email"] or "", s["phone"] or ""))

    def _add_supplier_dialog(self):
        fields = [("name", "Name"), ("contact_person", "Contact Person"),
                  ("email", "Email"), ("phone", "Phone")]

        def submit(values):
            if not values["name"]:
                messagebox.showerror("Invalid input", "Name is required.")
                return False
            self.db.add_supplier(values["name"], values["contact_person"], values["email"], values["phone"])
            self.db.log_activity(self.current_user["username"], f"Added supplier '{values['name']}'")
            self.refresh_suppliers_tab()
            self.refresh_items_tab()

        EntityFormDialog(self, "Add Supplier", fields, on_submit=submit)

    def _edit_supplier_dialog(self):
        sel = self.supplier_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a supplier first.")
            return
        supplier_id = int(sel[0])
        current = next((s for s in self.db.get_suppliers() if s["id"] == supplier_id), None)
        if not current:
            return
        fields = [("name", "Name"), ("contact_person", "Contact Person"),
                  ("email", "Email"), ("phone", "Phone")]

        def submit(values):
            if not values["name"]:
                messagebox.showerror("Invalid input", "Name is required.")
                return False
            self.db.update_supplier(supplier_id, values["name"], values["contact_person"],
                                     values["email"], values["phone"])
            self.db.log_activity(self.current_user["username"], f"Updated supplier '{values['name']}'")
            self.refresh_suppliers_tab()
            self.refresh_items_tab()

        EntityFormDialog(self, "Edit Supplier", fields, initial=current, on_submit=submit)

    def _delete_supplier(self):
        if not self.is_admin():
            messagebox.showwarning("Permission denied", "Only admins can delete suppliers.")
            return
        sel = self.supplier_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a supplier first.")
            return
        if messagebox.askyesno("Confirm delete", "Delete this supplier?"):
            self.db.delete_supplier(int(sel[0]))
            self.db.log_activity(self.current_user["username"], "Deleted a supplier")
            self.refresh_suppliers_tab()
            self.refresh_items_tab()

    # ==========================================================================
    # CUSTOMERS TAB
    # ==========================================================================
    def _build_customers_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        table_frame = ttk.Frame(parent)
        table_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        cols = ("id", "name", "email", "phone", "joined_date")
        heads = ("ID", "Name", "Email", "Phone", "Joined")
        self.customer_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c, h in zip(cols, heads):
            self.customer_tree.heading(c, text=h)
            self.customer_tree.column(c, width=140 if c != "id" else 50, anchor="w" if c != "id" else "center")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.customer_tree.yview)
        self.customer_tree.configure(yscrollcommand=vsb.set)
        self.customer_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        btns = ttk.Frame(parent)
        btns.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 8))
        ttk.Button(btns, text="Add Customer", command=self._add_customer_dialog).pack(side="left", padx=4)
        ttk.Button(btns, text="Edit Selected", command=self._edit_customer_dialog).pack(side="left", padx=4)
        ttk.Button(btns, text="Delete Selected", command=self._delete_customer).pack(side="left", padx=4)

    def refresh_customers_tab(self):
        for row in self.customer_tree.get_children():
            self.customer_tree.delete(row)
        for c in self.db.get_customers():
            self.customer_tree.insert("", "end", iid=str(c["id"]),
                                       values=(c["id"], c["name"], c["email"] or "",
                                               c["phone"] or "", c["joined_date"] or ""))

    def _add_customer_dialog(self):
        fields = [("name", "Name"), ("email", "Email"), ("phone", "Phone")]

        def submit(values):
            if not values["name"]:
                messagebox.showerror("Invalid input", "Name is required.")
                return False
            self.db.add_customer(values["name"], values["email"], values["phone"])
            self.db.log_activity(self.current_user["username"], f"Added customer '{values['name']}'")
            self.refresh_customers_tab()
            self.refresh_orders_tab()
            self.refresh_reviews_tab()

        EntityFormDialog(self, "Add Customer", fields, on_submit=submit)

    def _edit_customer_dialog(self):
        sel = self.customer_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a customer first.")
            return
        customer_id = int(sel[0])
        current = next((c for c in self.db.get_customers() if c["id"] == customer_id), None)
        if not current:
            return
        fields = [("name", "Name"), ("email", "Email"), ("phone", "Phone")]

        def submit(values):
            if not values["name"]:
                messagebox.showerror("Invalid input", "Name is required.")
                return False
            self.db.update_customer(customer_id, values["name"], values["email"], values["phone"])
            self.db.log_activity(self.current_user["username"], f"Updated customer '{values['name']}'")
            self.refresh_customers_tab()
            self.refresh_orders_tab()
            self.refresh_reviews_tab()

        EntityFormDialog(self, "Edit Customer", fields, initial=current, on_submit=submit)

    def _delete_customer(self):
        if not self.is_admin():
            messagebox.showwarning("Permission denied", "Only admins can delete customers.")
            return
        sel = self.customer_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a customer first.")
            return
        if messagebox.askyesno("Confirm delete", "Delete this customer?"):
            self.db.delete_customer(int(sel[0]))
            self.db.log_activity(self.current_user["username"], "Deleted a customer")
            self.refresh_customers_tab()
            self.refresh_orders_tab()
            self.refresh_reviews_tab()

    # ==========================================================================
    # ORDERS / SALES TAB
    # ==========================================================================
    def _build_orders_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        top = ttk.Frame(parent)
        top.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        ttk.Label(top, text="Search:").pack(side="left")
        self.order_search_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.order_search_var, width=28)
        entry.pack(side="left", padx=6)
        entry.bind("<KeyRelease>", lambda e: self.refresh_orders_tab())

        table_frame = ttk.Frame(parent)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=6)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        cols = ("id", "customer_name", "item_name", "quantity", "unit_price", "total", "order_date")
        heads = ("ID", "Customer", "Item", "Qty", "Unit Price", "Total", "Date")
        self.order_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c, h in zip(cols, heads):
            self.order_tree.heading(c, text=h)
            width = 60 if c in ("id", "quantity") else 110
            self.order_tree.column(c, width=width, anchor="center")
        self.order_tree.column("customer_name", width=140, anchor="w")
        self.order_tree.column("item_name", width=150, anchor="w")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=vsb.set)
        self.order_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        form = ttk.LabelFrame(parent, text="New Order (auto-updates stock & revenue)")
        form.grid(row=2, column=0, sticky="ew", padx=6, pady=6)
        for i in range(4):
            form.columnconfigure(i, weight=1)

        ttk.Label(form, text="Customer:").grid(row=0, column=0, sticky="w", padx=6, pady=(6, 0))
        self.order_customer_var = tk.StringVar()
        self.order_customer_combo = ttk.Combobox(form, textvariable=self.order_customer_var, state="readonly")
        self.order_customer_combo.grid(row=1, column=0, sticky="ew", padx=6)

        ttk.Label(form, text="Item:").grid(row=0, column=1, sticky="w", padx=6, pady=(6, 0))
        self.order_item_var = tk.StringVar()
        self.order_item_combo = ttk.Combobox(form, textvariable=self.order_item_var, state="readonly")
        self.order_item_combo.grid(row=1, column=1, sticky="ew", padx=6)
        self.order_item_combo.bind("<<ComboboxSelected>>", self._on_order_item_selected)

        ttk.Label(form, text="Quantity:").grid(row=0, column=2, sticky="w", padx=6, pady=(6, 0))
        self.order_quantity_var = tk.StringVar(value="1")
        ttk.Entry(form, textvariable=self.order_quantity_var).grid(row=1, column=2, sticky="ew", padx=6)

        ttk.Label(form, text="Unit Price:").grid(row=0, column=3, sticky="w", padx=6, pady=(6, 0))
        self.order_price_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.order_price_var).grid(row=1, column=3, sticky="ew", padx=6)

        btns = ttk.Frame(parent)
        btns.grid(row=3, column=0, sticky="ew", padx=6, pady=(0, 8))
        ttk.Button(btns, text="Place Order", command=self._place_order).pack(side="left", padx=4)
        ttk.Button(btns, text="Delete Selected (restores stock)", command=self._delete_order).pack(side="left", padx=4)

    def _on_order_item_selected(self, event=None):
        name = self.order_item_var.get()
        item_id = self._order_item_map.get(name)
        if item_id:
            item = self.db.get_item(item_id)
            if item:
                self.order_price_var.set(item["price"])

    def refresh_orders_tab(self):
        customers = self.db.get_customers()
        items = self.db.get_items()
        self._order_customer_map = {c["name"]: c["id"] for c in customers}
        self._order_item_map = {i["name"]: i["id"] for i in items}
        self.order_customer_combo["values"] = list(self._order_customer_map.keys())
        self.order_item_combo["values"] = list(self._order_item_map.keys())

        for row in self.order_tree.get_children():
            self.order_tree.delete(row)
        currency = self.db.get_setting("currency_symbol", "$")
        for o in self.db.get_orders(getattr(self, "order_search_var", tk.StringVar()).get().strip()):
            self.order_tree.insert(
                "", "end", iid=str(o["id"]),
                values=(o["id"], o["customer_name"] or "Walk-in", o["item_name"] or "—",
                        o["quantity"], format_currency(o["unit_price"], currency),
                        format_currency(o["total"], currency), o["order_date"]),
            )

    def _place_order(self):
        item_name = self.order_item_var.get()
        item_id = self._order_item_map.get(item_name)
        if not item_id:
            messagebox.showerror("Invalid input", "Select an item.")
            return
        customer_id = self._order_customer_map.get(self.order_customer_var.get())
        quantity = safe_int(self.order_quantity_var.get())
        unit_price = safe_float(self.order_price_var.get())
        if quantity <= 0:
            messagebox.showerror("Invalid input", "Quantity must be greater than zero.")
            return
        item = self.db.get_item(item_id)
        if item and quantity > item["quantity"]:
            if not messagebox.askyesno(
                "Insufficient stock",
                f"Only {item['quantity']} units in stock. Proceed anyway (stock will go negative)?",
            ):
                return
        self.db.create_order(customer_id, item_id, quantity, unit_price)
        self.db.log_activity(self.current_user["username"],
                              f"Placed order: {quantity} x '{item_name}'")
        self.order_quantity_var.set("1")
        self.refresh_orders_tab()
        self.refresh_items_tab()
        self.refresh_dashboard_tab()
        self.refresh_reports_tab()

    def _delete_order(self):
        if not self.is_admin():
            messagebox.showwarning("Permission denied", "Only admins can delete orders.")
            return
        sel = self.order_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select an order first.")
            return
        if messagebox.askyesno("Confirm delete", "Delete this order? Stock will be restored."):
            self.db.delete_order(int(sel[0]))
            self.db.log_activity(self.current_user["username"], "Deleted an order")
            self.refresh_orders_tab()
            self.refresh_items_tab()
            self.refresh_dashboard_tab()
            self.refresh_reports_tab()

    # ==========================================================================
    # CUSTOMER REVIEWS TAB
    # ==========================================================================
    def _build_reviews_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        top = ttk.Frame(parent)
        top.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        ttk.Label(top, text="Search:").pack(side="left")
        self.review_search_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.review_search_var, width=28)
        entry.pack(side="left", padx=6)
        entry.bind("<KeyRelease>", lambda e: self.refresh_reviews_tab())

        table_frame = ttk.Frame(parent)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=6)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        cols = ("id", "item_name", "customer_name", "rating", "comment", "review_date")
        heads = ("ID", "Item", "Customer", "Rating", "Comment", "Date")
        self.review_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c, h in zip(cols, heads):
            self.review_tree.heading(c, text=h)
            width = 60 if c in ("id", "rating") else 130
            self.review_tree.column(c, width=width, anchor="center")
        self.review_tree.column("item_name", width=140, anchor="w")
        self.review_tree.column("customer_name", width=130, anchor="w")
        self.review_tree.column("comment", width=260, anchor="w")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.review_tree.yview)
        self.review_tree.configure(yscrollcommand=vsb.set)
        self.review_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        form = ttk.LabelFrame(parent, text="Add Customer Review (recomputes the item's live rating)")
        form.grid(row=2, column=0, sticky="ew", padx=6, pady=6)
        for i in range(4):
            form.columnconfigure(i, weight=1)

        ttk.Label(form, text="Item:").grid(row=0, column=0, sticky="w", padx=6, pady=(6, 0))
        self.review_item_var = tk.StringVar()
        self.review_item_combo = ttk.Combobox(form, textvariable=self.review_item_var, state="readonly")
        self.review_item_combo.grid(row=1, column=0, sticky="ew", padx=6)

        ttk.Label(form, text="Customer:").grid(row=0, column=1, sticky="w", padx=6, pady=(6, 0))
        self.review_customer_var = tk.StringVar()
        self.review_customer_combo = ttk.Combobox(form, textvariable=self.review_customer_var, state="readonly")
        self.review_customer_combo.grid(row=1, column=1, sticky="ew", padx=6)

        ttk.Label(form, text="Rating (0-5):").grid(row=0, column=2, sticky="w", padx=6, pady=(6, 0))
        self.review_rating_var = tk.StringVar(value="5")
        ttk.Spinbox(form, from_=0, to=5, increment=0.5, textvariable=self.review_rating_var, width=8).grid(
            row=1, column=2, sticky="w", padx=6
        )

        ttk.Label(form, text="Comment:").grid(row=2, column=0, sticky="w", padx=6, pady=(8, 0))
        self.review_comment_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.review_comment_var).grid(
            row=3, column=0, columnspan=3, sticky="ew", padx=6, pady=(0, 8)
        )

        btns = ttk.Frame(parent)
        btns.grid(row=3, column=0, sticky="ew", padx=6, pady=(0, 8))
        ttk.Button(btns, text="Submit Review", command=self._add_review).pack(side="left", padx=4)
        ttk.Button(btns, text="Delete Selected", command=self._delete_review).pack(side="left", padx=4)

    def refresh_reviews_tab(self):
        items = self.db.get_items()
        customers = self.db.get_customers()
        self._review_item_map = {i["name"]: i["id"] for i in items}
        self._review_customer_map = {c["name"]: c["id"] for c in customers}
        self.review_item_combo["values"] = list(self._review_item_map.keys())
        self.review_customer_combo["values"] = list(self._review_customer_map.keys())

        for row in self.review_tree.get_children():
            self.review_tree.delete(row)
        for r in self.db.get_reviews(search=getattr(self, "review_search_var", tk.StringVar()).get().strip()):
            self.review_tree.insert(
                "", "end", iid=str(r["id"]),
                values=(r["id"], r["item_name"] or "—", r["customer_name"] or "Anonymous",
                        f"{r['rating']:.1f}", r["comment"] or "", r["review_date"]),
            )

    def _add_review(self):
        item_name = self.review_item_var.get()
        item_id = self._review_item_map.get(item_name)
        if not item_id:
            messagebox.showerror("Invalid input", "Select an item.")
            return
        customer_id = self._review_customer_map.get(self.review_customer_var.get())
        rating = safe_float(self.review_rating_var.get())
        if not (0 <= rating <= 5):
            messagebox.showerror("Invalid input", "Rating must be between 0 and 5.")
            return
        comment = self.review_comment_var.get().strip()
        self.db.add_review(item_id, customer_id, rating, comment)
        self.db.log_activity(self.current_user["username"], f"Added review for '{item_name}'")
        self.review_comment_var.set("")
        self.refresh_reviews_tab()
        self.refresh_items_tab()
        self.refresh_dashboard_tab()

    def _delete_review(self):
        if not self.is_admin():
            messagebox.showwarning("Permission denied", "Only admins can delete reviews.")
            return
        sel = self.review_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a review first.")
            return
        if messagebox.askyesno("Confirm delete", "Delete this review?"):
            self.db.delete_review(int(sel[0]))
            self.db.log_activity(self.current_user["username"], "Deleted a review")
            self.refresh_reviews_tab()
            self.refresh_items_tab()
            self.refresh_dashboard_tab()

    # ==========================================================================
    # REPORTS TAB
    # ==========================================================================
    def _build_reports_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(1, weight=1)

        ttk.Label(parent, text="Business Reports", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=8, pady=8
        )

        low_stock_frame = ttk.LabelFrame(parent, text="Low Stock Report")
        low_stock_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        low_stock_frame.columnconfigure(0, weight=1)
        low_stock_frame.rowconfigure(0, weight=1)
        self.low_stock_list = tk.Listbox(low_stock_frame, font=("Consolas", 10))
        self.low_stock_list.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        top_sellers_frame = ttk.LabelFrame(parent, text="Top Selling Items")
        top_sellers_frame.grid(row=1, column=1, sticky="nsew", padx=8, pady=8)
        top_sellers_frame.columnconfigure(0, weight=1)
        top_sellers_frame.rowconfigure(0, weight=1)
        self.top_sellers_list = tk.Listbox(top_sellers_frame, font=("Consolas", 10))
        self.top_sellers_list.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        activity_frame = ttk.LabelFrame(parent, text="Recent Activity Log")
        activity_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=8, pady=8)
        activity_frame.columnconfigure(0, weight=1)
        activity_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)
        self.activity_list = tk.Listbox(activity_frame, font=("Consolas", 9))
        self.activity_list.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        btns = ttk.Frame(parent)
        btns.grid(row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
        ttk.Button(btns, text="Export Summary Report (.txt)", command=self._export_summary_report).pack(side="left")

    def refresh_reports_tab(self):
        currency = self.db.get_setting("currency_symbol", "$")
        threshold = safe_int(self.db.get_setting("low_stock_threshold", 20), 20)

        self.low_stock_list.delete(0, tk.END)
        low_items = self.db.low_stock_items(threshold)
        if low_items:
            for it in low_items:
                self.low_stock_list.insert(
                    tk.END, f"{it['name']:<25} qty={it['quantity']:<5} ({it['category_name'] or '—'})"
                )
        else:
            self.low_stock_list.insert(tk.END, "All items are sufficiently stocked.")

        self.top_sellers_list.delete(0, tk.END)
        for rank, it in enumerate(self.db.top_selling_items(limit=10), start=1):
            flag = " 🔥" if it["trending"] else ""
            self.top_sellers_list.insert(tk.END, f"{rank}. {it['name']:<25} sold={it['units_sold']}{flag}")

        self.activity_list.delete(0, tk.END)
        for act in self.db.get_recent_activity(limit=30):
            self.activity_list.insert(tk.END, f"[{act['timestamp']}] {act['username']}: {act['action']}")

    def _export_summary_report(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text file", "*.txt")])
        if not path:
            return
        currency = self.db.get_setting("currency_symbol", "$")
        threshold = safe_int(self.db.get_setting("low_stock_threshold", 20), 20)
        lines = [f"{APP_TITLE} — Summary Report", f"Generated: {now_str()}", ""]
        lines.append(f"Total items: {len(self.db.get_items())}")
        lines.append(f"Total stock value: {format_currency(self.db.total_stock_value(), currency)}")
        lines.append(f"Total revenue (all time): {format_currency(self.db.total_revenue(), currency)}")
        lines.append(f"Average customer rating: {self.db.average_rating_overall():.2f} / 5")
        lines.append("")
        lines.append(f"Low stock items (threshold={threshold}):")
        for it in self.db.low_stock_items(threshold):
            lines.append(f"  - {it['name']}: {it['quantity']} left")
        lines.append("")
        lines.append("Top selling items:")
        for it in self.db.top_selling_items(limit=10):
            lines.append(f"  - {it['name']}: {it['units_sold']} sold")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        messagebox.showinfo("Export complete", f"Summary report saved to:\n{path}")

    # ==========================================================================
    # SETTINGS TAB
    # ==========================================================================
    def _build_settings_tab(self, parent):
        parent.columnconfigure(0, weight=1)

        general = ttk.LabelFrame(parent, text="General Settings")
        general.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        for i in range(2):
            general.columnconfigure(i, weight=1)

        ttk.Label(general, text="Currency Symbol:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.settings_currency_var = tk.StringVar(value=self.db.get_setting("currency_symbol", "$"))
        ttk.Entry(general, textvariable=self.settings_currency_var, width=10).grid(
            row=0, column=1, sticky="w", padx=6, pady=6
        )

        ttk.Label(general, text="Low Stock Threshold:").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        self.settings_threshold_var = tk.StringVar(value=self.db.get_setting("low_stock_threshold", "20"))
        ttk.Entry(general, textvariable=self.settings_threshold_var, width=10).grid(
            row=1, column=1, sticky="w", padx=6, pady=6
        )

        ttk.Button(general, text="Save Settings", command=self._save_settings).grid(
            row=2, column=0, sticky="w", padx=6, pady=(4, 8)
        )

        account = ttk.LabelFrame(parent, text="Account")
        account.grid(row=1, column=0, sticky="ew", padx=8, pady=8)
        ttk.Label(account, text="Change your password:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.new_password_var = tk.StringVar()
        ttk.Entry(account, textvariable=self.new_password_var, show="*", width=24).grid(
            row=0, column=1, sticky="w", padx=6, pady=6
        )
        ttk.Button(account, text="Update Password", command=self._change_password).grid(
            row=0, column=2, sticky="w", padx=6, pady=6
        )

        if self.is_admin():
            admin_frame = ttk.LabelFrame(parent, text="Admin: User Management")
            admin_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=8)
            ttk.Label(admin_frame, text="New username:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
            self.new_user_var = tk.StringVar()
            ttk.Entry(admin_frame, textvariable=self.new_user_var, width=18).grid(row=0, column=1, padx=6)
            ttk.Label(admin_frame, text="Password:").grid(row=0, column=2, sticky="w", padx=6)
            self.new_user_pass_var = tk.StringVar()
            ttk.Entry(admin_frame, textvariable=self.new_user_pass_var, show="*", width=18).grid(row=0, column=3, padx=6)
            self.new_user_role_var = tk.StringVar(value="staff")
            ttk.Combobox(admin_frame, textvariable=self.new_user_role_var, state="readonly",
                         values=["staff", "admin"], width=10).grid(row=0, column=4, padx=6)
            ttk.Button(admin_frame, text="Create User", command=self._create_user).grid(row=0, column=5, padx=6)

    def _save_settings(self):
        self.db.set_setting("currency_symbol", self.settings_currency_var.get() or "$")
        self.db.set_setting("low_stock_threshold", safe_int(self.settings_threshold_var.get(), 20))
        messagebox.showinfo("Saved", "Settings updated.")
        self.refresh_everything()

    def _change_password(self):
        new_password = self.new_password_var.get()
        if len(new_password) < 4:
            messagebox.showerror("Invalid password", "Password must be at least 4 characters.")
            return
        self.db.change_password(self.current_user["username"], new_password)
        self.new_password_var.set("")
        messagebox.showinfo("Password updated", "Your password has been changed.")

    def _create_user(self):
        username = self.new_user_var.get().strip()
        password = self.new_user_pass_var.get()
        role = self.new_user_role_var.get()
        if not username or len(password) < 4:
            messagebox.showerror("Invalid input", "Username required and password must be at least 4 characters.")
            return
        try:
            self.db.add_user(username, password, role)
            self.db.log_activity(self.current_user["username"], f"Created new {role} user '{username}'")
            messagebox.showinfo("User created", f"User '{username}' created with role '{role}'.")
            self.new_user_var.set("")
            self.new_user_pass_var.set("")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "That username already exists.")


# ==============================================================================
# ENTRY POINT
# ==============================================================================
def main():
    app = DashboardApp()
    app.mainloop()


if __name__ == "__main__":
    main()