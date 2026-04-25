import pyglet
import customtkinter as ctk

# Загружаем шрифт
pyglet.font.add_file("PixelifySans-Regular.ttf")

# Проверяем точное название
try:
    f = pyglet.font.load("Pixelify Sans")
    print(f"Шрифт найден: '{f.name}'")
except Exception as e:
    print(f"Ошибка загрузки: {e}")

app = ctk.CTk()
app.geometry("400x200")

pyglet.font.add_file("PixelifySans-Regular.ttf")

label1 = ctk.CTkLabel(app, text="Pixelify Sans CTkFont",
                       font=ctk.CTkFont(family="Pixelify Sans", size=24))
label1.pack(pady=20)

label2 = ctk.CTkLabel(app, text="Кортеж tuple",
                       font=("Pixelify Sans", 24))
label2.pack(pady=10)

app.mainloop()