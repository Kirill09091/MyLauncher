import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import subprocess
import os
import sys
import webbrowser 
import json 
import shlex # Добавлен для корректной обработки аргументов с пробелами

# Импортируем модули, которые мы создали
try:
    from data_manager import DataManager
except ImportError:
    messagebox.showerror("Ошибка", "Не найден файл data_manager.py. Убедитесь, что он находится в той же папке.")
    sys.exit()

try:
    from icon_extractor import get_icon_from_exe
except ImportError:
    messagebox.showwarning("Предупреждение", "Не найден файл icon_extractor.py или произошла ошибка при импорте. Иконки не будут отображаться.")
    def get_icon_from_exe(path, size=(32, 32)):
        return None

try:
    from system_integrator import open_file_location
except ImportError:
    messagebox.showwarning("Предупреждение", "Не найден файл system_integrator.py или произошла ошибка при импорте. Функции системной интеграции могут быть недоступны.")
    def open_file_location(path):
        messagebox.showerror("Ошибка", "Функция 'Открыть расположение файла' недоступна. Не найден system_integrator.py.")

class AppLauncher:
    def __init__(self, master):
        self.master = master
        self.master.title("Мой Многофункциональный Лаунчер")
        
        self.data_manager = DataManager("launcher_data.json")
        self.data_manager.load_data()

        saved_geometry = self.data_manager.get_window_geometry()
        if saved_geometry:
            self.master.geometry(saved_geometry)
        else:
            self.master.geometry("1000x600")

        self.icon_references = {} 

        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure("Dark.TFrame", background="#1a1a1a")
        self.style.configure("Dark.TLabel", background="#1a1a1a", foreground="white", font=("Segoe UI", 10))
        self.style.configure("Dark.TEntry", fieldbackground="#333333", foreground="white", insertbackground="white")
        self.style.configure("Dark.TPanedwindow", background="#1a1a1a")
        
        self.style.configure("Dark.Treeview", 
                             background="#2a2a2a", 
                             foreground="white", 
                             fieldbackground="#2a2a2a", 
                             bordercolor="#333333",
                             font=("Segoe UI", 10))
        self.style.map("Dark.Treeview", 
                       background=[('selected', '#007ACC')],
                       foreground=[('selected', 'white')])

        self.style.configure("Blue.TButton", background="#007ACC", foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0)
        self.style.map("Blue.TButton", 
                       background=[('active', '#005f99')],
                       foreground=[('active', 'white')])

        self.style.configure("Category.TButton", background="#333333", foreground="#007ACC", font=("Segoe UI", 10, "bold"), borderwidth=0)
        self.style.map("Category.TButton",
                       background=[('active', '#555555')],
                       foreground=[('active', 'white')])
        
        self.master.option_add("*TNotebook*background", "#1a1a1a")
        self.master.option_add("*TNotebook*Tab.background", "#333333")
        self.master.option_add("*TNotebook*Tab.foreground", "white")
        self.master.option_add("*TNotebook*Tab.selectbackground", "#007ACC")
        self.master.option_add("*TNotebook*Tab.selectforeground", "white")

        self.main_frame = ttk.Frame(master, style="Dark.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL, style="Dark.TPanedwindow")
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- Левая панель: Категории ---
        self.categories_frame = ttk.Frame(self.paned_window, style="Dark.TFrame")
        self.paned_window.add(self.categories_frame, weight=1)

        self.categories_label = ttk.Label(self.categories_frame, text="Категории", style="Dark.TLabel", font=("Segoe UI", 12, "bold"))
        self.categories_label.pack(pady=5)

        self.categories_listbox = tk.Listbox(self.categories_frame, 
                                             bg="#2a2a2a", fg="white", selectbackground="#007ACC",
                                             borderwidth=0, highlightthickness=0, relief=tk.FLAT,
                                             font=("Segoe UI", 10))
        self.categories_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.categories_listbox.bind("<<ListboxSelect>>", self.on_category_select)

        self.category_buttons_frame = ttk.Frame(self.categories_frame, style="Dark.TFrame")
        self.category_buttons_frame.pack(fill=tk.X, pady=5) # pack остался, т.к. кнопки занимают всю ширину

        self.add_category_button = ttk.Button(self.category_buttons_frame, text="Добавить", command=self.add_category, style="Blue.TButton")
        self.add_category_button.pack(side=tk.LEFT, expand=True, padx=2)

        self.rename_category_button = ttk.Button(self.category_buttons_frame, text="Переименовать", command=self.rename_category, style="Blue.TButton")
        self.rename_category_button.pack(side=tk.LEFT, expand=True, padx=2)
        
        self.delete_category_button = ttk.Button(self.category_buttons_frame, text="Удалить", command=self.delete_category, style="Blue.TButton")
        self.delete_category_button.pack(side=tk.LEFT, expand=True, padx=2)

        self.export_button = ttk.Button(self.category_buttons_frame, text="Экспорт данных", command=self.export_data, style="Blue.TButton")
        self.export_button.pack(side=tk.LEFT, expand=True, padx=2)

        self.import_button = ttk.Button(self.category_buttons_frame, text="Импорт данных", command=self.import_data, style="Blue.TButton")
        self.import_button.pack(side=tk.LEFT, expand=True, padx=2)

        # --- Правая панель: Программы и Детали ---
        self.right_panel_frame = ttk.Frame(self.paned_window, style="Dark.TFrame")
        self.paned_window.add(self.right_panel_frame, weight=3)

        self.program_details_paned_window = ttk.PanedWindow(self.right_panel_frame, orient=tk.VERTICAL, style="Dark.TPanedwindow")
        self.program_details_paned_window.pack(fill=tk.BOTH, expand=True)

        # Фрейм для списка программ
        self.programs_frame = ttk.Frame(self.program_details_paned_window, style="Dark.TFrame")
        self.program_details_paned_window.add(self.programs_frame, weight=2) # Weight 2, чтобы программы занимали больше места

        self.programs_label = ttk.Label(self.programs_frame, text="Программы", style="Dark.TLabel", font=("Segoe UI", 12, "bold"))
        self.programs_label.pack(pady=5)

        # Фрейм для поиска и сортировки (используем grid для лучшего контроля)
        self.search_and_sort_frame = ttk.Frame(self.programs_frame, style="Dark.TFrame")
        self.search_and_sort_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        self.search_and_sort_frame.grid_columnconfigure(1, weight=1) # Entry будет растягиваться
        self.search_and_sort_frame.grid_columnconfigure(3, weight=0) # ComboBox не будет растягиваться

        self.search_label = ttk.Label(self.search_and_sort_frame, text="Поиск:", style="Dark.TLabel")
        self.search_label.grid(row=0, column=0, padx=(0, 5), sticky="w")

        self.search_entry = ttk.Entry(self.search_and_sort_frame, style="Dark.TEntry")
        self.search_entry.grid(row=0, column=1, sticky="ew") # sticky="ew" для растягивания по ширине
        self.search_entry.bind("<KeyRelease>", self.filter_programs)

        self.sort_label = ttk.Label(self.search_and_sort_frame, text="Сортировка:", style="Dark.TLabel")
        self.sort_label.grid(row=0, column=2, padx=(10, 5), sticky="w")

        self.sort_options = ["Имя (А-Я)", "Имя (Я-А)", "Тип (А-Я)", "Тип (Я-А)"]
        self.sort_var = tk.StringVar(self.search_and_sort_frame)
        self.sort_var.set(self.sort_options[0]) 
        self.sort_var.trace("w", self.on_sort_change) 

        self.sort_combobox = ttk.Combobox(self.search_and_sort_frame, 
                                          textvariable=self.sort_var, 
                                          values=self.sort_options, 
                                          state="readonly", 
                                          width=15,
                                          style="Dark.TEntry") 
        self.sort_combobox.grid(row=0, column=3, padx=(0, 5), sticky="e") # sticky="e" для прижимания к правому краю

        self.programs_treeview = ttk.Treeview(self.programs_frame, style="Dark.Treeview", show="tree headings")
        self.programs_treeview.heading("#0", text="Название программы", anchor=tk.W)
        self.programs_treeview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5) # Treeview всегда должен растягиваться
        self.programs_treeview.bind("<<TreeviewSelect>>", self.on_program_select)
        self.programs_treeview.bind("<Double-1>", self.run_selected_program)
        self.programs_treeview.bind("<Button-3>", self._on_program_right_click)

        # Фреймы кнопок - используем grid, чтобы они правильно выстраивались и растягивались
        self.program_buttons_frame = ttk.Frame(self.programs_frame, style="Dark.TFrame")
        self.program_buttons_frame.pack(fill=tk.X, pady=5) # pack для фрейма кнопок
        for i in range(4): self.program_buttons_frame.grid_columnconfigure(i, weight=1) # Все колонки с кнопками должны растягиваться

        self.add_program_button = ttk.Button(self.program_buttons_frame, text="Добавить", command=self.add_program, style="Blue.TButton")
        self.add_program_button.grid(row=0, column=0, padx=2, sticky="ew") # sticky="ew" для кнопок

        self.run_program_button = ttk.Button(self.program_buttons_frame, text="Запустить", command=self.run_selected_program, style="Blue.TButton")
        self.run_program_button.grid(row=0, column=1, padx=2, sticky="ew")
        
        self.rename_program_button = ttk.Button(self.program_buttons_frame, text="Переименовать", command=self.rename_program, style="Blue.TButton")
        self.rename_program_button.grid(row=0, column=2, padx=2, sticky="ew")

        self.delete_program_button = ttk.Button(self.program_buttons_frame, text="Удалить", command=self.delete_program, style="Blue.TButton")
        self.delete_program_button.grid(row=0, column=3, padx=2, sticky="ew")

        self.favorite_buttons_frame = ttk.Frame(self.programs_frame, style="Dark.TFrame")
        self.favorite_buttons_frame.pack(fill=tk.X, pady=5) # pack для фрейма кнопок
        for i in range(3): self.favorite_buttons_frame.grid_columnconfigure(i, weight=1) # Все колонки с кнопками должны растягиваться

        self.add_favorite_button = ttk.Button(self.favorite_buttons_frame, text="Добавить в Избранное", command=self.add_selected_to_favorites, style="Blue.TButton")
        self.add_favorite_button.grid(row=0, column=0, padx=2, sticky="ew")

        self.remove_favorite_button = ttk.Button(self.favorite_buttons_frame, text="Удалить из Избранного", command=self.remove_selected_from_favorites, style="Blue.TButton")
        self.remove_favorite_button.grid(row=0, column=1, padx=2, sticky="ew")

        self.open_location_button = ttk.Button(self.favorite_buttons_frame, text="Открыть расположение файла", command=self.open_selected_file_location, style="Blue.TButton")
        self.open_location_button.grid(row=0, column=2, padx=2, sticky="ew")
        self.open_location_button.config(state=tk.DISABLED)

        # Фрейм для деталей программы
        self.details_frame = ttk.Frame(self.program_details_paned_window, style="Dark.TFrame")
        self.program_details_paned_window.add(self.details_frame, weight=1) # Weight 1, чтобы детали занимали меньше места

        self.details_label = ttk.Label(self.details_frame, text="Детали программы", style="Dark.TLabel", font=("Segoe UI", 12, "bold"))
        self.details_label.pack(pady=5)
        
        self.details_form_frame = ttk.Frame(self.details_frame, style="Dark.TFrame")
        self.details_form_frame.pack(fill=tk.X, padx=5, pady=5)
        self.details_form_frame.grid_columnconfigure(1, weight=1) # Поле ввода должно растягиваться

        ttk.Label(self.details_form_frame, text="Аргументы:", style="Dark.TLabel").grid(row=0, column=0, sticky="w", pady=2)
        self.args_entry = ttk.Entry(self.details_form_frame, style="Dark.TEntry")
        self.args_entry.grid(row=0, column=1, sticky="ew", padx=(5,0), pady=2)
        self.args_entry.bind("<KeyRelease>", self.on_details_change)

        ttk.Label(self.details_form_frame, text="Рабочий каталог:", style="Dark.TLabel").grid(row=1, column=0, sticky="w", pady=2)
        self.working_dir_entry = ttk.Entry(self.details_form_frame, style="Dark.TEntry")
        self.working_dir_entry.grid(row=1, column=1, sticky="ew", padx=(5,0), pady=2)
        self.working_dir_entry.bind("<KeyRelease>", self.on_details_change)

        self.browse_working_dir_button = ttk.Button(self.details_form_frame, text="Обзор...", command=self.browse_working_directory, style="Blue.TButton")
        self.browse_working_dir_button.grid(row=1, column=2, padx=(5,0), pady=2)
        
        ttk.Label(self.details_frame, text="Заметки:", style="Dark.TLabel").pack(pady=(5,0), padx=5, anchor="w")
        self.note_text = tk.Text(self.details_frame, 
                                 height=5, wrap=tk.WORD, 
                                 bg="#333333", fg="white", 
                                 insertbackground="white", 
                                 borderwidth=1, relief="solid",
                                 font=("Segoe UI", 10))
        self.note_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5) # Заметка должна растягиваться
        self.note_text.bind("<KeyRelease>", self.on_details_change) 

        self.save_details_button = ttk.Button(self.details_frame, text="Сохранить детали", command=self.save_program_details, style="Blue.TButton")
        self.save_details_button.pack(pady=5)
        self.save_details_button.config(state=tk.DISABLED)
        
        self.selected_program_path_for_details = None

        self.display_categories()
        
        last_category = self.data_manager.get_last_selected_category()
        if last_category:
            try:
                index = self.data_manager.get_categories().index(last_category)
                self.categories_listbox.selection_set(index)
                self.categories_listbox.activate(index)
                self.on_category_select()
            except ValueError:
                pass

        self.update_program_details_ui()

    def display_categories(self):
        self.categories_listbox.delete(0, tk.END)
        for category in self.data_manager.get_categories():
            self.categories_listbox.insert(tk.END, category)

    def add_category(self):
        category_name = simpledialog.askstring("Добавить категорию", "Введите название новой категории:")
        if category_name:
            category_name = category_name.strip()
            if not category_name:
                messagebox.showwarning("Предупреждение", "Название категории не может быть пустым.")
                return
            if category_name == "Избранное":
                messagebox.showwarning("Предупреждение", "Категория 'Избранное' является системной и не может быть добавлена вручную.")
                return

            if self.data_manager.add_category(category_name):
                self.display_categories()
                self.data_manager.save_data()
                messagebox.showinfo("Успех", f"Категория '{category_name}' добавлена.")
            # else: DataManager уже показывает предупреждение

    def rename_category(self, event=None):
        selected_index = self.categories_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Предупреждение", "Выберите категорию для переименования.")
            return

        old_name = self.categories_listbox.get(selected_index[0])
        if old_name == "Избранное":
            messagebox.showwarning("Предупреждение", "Категория 'Избранное' является системной и не может быть переименована.")
            return

        new_name = simpledialog.askstring("Переименовать категорию", f"Введите новое название для '{old_name}':", initialvalue=old_name)

        if new_name and new_name != old_name:
            new_name = new_name.strip()
            if not new_name:
                messagebox.showwarning("Предупреждение", "Новое название категории не может быть пустым.")
                return
            if new_name == "Избранное":
                messagebox.showwarning("Предупреждение", "Нельзя переименовать категорию в 'Избранное', так как это системная категория.")
                return

            if self.data_manager.rename_category(old_name, new_name):
                self.display_categories()
                try:
                    new_index = self.data_manager.get_categories().index(new_name)
                    self.categories_listbox.selection_set(new_index)
                    self.categories_listbox.activate(new_index)
                    self.data_manager.set_last_selected_category(new_name)
                    self.data_manager.save_data()
                    self.display_programs()
                except ValueError:
                    pass
                messagebox.showinfo("Успех", f"Категория '{old_name}' переименована в '{new_name}'.")
            else:
                messagebox.showwarning("Предупреждение", "Не удалось переименовать категорию. Возможно, новое название уже занято.")
        elif new_name == old_name:
            messagebox.showinfo("Информация", "Название не изменилось.")
        else: # Пользователь нажал Отмена
            pass

    def delete_category(self):
        selected_index = self.categories_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Предупреждение", "Выберите категорию для удаления.")
            return

        category_name = self.categories_listbox.get(selected_index[0])
        if category_name == "Избранное":
            messagebox.showwarning("Предупреждение", "Категория 'Избранное' является системной и не может быть удалена.")
            return

        confirm = messagebox.askyesno("Удалить категорию", f"Вы уверены, что хотите удалить категорию '{category_name}' и все ее программы?")
        
        if confirm:
            self.data_manager.delete_category(category_name)
            self.display_categories()
            self.programs_treeview.delete(*self.programs_treeview.get_children())
            self.data_manager.save_data()
            messagebox.showinfo("Успех", f"Категория '{category_name}' удалена.")
            self.data_manager.set_last_selected_category(None)
            self.update_program_details_ui()

    def on_category_select(self, event=None):
        selected_index = self.categories_listbox.curselection()
        if selected_index:
            category_name = self.categories_listbox.get(selected_index[0])
            self.data_manager.set_current_category_name(category_name)
            self.data_manager.set_last_selected_category(category_name)
            self.display_programs()
        else:
            self.data_manager.set_current_category_name(None)
            self.programs_treeview.delete(*self.programs_treeview.get_children())
            self.update_program_details_ui()

    def display_programs(self):
        current_category = self.data_manager.get_current_category_name()
        
        for item in self.programs_treeview.get_children():
            self.programs_treeview.delete(item)
        self.icon_references.clear()

        if current_category:
            programs = self.data_manager.get_programs_in_category(current_category)
            
            self._apply_sort(programs)

            for program_data in programs:
                program_name = program_data.get('name')
                program_path = program_data.get('path')
                
                icon = None
                if program_path:
                    icon = get_icon_from_exe(program_path, size=(32, 32))
                    if icon:
                        self.icon_references[program_path] = icon 

                self.programs_treeview.insert("", tk.END, text=program_name, image=icon, values=(program_path,))

        self.filter_programs()
        self.programs_treeview.selection_remove(self.programs_treeview.selection())
        self.update_program_details_ui() 

    def add_program(self):
        current_category = self.data_manager.get_current_category_name()
        if not current_category:
            messagebox.showwarning("Предупреждение", "Сначала выберите категорию.")
            return
        if current_category == "Избранное":
            messagebox.showwarning("Предупреждение", "Программы нельзя добавлять напрямую в категорию 'Избранное'. Используйте кнопку 'Добавить в Избранное' из других категорий.")
            return

        file_path = filedialog.askopenfilename(
            title="Выберите программу, файл или скрипт",
            filetypes=(("Исполняемые файлы", "*.exe"),
                       ("Все файлы", "*.*"),
                       ("Документы", "*.doc *.docx *.pdf *.txt"),
                       ("Веб-ссылки", "*.url"),
                       ("Скрипты", "*.py *.bat *.ps1"))
        )
        if file_path:
            program_name = os.path.basename(file_path)
            if file_path.lower().endswith(".url"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for line in content.splitlines():
                            if line.startswith("URL="):
                                program_name = line[4:].strip() 
                                break
                except Exception:
                    pass

            self._show_add_edit_program_dialog(
                current_category=current_category,
                program_name=program_name,
                program_path=file_path,
                is_edit=False
            )
        else:
            messagebox.showwarning("Отмена", "Добавление элемента отменено.")

    def run_selected_program(self, event=None):
        program_data = self._get_selected_program_details()
        if not program_data:
            messagebox.showwarning("Предупреждение", "Выберите программу для запуска.")
            return

        program_name = program_data['name']
        program_path = program_data['path']
        
        full_program_data = self.data_manager.get_program_data_by_path(program_path)
        arguments = full_program_data.get('arguments', '').strip() if full_program_data else ''
        working_directory = full_program_data.get('working_directory', '').strip() if full_program_data else ''

        if program_path:
            try:
                if not os.path.exists(program_path):
                    messagebox.showerror("Ошибка", f"Файл не найден: {program_path}. Возможно, он был перемещен или удален.")
                    return
                
                command = [program_path]
                if arguments:
                    args_list = shlex.split(arguments) # Используем shlex для корректного парсинга
                    command.extend(args_list)

                if working_directory and not os.path.isdir(working_directory):
                    messagebox.showwarning("Предупреждение", f"Указанный рабочий каталог не существует или недоступен: {working_directory}. Запуск будет выполнен из текущего каталога.")
                    working_directory = None 

                if program_path.lower().endswith(".exe") or program_path.lower().endswith((".py", ".bat", ".ps1")):
                    subprocess.Popen(command, cwd=working_directory if working_directory else None)
                elif program_path.lower().endswith(".url"):
                     webbrowser.open(program_path)
                else:
                    if arguments or working_directory:
                         messagebox.showwarning("Предупреждение", "Аргументы и рабочий каталог поддерживаются только для исполняемых файлов/скриптов. Будет открыт только файл.")
                    os.startfile(program_path)

            except Exception as e:
                messagebox.showerror("Ошибка запуска", f"Не удалось запустить '{program_name}': {e}")
                import traceback
                traceback.print_exc()
        else:
            messagebox.showwarning("Ошибка", "Путь к программе не указан.")

    def rename_program(self):
        program_data = self._get_selected_program_details()
        if not program_data:
            messagebox.showwarning("Предупреждение", "Выберите программу для переименования.")
            return

        old_name = program_data['name']
        program_path = program_data['path']

        current_category = self.data_manager.get_current_category_name()
        if current_category == "Избранное":
            messagebox.showwarning("Предупреждение", "Переименование программ в категории 'Избранное' не поддерживается. Переименуйте её в исходной категории.")
            return

        full_program_data = self.data_manager.get_program_data_by_path(program_path)
        if full_program_data:
            self._show_add_edit_program_dialog(
                current_category=current_category,
                program_name=old_name,
                program_path=program_path,
                arguments=full_program_data.get('arguments', ''),
                working_directory=full_program_data.get('working_directory', ''),
                is_edit=True
            )
        else:
            messagebox.showerror("Ошибка", "Не удалось получить полные данные программы для переименования.")

    def delete_program(self):
        program_data = self._get_selected_program_details()
        if not program_data:
            messagebox.showwarning("Предупреждение", "Выберите программу для удаления.")
            return

        program_name = program_data['name']
        program_path = program_data['path']

        current_category = self.data_manager.get_current_category_name()
        if current_category == "Избранное":
            messagebox.showwarning("Предупреждение", "Программы не могут быть удалены из категории 'Избранное' таким способом. Используйте кнопку 'Удалить из Избранного'.")
            return

        confirm = messagebox.askyesno("Удалить программу", f"Вы уверены, что хотите удалить программу '{program_name}'?")
        
        if confirm:
            if self.data_manager.delete_program(current_category, program_name):
                if self.data_manager.is_favorite(program_path):
                    self.data_manager.remove_favorite(program_path)

                self.display_programs()
                self.data_manager.save_data()
                messagebox.showinfo("Успех", f"Программа '{program_name}' удалена.")
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить программу.")

    def on_program_select(self, event=None):
        self.update_program_details_ui()

    def update_program_details_ui(self):
        program_data = self._get_selected_program_details()
        
        self.args_entry.config(state=tk.DISABLED)
        self.working_dir_entry.config(state=tk.DISABLED)
        self.browse_working_dir_button.config(state=tk.DISABLED)
        self.note_text.config(state=tk.DISABLED)
        self.save_details_button.config(state=tk.DISABLED)
        self.args_entry.delete(0, tk.END)
        self.working_dir_entry.delete(0, tk.END)
        self.note_text.delete("1.0", tk.END)

        if program_data:
            self.selected_program_path_for_details = program_data['path']
            
            program_full_data = self.data_manager.get_program_data_by_path(self.selected_program_path_for_details)
            if program_full_data:
                self.args_entry.config(state=tk.NORMAL)
                self.working_dir_entry.config(state=tk.NORMAL)
                self.browse_working_dir_button.config(state=tk.NORMAL)
                self.note_text.config(state=tk.NORMAL)

                self.args_entry.insert(0, program_full_data.get('arguments', ''))
                self.working_dir_entry.insert(0, program_full_data.get('working_directory', ''))
                self.note_text.insert("1.0", program_full_data.get('note', ''))
                
            self.add_favorite_button.config(state=tk.NORMAL)
            self.remove_favorite_button.config(state=tk.NORMAL)
            if self.data_manager.is_favorite(self.selected_program_path_for_details):
                self.add_favorite_button.config(state=tk.DISABLED)
            else:
                self.remove_favorite_button.config(state=tk.DISABLED)
            
            if self.selected_program_path_for_details and os.path.exists(self.selected_program_path_for_details):
                self.open_location_button.config(state=tk.NORMAL)
            else:
                self.open_location_button.config(state=tk.DISABLED)

        else:
            self.selected_program_path_for_details = None
            self.add_favorite_button.config(state=tk.DISABLED)
            self.remove_favorite_button.config(state=tk.DISABLED)
            self.open_location_button.config(state=tk.DISABLED)

    def on_details_change(self, event=None):
        self.save_details_button.config(state=tk.NORMAL)

    def save_program_details(self):
        if not self.selected_program_path_for_details:
            messagebox.showwarning("Предупреждение", "Выберите программу для сохранения деталей.")
            return
        
        new_note = self.note_text.get("1.0", tk.END).strip()
        new_arguments = self.args_entry.get().strip()
        new_working_directory = self.working_dir_entry.get().strip()

        if new_working_directory and not os.path.isdir(new_working_directory):
            confirm = messagebox.askyesno(
                "Рабочий каталог не найден", 
                f"Указанный рабочий каталог '{new_working_directory}' не существует. Сохранить все равно?", 
                icon='warning'
            )
            if not confirm:
                return 

        if self.data_manager.update_program_details_with_full_data(
            self.selected_program_path_for_details, 
            note=new_note, 
            arguments=new_arguments, 
            working_directory=new_working_directory
        ):
            self.data_manager.save_data()
            messagebox.showinfo("Успех", "Детали программы сохранены.")
            self.save_details_button.config(state=tk.DISABLED)
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить детали программы.")

    def browse_working_directory(self):
        directory = filedialog.askdirectory(title="Выберите рабочий каталог")
        if directory:
            self.working_dir_entry.delete(0, tk.END)
            self.working_dir_entry.insert(0, directory)
            self.on_details_change() 

    def add_selected_to_favorites(self):
        program_data = self._get_selected_program_details()
        if not program_data:
            messagebox.showwarning("Предупреждение", "Выберите программу, чтобы добавить в Избранное.")
            return
        
        program_name = program_data['name']
        program_path = program_data['path']

        program_full_data = self.data_manager.get_program_data_by_path(program_path)
        
        if program_full_data:
            if self.data_manager.add_favorite(program_full_data):
                self.data_manager.save_data()
                messagebox.showinfo("Успех", f"'{program_name}' добавлен в Избранное.")
                self.update_program_details_ui()
            else:
                messagebox.showwarning("Предупреждение", f"'{program_name}' уже есть в Избранном.")
        else:
            messagebox.showerror("Ошибка", "Не удалось получить данные о выбранной программе.")

    def remove_selected_from_favorites(self):
        program_data = self._get_selected_program_details()
        if not program_data:
            messagebox.showwarning("Предупреждение", "Выберите программу, чтобы удалить из Избранного.")
            return
        
        program_name = program_data['name']
        program_path = program_data['path']

        if self.data_manager.remove_favorite(program_path):
            self.data_manager.save_data()
            messagebox.showinfo("Успех", f"'{program_name}' удален из Избранного.")
            
            if self.data_manager.get_current_category_name() == "Избранное":
                self.display_programs()
            else:
                self.update_program_details_ui()

    def open_selected_file_location(self):
        program_data = self._get_selected_program_details()
        if not program_data:
            messagebox.showwarning("Предупреждение", "Выберите программу, чтобы открыть ее расположение.")
            return

        program_path = program_data['path']
        if program_path:
            open_file_location(program_path)
        else:
            messagebox.showwarning("Предупреждение", "Путь к выбранной программе не указан.")

    def filter_programs(self, event=None):
        search_query = self.search_entry.get().lower()
        current_category = self.data_manager.get_current_category_name()
        
        for item in self.programs_treeview.get_children():
            self.programs_treeview.delete(item)
        self.icon_references.clear()

        if current_category:
            if current_category == "Избранное":
                programs_to_filter = self.data_manager.get_favorites()
            else:
                programs_to_filter = self.data_manager.get_programs_in_category(current_category)

            filtered_programs = []
            for program_data in programs_to_filter:
                program_name = program_data.get('name', '').lower()
                if search_query in program_name:
                    filtered_programs.append(program_data)
            
            self._apply_sort(filtered_programs)

            for program_data in filtered_programs:
                program_name = program_data.get('name')
                program_path = program_data.get('path')
                
                icon = None
                if program_path:
                    icon = get_icon_from_exe(program_path, size=(32, 32))
                    if icon:
                        self.icon_references[program_path] = icon 

                self.programs_treeview.insert("", tk.END, text=program_name, image=icon, values=(program_path,))

        self.programs_treeview.selection_remove(self.programs_treeview.selection())
        self.update_program_details_ui()

    def _get_selected_program_details(self):
        selected_item = self.programs_treeview.selection()
        if not selected_item:
            return None
        
        item_id = selected_item[0]
        program_name = self.programs_treeview.item(item_id, "text")
        program_path = self.programs_treeview.item(item_id, "values")[0]
        
        return {'id': item_id, 'name': program_name, 'path': program_path}

    def _on_program_right_click(self, event):
        item_id = self.programs_treeview.identify_row(event.y)
        if item_id:
            self.programs_treeview.selection_set(item_id)
            self.on_program_select()

        program_data = self._get_selected_program_details()
        
        menu = tk.Menu(self.master, tearoff=0)

        menu.add_command(label="Запустить программу", command=self.run_selected_program, 
                          state=tk.NORMAL if program_data else tk.DISABLED)
        menu.add_command(label="Открыть расположение файла", command=self.open_selected_file_location,
                          state=tk.NORMAL if program_data and program_data['path'] and os.path.exists(program_data['path']) else tk.DISABLED)
        
        menu.add_separator() 

        menu.add_command(label="Редактировать", command=self.edit_program_from_context,
                          state=tk.NORMAL if program_data and self.data_manager.get_current_category_name() != "Избранное" else tk.DISABLED)
        
        current_category = self.data_manager.get_current_category_name()
        if program_data and current_category != "Избранное":
            menu.add_command(label="Переименовать", command=self.rename_program) 
        else:
            menu.add_command(label="Переименовать", state=tk.DISABLED)

        menu.add_separator() 
        
        if program_data:
            if self.data_manager.is_favorite(program_data['path']):
                menu.add_command(label="Удалить из Избранного", command=self.remove_selected_from_favorites)
                menu.entryconfig("Удалить из Избранного", state=tk.NORMAL)
                menu.add_command(label="Добавить в Избранное", state=tk.DISABLED)
            else:
                menu.add_command(label="Добавить в Избранное", command=self.add_selected_to_favorites)
                menu.entryconfig("Добавить в Избранное", state=tk.NORMAL)
                menu.add_command(label="Удалить из Избранного", state=tk.DISABLED)
        else:
            menu.add_command(label="Добавить в Избранное", state=tk.DISABLED)
            menu.add_command(label="Удалить из Избранного", state=tk.DISABLED)

        menu.add_separator()

        if program_data and current_category != "Избранное":
            menu.add_command(label="Удалить", command=self.delete_program)
        else:
            menu.add_command(label="Удалить", state=tk.DISABLED)

        menu.add_separator()

        menu.add_command(label="Копировать путь к файлу", command=self.copy_selected_program_path,
                          state=tk.NORMAL if program_data and program_data['path'] else tk.DISABLED)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def copy_selected_program_path(self):
        program_data = self._get_selected_program_details()
        if program_data and program_data['path']:
            self.master.clipboard_clear()
            self.master.clipboard_append(program_data['path'])
            messagebox.showinfo("Копирование", "Путь к файлу скопирован в буфер обмена.")
        else:
            messagebox.showwarning("Предупреждение", "Нечего копировать. Путь к файлу не найден.")

    def edit_program_from_context(self):
        program_data = self._get_selected_program_details()
        if not program_data:
            messagebox.showwarning("Предупреждение", "Выберите программу для редактирования.")
            return
        
        current_category = self.data_manager.get_current_category_name()
        if current_category == "Избранное":
            messagebox.showwarning("Предупреждение", "Программы в категории 'Избранное' не могут быть отредактированы напрямую. Редактируйте их в исходной категории.")
            return

        full_program_data = self.data_manager.get_program_data_by_path(program_data['path'])
        if full_program_data:
            self._show_add_edit_program_dialog(
                current_category=current_category,
                program_name=full_program_data.get('name'),
                program_path=full_program_data.get('path'),
                arguments=full_program_data.get('arguments', ''),
                working_directory=full_program_data.get('working_directory', ''),
                is_edit=True
            )
        else:
            messagebox.showerror("Ошибка", "Не удалось получить полные данные программы для редактирования.")


    def _show_add_edit_program_dialog(self, current_category, program_name="", program_path="", arguments="", working_directory="", is_edit=False):
        dialog_title = "Редактировать программу" if is_edit else "Добавить программу/файл"
        
        dialog = tk.Toplevel(self.master)
        dialog.title(dialog_title)
        dialog.transient(self.master)
        dialog.grab_set()
        dialog.focus_set()

        dialog.configure(bg="#1a1a1a")
        
        # Настройка растягивания колонок в диалоге
        dialog.grid_columnconfigure(1, weight=1) # Колонка с полями ввода должна растягиваться

        ttk.Label(dialog, text="Название:", style="Dark.TLabel").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        name_entry = ttk.Entry(dialog, style="Dark.TEntry", width=50) # width может быть ориентировочным
        name_entry.insert(0, program_name)
        name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew") # sticky="ew" для растягивания

        ttk.Label(dialog, text="Путь к файлу:", style="Dark.TLabel").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        path_entry = ttk.Entry(dialog, style="Dark.TEntry", width=50)
        path_entry.insert(0, program_path)
        path_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        def browse_path():
            new_file_path = filedialog.askopenfilename(
                title="Выберите новый путь к программе, файлу или скрипту",
                filetypes=(("Исполняемые файлы", "*.exe"),
                           ("Все файлы", "*.*"),
                           ("Документы", "*.doc *.docx *.pdf *.txt"),
                           ("Веб-ссылки", "*.url"),
                           ("Скрипты", "*.py *.bat *.ps1"))
            )
            if new_file_path:
                path_entry.delete(0, tk.END)
                path_entry.insert(0, new_file_path)
                if not is_edit or name_entry.get() == program_name:
                    name_entry.delete(0, tk.END)
                    name_entry.insert(0, os.path.basename(new_file_path))

        browse_path_button = ttk.Button(dialog, text="Обзор...", command=browse_path, style="Blue.TButton")
        browse_path_button.grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(dialog, text="Аргументы:", style="Dark.TLabel").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        args_entry = ttk.Entry(dialog, style="Dark.TEntry", width=50)
        args_entry.insert(0, arguments)
        args_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        ttk.Label(dialog, text="Рабочий каталог:", style="Dark.TLabel").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        working_dir_entry = ttk.Entry(dialog, style="Dark.TEntry", width=50)
        working_dir_entry.insert(0, working_directory)
        working_dir_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        def browse_working_dir():
            directory = filedialog.askdirectory(title="Выберите рабочий каталог", parent=dialog)
            if directory:
                working_dir_entry.delete(0, tk.END)
                working_dir_entry.insert(0, directory)

        browse_working_dir_button = ttk.Button(dialog, text="Обзор...", command=browse_working_dir, style="Blue.TButton")
        browse_working_dir_button.grid(row=3, column=2, padx=5, pady=5)

        # Фрейм для кнопок сохранения/отмены в диалоге
        button_frame = ttk.Frame(dialog, style="Dark.TFrame")
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        button_frame.grid_columnconfigure(0, weight=1) # Растягиваем первую колонку
        button_frame.grid_columnconfigure(1, weight=1) # Растягиваем вторую колонку


        def save_program():
            new_name = name_entry.get().strip()
            new_path = path_entry.get().strip()
            new_arguments = args_entry.get().strip()
            new_working_directory = working_dir_entry.get().strip()

            if not new_name:
                messagebox.showwarning("Предупреждение", "Название программы не может быть пустым.", parent=dialog)
                return
            if not new_path:
                messagebox.showwarning("Предупреждение", "Путь к файлу не может быть пустым.", parent=dialog)
                return
            
            if not os.path.exists(new_path):
                confirm_missing_path = messagebox.askyesno(
                    "Путь к файлу не найден", 
                    f"Указанный путь '{new_path}' не существует. Продолжить сохранение?", 
                    parent=dialog
                )
                if not confirm_missing_path:
                    return

            if new_working_directory and not os.path.isdir(new_working_directory):
                 confirm_missing_wd = messagebox.askyesno(
                    "Рабочий каталог не найден", 
                    f"Указанный рабочий каталог '{new_working_directory}' не существует. Сохранить все равно?", 
                    parent=dialog
                )
                 if not confirm_missing_wd:
                    return

            if is_edit:
                if self.data_manager.update_program_details(
                    current_category, 
                    program_path, 
                    new_name, 
                    new_path
                ):
                    self.data_manager.update_program_details_with_full_data(
                        new_path, 
                        arguments=new_arguments,
                        working_directory=new_working_directory
                    )
                    self.data_manager.save_data()
                    self.display_programs()
                    messagebox.showinfo("Успех", "Данные программы обновлены.", parent=dialog)
                    dialog.destroy()
                else:
                    messagebox.showerror("Ошибка", "Не удалось обновить данные программы. Возможно, новое название/путь уже существуют в этой категории.", parent=dialog)
            else: 
                item_type = "exe"
                if new_path.lower().endswith((".doc", ".docx", ".pdf", ".txt")):
                    item_type = "document"
                elif new_path.lower().endswith((".url", ".lnk")):
                    item_type = "link"
                elif os.path.isdir(new_path):
                    item_type = "folder"
                elif new_path.lower().endswith((".py", ".bat", ".ps1")):
                    item_type = "script"
                
                if self.data_manager.add_program(
                    current_category, 
                    new_name, 
                    new_path, 
                    item_type, 
                    arguments=new_arguments, 
                    working_directory=new_working_directory
                ):
                    self.display_programs()
                    self.data_manager.save_data()
                    messagebox.showinfo("Успех", f"'{new_name}' добавлен в категорию '{current_category}'.", parent=dialog)
                    dialog.destroy()
                else:
                    messagebox.showerror("Ошибка", "Не удалось добавить программу. Возможно, программа с таким именем/путем уже существует.", parent=dialog)

        save_button = ttk.Button(button_frame, text="Сохранить", command=save_program, style="Blue.TButton")
        save_button.grid(row=0, column=0, padx=5, sticky="ew")

        cancel_button = ttk.Button(button_frame, text="Отмена", command=dialog.destroy, style="Blue.TButton")
        cancel_button.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Центрирование диалога
        self.master.update_idletasks()
        dialog.update_idletasks() # Обновляем, чтобы получить корректный размер
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

    def on_sort_change(self, *args):
        self.display_programs()

    def _apply_sort(self, programs_list):
        sort_option = self.sort_var.get()

        if sort_option == "Имя (А-Я)":
            programs_list.sort(key=lambda x: x.get('name', '').lower())
        elif sort_option == "Имя (Я-А)":
            programs_list.sort(key=lambda x: x.get('name', '').lower(), reverse=True)
        elif sort_option == "Тип (А-Я)":
            programs_list.sort(key=lambda x: (x.get('type', '').lower(), x.get('name', '').lower()))
        elif sort_option == "Тип (Я-А)":
            programs_list.sort(key=lambda x: (x.get('type', '').lower(), x.get('name', '').lower()), reverse=True)

    def export_data(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Сохранить данные лаунчера как..."
        )
        if file_path:
            try:
                all_data = self.data_manager.get_all_data() 
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(all_data, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("Экспорт данных", f"Данные успешно экспортированы в:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка экспорта", f"Не удалось экспортировать данные: {e}")

    def import_data(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Выбрать файл для импорта данных"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_data = json.load(f)
                
                if not isinstance(imported_data, dict) or "categories" not in imported_data:
                    messagebox.showerror("Ошибка импорта", "Выбранный файл не является допустимым файлом данных лаунчера.")
                    return

                response = messagebox.askyesnocancel(
                    "Стратегия импорта",
                    "Вы хотите заменить текущие данные импортированными данными (Да), "
                    "объединить их (Нет), или отменить (Отмена)?\n\n"
                    "Да: Все текущие категории и программы будут удалены и заменены данными из файла.\n"
                    "Нет: Новые категории и программы будут добавлены, существующие будут обновлены, но ничего не будет удалено.",
                    icon='question'
                )

                if response is True: 
                    strategy = "replace"
                elif response is False: 
                    strategy = "merge"
                else: 
                    messagebox.showinfo("Импорт данных", "Импорт отменен.")
                    return
                
                self.data_manager.import_all_data(imported_data, strategy)
                self.data_manager.save_data()
                
                self.display_categories()
                self.display_programs()
                self.update_program_details_ui()
                messagebox.showinfo("Импорт данных", "Данные успешно импортированы и обновлены.")

            except json.JSONDecodeError:
                messagebox.showerror("Ошибка импорта", "Выбранный файл имеет неверный формат JSON.")
            except Exception as e:
                messagebox.showerror("Ошибка импорта", f"Не удалось импортировать данные: {e}")

def main():
    root = tk.Tk()
    app = AppLauncher(root)
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root, app.data_manager))
    root.mainloop()

def on_closing(root, data_manager):
    data_manager.set_window_geometry(root.winfo_geometry())
    data_manager.save_data()
    root.destroy()

if __name__ == "__main__":
    main()