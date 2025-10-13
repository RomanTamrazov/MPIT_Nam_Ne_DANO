from src.gui import GameGUI
import tkinter as tk

def main():
    root = tk.Tk()
    root.geometry("1000x700")
    root.title("Морской Бой 🎮")
    app = GameGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
