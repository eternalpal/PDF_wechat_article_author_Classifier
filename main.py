import os
import shutil
import tempfile
import re
import fitz  # 处理PDF的库 PyMuPDF
from rapidocr_onnxruntime import RapidOCR

# ================= 参数设置 =================
# 你的PDF所在的文件夹路径，"." 代表脚本当前所在的文件夹
folder_path = "." 

# ================= 1. 自定义作者名字 =================
# 运行脚本时，会弹出提示让你输入。支持用空格或逗号分隔多个作者
print("==================================================")
user_input = input("👉 请输入需要分类的作者名字（用空格或逗号隔开，例如：猫比刀 奶员外）：\n> ")

# 利用正则表达式，把用户输入的带有空格、全角逗号、半角逗号的内容自动拆分成列表
authors = [name.strip() for name in re.split(r'[，,\s]+', user_input) if name.strip()]

if not authors:
    print("未输入有效作者名，程序退出。")
    exit()

print(f"\n🔍 即将进行分类的作者有: {authors}")
print("==================================================\n")

print("正在加载OCR识别模块...")
ocr = RapidOCR()

# 自动为这些作者创建对应的文件夹
for author in authors:
    os.makedirs(os.path.join(folder_path, author), exist_ok=True)

# 生成一个安全的临时图片路径
temp_img_path = os.path.join(tempfile.gettempdir(), "temp_pdf_top_third.jpg")

# 获取当前文件夹下所有PDF文件
pdf_files =[f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
print(f"共找到 {len(pdf_files)} 个PDF文件，开始自动分类...\n")

for filename in pdf_files:
    pdf_path = os.path.join(folder_path, filename)
    try:
        # 打开PDF提取第一页
        doc = fitz.open(pdf_path)
        page = doc[0] # 第一页
        
        # ================= 2. 仅提取前1/3区域 =================
        # 获取页面的完整尺寸 (x0, y0, 宽度, 高度)
        rect = page.rect 
        # 计算前 1/3 的坐标区域：横坐标不变，纵坐标取高度的 1/3
        clip_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + (rect.height / 4))
        
        # 只把这 1/3 的区域渲染成图片（大幅提升生成速度和OCR识别速度，且避免内文干扰）
        pix = page.get_pixmap(dpi=150, clip=clip_rect)
        pix.save(temp_img_path)
        doc.close()

        # 对裁剪后的局部图片进行OCR文字识别
        result, _ = ocr(temp_img_path)
        
        # 提取识别到的所有文字
        full_text = ""
        if result:
            for line in result:
                full_text += line[1]

        # 根据文字内容移动PDF
        matched = False
        for author in authors:
            if author in full_text:
                shutil.move(pdf_path, os.path.join(folder_path, author, filename))
                print(f"✅ 成功: [{filename}] -> 已移动到 【{author}】")
                matched = True
                break # 匹配到一个作者就跳出循环，防止重复移动
        
        if not matched:
            print(f"⚠️ 略过: [{filename}] -> 未在前1/3区域找到上述任何作者名")

    except Exception as e:
        print(f"❌ 错误: 处理 [{filename}] 时发生问题 ({e})")

# 清理临时文件
if os.path.exists(temp_img_path):
    try: os.remove(temp_img_path)
    except: pass

print("\n🎉 全部处理完成！")
input("按回车键退出...")