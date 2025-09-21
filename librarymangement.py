"""
Library Management System (Tkinter + MySQL)
- Separate pages (frames): Home, Students, Books, Issue/Return
- Uses PyMySQL for DB access
- Edit DB credentials under DB_CONFIG before running
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
from datetime import datetime, date

# ------------------------ CONFIG ------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",       # <-- change this
    "password": "password",   # <-- change this
    "database": "library_db"      # database name (will be created if missing)
}

# ------------------------ DATABASE HELPERS ------------------------
def connect_db(create_db_if_missing=True):
    """Return a new DB connection. Creates database if missing (optional)."""
    # Connect without specifying DB first if creation may be needed
    try:
        conn = pymysql.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG.get("database", None),
            autocommit=True
        )
        return conn
    except pymysql.err.OperationalError as e:
        # Try to create database if missing and credentials allow
        if create_db_if_missing and ("Unknown database" in str(e) or "1049" in str(e)):
            tmp = pymysql.connect(host=DB_CONFIG["host"],
                                  user=DB_CONFIG["user"],
                                  password=DB_CONFIG["password"],
                                  autocommit=True)
            cur = tmp.cursor()
            cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            tmp.close()
            # reconnect with DB
            conn = pymysql.connect(
                host=DB_CONFIG["host"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                database=DB_CONFIG["database"],
                autocommit=True
            )
            return conn
        raise

def init_db():
    """Create necessary tables if they don't exist."""
    conn = connect_db()
    cur = conn.cursor()
    # students
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        age INT,
        course VARCHAR(100),
        year INT
    ) ENGINE=InnoDB;
    """)
    # books
    cur.execute("""
    CREATE TABLE IF NOT EXISTS books (
        book_id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        author VARCHAR(150),
        pub_year INT,
        status VARCHAR(20) DEFAULT 'Available'
    ) ENGINE=InnoDB;
    """)
    # issued_books
    cur.execute("""
    CREATE TABLE IF NOT EXISTS issued_books (
        issue_id INT AUTO_INCREMENT PRIMARY KEY,
        student_id INT,
        book_id INT,
        issue_date DATE,
        return_date DATE NULL,
        FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
        FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE
    ) ENGINE=InnoDB;
    """)
    conn.close()

# ------------------------ APPLICATION ------------------------
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Library Management System")
        self.geometry("1000x650")
        self.resizable(False, False)

        # container for pages
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # initialize DB
        try:
            init_db()
        except Exception as e:
            messagebox.showerror("Database error", f"Failed to initialize DB:\n{e}")
            self.destroy()
            return

        # frames
        self.frames = {}
        for F in (HomePage, StudentPage, BookPage, IssuePage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("HomePage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        # call on_show if exists (so page can refresh data)
        if hasattr(frame, "on_show"):
            try:
                frame.on_show()
            except Exception as e:
                print("on_show error:", e)
        frame.tkraise()

# ------------------------ PAGES ------------------------
class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        title = tk.Label(self, text="📚 Library Management System", font=("Helvetica", 28))
        title.pack(pady=30)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Manage Students", width=25,
                   command=lambda: controller.show_frame("StudentPage")).grid(row=0, column=0, padx=10, pady=10)
        ttk.Button(btn_frame, text="Manage Books", width=25,
                   command=lambda: controller.show_frame("BookPage")).grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(btn_frame, text="Issue / Return Books", width=25,
                   command=lambda: controller.show_frame("IssuePage")).grid(row=0, column=2, padx=10, pady=10)

        # Simple stats
        self.stats_frame = tk.Frame(self, bd=1, relief=tk.RIDGE, padx=20, pady=20)
        self.stats_frame.pack(pady=20)

        self.total_students_label = tk.Label(self.stats_frame, text="Total Students: -", font=("Arial", 14))
        self.total_books_label = tk.Label(self.stats_frame, text="Total Books: -", font=("Arial", 14))
        self.issued_books_label = tk.Label(self.stats_frame, text="Currently Issued: -", font=("Arial", 14))

        self.total_students_label.pack(anchor="w")
        self.total_books_label.pack(anchor="w")
        self.issued_books_label.pack(anchor="w")

    def on_show(self):
        # refresh stats
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM students")
        tot_students = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM books")
        tot_books = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM issued_books WHERE return_date IS NULL")
        tot_issued = cur.fetchone()[0]
        conn.close()

        self.total_students_label.config(text=f"Total Students: {tot_students}")
        self.total_books_label.config(text=f"Total Books: {tot_books}")
        self.issued_books_label.config(text=f"Currently Issued: {tot_issued}")

class StudentPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        header = tk.Frame(self)
        header.pack(fill="x", pady=6)
        ttk.Button(header, text="⬅ Back", command=lambda: controller.show_frame("HomePage")).pack(side="left", padx=8)
        tk.Label(header, text="Manage Students", font=("Arial", 20)).pack(side="left", padx=14)

        # Left form
        form = tk.Frame(self, padx=10, pady=10)
        form.pack(side="left", fill="y")

        tk.Label(form, text="Name *").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar()
        tk.Entry(form, textvariable=self.name_var, width=30).grid(row=0, column=1, pady=4)

        tk.Label(form, text="Age").grid(row=1, column=0, sticky="w")
        self.age_var = tk.StringVar()
        tk.Entry(form, textvariable=self.age_var, width=30).grid(row=1, column=1, pady=4)

        tk.Label(form, text="Course").grid(row=2, column=0, sticky="w")
        self.course_var = tk.StringVar()
        tk.Entry(form, textvariable=self.course_var, width=30).grid(row=2, column=1, pady=4)

        tk.Label(form, text="Year").grid(row=3, column=0, sticky="w")
        self.year_var = tk.StringVar()
        tk.Entry(form, textvariable=self.year_var, width=30).grid(row=3, column=1, pady=4)

        btn_frame = tk.Frame(form, pady=10)
        btn_frame.grid(row=4, column=0, columnspan=2)

        ttk.Button(btn_frame, text="Add Student", command=self.add_student).grid(row=0, column=0, padx=4)
        ttk.Button(btn_frame, text="Update Student", command=self.update_student).grid(row=0, column=1, padx=4)
        ttk.Button(btn_frame, text="Delete Student", command=self.delete_student).grid(row=0, column=2, padx=4)
        ttk.Button(btn_frame, text="Clear", command=self.clear_fields).grid(row=0, column=3, padx=4)

        # Right: Table and search
        right = tk.Frame(self)
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        searchbar = tk.Frame(right)
        searchbar.pack(fill="x", pady=6)
        self.search_var = tk.StringVar()
        tk.Entry(searchbar, textvariable=self.search_var, width=30).pack(side="left", padx=6)
        ttk.Button(searchbar, text="Search", command=self.search_students).pack(side="left", padx=6)
        ttk.Button(searchbar, text="Show All", command=self.fetch_students).pack(side="left", padx=6)

        cols = ("ID", "Name", "Age", "Course", "Year")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120 if c=="Name" else 80, anchor="center")
        vsb = ttk.Scrollbar(right, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<ButtonRelease-1>", self.on_select)

    # DB ops
    def add_student(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Input error", "Name is required")
            return
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("INSERT INTO students (name, age, course, year) VALUES (%s,%s,%s,%s)",
                        (name, self._int_or_none(self.age_var.get()), self.course_var.get().strip(), self._int_or_none(self.year_var.get())))
            conn.close()
            messagebox.showinfo("Success", "Student added.")
            self.clear_fields()
            self.fetch_students()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def fetch_students(self):
        try:
            for row in self.tree.get_children():
                self.tree.delete(row)
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("SELECT student_id, name, age, course, year FROM students")
            for r in cur.fetchall():
                self.tree.insert("", "end", values=r)
            conn.close()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def update_student(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showerror("Selection", "Select a student first")
            return
        vals = self.tree.item(sel, "values")
        sid = vals[0]
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Input error", "Name is required")
            return
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("UPDATE students SET name=%s, age=%s, course=%s, year=%s WHERE student_id=%s",
                        (name, self._int_or_none(self.age_var.get()), self.course_var.get().strip(), self._int_or_none(self.year_var.get()), sid))
            conn.close()
            messagebox.showinfo("Success", "Student updated.")
            self.fetch_students()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def delete_student(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showerror("Selection", "Select a student first")
            return
        vals = self.tree.item(sel, "values")
        sid = vals[0]
        if not messagebox.askyesno("Confirm", "Delete selected student?"):
            return
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("DELETE FROM students WHERE student_id=%s", (sid,))
            conn.close()
            messagebox.showinfo("Success", "Student deleted.")
            self.fetch_students()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def on_select(self, event=None):
        sel = self.tree.focus()
        if not sel:
            return
        vals = self.tree.item(sel, "values")
        self.name_var.set(vals[1])
        self.age_var.set(vals[2] if vals[2] is not None else "")
        self.course_var.set(vals[3] if vals[3] is not None else "")
        self.year_var.set(vals[4] if vals[4] is not None else "")

    def clear_fields(self):
        self.name_var.set("")
        self.age_var.set("")
        self.course_var.set("")
        self.year_var.set("")
        self.search_var.set("")
        # clear selection
        for s in self.tree.selection():
            self.tree.selection_remove(s)

    def search_students(self):
        q = self.search_var.get().strip()
        if not q:
            self.fetch_students()
            return
        try:
            for row in self.tree.get_children():
                self.tree.delete(row)
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("SELECT student_id, name, age, course, year FROM students WHERE name LIKE %s OR course LIKE %s",
                        ("%"+q+"%", "%"+q+"%"))
            for r in cur.fetchall():
                self.tree.insert("", "end", values=r)
            conn.close()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def on_show(self):
        self.fetch_students()

    @staticmethod
    def _int_or_none(s):
        try:
            return int(s)
        except:
            return None

class BookPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        header = tk.Frame(self)
        header.pack(fill="x", pady=6)
        ttk.Button(header, text="⬅ Back", command=lambda: controller.show_frame("HomePage")).pack(side="left", padx=8)
        tk.Label(header, text="Manage Books", font=("Arial", 20)).pack(side="left", padx=14)

        # Left form
        form = tk.Frame(self, padx=10, pady=10)
        form.pack(side="left", fill="y")

        tk.Label(form, text="Title *").grid(row=0, column=0, sticky="w")
        self.title_var = tk.StringVar()
        tk.Entry(form, textvariable=self.title_var, width=35).grid(row=0, column=1, pady=4)

        tk.Label(form, text="Author").grid(row=1, column=0, sticky="w")
        self.author_var = tk.StringVar()
        tk.Entry(form, textvariable=self.author_var, width=35).grid(row=1, column=1, pady=4)

        tk.Label(form, text="Publication Year").grid(row=2, column=0, sticky="w")
        self.pubyear_var = tk.StringVar()
        tk.Entry(form, textvariable=self.pubyear_var, width=35).grid(row=2, column=1, pady=4)

        btn_frame = tk.Frame(form, pady=10)
        btn_frame.grid(row=3, column=0, columnspan=2)

        ttk.Button(btn_frame, text="Add Book", command=self.add_book).grid(row=0, column=0, padx=4)
        ttk.Button(btn_frame, text="Update Book", command=self.update_book).grid(row=0, column=1, padx=4)
        ttk.Button(btn_frame, text="Delete Book", command=self.delete_book).grid(row=0, column=2, padx=4)
        ttk.Button(btn_frame, text="Clear", command=self.clear_fields).grid(row=0, column=3, padx=4)

        # Right: Table and search
        right = tk.Frame(self)
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        searchbar = tk.Frame(right)
        searchbar.pack(fill="x", pady=6)
        self.search_var = tk.StringVar()
        tk.Entry(searchbar, textvariable=self.search_var, width=30).pack(side="left", padx=6)
        ttk.Button(searchbar, text="Search", command=self.search_books).pack(side="left", padx=6)
        ttk.Button(searchbar, text="Show All", command=self.fetch_books).pack(side="left", padx=6)

        cols = ("ID", "Title", "Author", "Year", "Status")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=160 if c=="Title" else 100, anchor="center")
        vsb = ttk.Scrollbar(right, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<ButtonRelease-1>", self.on_select)

    def add_book(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showerror("Input error", "Title required")
            return
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("INSERT INTO books (title, author, pub_year) VALUES (%s,%s,%s)",
                        (title, self.author_var.get().strip(), self._int_or_none(self.pubyear_var.get())))
            conn.close()
            messagebox.showinfo("Success", "Book added.")
            self.clear_fields()
            self.fetch_books()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def fetch_books(self):
        try:
            for row in self.tree.get_children():
                self.tree.delete(row)
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("SELECT book_id, title, author, pub_year, status FROM books")
            for r in cur.fetchall():
                self.tree.insert("", "end", values=r)
            conn.close()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def update_book(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showerror("Selection", "Select a book first")
            return
        vals = self.tree.item(sel, "values")
        bid = vals[0]
        title = self.title_var.get().strip()
        if not title:
            messagebox.showerror("Input error", "Title required")
            return
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("UPDATE books SET title=%s, author=%s, pub_year=%s WHERE book_id=%s",
                        (title, self.author_var.get().strip(), self._int_or_none(self.pubyear_var.get()), bid))
            conn.close()
            messagebox.showinfo("Success", "Book updated.")
            self.fetch_books()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def delete_book(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showerror("Selection", "Select a book first")
            return
        vals = self.tree.item(sel, "values")
        bid = vals[0]
        if not messagebox.askyesno("Confirm", "Delete selected book?"):
            return
        try:
            conn = connect_db()
            cur = conn.cursor()
            # if book is issued, we allow deletion; foreign key ON DELETE CASCADE handles issued entries
            cur.execute("DELETE FROM books WHERE book_id=%s", (bid,))
            conn.close()
            messagebox.showinfo("Success", "Book deleted.")
            self.fetch_books()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def on_select(self, event=None):
        sel = self.tree.focus()
        if not sel:
            return
        vals = self.tree.item(sel, "values")
        self.title_var.set(vals[1])
        self.author_var.set(vals[2] if vals[2] is not None else "")
        self.pubyear_var.set(vals[3] if vals[3] is not None else "")

    def clear_fields(self):
        self.title_var.set("")
        self.author_var.set("")
        self.pubyear_var.set("")
        self.search_var.set("")
        for s in self.tree.selection():
            self.tree.selection_remove(s)

    def search_books(self):
        q = self.search_var.get().strip()
        if not q:
            self.fetch_books()
            return
        try:
            for row in self.tree.get_children():
                self.tree.delete(row)
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("SELECT book_id, title, author, pub_year, status FROM books WHERE title LIKE %s OR author LIKE %s",
                        ("%"+q+"%", "%"+q+"%"))
            for r in cur.fetchall():
                self.tree.insert("", "end", values=r)
            conn.close()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def on_show(self):
        self.fetch_books()

    @staticmethod
    def _int_or_none(s):
        try:
            return int(s)
        except:
            return None

class IssuePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        header = tk.Frame(self)
        header.pack(fill="x", pady=6)
        ttk.Button(header, text="⬅ Back", command=lambda: controller.show_frame("HomePage")).pack(side="left", padx=8)
        tk.Label(header, text="Issue / Return Books", font=("Arial", 20)).pack(side="left", padx=14)

        main = tk.Frame(self, padx=10, pady=10)
        main.pack(fill="both", expand=True)

        left = tk.Frame(main)
        left.pack(side="left", fill="y", padx=10)

        tk.Label(left, text="Select Student").pack(anchor="w")
        self.student_cb = ttk.Combobox(left, state="readonly", width=40)
        self.student_cb.pack(pady=4)

        tk.Label(left, text="Select Book (Available)").pack(anchor="w")
        self.book_cb = ttk.Combobox(left, state="readonly", width=40)
        self.book_cb.pack(pady=4)

        ttk.Button(left, text="Issue Book", command=self.issue_book).pack(pady=8, fill="x")
        ttk.Button(left, text="Return Selected Book", command=self.return_book).pack(pady=8, fill="x")

        right = tk.Frame(main)
        right.pack(side="right", fill="both", expand=True)

        tk.Label(right, text="Issued Books (Active & Past)").pack(anchor="w")
        cols = ("IssueID", "StudentID", "StudentName", "BookID", "Title", "IssueDate", "ReturnDate")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120 if c in ("StudentName", "Title") else 90, anchor="center")
        vsb = ttk.Scrollbar(right, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<ButtonRelease-1>", self.on_select)

    def refresh_comboboxes(self):
        # students
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT student_id, name FROM students")
        students = cur.fetchall()
        conn.close()
        student_map = {f"{r[0]} - {r[1]}": r[0] for r in students}
        self._student_map = student_map
        self.student_cb['values'] = list(student_map.keys())

        # available books only
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT book_id, title FROM books WHERE status='Available'")
        books = cur.fetchall()
        conn.close()
        book_map = {f"{r[0]} - {r[1]}": r[0] for r in books}
        self._book_map = book_map
        self.book_cb['values'] = list(book_map.keys())

    def issue_book(self):
        ssel = self.student_cb.get()
        bsel = self.book_cb.get()
        if not ssel or not bsel:
            messagebox.showerror("Input", "Select student and book to issue")
            return
        sid = self._student_map.get(ssel)
        bid = self._book_map.get(bsel)
        today = date.today()
        try:
            conn = connect_db()
            cur = conn.cursor()
            # insert into issued_books and mark book as Issued
            cur.execute("INSERT INTO issued_books (student_id, book_id, issue_date) VALUES (%s,%s,%s)", (sid, bid, today))
            cur.execute("UPDATE books SET status='Issued' WHERE book_id=%s", (bid,))
            conn.close()
            messagebox.showinfo("Success", "Book issued.")
            self.refresh_all()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def return_book(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showerror("Selection", "Select an issued record to return")
            return
        vals = self.tree.item(sel, "values")
        issue_id = vals[0]
        book_id = vals[3]
        # If return_date already set, inform user
        if vals[6] not in (None, "", "None"):
            messagebox.showinfo("Info", "This book is already returned.")
            return
        if not messagebox.askyesno("Confirm", "Mark this book as returned?"):
            return
        try:
            today = date.today()
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("UPDATE issued_books SET return_date=%s WHERE issue_id=%s", (today, issue_id))
            cur.execute("UPDATE books SET status='Available' WHERE book_id=%s", (book_id,))
            conn.close()
            messagebox.showinfo("Success", "Book returned.")
            self.refresh_all()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def fetch_issued(self):
        try:
            for row in self.tree.get_children():
                self.tree.delete(row)
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT ib.issue_id, s.student_id, s.name, b.book_id, b.title, ib.issue_date, ib.return_date
                FROM issued_books ib
                JOIN students s ON ib.student_id = s.student_id
                JOIN books b ON ib.book_id = b.book_id
                ORDER BY ib.issue_id DESC
            """)
            for r in cur.fetchall():
                # format dates as iso strings or empty
                issue_date = r[5].isoformat() if r[5] else ""
                return_date = r[6].isoformat() if r[6] else ""
                self.tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4], issue_date, return_date))
            conn.close()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def on_select(self, event=None):
        pass

    def refresh_all(self):
        self.refresh_comboboxes()
        self.fetch_issued()

    def on_show(self):
        self.refresh_all()

# ------------------------ RUN ------------------------
if __name__ == "__main__":
    # Quick check for DB config placeholders
    if DB_CONFIG["user"] == "your_db_user" or DB_CONFIG["password"] == "your_db_pass":
        msg = ("Please edit DB_CONFIG at the top of the script with your MySQL credentials "
               "before running. Example:\n\n"
               "DB_CONFIG = {'host':'localhost','user':'bhavik','password':'mypass','database':'library_db'}")
        print(msg)
        messagebox.showwarning("Configure DB", msg)

    app = MainApp()
    app.mainloop()
