#Developed by ODAT project
#please see https://odat.info
#please see https://github.com/ODAT-Project
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import io

STYLE_CONFIG = {
    "font_family": "Segoe UI",
    "font_size_normal": 10,
    "font_size_header": 14,
    "bg_root": "#F0F0F0",
    "bg_widget": "#FFFFFF",
    "fg_text": "#333333",
    "fg_header": "#000000",
    "accent_color": "#0078D4",
    "accent_text_color": "#FFFFFF",
    "border_color": "#CCCCCC",
    "listbox_select_bg": "#0078D4",
    "listbox_select_fg": "#FFFFFF",
    "disabled_bg": "#E0E0E0",
}

class EnhancedCSVPlotterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Data Visualizer")
        self.root.geometry("1300x850")
        self.root.minsize(900, 700)
        self.root.configure(bg=STYLE_CONFIG["bg_root"])

        self.df = None
        self.current_fig = None
        self.filename = ""
        self.plot_type = tk.StringVar(value="Histogram")
        self.log_scale_var = tk.BooleanVar(value=False)
        self.hist_bins_var = tk.StringVar(value="30")
        
        self.setup_styles()
        self.create_menu()
        self.create_main_layout()
        self.toggle_button_states() # Initial state

    def setup_styles(self):
        s = ttk.Style(self.root)
        s.theme_use("default")
        
        font_normal = (STYLE_CONFIG["font_family"], STYLE_CONFIG["font_size_normal"])
        font_bold = (STYLE_CONFIG["font_family"], STYLE_CONFIG["font_size_normal"], "bold")
        font_header = (STYLE_CONFIG["font_family"], STYLE_CONFIG["font_size_header"], "bold")
        
        s.configure("TFrame", background=STYLE_CONFIG["bg_root"])
        s.configure("Content.TFrame", background=STYLE_CONFIG["bg_widget"])
        s.configure("TLabel", background=STYLE_CONFIG["bg_widget"], foreground=STYLE_CONFIG["fg_text"], font=font_normal)
        s.configure("Header.TLabel", font=font_header, foreground=STYLE_CONFIG["fg_header"], background=STYLE_CONFIG["bg_root"])
        s.configure("TButton", font=font_bold, padding=6, background=STYLE_CONFIG["accent_color"], foreground=STYLE_CONFIG["accent_text_color"])
        s.map("TButton", background=[("active", "#005a9e"), ("disabled", STYLE_CONFIG["disabled_bg"])])
        s.configure("TCombobox", padding=5)
        self.root.option_add('*TCombobox*Listbox.background', STYLE_CONFIG["bg_widget"])
        self.root.option_add('*TCombobox*Listbox.foreground', STYLE_CONFIG["fg_text"])
        self.root.option_add('*TCombobox*Listbox.selectBackground', STYLE_CONFIG["listbox_select_bg"])
        self.root.option_add('*TCombobox*Listbox.selectForeground', STYLE_CONFIG["listbox_select_fg"])
        s.configure("TLabelFrame", background=STYLE_CONFIG["bg_widget"], bordercolor=STYLE_CONFIG["border_color"])
        s.configure("TLabelFrame.Label", background=STYLE_CONFIG["bg_widget"], foreground=STYLE_CONFIG["fg_header"], font=font_bold)
        s.configure("TCheckbutton", background=STYLE_CONFIG["bg_widget"])

    def create_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load CSV...", command=self.load_csv, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="About", command=self.show_about_dialog)
        file_menu.add_command(label="Quit", command=self.root.quit, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)
        self.root.bind_all("<Control-o>", lambda e: self.load_csv())
        self.root.bind_all("<Control-q>", lambda e: self.root.quit())

    def create_main_layout(self):
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        control_panel = ttk.Frame(main_pane, style="Content.TFrame", width=320)
        main_pane.add(control_panel, weight=1)
        control_panel.pack_propagate(False)
        
        self.plot_frame = ttk.Frame(main_pane, style="Content.TFrame")
        main_pane.add(self.plot_frame, weight=3)
        
        self.create_control_widgets(control_panel)

    def create_control_widgets(self, parent):
        parent.columnconfigure(0, weight=1)

        file_frame = ttk.LabelFrame(parent, text="File Operations")
        file_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        file_frame.columnconfigure(0, weight=1)
        
        load_button = ttk.Button(file_frame, text="Load CSV File", command=self.load_csv)
        load_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.file_label = ttk.Label(file_frame, text="No file loaded.", wraplength=280)
        self.file_label.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        self.summary_button = ttk.Button(file_frame, text="Show Data Summary", command=self.show_data_summary)
        self.summary_button.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 5))

        plot_config_frame = ttk.LabelFrame(parent, text="Plot Configuration")
        plot_config_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        plot_config_frame.columnconfigure(1, weight=1)
        
        ttk.Label(plot_config_frame, text="Plot Type:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        plot_options = ["Histogram", "Bar Chart (Counts)", "Pie Chart", "Box Plot", "Scatter Plot", "Line Plot", "Violin Plot", "Heatmap (Correlation)", "Pair Plot"]
        self.plot_combo = ttk.Combobox(plot_config_frame, textvariable=self.plot_type, values=plot_options, state='readonly')
        self.plot_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.plot_combo.bind("<<ComboboxSelected>>", self.update_column_selection_ui)
        
        self.column_selection_frame = ttk.LabelFrame(parent, text="Column Selection")
        self.column_selection_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        parent.rowconfigure(2, weight=1)

        self.plot_options_frame = ttk.LabelFrame(parent, text="Plot Customization")
        self.plot_options_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

        action_frame = ttk.LabelFrame(parent, text="Actions")
        action_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=10)
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)

        self.generate_button = ttk.Button(action_frame, text="Generate Plot", command=self.generate_plot)
        self.generate_button.grid(row=0, column=0, sticky="ew", padx=(5,2), pady=5)
        self.save_button = ttk.Button(action_frame, text="Save Plot", command=self.save_plot)
        self.save_button.grid(row=0, column=1, sticky="ew", padx=(2,5), pady=5)

        self.update_column_selection_ui()
    
    def toggle_button_states(self):
        """Enable or disable buttons based on application state."""
        data_loaded = self.df is not None
        plot_exists = self.current_fig is not None

        self.summary_button.config(state=tk.NORMAL if data_loaded else tk.DISABLED)
        self.generate_button.config(state=tk.NORMAL if data_loaded else tk.DISABLED)
        self.save_button.config(state=tk.NORMAL if plot_exists else tk.DISABLED)


    def update_column_selection_ui(self, event=None):
        for widget in self.column_selection_frame.winfo_children():
            widget.destroy()
        for widget in self.plot_options_frame.winfo_children():
            widget.destroy()

        plot = self.plot_type.get()
        self.column_selection_frame.columnconfigure(0, weight=1)

        font_bold = (STYLE_CONFIG["font_family"], STYLE_CONFIG["font_size_normal"], "bold")

        if plot in ["Histogram", "Bar Chart (Counts)", "Pie Chart"]:
            ttk.Label(self.column_selection_frame, text="Select Column:", font=font_bold).pack(fill=tk.X, padx=5, pady=5)
            self.col1_listbox = tk.Listbox(self.column_selection_frame, exportselection=False, height=8, selectbackground=STYLE_CONFIG["listbox_select_bg"], selectforeground=STYLE_CONFIG["listbox_select_fg"])
            self.col1_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
            if plot == 'Histogram':
                self.setup_hist_options()
        
        elif plot in ["Scatter Plot", "Line Plot", "Box Plot", "Violin Plot"]:
            self.column_selection_frame.rowconfigure(1, weight=1)
            self.column_selection_frame.rowconfigure(3, weight=1)
            
            ttk.Label(self.column_selection_frame, text="X-Axis Column:", font=font_bold).grid(row=0, column=0, sticky="w", padx=5)
            self.col1_listbox = tk.Listbox(self.column_selection_frame, exportselection=False, height=4, selectbackground=STYLE_CONFIG["listbox_select_bg"], selectforeground=STYLE_CONFIG["listbox_select_fg"])
            self.col1_listbox.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
            
            ttk.Label(self.column_selection_frame, text="Y-Axis Column:", font=font_bold).grid(row=2, column=0, sticky="w", padx=5)
            self.col2_listbox = tk.Listbox(self.column_selection_frame, exportselection=False, height=4, selectbackground=STYLE_CONFIG["listbox_select_bg"], selectforeground=STYLE_CONFIG["listbox_select_fg"])
            self.col2_listbox.grid(row=3, column=0, sticky="nsew", padx=5, pady=(0, 5))
            
            if plot in ["Scatter Plot", "Violin Plot", "Box Plot"]:
                ttk.Label(self.column_selection_frame, text="Color (Hue) Column (Optional):", font=font_bold).grid(row=4, column=0, sticky="w", padx=5)
                self.col3_listbox = tk.Listbox(self.column_selection_frame, exportselection=False, height=4, selectbackground=STYLE_CONFIG["listbox_select_bg"], selectforeground=STYLE_CONFIG["listbox_select_fg"])
                self.col3_listbox.grid(row=5, column=0, sticky="nsew", padx=5, pady=(0, 5))
                self.column_selection_frame.rowconfigure(5, weight=1)
            if plot == 'Scatter Plot':
                self.setup_scatter_options()

        elif plot in ["Heatmap (Correlation)", "Pair Plot"]:
            ttk.Label(self.column_selection_frame, text=f"{plot} will be generated for all numerical columns.", wraplength=280).pack(fill=tk.X, padx=5, pady=10)

        self.populate_listboxes()

    def setup_hist_options(self):
        self.plot_options_frame.columnconfigure(1, weight=1)
        ttk.Checkbutton(self.plot_options_frame, text="Logarithmic Scale (X-axis)", variable=self.log_scale_var).grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ttk.Label(self.plot_options_frame, text="Number of Bins:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(self.plot_options_frame, textvariable=self.hist_bins_var, width=10).grid(row=1, column=1, sticky='w', padx=5, pady=2)
        
    def setup_scatter_options(self):
        ttk.Checkbutton(self.plot_options_frame, text="Logarithmic Scale (X & Y axes)", variable=self.log_scale_var).grid(row=0, column=0, sticky='w', padx=5, pady=2)

    def load_csv(self):
        filepath = filedialog.askopenfilename(initialdir=".", title="Select a CSV File", filetypes=(("CSV Files", "*.csv"), ("All files", "*.*")))
        if filepath:
            try:
                self.df = pd.read_csv(filepath)
                self.filename = filepath.split('/')[-1]
                self.file_label.config(text=self.filename)
                self.populate_listboxes()
                messagebox.showinfo("Success", "CSV file loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
                self.df = None
                self.filename = ""
                self.file_label.config(text="No file loaded.")
            finally:
                self.toggle_button_states()


    def populate_listboxes(self):
        if self.df is not None:
            columns = sorted(self.df.columns.tolist())
            listboxes = ['col1_listbox', 'col2_listbox', 'col3_listbox']
            for lb_name in listboxes:
                if hasattr(self, lb_name):
                    lb = getattr(self, lb_name)
                    lb.delete(0, tk.END)
                    for col in columns:
                        lb.insert(tk.END, col)
    
    def get_selected_from_listbox(self, listbox, allow_none=False):
        if not hasattr(self, listbox):
            return None
        lb = getattr(self, listbox)
        indices = lb.curselection()
        if indices:
            return lb.get(indices[0])
        if allow_none:
            return None
        raise IndexError("No selection made in a required listbox.")

    def clear_plot_frame(self):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
        self.current_fig = None
        self.toggle_button_states()

    def generate_plot(self):
        if self.df is None:
            messagebox.showwarning("Warning", "Please load a CSV file first.")
            return

        plot_choice = self.plot_type.get()
        try:
            self.clear_plot_frame()
            fig = plt.Figure(figsize=(8, 6), dpi=100)
            ax = fig.add_subplot(111)

            col1, col2, col3 = None, None, None
            log_scale = self.log_scale_var.get()
            
            if plot_choice in ["Histogram", "Bar Chart (Counts)", "Pie Chart", "Box Plot", "Scatter Plot", "Line Plot", "Violin Plot"]:
                col1 = self.get_selected_from_listbox('col1_listbox')
            if plot_choice in ["Scatter Plot", "Line Plot", "Box Plot", "Violin Plot"]:
                col2 = self.get_selected_from_listbox('col2_listbox')
            if plot_choice in ["Scatter Plot", "Box Plot", "Violin Plot"]:
                col3 = self.get_selected_from_listbox('col3_listbox', allow_none=True)

            if plot_choice == "Histogram":
                if pd.api.types.is_numeric_dtype(self.df[col1]):
                    try:
                        bins = int(self.hist_bins_var.get())
                    except ValueError:
                        bins = 30
                        messagebox.showwarning("Warning", "Invalid bin number, defaulting to 30.")
                    sns.histplot(self.df[col1], kde=True, ax=ax, bins=bins, log_scale=log_scale)
                    ax.set_title(f'Histogram of {col1}')
                else:
                    messagebox.showerror("Error", "Please select a numeric column for Histogram.")
                    return
            
            elif plot_choice == "Bar Chart (Counts)":
                sns.countplot(x=self.df[col1], ax=ax, order=self.df[col1].value_counts().index, palette='viridis')
                ax.set_title(f'Distribution of {col1}')
                ax.tick_params(axis='x', rotation=45)

            elif plot_choice == "Pie Chart":
                counts = self.df[col1].value_counts()
                ax.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=90, colors=sns.color_palette('pastel'))
                ax.set_title(f'Proportion of {col1}')
                ax.axis('equal')

            elif plot_choice in ["Box Plot", "Violin Plot"]:
                if pd.api.types.is_numeric_dtype(self.df[col2]):
                    plot_func = sns.boxplot if plot_choice == "Box Plot" else sns.violinplot
                    plot_func(x=self.df[col1], y=self.df[col2], hue=self.df[col3] if col3 else None, ax=ax, palette='muted')
                    ax.set_title(f'{plot_choice}: {col2} by {col1}')
                    ax.tick_params(axis='x', rotation=45)
                else:
                    messagebox.showerror("Error", "Y-Axis must be numeric for this plot.")
                    return

            elif plot_choice in ["Scatter Plot", "Line Plot"]:
                if pd.api.types.is_numeric_dtype(self.df[col1]) and pd.api.types.is_numeric_dtype(self.df[col2]):
                    if plot_choice == "Scatter Plot":
                        sns.scatterplot(x=self.df[col1], y=self.df[col2], hue=self.df[col3] if col3 else None, ax=ax)
                        ax.set_title(f'Scatter Plot: {col2} vs {col1}')
                        if log_scale:
                           ax.set_xscale('log')
                           ax.set_yscale('log')
                    elif plot_choice == "Line Plot":
                        sorted_df = self.df.sort_values(by=col1)
                        sns.lineplot(x=sorted_df[col1], y=sorted_df[col2], ax=ax)
                        ax.set_title(f'Line Plot: {col2} vs {col1}')
                else:
                    messagebox.showerror("Error", "Please select numeric columns for this plot.")
                    return

            elif plot_choice == "Heatmap (Correlation)":
                numeric_df = self.df.select_dtypes(include=np.number)
                if numeric_df.shape[1] < 2:
                    messagebox.showerror("Error", "Need at least two numeric columns for a heatmap.")
                    return
                sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm', fmt=".2f", ax=ax)
                ax.set_title('Correlation Heatmap')

            elif plot_choice == "Pair Plot":
                plt.close(fig) 
                numeric_df = self.df.select_dtypes(include=np.number)
                if numeric_df.shape[1] > 8:
                    numeric_df = numeric_df.iloc[:, :8]
                    messagebox.showinfo("Info", "Pair Plot limited to the first 8 numeric columns for performance.")
                if numeric_df.shape[1] < 2:
                    messagebox.showerror("Error", "Need at least two numeric columns for pair plot.")
                    return
                pair_fig = sns.pairplot(numeric_df, corner=True)
                pair_fig.fig.suptitle('Pair Plot of Numerical Variables', y=1.02)
                self.embed_plot(pair_fig.fig)
                return

            fig.tight_layout()
            self.embed_plot(fig)

        except IndexError:
             messagebox.showerror("Selection Error", "Please select the required column(s) from the list.")
        except Exception as e:
            messagebox.showerror("Plotting Error", f"An error occurred: {e}")
            plt.close('all')
            self.current_fig = None
        finally:
            self.toggle_button_states()

    def embed_plot(self, fig):
        self.current_fig = fig
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.toggle_button_states()

    def save_plot(self):
        if not self.current_fig:
            messagebox.showwarning("Warning", "No plot to save. Please generate a plot first.")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG Image", "*.png"),
                ("JPEG Image", "*.jpg"),
                ("PDF Document", "*.pdf"),
                ("SVG Vector Image", "*.svg"),
                ("All Files", "*.*"),
            ],
            title="Save Plot As"
        )

        if not filepath:
            return

        try:
            self.current_fig.savefig(filepath, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Success", f"Plot successfully saved to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save the plot.\nError: {e}")

    def show_data_summary(self):
        if self.df is None: return
        summary_window = tk.Toplevel(self.root)
        summary_window.title(f"Data Summary: {self.filename}")
        summary_window.geometry("700x500")
        summary_window.configure(bg=STYLE_CONFIG["bg_widget"])

        text_area = scrolledtext.ScrolledText(summary_window, wrap=tk.WORD, font=("Courier New", 10))
        text_area.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)

        buffer = io.StringIO()
        self.df.info(buf=buffer)
        info_str = buffer.getvalue()
        
        summary_str = f"DATASET OVERVIEW\n"
        summary_str += f"{'='*30}\n"
        summary_str += info_str
        summary_str += f"\n\nNUMERICAL DATA SUMMARY (describe())\n"
        summary_str += f"{'='*40}\n"
        summary_str += self.df.describe().to_string()
        summary_str += f"\n\nCATEGORICAL DATA SUMMARY (describe())\n"
        summary_str += f"{'='*40}\n"
        summary_str += self.df.describe(include=['object', 'category']).to_string()

        text_area.insert(tk.END, summary_str)
        text_area.config(state=tk.DISABLED)

    def show_about_dialog(self):
        messagebox.showinfo(
            "About ODAT Data Visualizer",
            "This application allows for dynamic loading and visualization of data from CSV files.\n\n"
            "Developed by ODAT project."
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedCSVPlotterApp(root)
    root.mainloop()
