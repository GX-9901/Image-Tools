import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import sys

# 尝试导入TkinterDnD2
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES

    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("警告：未安装tkinterdnd2库，拖放功能将不可用。请运行: pip install tkinterdnd2")


class ImageStitcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图像拼接工具")
        self.root.geometry("800x650")  # 增加默认高度
        self.root.minsize(800, 650)  # 设置最小窗口大小，确保按钮可见

        # 存储原始图像
        self.left_image = None
        self.right_image = None
        self.left_image_path = None
        self.right_image_path = None
        self.merged_image = None  # 初始化合并图像变量

        # 跟踪最近拖放的图片
        self.drag_drop_images = []

        # 创建整体布局
        self.create_widgets()

        # 只在拖放库可用时启用拖放功能
        if HAS_DND:
            self.setup_drag_drop()

    def create_widgets(self):
        # 使用网格布局代替pack，更精确控制位置
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=3)  # 预览区域占更多空间
        self.root.grid_rowconfigure(1, weight=2)  # 拼合预览区域
        self.root.grid_rowconfigure(2, weight=0)  # 合成按钮行
        self.root.grid_rowconfigure(3, weight=0)  # 状态栏行

        # 创建主框架
        main_frame = tk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=0)  # 工具栏
        main_frame.grid_rowconfigure(1, weight=1)  # 预览区域

        # 工具栏框架
        toolbar_frame = tk.Frame(main_frame)
        toolbar_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=2)

        # 左右互换按钮
        self.swap_btn = tk.Button(
            toolbar_frame,
            text="左右互换",
            command=self.swap_images,
            bg="#FFCC99",
            width=10,
            height=1,
            font=("Arial", 9, "bold")
        )
        self.swap_btn.pack(side=tk.TOP, pady=3)

        # 拖放提示标签
        if HAS_DND:
            drag_hint = tk.Label(toolbar_frame, text="提示: 可以同时拖入两张图片，第一张将作为右图，第二张将作为左图",
                                 fg="blue")
            drag_hint.pack(side=tk.TOP, pady=2)

        # 左图片部分
        left_frame = tk.Frame(main_frame, bd=2, relief=tk.GROOVE)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        left_btn_frame = tk.Frame(left_frame)
        left_btn_frame.grid(row=0, column=0, sticky="ew")

        self.left_import_btn = tk.Button(left_btn_frame, text="导入左图片", command=self.import_left_image)
        self.left_import_btn.pack(pady=5)

        self.left_preview = tk.Label(left_frame, text="左侧图片预览区域", bg="lightgray")
        self.left_preview.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # 右图片部分
        right_frame = tk.Frame(main_frame, bd=2, relief=tk.GROOVE)
        right_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        right_btn_frame = tk.Frame(right_frame)
        right_btn_frame.grid(row=0, column=0, sticky="ew")

        self.right_import_btn = tk.Button(right_btn_frame, text="导入右图片", command=self.import_right_image)
        self.right_import_btn.pack(pady=5)

        self.right_preview = tk.Label(right_frame, text="右侧图片预览区域", bg="lightgray")
        self.right_preview.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # 创建下半部分的框架（拼接图片预览）
        bottom_frame = tk.Frame(self.root, bd=2, relief=tk.GROOVE)
        bottom_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        bottom_frame.grid_rowconfigure(1, weight=1)
        bottom_frame.grid_columnconfigure(0, weight=1)

        bottom_label = tk.Label(bottom_frame, text="拼接预览区域")
        bottom_label.grid(row=0, column=0, pady=5)

        self.merged_preview = tk.Label(bottom_frame, text="拼接预览将显示在这里", bg="lightgray")
        self.merged_preview.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # 合成按钮 - 确保它位于固定位置
        self.merge_btn_frame = tk.Frame(self.root)
        self.merge_btn_frame.grid(row=2, column=0, sticky="ew", pady=5, padx=5)

        self.merge_btn = tk.Button(
            self.merge_btn_frame,
            text="合成",
            command=self.save_merged_image,
            state=tk.DISABLED,
            height=2,
            bg="lightblue",
            font=("Arial", 10, "bold")
        )
        self.merge_btn.pack(fill=tk.X, pady=5)

        # 状态标签
        self.status_label = tk.Label(self.root, text="等待导入图片...", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=3, column=0, sticky="ew")

    def setup_drag_drop(self):
        if not HAS_DND:
            return

        # 为左右预览区域和整个窗口设置拖放功能
        self.left_preview.drop_target_register(DND_FILES)
        self.left_preview.dnd_bind('<<Drop>>', self.drop_left)

        self.right_preview.drop_target_register(DND_FILES)
        self.right_preview.dnd_bind('<<Drop>>', self.drop_right)

        # 设置整个窗口为拖放目标，用于批量拖放
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.drop_multiple)

    def drop_multiple(self, event):
        """处理一次性拖入多个文件的情况"""
        files = self.parse_drop_files(event.data)

        # 如果拖入了至少两个文件
        if len(files) >= 2:
            self.status_label.config(
                text=f"收到多个文件，处理前两个: {', '.join([os.path.basename(f) for f in files[:2]])}")
            self.root.update()

            # 第一个文件作为右图
            self.process_right_image(files[0])

            # 第二个文件作为左图
            self.process_left_image(files[1])

            self.status_label.config(text=f"已加载：第一个文件作为右图，第二个文件作为左图")
        elif len(files) == 1:
            # 如果只拖入一个文件，看哪边还没有图片
            if not self.right_image:
                self.process_right_image(files[0])
            elif not self.left_image:
                self.process_left_image(files[0])
            else:
                # 两边都有图片了，默认替换右图
                self.process_right_image(files[0])

    def parse_drop_files(self, drop_data):
        """解析拖放的文件路径数据"""
        # 处理Windows上的多文件拖放格式
        if '{' in drop_data:
            files = []
            # 使用}分割多个文件路径
            parts = drop_data.split("} {")
            for part in parts:
                # 清理每个文件路径
                clean_part = part.replace("{", "").replace("}", "")
                if clean_part.startswith('"') and clean_part.endswith('"'):
                    clean_part = clean_part[1:-1]
                files.append(clean_part)
            return files
        else:
            # 单文件情况
            if drop_data.startswith('{'):
                drop_data = drop_data[1:-1]
            if drop_data.startswith('"') and drop_data.endswith('"'):
                drop_data = drop_data[1:-1]
            return [drop_data]

    def drop_left(self, event):
        file_paths = self.parse_drop_files(event.data)
        if file_paths:
            self.process_left_image(file_paths[0])

    def drop_right(self, event):
        file_paths = self.parse_drop_files(event.data)
        if file_paths:
            self.process_right_image(file_paths[0])

    def swap_images(self):
        """左右图片互换功能"""
        if not self.left_image and not self.right_image:
            messagebox.showinfo("提示", "没有可互换的图片")
            return

        # 交换图片和路径
        self.left_image, self.right_image = self.right_image, self.left_image
        self.left_image_path, self.right_image_path = self.right_image_path, self.left_image_path

        # 更新显示
        self.status_label.config(text="正在交换左右图片...")
        self.root.update()

        # 重新显示左右图片
        if self.left_image:
            self.display_image(self.left_image, self.left_preview)
        else:
            self.left_preview.config(image='', text="左侧图片预览区域")

        if self.right_image:
            self.display_image(self.right_image, self.right_preview)
        else:
            self.right_preview.config(image='', text="右侧图片预览区域")

        # 更新合并预览
        if self.left_image and self.right_image:
            self.create_merged_preview()
            self.status_label.config(text="左右图片已互换，预览已更新")
        else:
            self.status_label.config(text="左右图片已互换")

    def import_left_image(self):
        file_path = filedialog.askopenfilename(
            title="选择左侧图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if file_path:
            self.process_left_image(file_path)

    def import_right_image(self):
        file_path = filedialog.askopenfilename(
            title="选择右侧图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if file_path:
            self.process_right_image(file_path)

    def process_left_image(self, file_path):
        try:
            self.status_label.config(text=f"正在处理左侧图片: {os.path.basename(file_path)}")
            self.root.update()  # 强制更新界面

            self.left_image = Image.open(file_path)
            self.left_image_path = file_path
            self.display_image(self.left_image, self.left_preview)
            self.check_and_merge_preview()

            self.status_label.config(text=f"左侧图片已加载: {os.path.basename(file_path)}")
        except Exception as e:
            self.status_label.config(text=f"错误: {str(e)}")
            messagebox.showerror("错误", f"无法打开图片: {str(e)}")

    def process_right_image(self, file_path):
        try:
            self.status_label.config(text=f"正在处理右侧图片: {os.path.basename(file_path)}")
            self.root.update()  # 强制更新界面

            self.right_image = Image.open(file_path)
            self.right_image_path = file_path
            self.display_image(self.right_image, self.right_preview)
            self.check_and_merge_preview()

            self.status_label.config(text=f"右侧图片已加载: {os.path.basename(file_path)}")
        except Exception as e:
            self.status_label.config(text=f"错误: {str(e)}")
            messagebox.showerror("错误", f"无法打开图片: {str(e)}")

    def display_image(self, image, label_widget, max_size=(300, 200)):
        # 调整图像大小以适应预览区域
        display_image = image.copy()
        display_image.thumbnail(max_size)
        photo = ImageTk.PhotoImage(display_image)

        label_widget.config(image=photo, text="")
        label_widget.image = photo  # 保持引用，防止被垃圾回收

    def check_and_merge_preview(self):
        if self.left_image and self.right_image:
            self.status_label.config(text="正在生成预览...")
            self.root.update()  # 强制更新界面

            self.create_merged_preview()

            # 确保合成按钮可用并可见
            self.merge_btn.config(state=tk.NORMAL)
            # 确保按钮可见
            self.merge_btn_frame.tkraise()  # 使按钮框架置于最上层
            self.root.update()  # 再次强制更新界面

            self.status_label.config(text="预览已生成，可以点击合成按钮保存拼接图片")
        else:
            self.merge_btn.config(state=tk.DISABLED)
            if self.left_image:
                self.status_label.config(text="请导入右侧图片...")
            elif self.right_image:
                self.status_label.config(text="请导入左侧图片...")

    def create_merged_preview(self):
        if not self.left_image or not self.right_image:
            return

        try:
            # 获取两张图片的高度
            left_height = self.left_image.height
            right_height = self.right_image.height

            # 取最大高度
            max_height = max(left_height, right_height)

            # 创建新图像 - 使用RGBA模式支持透明度
            merged_width = self.left_image.width + self.right_image.width
            merged_image = Image.new('RGBA', (merged_width, max_height), (255, 255, 255, 0))

            # 转换图像到RGBA模式（如果需要）
            left_rgba = self.left_image.convert('RGBA') if self.left_image.mode != 'RGBA' else self.left_image
            right_rgba = self.right_image.convert('RGBA') if self.right_image.mode != 'RGBA' else self.right_image

            # 粘贴左图和右图
            merged_image.paste(left_rgba, (0, 0))
            merged_image.paste(right_rgba, (self.left_image.width, 0))

            # 显示预览
            self.display_image(merged_image, self.merged_preview, max_size=(600, 300))
            self.merged_image = merged_image
        except Exception as e:
            self.status_label.config(text=f"生成预览时出错: {str(e)}")
            messagebox.showerror("错误", f"生成预览时出错: {str(e)}")

    def save_merged_image(self):
        if self.merged_image is None:
            messagebox.showerror("错误", "没有可保存的拼接图像")
            return

        try:
            self.status_label.config(text="正在保存拼接图片...")
            self.root.update()  # 强制更新界面

            # 获取左右图像的文件名（不含扩展名）
            left_filename = os.path.splitext(os.path.basename(self.left_image_path))[0]
            right_filename = os.path.splitext(os.path.basename(self.right_image_path))[0]

            # 生成新文件名：右图片文件名-左图片文件名
            output_filename = f"{right_filename}-{left_filename}"

            # 使用左图片的扩展名
            extension = os.path.splitext(self.left_image_path)[1]

            # 获取左图片所在的目录
            output_dir = os.path.dirname(self.left_image_path)

            # 完整的输出路径
            output_path = os.path.join(output_dir, output_filename + extension)

            # 转换到RGB模式（如果保存为JPEG）
            if extension.lower() in ['.jpg', '.jpeg']:
                save_image = self.merged_image.convert('RGB')
            else:
                save_image = self.merged_image

            # 保存拼接图像
            save_image.save(output_path)

            self.status_label.config(text=f"拼接图片已保存至: {output_path}")
            messagebox.showinfo("成功", f"拼接图像已保存到:\n{output_path}")

        except Exception as e:
            self.status_label.config(text=f"保存图片时出错: {str(e)}")
            messagebox.showerror("错误", f"保存图像时出错: {str(e)}")


# 主程序
def main():
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = ImageStitcherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()