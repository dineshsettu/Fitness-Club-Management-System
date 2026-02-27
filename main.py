import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from tkcalendar import DateEntry

# ================= DATABASE =================
conn = sqlite3.connect("gym.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS members(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, age INTEGER, gender TEXT,
    plan TEXT, fees REAL, start_date TEXT,
    expiry TEXT, contact TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS payments(
    pid INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    amount REAL,
    pay_date TEXT,
    mode TEXT
)
""")
conn.commit()

# ================= LOGIN =================
def show_login():
    global login_win
    login_win = tk.Tk()
    login_win.title("Gym Login")
    login_win.geometry("300x220")
    login_win.configure(bg="#ecf0f1")

    global user_var, pass_var
    user_var = tk.StringVar()
    pass_var = tk.StringVar()

    tk.Label(login_win, text="Gym Management Login",
             font=("Segoe UI", 14, "bold"),
             bg="#ecf0f1").pack(pady=10)

    tk.Entry(login_win, textvariable=user_var).pack(pady=5)
    tk.Entry(login_win, textvariable=pass_var, show="*").pack(pady=5)
    tk.Button(login_win, text="Login", width=15,
              command=login).pack(pady=15)
    login_win.mainloop()

def login():
    if user_var.get() == "dinesh" and pass_var.get() == "sai@123":
        login_win.destroy()
        main_app()
    else:
        messagebox.showerror("Error", "Invalid credentials")

# ================= MAIN APP =================
def main_app():
    root = tk.Tk()
    root.title("Gym Management System")
    root.geometry("1400x700")
    root.configure(bg="#f4f6f9")

    style = ttk.Style()
    style.theme_use("clam")

    # ---------- VARIABLES ----------
    idv = tk.StringVar()
    namev = tk.StringVar()
    agev = tk.StringVar()
    genderv = tk.StringVar()
    planv = tk.StringVar()
    feesv = tk.StringVar()
    startv = tk.StringVar()
    expiryv = tk.StringVar()
    contactv = tk.StringVar()
    pay_mode = tk.StringVar(value="Cash")
    search_var = tk.StringVar()

    # ---------- DASHBOARD STATS ----------
    def get_dashboard_stats():
        today = datetime.now().strftime("%Y-%m-%d")
        total = cur.execute("SELECT COUNT(*) FROM members").fetchone()[0]
        active = cur.execute(
            "SELECT COUNT(*) FROM members WHERE expiry >= ?", (today,)
        ).fetchone()[0]
        expired = total - active
        revenue = cur.execute(
            "SELECT IFNULL(SUM(amount),0) FROM payments"
        ).fetchone()[0]
        return total, active, expired, revenue

    # ---------- MEMBER FUNCTIONS ----------
    def calculate_expiry(*args):
        try:
            start = datetime.strptime(startv.get(), "%Y-%m-%d")
        except ValueError:
            start = datetime.now()
        days_dict = {"Monthly":30, "Quarterly":90, "Yearly":365}
        days = days_dict.get(planv.get(), 30)
        expiry = start + timedelta(days=days)
        expiryv.set(expiry.strftime("%Y-%m-%d"))

    def add_member():
        if not startv.get():
            startv.set(datetime.now().strftime("%Y-%m-%d"))

        cur.execute("""
        INSERT INTO members(name, age, gender, plan, fees, start_date, expiry, contact)
        VALUES (?,?,?,?,?,?,?,?)
        """, (namev.get(), agev.get(), genderv.get(),
              planv.get(), feesv.get(), startv.get(),
              expiryv.get(), contactv.get()))
        conn.commit()

        member_id = cur.lastrowid

        # Record payment
        cur.execute("""
        INSERT INTO payments(member_id, amount, pay_date, mode)
        VALUES (?,?,?,?)
        """, (member_id, feesv.get(),
              datetime.now().strftime("%Y-%m-%d"), pay_mode.get()))
        conn.commit()

        load_members()
        refresh_cards()
        clear()
        check_expiry_alerts()

    def update_member():
        if not idv.get():
            messagebox.showerror("Error", "Select a member first")
            return
        confirm = messagebox.askyesno("Confirm Update", f"Are you sure you want to update member '{namev.get()}'?")
        if confirm:
            cur.execute("""
            UPDATE members SET name=?,age=?,gender=?,plan=?,fees=?,start_date=?,expiry=?,contact=?
            WHERE id=?
            """, (namev.get(), agev.get(), genderv.get(),
                  planv.get(), feesv.get(), startv.get(),
                  expiryv.get(), contactv.get(), idv.get()))
            conn.commit()
            load_members()
            refresh_cards()
            check_expiry_alerts()

    def delete_member():
        if not idv.get():
            messagebox.showerror("Error", "Select a member first")
            return
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete member '{namev.get()}'?")
        if confirm:
            cur.execute("DELETE FROM members WHERE id=?", (idv.get(),))
            conn.commit()
            load_members()
            refresh_cards()
            clear()

    def clear():
        for v in [idv,namev,agev,genderv,planv,feesv,startv,expiryv,contactv]:
            v.set("")

    # ---------- INVOICE ----------
    def generate_invoice():
        if not idv.get():
            messagebox.showerror("Error", "Select a member first")
            return
        inv = tk.Toplevel(root)
        inv.title("Invoice")
        inv.geometry("350x420")
        text = tk.Text(inv)
        text.pack(fill="both", expand=True)

        invoice = f"""
        XYZ GYM
        ----------------------------
        Member ID: {idv.get()}
        Name: {namev.get()}
        Plan: {planv.get()}
        Fees: ₱{feesv.get()}
        Payment Mode: {pay_mode.get()}
        Start Date: {startv.get()}
        Expiry Date: {expiryv.get()}
        Date: {datetime.now().strftime('%Y-%m-%d')}
        ----------------------------
        Thank you for joining!
        """
        text.insert("1.0", invoice)

    # ---------- RENEW MEMBERSHIP ----------
    def renew_membership():
        if not idv.get():
            messagebox.showerror("Error", "Select a member first")
            return

        today = datetime.now().date()
        expiry_date = datetime.strptime(expiryv.get(), "%Y-%m-%d").date()
        if expiry_date >= today:
            messagebox.showinfo("Info", "Membership is still active. Can only renew expired memberships.")
            return

        new_plan = planv.get()
        if new_plan not in ["Monthly","Quarterly","Yearly"]:
            messagebox.showerror("Error", "Select a valid plan to renew")
            return

        start_date = datetime.now().strftime("%Y-%m-%d")
        days_dict = {"Monthly":30, "Quarterly":90, "Yearly":365}
        new_expiry = (datetime.now() + timedelta(days=days_dict[new_plan])).strftime("%Y-%m-%d")

        # Update member
        cur.execute("""
        UPDATE members SET plan=?, start_date=?, expiry=? WHERE id=?
        """, (new_plan, start_date, new_expiry, idv.get()))
        conn.commit()

        # Record payment
        cur.execute("""
        INSERT INTO payments(member_id, amount, pay_date, mode)
        VALUES (?,?,?,?)
        """, (idv.get(), feesv.get(), start_date, pay_mode.get()))
        conn.commit()

        messagebox.showinfo("Success", "Membership renewed successfully")
        load_members()
        refresh_cards()
        check_expiry_alerts()

    # ---------- LOGOUT ----------
    def logout():
        if messagebox.askyesno("Logout", "Do you want to logout?"):
            root.destroy()
            show_login()

    # ---------- EXPIRY ALERTS ----------
    def check_expiry_alerts():
        today = datetime.now().date()
        alert_list = []
        for row in cur.execute("SELECT name, expiry FROM members"):
            expiry_date = datetime.strptime(row[1], "%Y-%m-%d").date()
            days_left = (expiry_date - today).days
            if 0 <= days_left <= 7:
                alert_list.append(f"{row[0]} ({days_left} days left)")
        if alert_list:
            messagebox.showwarning(
                "Membership Expiry Alert",
                "Following members are about to expire:\n" + "\n".join(alert_list)
            )

    # ---------- SEARCH FUNCTION ----------
    def search_member(*args):
        query = search_var.get().lower()
        tree.delete(*tree.get_children())
        today = datetime.now().date()
        for row in cur.execute("SELECT * FROM members"):
            # Filter by search text
            if (query in str(row[0]).lower() or query in row[1].lower() or 
                query in row[4].lower() or query in row[8].lower()):
                expiry_date = datetime.strptime(row[7], "%Y-%m-%d").date()
                days_left = (expiry_date - today).days
                item_id = tree.insert("", tk.END, values=row)
                if days_left < 0:
                    tree.item(item_id, tags=('expired',))
                elif days_left <= 7:
                    tree.item(item_id, tags=('expiring',))
        tree.tag_configure('expired', background='lightgray')
        tree.tag_configure('expiring', background='orange')

    # ================= UI =================
    header = tk.Frame(root, bg="#2c3e50", height=60)
    header.pack(fill="x")
    tk.Label(header, text="🏋️ Gym Management System",
             fg="white", bg="#2c3e50",
             font=("Segoe UI", 20, "bold")).pack(side="left", padx=20)
    ttk.Button(header, text="Logout", command=logout).pack(side="right", padx=20)

    # ---------- DASHBOARD CARDS ----------
    cards_frame = tk.Frame(root, bg="#f4f6f9")
    cards_frame.pack(fill="x", padx=20, pady=10)
    card_labels = []
    def create_card(title, icon, color):
        frame = tk.Frame(cards_frame, bg=color, width=180, height=100)  # card size
        frame.pack(side="left", padx=8)
        frame.pack_propagate(False)

    # Title on top
        tk.Label(frame, text=title, font=("Segoe UI", 10, "bold"), bg=color, fg="white").pack(anchor="w", padx=10, pady=(8,0))
    # Value in middle
        value = tk.Label(frame, text="0", font=("Segoe UI", 18, "bold"), bg=color, fg="white")
        value.pack(anchor="w", padx=10, pady=(5,0))
    # Icon on right-top
        tk.Label(frame, text=icon, font=("Segoe UI", 22), bg=color, fg="white").place(relx=0.70, rely=0.1)

        return value



    card_labels.append(create_card("Total Members", "👥", "#3498db"))
    card_labels.append(create_card("Active Members", "✅", "#2ecc71"))
    card_labels.append(create_card("Expired Members", "❌", "#e74c3c"))
    card_labels.append(create_card("Revenue", "💰", "#f39c12"))

    def refresh_cards():
        total, active, expired, revenue = get_dashboard_stats()
        values = [total, active, expired, f"₱{revenue}"]
        for lbl, val in zip(card_labels, values):
            lbl.config(text=val)

    # ---------- MAIN CONTENT ----------
    content = tk.Frame(root, bg="#f4f6f9")
    content.pack(fill="both", expand=True, padx=20, pady=10)

    # ---------- LEFT FORM ----------
    left = tk.LabelFrame(content, text=" Member Details ",
                         font=("Segoe UI", 11, "bold"),
                         bg="#f4f6f9", padx=15, pady=15)
    left.pack(side="left", fill="y")

    tk.Label(left, text="Name", bg="#f4f6f9").grid(row=0, column=0, sticky="w", pady=5)
    ttk.Entry(left, textvariable=namev, width=25).grid(row=0, column=1, pady=5)
    tk.Label(left, text="Age", bg="#f4f6f9").grid(row=1, column=0, sticky="w", pady=5)
    ttk.Entry(left, textvariable=agev, width=25).grid(row=1, column=1, pady=5)
    tk.Label(left, text="Gender", bg="#f4f6f9").grid(row=2, column=0, sticky="w", pady=5)
    ttk.Combobox(left, textvariable=genderv, values=["Male","Female"], state="readonly", width=23).grid(row=2,column=1,pady=5)
    tk.Label(left, text="Plan", bg="#f4f6f9").grid(row=3,column=0,sticky="w",pady=5)
    plan_combobox = ttk.Combobox(left, textvariable=planv, values=["Monthly","Quarterly","Yearly"], width=23)
    plan_combobox.grid(row=3,column=1,pady=5)
    plan_combobox.bind("<<ComboboxSelected>>", calculate_expiry)
    tk.Label(left, text="Fees", bg="#f4f6f9").grid(row=4,column=0,sticky="w",pady=5)
    ttk.Entry(left, textvariable=feesv, width=25).grid(row=4,column=1,pady=5)
    tk.Label(left, text="Expiry", bg="#f4f6f9").grid(row=5,column=0,sticky="w",pady=5)
    expiry_entry = DateEntry(left, textvariable=expiryv, width=22, state="readonly", date_pattern="yyyy-mm-dd")
    expiry_entry.grid(row=5,column=1,pady=5)
    tk.Label(left, text="Contact", bg="#f4f6f9").grid(row=6,column=0,sticky="w",pady=5)
    ttk.Entry(left, textvariable=contactv, width=25).grid(row=6,column=1,pady=5)
    tk.Label(left, text="Payment Mode", bg="#f4f6f9").grid(row=7,column=0,sticky="w",pady=5)
    ttk.Combobox(left, textvariable=pay_mode, values=["Cash","Card","UPI"], width=23).grid(row=7,column=1,pady=5)
    tk.Label(left, text="Start Date", bg="#f4f6f9").grid(row=8,column=0,sticky="w",pady=5)
    start_entry = DateEntry(left, textvariable=startv, width=22, date_pattern="yyyy-mm-dd")
    start_entry.grid(row=8,column=1,pady=5)
    startv.trace_add("write", calculate_expiry)

    ttk.Button(left, text="Add Member", command=add_member).grid(row=9,column=0,pady=10)
    ttk.Button(left, text="Update", command=update_member).grid(row=9,column=1)
    ttk.Button(left, text="Delete", command=delete_member).grid(row=10,column=0)
    ttk.Button(left, text="Invoice", command=generate_invoice).grid(row=10,column=1)
    ttk.Button(left, text="Renew Membership", command=renew_membership).grid(row=11,column=0,columnspan=2, pady=10)

    # ---------- RIGHT TABLE WITH SEARCH & SCROLLBARS ----------
    right = tk.LabelFrame(content, text=" Members List ",
                          font=("Segoe UI", 11, "bold"),
                          bg="#f4f6f9", padx=10, pady=10)
    right.pack(side="right", fill="both", expand=True)

    tk.Label(right, text="Search:", bg="#f4f6f9").grid(row=0,column=0,sticky="w", padx=5)
    search_entry = ttk.Entry(right, textvariable=search_var)
    search_entry.grid(row=0,column=1,sticky="we", padx=5)
    search_var.trace_add("write", search_member)

    cols = ("ID","Name","Age","Gender","Plan","Fees","Start Date","Expiry","Contact")
    tree = ttk.Treeview(right, columns=cols, show="headings")
    v_scroll = ttk.Scrollbar(right, orient="vertical", command=tree.yview)
    h_scroll = ttk.Scrollbar(right, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
    tree.grid(row=1, column=0, columnspan=2, sticky="nsew")
    v_scroll.grid(row=1, column=2, sticky="ns")
    h_scroll.grid(row=2, column=0, columnspan=2, sticky="ew")
    right.grid_rowconfigure(1, weight=1)
    right.grid_columnconfigure(1, weight=1)
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=120, anchor="center")

    def load_members():
        tree.delete(*tree.get_children())
        today = datetime.now().date()
        for row in cur.execute("SELECT * FROM members"):
            expiry_date = datetime.strptime(row[7], "%Y-%m-%d").date()
            days_left = (expiry_date - today).days
            item_id = tree.insert("", tk.END, values=row)
            if days_left < 0:
                tree.item(item_id, tags=('expired',))
            elif days_left <= 7:
                tree.item(item_id, tags=('expiring',))
        tree.tag_configure('expired', background='lightgray')
        tree.tag_configure('expiring', background='orange')

    def select(event):
        data = tree.item(tree.focus(),"values")
        if data:
            idv.set(data[0])
            namev.set(data[1])
            agev.set(data[2])
            genderv.set(data[3])
            planv.set(data[4])
            feesv.set(data[5])
            startv.set(data[6])
            expiryv.set(data[7])
            contactv.set(data[8])

    tree.bind("<ButtonRelease-1>", select)

    # ---------- INITIAL LOAD ----------
    load_members()
    refresh_cards()
    check_expiry_alerts()
    root.mainloop()

# Start the login
show_login()
