"""
STADIUM TICKET MANAGER
Python: Tkinter GUI + application logic
Database: MySQL (all persistent data is stored in SQL)

Before running:
1. Install MySQL Server and start it.
2. Run stadium_booking_setup.sql in MySQL.
3. Install connector: pip install mysql-connector-python
4. Update DB_CONFIG below with your MySQL credentials.
5. Run: python stadium_ticket_manager.py
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error


# -------------------- DATABASE CONFIGURATION --------------------
# You can override these values with environment variables.
DB_CONFIG = {
    "host": os.getenv("STADIUM_DB_HOST", "localhost"),
    "user": os.getenv("STADIUM_DB_USER", "root"),
    "password": os.getenv("STADIUM_DB_PASSWORD", "1234"),
    "database": os.getenv("STADIUM_DB_NAME", "stadium_booking"),
}


def connect_db():
    """Open a MySQL connection. Returns None if the connection fails."""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as exc:
        messagebox.showerror(
            "Database connection failed",
            "Could not connect to MySQL.\n\n"
            "Check that MySQL is running, the database setup SQL has been run, "
            "and DB_CONFIG contains the correct username/password.\n\n"
            f"Details: {exc}",
        )
        return None


# -------------------- APPLICATION --------------------
class StadiumBookingApp:
    BG = "#0B1220"
    PANEL = "#121D30"
    PANEL_LIGHT = "#1B2A41"
    TEXT = "#F4F7FB"
    MUTED = "#9DAEC4"
    TEAL = "#25D0B1"
    GOLD = "#FFC857"
    RED = "#FF647C"
    BLUE = "#66A6FF"

    TICKET_TYPES = {
        "VIP": 150.00,
        "Premium": 90.00,
        "Standard": 40.00,
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Stadium Ticket Manager")
        self.root.geometry("1120x740")
        self.root.minsize(900, 620)
        self.root.configure(bg=self.BG)

        self.animation_step = 0
        self._setup_style()
        self._build_ui()
        self.refresh_tickets()
        self._animate_header()

    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Treeview",
            background=self.PANEL,
            fieldbackground=self.PANEL,
            foreground=self.TEXT,
            rowheight=34,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Treeview.Heading",
            background=self.PANEL_LIGHT,
            foreground=self.TEAL,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padding=(8, 10),
        )
        style.map(
            "Treeview",
            background=[("selected", "#244B5B")],
            foreground=[("selected", "#FFFFFF")],
        )
        style.configure(
            "TCombobox",
            fieldbackground="#EAF0F7",
            background="#EAF0F7",
            foreground="#142033",
            padding=7,
        )
        style.configure("Vertical.TScrollbar", background=self.PANEL_LIGHT)

    def _build_ui(self):
        # Header with a custom animated ticket mark.
        header = tk.Frame(self.root, bg="#101D31", padx=24, pady=18)
        header.pack(fill="x")

        logo_area = tk.Frame(header, bg="#101D31")
        logo_area.pack(side="left")

        self.logo_canvas = tk.Canvas(
            logo_area, width=58, height=58, bg="#101D31",
            highlightthickness=0
        )
        self.logo_canvas.pack(side="left", padx=(0, 14))
        self._draw_ticket_logo()

        title_area = tk.Frame(logo_area, bg="#101D31")
        title_area.pack(side="left", anchor="center")
        tk.Label(
            title_area, text="STADIUM", bg="#101D31", fg=self.TEXT,
            font=("Segoe UI", 22, "bold")
        ).pack(anchor="w")
        tk.Label(
            title_area, text="TICKET MANAGER  •  BOOKING CONTROL",
            bg="#101D31", fg=self.MUTED, font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=(2, 0))

        self.header_status = tk.Label(
            header, text="●  SYSTEM READY", bg="#101D31", fg=self.TEAL,
            font=("Segoe UI", 10, "bold")
        )
        self.header_status.pack(side="right", anchor="center")

        # Thin animated accent line.
        self.accent = tk.Canvas(
            self.root, height=4, bg=self.PANEL, highlightthickness=0
        )
        self.accent.pack(fill="x")
        self.accent.bind("<Configure>", lambda _event: self._draw_accent())

        # Main content.
        body = tk.Frame(self.root, bg=self.BG, padx=20, pady=18)
        body.pack(fill="both", expand=True)

        # Left form panel.
        form = tk.Frame(body, bg=self.PANEL, padx=20, pady=20)
        form.pack(side="left", fill="y", padx=(0, 16))
        form.configure(width=300)
        form.pack_propagate(False)

        tk.Label(
            form, text="NEW BOOKING", bg=self.PANEL, fg=self.TEXT,
            font=("Segoe UI", 15, "bold")
        ).pack(anchor="w")
        tk.Label(
            form, text="Fill in the match-day details",
            bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(4, 20))

        self.name_var = tk.StringVar()
        self.match_var = tk.StringVar()
        self.seat_var = tk.StringVar()
        self.type_var = tk.StringVar(value="Standard")

        self._field_label(form, "CUSTOMER NAME")
        self.name_entry = self._entry(form, self.name_var, "e.g. Alex Thomas")
        self._field_label(form, "MATCH / EVENT")
        self.match_entry = self._entry(form, self.match_var, "e.g. City vs United")
        self._field_label(form, "SEAT NUMBER")
        self.seat_entry = self._entry(form, self.seat_var, "A1, B4, F10 ...")

        self._field_label(form, "TICKET CATEGORY")
        self.type_combo = ttk.Combobox(
            form, textvariable=self.type_var,
            values=list(self.TICKET_TYPES.keys()), state="readonly"
        )
        self.type_combo.pack(fill="x", ipady=3, pady=(0, 8))
        self.type_combo.bind("<<ComboboxSelected>>", self._update_price)

        self.price_card = tk.Frame(form, bg="#1A3547", padx=13, pady=12)
        self.price_card.pack(fill="x", pady=(10, 18))
        tk.Label(
            self.price_card, text="TICKET PRICE", bg="#1A3547", fg=self.MUTED,
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")
        self.price_label = tk.Label(
            self.price_card, text="₹40.00", bg="#1A3547", fg=self.GOLD,
            font=("Segoe UI", 22, "bold")
        )
        self.price_label.pack(anchor="w", pady=(2, 0))

        self.book_button = tk.Button(
            form, text="🎟  BOOK TICKET", command=self.book_ticket,
            bg=self.TEAL, fg="#06151A", activebackground="#61E5CE",
            activeforeground="#06151A", relief="flat", bd=0,
            font=("Segoe UI", 10, "bold"), cursor="hand2", pady=12
        )
        self.book_button.pack(fill="x", pady=(0, 9))
        self.clear_button = tk.Button(
            form, text="↺  CLEAR FORM", command=self.clear_form,
            bg=self.PANEL_LIGHT, fg=self.TEXT, activebackground="#2A3B54",
            activeforeground=self.TEXT, relief="flat", bd=0,
            font=("Segoe UI", 10, "bold"), cursor="hand2", pady=10
        )
        self.clear_button.pack(fill="x")

        tk.Label(
            form, text="Seats accepted: A1–A10, B1–B10,\nC1–C10, D1–D10 and F1–F10",
            bg=self.PANEL, fg=self.MUTED, justify="left",
            font=("Segoe UI", 8)
        ).pack(anchor="w", side="bottom", pady=(16, 0))

        # Right panel: overview and table.
        right = tk.Frame(body, bg=self.BG)
        right.pack(side="left", fill="both", expand=True)

        stats = tk.Frame(right, bg=self.BG)
        stats.pack(fill="x", pady=(0, 14))
        self._stat_card(stats, "TOTAL BOOKINGS", "0", self.total_value)
        self._stat_card(stats, "VIP BOOKINGS", "0", self.vip_value)
        self._stat_card(stats, "REVENUE", "₹0.00", self.revenue_value)

        list_panel = tk.Frame(right, bg=self.PANEL, padx=14, pady=14)
        list_panel.pack(fill="both", expand=True)

        toolbar = tk.Frame(list_panel, bg=self.PANEL)
        toolbar.pack(fill="x", pady=(0, 12))
        tk.Label(
            toolbar, text="BOOKED TICKETS", bg=self.PANEL, fg=self.TEXT,
            font=("Segoe UI", 14, "bold")
        ).pack(side="left")
        self.search_var = tk.StringVar()
        search = tk.Entry(
            toolbar, textvariable=self.search_var, width=22,
            bg="#EAF0F7", fg="#142033", insertbackground="#142033",
            relief="flat", font=("Segoe UI", 10)
        )
        search.pack(side="right", ipady=7, padx=(8, 0))
        search.insert(0, "")
        search.bind("<KeyRelease>", lambda _event: self._filter_rows())
        tk.Label(
            toolbar, text="Search:", bg=self.PANEL, fg=self.MUTED,
            font=("Segoe UI", 9)
        ).pack(side="right")

        table_frame = tk.Frame(list_panel, bg=self.PANEL)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "customer", "match", "seat", "type", "price")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", selectmode="browse"
        )
        headings = {
            "id": ("ID", 55, "center"),
            "customer": ("CUSTOMER", 150, "w"),
            "match": ("MATCH / EVENT", 170, "w"),
            "seat": ("SEAT", 70, "center"),
            "type": ("CATEGORY", 95, "center"),
            "price": ("PRICE", 95, "e"),
        }
        for key, (label, width, anchor) in headings.items():
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, minwidth=45, anchor=anchor)

        scroll = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.tag_configure("even", background="#142137")
        self.tree.tag_configure("odd", background="#101B2D")

        actions = tk.Frame(list_panel, bg=self.PANEL)
        actions.pack(fill="x", pady=(13, 0))
        self._action_button(
            actions, "⟳  REFRESH", self.refresh_tickets,
            bg="#233A55", fg=self.TEXT
        ).pack(side="left", padx=(0, 8))
        self._action_button(
            actions, "✕  CANCEL SELECTED TICKET", self.cancel_ticket,
            bg="#492536", fg="#FFB4C0"
        ).pack(side="left")
        tk.Label(
            actions, text="Select a row before cancelling",
            bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 8)
        ).pack(side="right", padx=(6, 0))

        # Bottom status bar.
        self.status_var = tk.StringVar(value="Ready. Connect to MySQL to manage bookings.")
        footer = tk.Label(
            self.root, textvariable=self.status_var, anchor="w",
            bg="#101D31", fg=self.MUTED, padx=20, pady=8,
            font=("Segoe UI", 9)
        )
        footer.pack(fill="x")

    def _draw_ticket_logo(self):
        self.logo_canvas.delete("all")
        # Rounded ticket-style logo, with animated accent dot.
        self.logo_canvas.create_rectangle(
            5, 10, 53, 48, fill="#173D4A", outline=self.TEAL, width=2
        )
        self.logo_canvas.create_line(
            29, 12, 29, 46, fill=self.TEAL, width=2, dash=(3, 3)
        )
        self.logo_canvas.create_text(
            17, 29, text="★", fill=self.GOLD, font=("Segoe UI Symbol", 15, "bold")
        )
        pulse = self.TEAL if self.animation_step % 2 == 0 else self.GOLD
        self.logo_canvas.create_oval(
            44, 5, 54, 15, fill=pulse, outline="#101D31", width=2
        )

    def _draw_accent(self):
        self.accent.delete("all")
        width = max(self.accent.winfo_width(), 1)
        marker = (self.animation_step * 9) % max(width, 1)
        self.accent.create_rectangle(0, 0, width, 4, fill="#1B2A41", outline="")
        self.accent.create_rectangle(
            max(0, marker - 70), 0, min(width, marker + 70), 4,
            fill=self.TEAL, outline=""
        )

    def _animate_header(self):
        self.animation_step += 1
        if self.root.winfo_exists():
            self._draw_ticket_logo()
            self._draw_accent()
            self.root.after(180, self._animate_header)

    def _field_label(self, parent, text):
        tk.Label(
            parent, text=text, bg=self.PANEL, fg=self.MUTED,
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", pady=(0, 6))

    def _entry(self, parent, variable, placeholder):
        entry = tk.Entry(
            parent, textvariable=variable, bg="#EAF0F7", fg="#142033",
            insertbackground="#142033", relief="flat", bd=0,
            font=("Segoe UI", 10)
        )
        entry.pack(fill="x", ipady=9, pady=(0, 15))
        entry.bind("<FocusIn>", lambda _e: entry.configure(highlightthickness=2,
                                                           highlightbackground=self.TEAL))
        entry.bind("<FocusOut>", lambda _e: entry.configure(highlightthickness=0))
        return entry

    def _stat_card(self, parent, title, initial, variable):
        card = tk.Frame(parent, bg=self.PANEL, padx=14, pady=12)
        card.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(
            card, text=title, bg=self.PANEL, fg=self.MUTED,
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")
        tk.Label(
            card, textvariable=variable, bg=self.PANEL, fg=self.TEXT,
            font=("Segoe UI", 18, "bold")
        ).pack(anchor="w", pady=(4, 0))

    def _action_button(self, parent, text, command, bg, fg):
        return tk.Button(
            parent, text=text, command=command, bg=bg, fg=fg,
            activebackground=bg, activeforeground=fg, relief="flat", bd=0,
            font=("Segoe UI", 9, "bold"), cursor="hand2", padx=12, pady=9
        )

    def _update_price(self, _event=None):
        price = self.TICKET_TYPES.get(self.type_var.get(), 40.0)
        self.price_label.configure(text=f"₹{price:.2f}")

    def clear_form(self):
        self.name_var.set("")
        self.match_var.set("")
        self.seat_var.set("")
        self.type_var.set("Standard")
        self._update_price()
        self.name_entry.focus_set()
        self.status_var.set("Form cleared.")
        self.header_status.configure(text="●  READY", fg=self.TEAL)

    @staticmethod
    def _valid_seat(seat):
        import re
        return re.fullmatch(r"[ABCDF](?:[1-9]|10)", seat) is not None

    def book_ticket(self):
        customer = self.name_var.get().strip()
        match = self.match_var.get().strip()
        seat = self.seat_var.get().strip().upper()
        category = self.type_var.get()

        if not customer or not match or not seat:
            messagebox.showwarning(
                "Missing information",
                "Please enter the customer name, match/event, and seat number."
            )
            return
        if not self._valid_seat(seat):
            messagebox.showerror(
                "Invalid seat",
                "Use one of these seat formats: A1–A10, B1–B10, C1–C10, "
                "D1–D10, or F1–F10."
            )
            return
        if category not in self.TICKET_TYPES:
            messagebox.showerror("Invalid category", "Choose a valid ticket category.")
            return

        price = self.TICKET_TYPES[category]
        conn = connect_db()
        if conn is None:
            return
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO tickets
                   (customer_name, match_name, seat_number, ticket_type, price)
                   VALUES (%s, %s, %s, %s, %s)""",
                (customer, match, seat, category, price),
            )
            conn.commit()
            self.status_var.set(f"Ticket booked for {customer} — seat {seat}.")
            self.header_status.configure(text="●  BOOKING SAVED", fg=self.TEAL)
            messagebox.showinfo(
                "Booking successful",
                f"Ticket booked successfully!\n\n"
                f"Customer: {customer}\nMatch: {match}\n"
                f"Seat: {seat}\nCategory: {category}\nPrice: ₹{price:.2f}"
            )
            self.clear_form()
            self.refresh_tickets()
        except Error as exc:
            conn.rollback()
            if getattr(exc, "errno", None) == 1062:
                messagebox.showerror(
                    "Seat already booked",
                    f"Seat {seat} is already booked for this match/event."
                )
            else:
                messagebox.showerror("Booking error", f"Could not book ticket:\n{exc}")
        finally:
            if cursor is not None:
                cursor.close()
            conn.close()

    def refresh_tickets(self):
        conn = connect_db()
        if conn is None:
            return
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT ticket_id, customer_name, match_name,
                          seat_number, ticket_type, price
                   FROM tickets ORDER BY ticket_id DESC"""
            )
            self.all_rows = cursor.fetchall()
            self._filter_rows()
            self._update_stats()
            self.status_var.set(f"Loaded {len(self.all_rows)} booking(s) from MySQL.")
            self.header_status.configure(text="●  DATABASE CONNECTED", fg=self.TEAL)
        except Error as exc:
            messagebox.showerror("Load error", f"Could not load tickets:\n{exc}")
        finally:
            if cursor is not None:
                cursor.close()
            conn.close()

    def _filter_rows(self):
        if not hasattr(self, "tree"):
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        query = self.search_var.get().strip().casefold() if hasattr(self, "search_var") else ""
        rows = getattr(self, "all_rows", [])
        visible = []
        for row in rows:
            searchable = " ".join(str(value) for value in row).casefold()
            if query in searchable:
                visible.append(row)
        for index, row in enumerate(visible):
            price = f"₹{float(row[5]):.2f}"
            self.tree.insert(
                "", "end",
                values=(row[0], row[1], row[2], row[3], row[4], price),
                tags=("even" if index % 2 == 0 else "odd",)
            )

    def _update_stats(self):
        rows = getattr(self, "all_rows", [])
        self.total_value.set(str(len(rows)))
        self.vip_value.set(str(sum(1 for row in rows if row[4] == "VIP")))
        revenue = sum(float(row[5]) for row in rows)
        self.revenue_value.set(f"₹{revenue:,.2f}")

    def cancel_ticket(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning(
                "No ticket selected",
                "Select a ticket in the table first, then press Cancel Selected Ticket."
            )
            return

        values = self.tree.item(selection[0], "values")
        ticket_id, customer, match, seat = values[0], values[1], values[2], values[3]
        confirm = messagebox.askyesno(
            "Confirm ticket cancellation",
            f"Cancel this booking?\n\nCustomer: {customer}\nMatch: {match}\n"
            f"Seat: {seat}\nTicket ID: {ticket_id}\n\n"
            "This will permanently delete the booking record."
        )
        if not confirm:
            self.status_var.set("Cancellation aborted.")
            return

        conn = connect_db()
        if conn is None:
            return
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tickets WHERE ticket_id = %s", (ticket_id,))
            conn.commit()
            if cursor.rowcount:
                messagebox.showinfo(
                    "Ticket cancelled",
                    f"Booking {ticket_id} for seat {seat} has been cancelled."
                )
                self.status_var.set(f"Ticket {ticket_id} cancelled.")
            else:
                messagebox.showwarning(
                    "Ticket not found",
                    "This ticket may already have been cancelled. Refresh the list."
                )
            self.refresh_tickets()
        except Error as exc:
            conn.rollback()
            messagebox.showerror("Cancellation error", f"Could not cancel ticket:\n{exc}")
        finally:
            if cursor is not None:
                cursor.close()
            conn.close()


if __name__ == "__main__":
    root = tk.Tk()
    # Use a modern default font when available.
    try:
        root.option_add("*Font", "Segoe UI 10")
    except tk.TclError:
        pass
    app = StadiumBookingApp(root)
    root.mainloop()
