import os
import subprocess
import sys
from tkinter import messagebox

def open_file_location(path):
    """
    Открывает расположение файла или папки в проводнике (Windows)
    или файловом менеджере (macOS/Linux) и выделяет файл/папку, если возможно.
    """
    print(f"[DEBUG] open_file_location вызван с путем: {path}")

    if not path:
        messagebox.showwarning("Предупреждение", "Путь к файлу или папке не указан.")
        print("[DEBUG] Путь пустой.")
        return

    # НОВОЕ: Нормализуем путь для использования системных разделителей (обратные слеши для Windows)
    normalized_path = os.path.normpath(path)
    print(f"[DEBUG] Нормализованный путь: {normalized_path}")

    if not os.path.exists(normalized_path):
        messagebox.showwarning("Ошибка", f"Файл или папка не найдены: {normalized_path}")
        print(f"[DEBUG] Нормализованный путь не существует: {normalized_path}")
        return

    try:
        if sys.platform == "win32":
            print("[DEBUG] Обнаружена платформа: Windows.")
            if os.path.isfile(normalized_path):
                print(f"[DEBUG] Путь указывает на файл. Попытка: explorer /select, \"{normalized_path}\"")
                # Для Windows: используем subprocess.Popen с аргументами в виде списка.
                # '/select,' с запятой - это правильный синтаксис для explorer, чтобы выделить файл.
                subprocess.Popen(['explorer', '/select,', normalized_path])
            elif os.path.isdir(normalized_path):
                print(f"[DEBUG] Путь указывает на папку. Попытка: explorer \"{normalized_path}\"")
                subprocess.Popen(['explorer', normalized_path]) # Просто открываем папку
            else:
                print(f"[DEBUG] Путь существует, но не является файлом или папкой. Попытка открыть родительскую папку.")
                # Если путь существует, но это не файл и не папка (например, сетевая ссылка,
                # или что-то не совсем обычное), попытаемся открыть родительскую папку.
                parent_dir = os.path.dirname(normalized_path)
                if os.path.exists(parent_dir):
                    print(f"[DEBUG] Родительская папка найдена: '{parent_dir}'. Попытка: explorer \"{parent_dir}\"")
                    subprocess.Popen(['explorer', parent_dir])
                else:
                    messagebox.showwarning("Предупреждение", f"Не удалось определить тип объекта или найти родительскую папку для {normalized_path}.")
                    print(f"[DEBUG] Родительская папка также не найдена для {normalized_path}.")


        elif sys.platform == "darwin": # macOS
            print("[DEBUG] Обнаружена платформа: macOS.")
            # -R (reveal) открывает Finder и выделяет элемент
            subprocess.Popen(["open", "-R", normalized_path])

        else: # Linux (используем xdg-open для универсальности)
            print("[DEBUG] Обнаружена платформа: Linux/Unix.")
            # xdg-open является стандартным способом для открытия файлов/папок в большинстве DE
            if os.path.isfile(normalized_path):
                print(f"[DEBUG] Путь указывает на файл. Попытка: xdg-open \"{os.path.dirname(normalized_path)}\"")
                # Для файла, открываем содержащую папку. xdg-open обычно не выделяет файл.
                subprocess.Popen(["xdg-open", os.path.dirname(normalized_path)]) 
            elif os.path.isdir(normalized_path):
                print(f"[DEBUG] Путь указывает на папку. Попытка: xdg-open \"{normalized_path}\"")
                subprocess.Popen(["xdg-open", normalized_path]) # Открываем саму папку
            else:
                print(f"[DEBUG] Путь существует, но не является файлом или папкой. Попытка открыть родительскую папку.")
                # Fallback для Linux, если путь существует, но не является файлом/папкой.
                parent_dir = os.path.dirname(normalized_path)
                if os.path.exists(parent_dir):
                    print(f"[DEBUG] Родительская папка найдена: '{parent_dir}'. Попытка: xdg-open \"{parent_dir}\"")
                    subprocess.Popen(["xdg-open", parent_dir])
                else:
                    messagebox.showwarning("Предупреждение", f"Не удалось определить тип объекта или найти родительскую папку для {normalized_path}.")
                    print(f"[DEBUG] Родительская папка также не найдена для {normalized_path}.")
            
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось открыть расположение файла/папки: {e}")
        import traceback
        traceback.print_exc() # Для отладки
        print(f"[DEBUG] Возникла ошибка: {e}")

if __name__ == '__main__':
    # Пример использования для тестирования модуля:
    print("Тестирование system_integrator.py (как отдельного скрипта).")

    # Получаем путь к текущему скрипту для теста
    current_script_path = os.path.abspath(__file__)
    current_directory_path = os.path.dirname(current_script_path)

    # Открываем текущий скрипт
    print(f"Попытка открыть расположение файла: {current_script_path}")
    open_file_location(current_script_path)
    input("Нажмите Enter для продолжения теста...")

    # Открываем текущую директорию
    print(f"Попытка открыть расположение папки: {current_directory_path}")
    open_file_location(current_directory_path)
    input("Нажмите Enter для продолжения теста...")

    # Попытка открыть несуществующий путь
    print("Попытка открыть несуществующий путь...")
    open_file_location("C:\\NonExistentFolder\\NonExistentFile.txt") # Пример для Windows
    open_file_location("/nonexistent/path/to/file.sh") # Пример для Linux/macOS
    
    print("Тесты завершены.")