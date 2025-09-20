import os
import sys
from PIL import Image, ImageTk
import io
import traceback
import tkinter as tk

# Попытка импорта icoextract
try:
    from icoextract import IconExtractor
except ImportError:
    IconExtractor = None
    print("Предупреждение: Библиотека 'icoextract' не найдена. Извлечение иконок может быть недоступно.")
    print("Установите ее командой: pip install icoextract")

def get_icon_from_exe(exe_path, size=(32, 32)):
    """
    Извлекает иконку из исполняемого файла (.exe) и возвращает ее как объект PhotoImage Tkinter.
    Использует библиотеку icoextract.
    """
    if IconExtractor is None:
        print("Ошибка: icoextract не импортирован. Невозможно извлечь иконку.")
        return None

    if not os.path.exists(exe_path):
        print(f"Файл не найден для извлечения иконки: {exe_path}")
        return None

    try:
        extractor = IconExtractor(exe_path)
        
        # Попытка получить иконку с заданным размером
        try:
            # icoextract.get_icon() может вернуть BytesIO или PIL.Image
            pil_image = extractor.get_icon(size[0])
        except Exception: 
            pil_image = extractor.get_icon() 
            
        if pil_image:
            # Преобразуем BytesIO в PIL Image, если необходимо
            if isinstance(pil_image, io.BytesIO):
                try:
                    pil_image = Image.open(pil_image)
                except Exception as e:
                    print(f"Ошибка при открытии изображения из BytesIO: {e}")
                    return None

            # Изменение размера PIL.Image до нужного, если он отличается
            if pil_image.width != size[0] or pil_image.height != size[1]:
                pil_image = pil_image.resize(size, Image.LANCZOS)
            
            # Конвертируем в формат PhotoImage Tkinter
            tk_image = ImageTk.PhotoImage(pil_image)
            return tk_image
        else:
            print(f"Не удалось извлечь иконку из {exe_path} с помощью icoextract.")
            return None

    except Exception as e:
        print(f"Ошибка при извлечении иконки из {exe_path} с помощью icoextract: {e}")
        print(traceback.format_exc()) 
        return None

if __name__ == '__main__':
    # Пример использования (для тестирования модуля)
    test_exe_path = r"C:\Windows\notepad.exe" 

    if IconExtractor is not None and os.path.exists(test_exe_path):
        root = tk.Tk()
        root.title("Тест извлечения иконки")
        root.geometry("200x200")

        icon_image = get_icon_from_exe(test_exe_path)
        if icon_image:
            label = tk.Label(root, image=icon_image)
            label.pack(pady=20)
            print(f"Иконка извлечена из: {test_exe_path}")
        else:
            tk.Label(root, text="Не удалось извлечь иконку.").pack(pady=20)
            print(f"Не удалось извлечь иконку из: {test_exe_path}")

        root.mainloop()
    elif IconExtractor is None:
        print("Библиотека icoextract не установлена. Пожалуйста, установите ее.")
    else:
        print(f"Тестовый файл '{test_exe_path}' не найден.")