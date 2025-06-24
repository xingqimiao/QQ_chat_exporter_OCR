# config_ui.py
import tkinter as tk

class RegionSelector:
    def __init__(self):
        self.root = tk.Tk()
        # 设置窗口全屏、无边框、置顶、半透明
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)
        self.root.attributes('-topmost', True)
        self.root.wait_visibility(self.root) # 等待窗口可见
        
        self.canvas = tk.Canvas(self.root, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)

        self.rect = None
        self.start_x = None
        self.start_y = None
        self.selection_box = None
        
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        
        # 添加一个提示标签
        self.label = tk.Label(self.root, text="请拖动鼠标框选聊天记录区域", font=("Arial", 24), bg="black", fg="white")
        self.label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def on_button_press(self, event):
        self.label.destroy() # 开始选择时销毁提示
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        if not self.rect:
            self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)

    def on_move_press(self, event):
        curX = self.canvas.canvasx(event.x)
        curY = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)

    def on_button_release(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        
        # 确保坐标是从左上到右下
        left = min(self.start_x, end_x)
        top = min(self.start_y, end_y)
        right = max(self.start_x, end_x)
        bottom = max(self.start_y, end_y)
        
        self.selection_box = (int(left), int(top), int(right - left), int(bottom - top))
        self.root.quit()

    def get_selection(self):
        self.root.mainloop()
        self.root.destroy()
        return self.selection_box

if __name__ == '__main__':
    selector = RegionSelector()
    selection = selector.get_selection()
    print(f"选择的区域是: {selection}")