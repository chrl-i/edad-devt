import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import ImageTk, Image
import mysql.connector
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("EDAD")
        self.root.geometry("1200x600")

        try:
            icon = tk.PhotoImage(file="edad-icon.png")
            self.root.iconphoto(True, icon)
            self.window_icon = icon
        except tk.TclError:
            print("Warning: Could not load icon file")
            self.window_icon = None

        # Menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Plot menu
        self.plot_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Plot", menu=self.plot_menu)
        
        # Add Bar Plot option
        self.plot_menu.add_command(label="Bar Plot", command=self.plot_bar_graph)
        
        # Add Scatter Plot submenu
        self.scatter_menu = tk.Menu(self.plot_menu, tearoff=0)
        self.plot_menu.add_cascade(label="Scatter Plot", menu=self.scatter_menu)
        
        # Add sample class options to scatter menu
        self.scatter_menu.add_command(label="ADD", command=lambda: self.plot_scatter_plot("ADD"))
        self.scatter_menu.add_command(label="ADMCI", command=lambda: self.plot_scatter_plot("ADMCI"))
        self.scatter_menu.add_command(label="CU", command=lambda: self.plot_scatter_plot("CU"))
        self.scatter_menu.add_command(label="NoAD", command=lambda: self.plot_scatter_plot("NoAD"))

        # EDAD Banner
        self.banner = ImageTk.PhotoImage(Image.open("edad-banner.gif"))
        self.panel_banner = tk.Label(root, image=self.banner)
        self.panel_banner.pack()

         # Top frame for search, table selection, and database status
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(fill=tk.X, padx=5, pady=5)

        # Search and Sort Frame
        self.search_sort_frame = tk.Frame(self.top_frame)
        self.search_sort_frame.pack(side=tk.LEFT, padx=5)

        # Column Selection Dropdown for Search
        self.search_column_var = tk.StringVar()
        self.search_column_dropdown = ttk.Combobox(self.search_sort_frame, textvariable=self.search_column_var, state="readonly")
        self.search_column_dropdown.pack(side=tk.LEFT, padx=5)

        # Search Entry
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(self.search_sort_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)

        # Search Button
        self.search_button = tk.Button(self.search_sort_frame, text="Search", command=self.search_table)
        self.search_button.pack(side=tk.LEFT, padx=5)

        # Refresh Button
        self.refresh_button = tk.Button(self.search_sort_frame, text="Refresh", command=self.refresh_table)
        self.refresh_button.pack(side=tk.LEFT, padx=5)

        # Label for Database Dropdown
        self.db_label = tk.Label(self.top_frame, text="Database:")
        self.db_label.pack(side=tk.LEFT, padx=5)

        # Database selection dropdown
        self.db_var = tk.StringVar()
        self.db_dropdown = ttk.Combobox(self.top_frame, textvariable=self.db_var, state="readonly")
        self.db_dropdown.pack(side=tk.LEFT, padx=5)
        self.db_dropdown.bind("<<ComboboxSelected>>", self.on_db_select)

        # Label for Table Dropdown
        self.table_label = tk.Label(self.top_frame, text="Table:")
        self.table_label.pack(side=tk.LEFT, padx=5)

        # Dropdown for table selection
        self.table_var = tk.StringVar()
        self.table_dropdown = ttk.Combobox(self.top_frame, textvariable=self.table_var, state="readonly")
        self.table_dropdown.pack(side=tk.LEFT, padx=5)
        self.table_dropdown.bind("<<ComboboxSelected>>", self.on_table_select)

        # Status bar frame
        self.status_frame = tk.Frame(self.top_frame)
        self.status_frame.pack(side=tk.RIGHT, padx=5)

        self.db_status_label = tk.Label(self.status_frame, text="Checking DB Connection...", fg="black")
        self.db_status_label.pack(side=tk.RIGHT, padx=10)

        # Database content viewer with padding
        self.db_viewer_frame = tk.Frame(root, width=600, height=400)
        self.db_viewer_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a frame for the Treeview with a border effect
        self.tree_frame = tk.Frame(self.db_viewer_frame, relief="solid", borderwidth=1)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)

        # Add scrollbars
        self.vsb = ttk.Scrollbar(self.tree_frame, orient="vertical")
        self.hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal")
        
        # Configure Treeview with scrollbars
        self.tree = ttk.Treeview(self.tree_frame, show="headings",
                                yscrollcommand=self.vsb.set,
                                xscrollcommand=self.hsb.set)
        
        # Configure scrollbar commands
        self.vsb.config(command=self.tree.yview)
        self.hsb.config(command=self.tree.xview)
        
        # Pack scrollbars and tree
        self.vsb.pack(side="right", fill="y")
        self.hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Stylize the Treeview for a clean, compact look
        self.style = ttk.Style()
        self.style.configure("Treeview",
                            background="#ffffff",
                            foreground="#333333",
                            fieldbackground="#ffffff",
                            rowheight=20,          # Reduced row height for compactness
                            font=("Terminal", 9))  # Slightly smaller font
                            
        self.style.configure("Treeview.Heading",
                            background="#f0f0f0",
                            foreground="#241965",
                            relief="flat",
                            font=("Terminal", 9, "bold"))  # Bold headers
                            
        # Configure selection colors
        self.style.map("Treeview",
                    background=[("selected", "#e6e6e6")],   # Light gray selection
                    foreground=[("selected", "#241965")])

        # Track sort order for each column
        self.sort_order = {}  # Key: column name, Value: "asc" or "desc"

        # Database connection
        self.conn = None
        self.cursor = None
        self.databases = self.fetch_databases()  # Fetch available databases
        self.db_dropdown["values"] = self.databases

        if self.databases:
            self.db_var.set(self.databases[0])  # Set default database
            self.connect_database(self.databases[0])  # Connect to the default database
        
    def plot_bar_graph(self):
        """Plot a bar graph for ab38, ab40, ab42, and ab43 readings for all sample classes."""
        if self.table_var.get().lower() != "edad_amyloidbeta_reading":
            messagebox.showwarning("Invalid Table", "Please select the 'EDAD_AmyloidBeta_Reading' table.")
            return

        # Create a new window for the plot
        plot_window = tk.Toplevel(self.root)
        plot_window.title("Bar Graph: AB Readings for All Sample Classes")
        
        # Set the icon for the plot window
        if hasattr(self, 'window_icon') and self.window_icon:
            plot_window.iconphoto(True, self.window_icon)

        # Fetch data for all sample classes
        sample_classes = ["ADD", "ADMCI", "CU", "NoAD"]
        sample_class_mapping = {"ADD": 3, "ADMCI": 2, "CU": 1, "NoAD": 0}
        
        # Define colors for each class
        class_colors = {
            "ADD": "#241985",    # Dark blue
            "ADMCI": "#BC3D6E",  # Pink
            "CU": "#653993",     # Purple
            "NoAD": "#F19406"    # Orange
        }

        # Store averages for each sample class
        averages = {cls: {"AB38": 0, "AB40": 0, "AB42": 0, "AB43": 0} for cls in sample_classes}

        # Calculate averages for each sample class
        for cls in sample_classes:
            query = """
            SELECT ab38, ab40, ab42, ab43 
            FROM EDAD_AmyloidBeta_Reading 
            JOIN EDAD_Classification 
            ON EDAD_AmyloidBeta_Reading.sample_id = EDAD_Classification.sample_id 
            WHERE EDAD_Classification.sample_class = %s
            """
            self.cursor.execute(query, (sample_class_mapping[cls],))
            data = self.cursor.fetchall()

            if data:
                ab38_avg = sum(row[0] for row in data) / len(data)
                ab40_avg = sum(row[1] for row in data) / len(data)
                ab42_avg = sum(row[2] for row in data) / len(data)
                ab43_avg = sum(row[3] for row in data) / len(data)
                averages[cls]["AB38"] = ab38_avg
                averages[cls]["AB40"] = ab40_avg
                averages[cls]["AB42"] = ab42_avg
                averages[cls]["AB43"] = ab43_avg

        # Create a new window for the plot
        plot_window = tk.Toplevel(self.root)
        plot_window.title("Bar Graph: AB Readings for All Sample Classes")

        # Create the bar graph
        fig, ax = plt.subplots(figsize=(8, 6))
        ab_types = ["AB38", "AB40", "AB42", "AB43"]
        x = range(len(ab_types))

        # Plot bars for each sample class with custom colors
        width = 0.2
        for i, cls in enumerate(sample_classes):
            ax.bar([p + width * i for p in x], 
                [averages[cls][ab] for ab in ab_types], 
                width=width, 
                label=cls, 
                color=class_colors[cls])

        # Set x-ticks and labels
        ax.set_xticks([p + 1.5 * width for p in x])
        ax.set_xticklabels(ab_types)

        # Set y-axis limit based on the maximum value across all sample classes
        max_value = max(max(averages[cls][ab] for ab in ab_types) for cls in sample_classes)
        ax.set_ylim(0, max_value * 1.1)  # Add 10% padding

        # Add labels and title
        ax.set_ylabel("Average Reading")
        ax.set_title("Average Amyloid Beta Readings for All Sample Classes")
        ax.legend()

        # Embed the plot in the Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def plot_scatter_plot(self, sample_class):
        """Plot scatter plots for all pairs of AB types for a specific sample class."""
        if self.table_var.get().lower() != "edad_amyloidbeta_reading":
            messagebox.showwarning("Invalid Table", "Please select the 'EDAD_AmyloidBeta_Reading' table.")
            return

        # Create a new window for the plot
        plot_window = tk.Toplevel(self.root)
        plot_window.title(f"Scatter Plots: AB Readings for {sample_class}")
        
        # Set the icon for the plot window
        if hasattr(self, 'window_icon') and self.window_icon:
            plot_window.iconphoto(True, self.window_icon)

        # Map the sample class to its corresponding value in the database
        sample_class_mapping = {"ADD": 3, "ADMCI": 2, "CU": 1, "NoAD": 0}
        sample_class_value = sample_class_mapping.get(sample_class, 3)

        # Fetch data from the table, filtered by sample class
        query = """
        SELECT ab38, ab40, ab42, ab43 
        FROM EDAD_AmyloidBeta_Reading 
        JOIN EDAD_Classification 
        ON EDAD_AmyloidBeta_Reading.sample_id = EDAD_Classification.sample_id 
        WHERE EDAD_Classification.sample_class = %s
        """
        self.cursor.execute(query, (sample_class_value,))
        data = self.cursor.fetchall()

        if not data:
            messagebox.showwarning("No Data", f"No data found for sample class: {sample_class}")
            return

        # Create a new window for the plot
        plot_window = tk.Toplevel(self.root)
        plot_window.title(f"Scatter Plots: AB Readings for {sample_class}")

        # Create subplots for each pair
        fig, axs = plt.subplots(2, 3, figsize=(10, 6))
        fig.suptitle(f"Scatter Plots for Amyloid Beta Readings ({sample_class})")

        # Plot AB38 vs AB40
        axs[0, 0].scatter([row[0] for row in data], [row[1] for row in data], color='#BC3D6E')
        axs[0, 0].set_xlabel("AB38")
        axs[0, 0].set_ylabel("AB40")
        axs[0, 0].set_title("AB38 vs AB40")

        # Plot AB38 vs AB42
        axs[0, 1].scatter([row[0] for row in data], [row[2] for row in data], color='#BC3D6E')
        axs[0, 1].set_xlabel("AB38")
        axs[0, 1].set_ylabel("AB42")
        axs[0, 1].set_title("AB38 vs AB42")

        # Plot AB38 vs AB43
        axs[0, 2].scatter([row[0] for row in data], [row[3] for row in data], color='#BC3D6E')
        axs[0, 2].set_xlabel("AB38")
        axs[0, 2].set_ylabel("AB43")
        axs[0, 2].set_title("AB38 vs AB43")

        # Plot AB40 vs AB42
        axs[1, 0].scatter([row[1] for row in data], [row[2] for row in data], color='#BC3D6E')
        axs[1, 0].set_xlabel("AB40")
        axs[1, 0].set_ylabel("AB42")
        axs[1, 0].set_title("AB40 vs AB42")

        # Plot AB40 vs AB43
        axs[1, 1].scatter([row[1] for row in data], [row[3] for row in data], color='#BC3D6E')
        axs[1, 1].set_xlabel("AB40")
        axs[1, 1].set_ylabel("AB43")
        axs[1, 1].set_title("AB40 vs AB43")

        # Plot AB42 vs AB43
        axs[1, 2].scatter([row[2] for row in data], [row[3] for row in data], color='#BC3D6E')
        axs[1, 2].set_xlabel("AB42")
        axs[1, 2].set_ylabel("AB43")
        axs[1, 2].set_title("AB42 vs AB43")

        # Adjust layout and embed the plot in the Tkinter window
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def fetch_databases(self):
        """Fetch available databases from the MySQL server."""
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="edad"
            )
            cursor = conn.cursor()
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            cursor.close()
            conn.close()
            return databases
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to fetch databases: {err}")
            return []

    def on_db_select(self, event):
        """Handle database selection from the dropdown."""
        selected_db = self.db_var.get()
        if selected_db:
            self.connect_database(selected_db)

    def connect_database(self, database_name):
        """Connect to the selected database."""
        try:
            self.conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="edad",
                database=database_name
            )
            self.cursor = self.conn.cursor()
            self.db_status_label.config(text=f"Connected to {database_name}", fg="green")

            # Fetch table names from the selected database
            self.cursor.execute("SHOW TABLES")
            self.tables = [table[0] for table in self.cursor.fetchall()]
            self.table_dropdown["values"] = self.tables

            # Load the first table by default (if any tables exist)
            if self.tables:
                self.table_var.set(self.tables[0])
                self.load_table_data(self.tables[0])
        except mysql.connector.Error as err:
            self.db_status_label.config(text=f"Failed to connect to {database_name}", fg="red")

    def load_table_data(self, table_name):
        """Load data from the selected table into the Treeview."""
        # Clear the existing data in the Treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Fetch column names and data from the selected table
        self.cursor.execute(f"SELECT * FROM {table_name}")
        self.rows = self.cursor.fetchall()

        # Get column names
        self.cursor.execute(f"DESCRIBE {table_name}")
        self.columns = [column[0] for column in self.cursor.fetchall()]

        # Configure Treeview columns
        self.tree["columns"] = self.columns
        for col in self.columns:
            self.tree.heading(col, 
                            text=f" {col} ",  # Add spaces around column headers
                            command=lambda c=col: self.sort_treeview(c))  # Add sorting command
            self.tree.column(col, width=100, minwidth=50, anchor=tk.W)
            self.sort_order[col] = "asc"  # Initialize sort order for each column

        # Update the search column dropdown
        self.search_column_dropdown["values"] = self.columns
        if self.columns:
            self.search_column_var.set(self.columns[0])  # Set default search column

        # Find the index of the 'sample_class' column
        self.sample_class_index = self.columns.index("sample_class") if "sample_class" in self.columns else -1

        # Insert data into the Treeview
        self.insert_rows_into_treeview(self.rows)

    def insert_rows_into_treeview(self, rows):
        """Insert rows into the Treeview with mapped labels for 'sample_class' and spacing."""
        for row in rows:
            if self.sample_class_index != -1:
                # Convert the sample_class value to its corresponding label
                row = list(row)  # Convert tuple to list to modify it
                sample_class_value = row[self.sample_class_index]
                if sample_class_value == 0:
                    row[self.sample_class_index] = "NoAD"
                elif sample_class_value == 1:
                    row[self.sample_class_index] = "CU"
                elif sample_class_value == 2:
                    row[self.sample_class_index] = "ADMCI"
                elif sample_class_value == 3:
                    row[self.sample_class_index] = "ADD"
                
                # Add spaces to create visual padding
                row = [f" {str(val)} " for val in row]
                row = tuple(row)  # Convert back to tuple

            else:
                # Add spaces to create visual padding for rows without sample_class
                row = [f" {str(val)} " for val in row]
                row = tuple(row)

            self.tree.insert("", tk.END, values=row)

    def on_table_select(self, event):
        """Fetch and display data for the selected table."""
        selected_table = self.table_var.get()
        self.load_table_data(selected_table)

    def search_table(self):
        """Search the table based on the selected column and search text."""
        search_text = self.search_var.get().strip()
        search_column = self.search_column_var.get()

        if not search_text or not search_column:
            return  # Do nothing if search text or column is empty

        # Clear the Treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Find the index of the selected column
        column_index = self.columns.index(search_column)

        # Handle search for 'sample_class' column
        if search_column == "sample_class":
            # Map search term to database value
            search_mapping = {"ADD": 3, "ADMCI": 2, "CU": 1, "NoAD": 0}
            if search_text in search_mapping:
                search_value = search_mapping[search_text]
            elif search_text in {"0", "1", "2", "3"}:
                # Explicitly return no results if search term is 0, 1, 2, or 3
                messagebox.showinfo("Search Result", "No results found.")
                return
            else:
                # Invalid search term
                messagebox.showinfo("Search Result", "No results found.")
                return
        else:
            search_value = search_text

        # Filter rows based on exact match in the selected column
        found = False
        filtered_rows = []
        for row in self.rows:
            if search_column == "sample_class":
                # Compare with the original database value
                if row[column_index] == search_value:
                    filtered_rows.append(row)
                    found = True
            else:
                # Compare with the displayed value
                if str(row[column_index]) == search_value:
                    filtered_rows.append(row)
                    found = True

        # Insert filtered rows into the Treeview with mapped labels
        self.insert_rows_into_treeview(filtered_rows)

        # Show "No results found" if no matches are found
        if not found:
            messagebox.showinfo("Search Result", "No results found.")

    def refresh_table(self):
        """Reload the table data from the database."""
        selected_table = self.table_var.get()
        self.load_table_data(selected_table)

    def sort_treeview(self, col):
        """Sort the Treeview based on the selected column."""
        # Get all rows from the Treeview
        rows = [(self.tree.set(child, col).strip(), child) for child in self.tree.get_children("")]
        
        # Handle empty treeview
        if not rows:
            return

        # Determine if the column contains numeric data
        try:
            # Try to convert the first stripped value to a float
            float(rows[0][0])
            is_numeric = True
        except (ValueError, IndexError):
            is_numeric = False

        # Special handling for sample_class column
        if col == "sample_class":
            # Define the order for sample classes
            class_order = {"NoAD": 0, "CU": 1, "ADMCI": 2, "ADD": 3}
            rows.sort(key=lambda x: class_order.get(x[0].strip(), 4), 
                    reverse=self.sort_order[col] == "desc")
        else:
            # Sort rows based on the column values
            if is_numeric:
                # Sort as floats, handling potential empty or invalid values
                def safe_float(x):
                    try:
                        return float(x.strip())
                    except (ValueError, TypeError):
                        return float('-inf')  # Put invalid values at the start
                
                rows.sort(key=lambda x: safe_float(x[0]), 
                        reverse=self.sort_order[col] == "desc")
            else:
                # Sort as strings, ignoring the padding spaces
                rows.sort(key=lambda x: x[0].strip().lower(), 
                        reverse=self.sort_order[col] == "desc")

        # Toggle sort order for the next click
        self.sort_order[col] = "desc" if self.sort_order[col] == "asc" else "asc"

        # Reinsert rows into the Treeview in sorted order
        for index, (val, child) in enumerate(rows):
            self.tree.move(child, "", index)

    def open_file(self):
        """Open a file using a file dialog."""
        file_path = filedialog.askopenfilename(title="Open File")
        if file_path:
            messagebox.showinfo("File Opened", f"Opened: {file_path}")

    def save_file(self):
        """Save a file using a file dialog."""
        file_path = filedialog.asksaveasfilename(title="Save File", defaultextension=".txt")
        if file_path:
            messagebox.showinfo("File Saved", f"Saved: {file_path}")

    def show_about(self):
        """Display the About dialog."""
        messagebox.showinfo("About", "EDAD Application v1.0\nCreated with Tkinter")

    def __del__(self):
        """Close the database connection when the application exits."""
        if hasattr(self, "cursor"):
            self.cursor.close()
        if hasattr(self, "conn"):
            self.conn.close()
        
root = tk.Tk()
app = App(root)
root.mainloop()