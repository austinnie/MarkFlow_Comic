# 生成漫画
python -m markflow.cli.commands execute comics.manga_generator \
    source_type=text \
    source_content="一个少年在异世界冒险的故事" \
    style=anime \
    pages=4

# 生成剧本
python -m markflow.cli.commands execute comics.manga_script_writer \
    genre=奇幻 \
    theme=冒险 \
    pages=6

# 添加对话气泡
python -m markflow.cli.commands execute comics.manga_bubble_adder \
    image_path=./page1.png \
    dialogues="你好！, 欢迎来到我的世界" \
    positions="50,50, 50,200"
	
### 1. 生成剧本

 python -m markflow.cli.commands execute comics.manga_script_writer genre=奇幻 theme=冒险 pages=6 characters="勇者, 法师, 精灵"

### 2. 生成漫画

 python -m markflow.cli.commands execute comics.manga_generator source_type=text source_content="勇者踏上冒险之旅，在森林中遇到了法师和精灵伙伴..." style=anime pages=6

### 3. 统一画风

 python -m markflow.cli.commands execute comics.manga_style_unifier image_paths="page1.png,page2.png,page3.png" style=anime

### 4. 添加对话气泡

 python -m markflow.cli.commands execute comics.manga_bubble_adder image_paths="page1.png" dialogues="欢迎来到冒险世界！, 我们一起出发吧！"

### 5. 排版

 python -m markflow.cli.commands execute comics.manga_layout_editor image_paths="page1.png,page2.png,page3.png" layout_type=grid title="勇者冒险"

### 6. 导出 PDF

 python -m markflow.cli.commands execute comics.manga_to_pdf image_paths="page1.png,page2.png,page3.png" title="勇者冒险"

### 7. 导出 EPUB

 python -m markflow.cli.commands execute comics.manga_to_epub image_paths="page1.png,page2.png,page3.png" title="勇者冒险"

### 8. 生成有声版

 python -m markflow.cli.commands execute comics.manga_audio_book image_paths="page1.png,page2.png,page3.png"