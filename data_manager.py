import json
import os

class DataManager:
    def __init__(self, filename="launcher_data.json"):
        self.filename = filename
        self.data = {
            "categories": {},
            "last_selected_category": None,
            "window_geometry": "1000x600",
            "favorites": [] 
        }
        self.current_category_name = None

    def load_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    
                    # Инициализируем отсутствующие ключи с значениями по умолчанию
                    self.data["categories"] = loaded_data.get("categories", {})
                    self.data["last_selected_category"] = loaded_data.get("last_selected_category", None)
                    self.data["window_geometry"] = loaded_data.get("window_geometry", "1000x600")
                    self.data["favorites"] = loaded_data.get("favorites", []) 
                    
                    # Обеспечиваем наличие всех полей для существующих программ
                    for category, programs in self.data["categories"].items():
                        for program in programs:
                            self._ensure_program_fields(program)
                    for program in self.data["favorites"]:
                        self._ensure_program_fields(program)

            except json.JSONDecodeError:
                print(f"Ошибка чтения JSON из {self.filename}. Создан новый пустой файл.")
                self.data = {"categories": {}, "last_selected_category": None, "window_geometry": "1000x600", "favorites": []}
            except Exception as e:
                print(f"Неожиданная ошибка при загрузке данных: {e}")
                self.data = {"categories": {}, "last_selected_category": None, "window_geometry": "1000x600", "favorites": []}
        else:
            self.save_data()

    def save_data(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def _ensure_program_fields(self, program):
        """Гарантирует, что у словаря программы есть все необходимые поля."""
        if "note" not in program:
            program["note"] = ""
        if "arguments" not in program:
            program["arguments"] = ""
        if "working_directory" not in program:
            program["working_directory"] = ""
        if "type" not in program: # На случай, если старые записи не имели типа
            program["type"] = "exe" # По умолчанию
        return program

    def get_categories(self):
        return list(self.data["categories"].keys())

    def add_category(self, category_name):
        if category_name not in self.data["categories"]:
            self.data["categories"][category_name] = []
            return True
        return False

    def rename_category(self, old_name, new_name):
        if old_name in self.data["categories"] and new_name not in self.data["categories"]:
            self.data["categories"][new_name] = self.data["categories"].pop(old_name)
            if self.data["last_selected_category"] == old_name:
                self.data["last_selected_category"] = new_name
            if self.current_category_name == old_name:
                self.current_category_name = new_name
            return True
        return False

    def delete_category(self, category_name):
        if category_name in self.data["categories"]:
            del self.data["categories"][category_name]
            if self.data["last_selected_category"] == category_name:
                self.data["last_selected_category"] = None
            if self.current_category_name == category_name:
                self.current_category_name = None
            return True
        return False

    def get_programs_in_category(self, category_name):
        return self.data["categories"].get(category_name, [])

    def add_program(self, category_name, program_name, program_path, program_type="exe", arguments="", working_directory=""):
        if category_name in self.data["categories"]:
            for program in self.data["categories"][category_name]:
                if program.get('name') == program_name or program.get('path') == program_path:
                    return False 
            
            new_program_data = {
                "name": program_name,
                "path": program_path,
                "type": program_type,
                "note": "",
                "arguments": arguments,
                "working_directory": working_directory
            }
            self.data["categories"][category_name].append(new_program_data)
            return True
        return False
    
    def update_program_details(self, category_name, old_program_path, new_program_name, new_program_path):
        """
        Обновляет имя и/или путь к программе в указанной категории.
        Этот метод предназначен для обновления 'name' и 'path' из диалога редактирования/добавления.
        Он также обновит путь в избранном, если программа там есть.
        """
        program_updated = False
        
        # Обновляем в текущей категории
        if category_name in self.data["categories"]:
            for program in self.data["categories"][category_name]:
                if program.get('path') == old_program_path:
                    program['name'] = new_program_name
                    program['path'] = new_program_path
                    program_updated = True
                    break
        
        # Также обновляем в избранном, если программа там есть
        for fav_program in self.data["favorites"]:
            if fav_program.get('path') == old_program_path:
                fav_program['name'] = new_program_name
                fav_program['path'] = new_program_path
                # Note, arguments, working_directory остаются прежними,
                # так как они управляются update_program_details_with_full_data

        return program_updated


    def delete_program(self, category_name, program_name):
        if category_name in self.data["categories"]:
            initial_len = len(self.data["categories"][category_name])
            self.data["categories"][category_name] = [
                p for p in self.data["categories"][category_name] if p.get('name') != program_name
            ]
            return len(self.data["categories"][category_name]) < initial_len
        return False

    def set_current_category_name(self, name):
        self.current_category_name = name

    def get_current_category_name(self):
        return self.current_category_name

    def set_last_selected_category(self, category_name):
        self.data["last_selected_category"] = category_name

    def get_last_selected_category(self):
        return self.data["last_selected_category"]

    def set_window_geometry(self, geometry_string):
        """Сохраняет строку геометрии окна."""
        self.data["window_geometry"] = geometry_string

    def get_window_geometry(self):
        """Возвращает сохраненную строку геометрии окна."""
        return self.data.get("window_geometry", "1000x600")

    def add_favorite(self, program_data):
        """
        Добавляет программу в список избранных.
        program_data должен быть полным словарем данных программы.
        """
        for fav_program in self.data["favorites"]:
            if fav_program.get('path') == program_data.get('path'):
                return False
        
        self._ensure_program_fields(program_data) # Гарантируем наличие всех полей
        self.data["favorites"].append(program_data)
        return True

    def remove_favorite(self, program_path):
        """Удаляет программу из списка избранных по пути."""
        initial_len = len(self.data["favorites"])
        self.data["favorites"] = [
            p for p in self.data["favorites"] if p.get('path') != program_path
        ]
        return len(self.data["favorites"]) < initial_len

    def get_favorites(self):
        """Возвращает список всех избранных программ."""
        return self.data["favorites"]
    
    def is_favorite(self, program_path):
        """Проверяет, является ли программа избранной по пути."""
        for fav_program in self.data["favorites"]:
            if fav_program.get('path') == program_path:
                return True
        return False

    def get_program_data_by_path(self, program_path):
        """
        Ищет и возвращает полный словарь данных программы по ее пути
        как в категориях, так и в избранном.
        Возвращает None, если программа не найдена.
        """
        for category, programs in self.data["categories"].items():
            for program in programs:
                if program.get('path') == program_path:
                    return self._ensure_program_fields(program) # Убедимся, что все поля есть
        
        for program in self.data["favorites"]:
            if program.get('path') == program_path:
                return self._ensure_program_fields(program) # Убедимся, что все поля есть
        
        return None

    def update_program_details_with_full_data(self, program_path, note=None, arguments=None, working_directory=None):
        """
        Обновляет заметку, аргументы и рабочий каталог для программы, найденной по ее пути.
        Если соответствующее значение None, оно не обновляется.
        """
        program = self.get_program_data_by_path(program_path)
        if program:
            if note is not None:
                program['note'] = note
            if arguments is not None:
                program['arguments'] = arguments
            if working_directory is not None:
                program['working_directory'] = working_directory
            return True
        return False

    def get_all_data(self):
        """Возвращает все сохраненные данные."""
        return self.data

    def import_all_data(self, imported_data, strategy="merge"):
        """
        Импортирует данные из внешнего источника.
        strategy: "replace" (заменяет все текущие данные) или "merge" (объединяет данные).
        """
        if strategy == "replace":
            self.data = {
                "categories": {},
                "last_selected_category": None,
                "window_geometry": self.data["window_geometry"], # Сохраняем текущую геометрию окна
                "favorites": []
            }

        # Импорт категорий
        for category_name, programs_list in imported_data.get("categories", {}).items():
            if category_name not in self.data["categories"]:
                self.data["categories"][category_name] = []
            
            for imported_program in programs_list:
                self._ensure_program_fields(imported_program) # Убедимся, что импортированная программа имеет все поля
                existing_program = next((p for p in self.data["categories"][category_name] if p.get('path') == imported_program.get('path')), None)
                if existing_program:
                    # Обновляем существующую программу
                    existing_program.update(imported_program)
                else:
                    self.data["categories"][category_name].append(imported_program)

        # Импорт избранного
        for imported_favorite in imported_data.get("favorites", []):
            self._ensure_program_fields(imported_favorite) # Убедимся, что импортированное избранное имеет все поля
            existing_favorite = next((f for f in self.data["favorites"] if f.get('path') == imported_favorite.get('path')), None)
            if existing_favorite:
                # Обновляем существующее избранное
                existing_favorite.update(imported_favorite)
            else:
                self.data["favorites"].append(imported_favorite)

        # Обновляем last_selected_category, если он есть в импортированных данных
        if "last_selected_category" in imported_data and imported_data["last_selected_category"] in self.data["categories"]:
            self.data["last_selected_category"] = imported_data["last_selected_category"]
        elif "last_selected_category" in self.data and self.data["last_selected_category"] not in self.data["categories"]:
             self.data["last_selected_category"] = None # Сбрасываем, если категория больше не существует