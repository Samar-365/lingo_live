"""
Selection Helper - Runs as separate process.
"""
import tkinter as tk
import sys
import json


def main():
    root = tk.Tk()
    root.withdraw()
    
    w = root.winfo_screenwidth()
    h = root.winfo_screenheight()
    
    root.geometry(f"{w}x{h}+0+0")
    root.overrideredirect(True)
    root.attributes('-topmost', True)
    root.attributes('-alpha', 0.3)
    root.configure(bg='#222222')
    root.config(cursor='cross')
    
    canvas = tk.Canvas(root, width=w, height=h, highlightthickness=0, bg='#222222')
    canvas.pack()
    
    canvas.create_text(w//2, 40, text="DRAG to select text area | ESC to cancel",
                       font=("Segoe UI", 18, "bold"), fill="lime")
    
    state = {"start": None, "rect": None, "result": None}
    
    def press(e):
        state["start"] = (e.x, e.y)
        if state["rect"]:
            canvas.delete(state["rect"])
        state["rect"] = canvas.create_rectangle(e.x, e.y, e.x, e.y, 
                                                 outline='lime', width=3)
    
    def drag(e):
        if state["start"] and state["rect"]:
            canvas.coords(state["rect"], state["start"][0], state["start"][1], e.x, e.y)
    
    def release(e):
        if state["start"]:
            x1 = min(state["start"][0], e.x)
            y1 = min(state["start"][1], e.y)
            x2 = max(state["start"][0], e.x)
            y2 = max(state["start"][1], e.y)
            if x2 - x1 > 10 and y2 - y1 > 10:
                state["result"] = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
        root.quit()
    
    def cancel(e):
        root.quit()
    
    canvas.bind("<Button-1>", press)
    canvas.bind("<B1-Motion>", drag)
    canvas.bind("<ButtonRelease-1>", release)
    root.bind("<Escape>", cancel)
    
    root.deiconify()
    root.focus_force()
    root.mainloop()
    
    try:
        root.destroy()
    except:
        pass
    
    # Output result as JSON
    if state["result"]:
        print(json.dumps(state["result"]))
    else:
        print("{}")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
