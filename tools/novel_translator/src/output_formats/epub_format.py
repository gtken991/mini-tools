#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EPUB格式输出
"""

import os
from typing import Dict, Any, List
from pathlib import Path
import uuid
import datetime

import ebooklib
from ebooklib import epub

from ..models import Document, Paragraph, Chapter
from ..utils import ensure_dir

def format_as_epub(document: Document, options: Dict[str, Any], output_path: str) -> str:
    """
    将文档导出为EPUB格式
    
    Args:
        document: 文档对象
        options: 格式选项
        output_path: 输出路径
        
    Returns:
        输出文件路径
    """
    # 解析选项
    bilingual = options.get("bilingual_output", False)
    include_titles = options.get("include_titles", True)
    author = options.get("author", "Unknown")
    language = options.get("language", document.target_language if not bilingual else document.source_language)
    css_style = options.get("css_style", DEFAULT_CSS)
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    ensure_dir(output_dir)
    
    # 创建EPUB书籍
    book = epub.EpubBook()
    
    # 设置元数据
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(document.title)
    book.set_language(language)
    book.add_author(author)
    
    # 添加CSS
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=NAV_CSS
    )
    book.add_item(nav_css)
    
    main_css = epub.EpubItem(
        uid="style_main",
        file_name="style/main.css",
        media_type="text/css",
        content=css_style
    )
    book.add_item(main_css)
    
    # 章节列表
    chapters = []
    toc = []
    
    # 创建封面页
    cover = epub.EpubHtml(
        title="封面",
        file_name="cover.xhtml",
        lang=language
    )
    
    cover_content = f"""
    <html>
    <head>
        <title>{document.title}</title>
        <link rel="stylesheet" href="style/main.css" type="text/css" />
    </head>
    <body>
        <div class="cover">
            <h1>{document.title}</h1>
            <p class="author">{author}</p>
        </div>
    </body>
    </html>
    """
    
    cover.content = cover_content
    book.add_item(cover)
    chapters.append(cover)
    
    # 创建介绍页
    intro = epub.EpubHtml(
        title="简介",
        file_name="intro.xhtml",
        lang=language
    )
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    intro_content = f"""
    <html>
    <head>
        <title>简介</title>
        <link rel="stylesheet" href="style/main.css" type="text/css" />
    </head>
    <body>
        <h1>简介</h1>
        <p>本书由小说翻译工具自动翻译生成，原文语言为{document.source_language}，目标语言为{document.target_language}。</p>
        <p>生成日期：{today}</p>
        <p>总段落数：{len(document.paragraphs)}</p>
        <p>章节数：{len(document.chapters)}</p>
    </body>
    </html>
    """
    
    intro.content = intro_content
    book.add_item(intro)
    chapters.append(intro)
    
    # 按章节添加内容
    if document.chapters:
        # 有章节结构的情况
        for chapter_id, chapter in sorted(document.chapters.items(), key=lambda x: x[0]):
            # 创建章节
            epub_chapter = create_chapter_html(document, chapter, bilingual, language, main_css)
            book.add_item(epub_chapter)
            chapters.append(epub_chapter)
            toc.append(epub.Link(epub_chapter.file_name, chapter.title, chapter.title))
    else:
        # 无章节结构，将所有内容作为一个章节
        all_content = epub.EpubHtml(
            title="全文",
            file_name="content.xhtml",
            lang=language
        )
        
        content_html = "<h1>全文</h1>\n"
        
        # 按顺序处理每个段落
        for para_id, para in sorted(document.paragraphs.items(), key=lambda x: x[0]):
            if not para.is_title or include_titles:
                content_html += f"<p>{para.content}</p>\n"
                
                if bilingual and para.is_translated:
                    content_html += f"<p class='translation'>{para.translated}</p>\n"
        
        all_content.content = f"""
        <html>
        <head>
            <title>全文</title>
            <link rel="stylesheet" href="style/main.css" type="text/css" />
        </head>
        <body>
            {content_html}
        </body>
        </html>
        """
        
        book.add_item(all_content)
        chapters.append(all_content)
        toc.append(epub.Link(all_content.file_name, "全文", "content"))
    
    # 添加目录
    book.toc = toc
    
    # 添加spine
    book.spine = ['nav'] + chapters
    
    # 添加NCX和Nav文件
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # 写入文件
    epub.write_epub(output_path, book, {})
    
    # 如果是双语模式，再生成两个单语言的版本
    if bilingual:
        # 源语言版本
        source_path = f"{os.path.splitext(output_path)[0]}_source.epub"
        options_source = dict(options)
        options_source["bilingual_output"] = False
        options_source["language"] = document.source_language
        format_single_language_epub(document, False, options_source, source_path)
        
        # 目标语言版本
        target_path = f"{os.path.splitext(output_path)[0]}_target.epub"
        options_target = dict(options)
        options_target["bilingual_output"] = False
        options_target["language"] = document.target_language
        format_single_language_epub(document, True, options_target, target_path)
    
    return output_path

def create_chapter_html(document: Document, chapter: Chapter, bilingual: bool, language: str, css_item: epub.EpubItem) -> epub.EpubHtml:
    """
    创建章节HTML
    
    Args:
        document: 文档对象
        chapter: 章节对象
        bilingual: 是否双语
        language: 语言
        css_item: CSS项目
        
    Returns:
        章节HTML
    """
    # 清理章节标题作为文件名
    file_name = f"chapter_{chapter.id}.xhtml"
    
    # 创建章节
    epub_chapter = epub.EpubHtml(
        title=chapter.title,
        file_name=file_name,
        lang=language
    )
    
    # 构建章节内容
    content_html = f"<h1>{chapter.title}</h1>\n"
    
    # 章节标题段落
    title_para = None
    for para_id in chapter.paragraphs:
        para = document.paragraphs.get(para_id)
        if para and para.is_title:
            title_para = para
            break
    
    # 如果找到标题段落且为双语模式，添加译文标题
    if title_para and bilingual and title_para.is_translated:
        content_html += f"<h2 class='translated-title'>{title_para.translated}</h2>\n"
    
    # 处理章节中的每个段落
    for para_id in chapter.paragraphs:
        para = document.paragraphs.get(para_id)
        if para and not para.is_title:  # 跳过标题段落，已单独处理
            content_html += f"<p>{para.content}</p>\n"
            
            if bilingual and para.is_translated:
                content_html += f"<p class='translation'>{para.translated}</p>\n"
    
    # 设置章节内容
    epub_chapter.content = f"""
    <html>
    <head>
        <title>{chapter.title}</title>
        <link rel="stylesheet" href="style/main.css" type="text/css" />
    </head>
    <body>
        {content_html}
    </body>
    </html>
    """
    
    return epub_chapter

def format_single_language_epub(document: Document, target_language: bool, options: Dict[str, Any], output_path: str) -> str:
    """
    将文档导出为单语言EPUB格式
    
    Args:
        document: 文档对象
        target_language: 是否为目标语言
        options: 格式选项
        output_path: 输出路径
        
    Returns:
        输出文件路径
    """
    # 创建临时文档副本，根据语言选择设置内容
    temp_doc = Document(
        id=document.id,
        title=document.title,
        source_language=document.source_language if not target_language else document.target_language,
        target_language=document.target_language if not target_language else document.source_language
    )
    
    # 复制段落和章节结构
    for para_id, para in document.paragraphs.items():
        new_para = Paragraph(
            id=para.id,
            content=para.translated if target_language and para.is_translated else para.content,
            chapter=para.chapter,
            is_title=para.is_title,
            is_translated=False  # 单语言版本中不需要翻译标记
        )
        temp_doc.paragraphs[para_id] = new_para
    
    for chapter_id, chapter in document.chapters.items():
        temp_doc.chapters[chapter_id] = Chapter(
            id=chapter.id,
            title=chapter.title,
            paragraphs=chapter.paragraphs.copy()
        )
    
    # 使用标准EPUB导出
    options["bilingual_output"] = False
    return format_as_epub(temp_doc, options, output_path)

# 默认CSS样式
DEFAULT_CSS = """
body {
    font-family: "Noto Serif", "Noto Serif CJK SC", serif;
    line-height: 1.5;
    margin: 2em;
    padding: 0;
    background-color: #fefefe;
    color: #333;
}

h1 {
    font-size: 1.5em;
    text-align: center;
    margin: 1em 0;
    page-break-before: always;
}

h2 {
    font-size: 1.3em;
    margin: 0.83em 0;
}

.cover {
    text-align: center;
    margin-top: 30%;
}

.cover h1 {
    font-size: 2em;
    margin-bottom: 1em;
}

.author {
    font-size: 1.2em;
    margin-top: 1em;
}

p {
    text-indent: 2em;
    margin: 0.5em 0;
}

.translation {
    color: #555;
    margin-top: 0.5em;
    border-left: 3px solid #ccc;
    padding-left: 0.5em;
    font-style: italic;
}

.translated-title {
    color: #555;
    font-style: italic;
    text-align: center;
    margin-top: -0.5em;
    margin-bottom: 1em;
}
"""

# 导航样式
NAV_CSS = """
nav#guide {
    display: none;
}

nav#toc ol {
    list-style-type: none;
    margin: 0;
    padding: 0;
}

nav#toc ol li {
    margin: 0.5em 0;
}

nav#toc ol li a {
    text-decoration: none;
    color: #0066cc;
}
""" 