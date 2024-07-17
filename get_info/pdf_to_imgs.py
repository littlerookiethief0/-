import os
import time
import fitz
import pandas as pd
import re
import asyncio
from concurrent.futures import ProcessPoolExecutor
from PIL import Image


def find_sections_by_keyword(pdf_path, keyword):
    doc = fitz.open(pdf_path)
    sections = []
    start_page = None
    name = None

    for page_num, page in enumerate(doc):
        text = page.get_text()
        if '套餐介绍-图⽂介绍' in text:
            name = text.replace("套餐介绍-图⽂介绍", "").replace(" ", "").replace("\n", "")
            start_page = page_num
        if keyword in text and start_page is not None:
            end_page = page_num
            sections.append((start_page, end_page, name))
            start_page = None
    return sections, doc


def save_page(doc_path, page_num, folder_path):
    doc = fitz.open(doc_path)
    page = doc.load_page(page_num)
    mat = fitz.Matrix(4.0, 4.0)  # 使用较低的缩放因子
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_path = os.path.join(folder_path, f"page_{page_num + 1}.jpeg")

    # 使用Pillow进行压缩和保存
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img.save(img_path, format="JPEG", quality=85)  # 调整质量参数
    return img_path


async def save_pages_to_folder(doc_path, sections, base_folder):
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
        tasks = []
        for i, (start, end, filename) in enumerate(sections):
            folder_path = os.path.join(base_folder, filename)
            os.makedirs(folder_path, exist_ok=True)
            row = {"目录路径": folder_path, "图片路径": []}

            for page_num in range(start, end + 1):
                task = loop.run_in_executor(pool, save_page, doc_path, page_num, folder_path)
                tasks.append(task)

            for img_path in await asyncio.gather(*tasks):
                row["图片路径"].append(os.path.abspath(img_path))
            print(f"Section {i}: saved images to {folder_path}")


async def main():
    pdf_path = '推广文章.pdf'
    sections, doc = find_sections_by_keyword(pdf_path, "店铺⼆维码")
    doc.close()  # 关闭文档以避免多进程中的潜在问题

    base_folder = r"图文汇总"
    await save_pages_to_folder(pdf_path, sections, base_folder)


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    print(f"Total time: {end_time - start_time:.2f} seconds.")
