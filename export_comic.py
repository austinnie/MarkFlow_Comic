from pathlib import Path
import img2pdf

# 图片所在目录（正确路径）
image_dir = Path('skills/image/sd_image_generator/output/images')

# 只取漫画相关的图片（按时间排序，取最新的4张）
all_images = sorted(image_dir.glob('*.png'), key=lambda p: p.stat().st_mtime)
# 过滤掉旧图片（只取2026-09-03生成的）
images = [p for p in all_images if '20260903' in p.name]

if not images:
    # 如果没有过滤到，取所有图片
    images = all_images

if images:
    # 生成 PDF
    pdf_path = Path('skills/comics/manga_generator/output/comic.pdf')
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(pdf_path, 'wb') as f:
        f.write(img2pdf.convert([str(p) for p in images]))
    
    print(f'✅ PDF 已生成: {pdf_path}')
    print(f'📊 共 {len(images)} 页')
    for img in images:
        print(f'   - {img.name}')
else:
    print('❌ 没有找到图片')