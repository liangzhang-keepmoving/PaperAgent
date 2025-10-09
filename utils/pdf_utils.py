#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF处理工具
功能：
1. 从PDF文件中提取文本内容
2. 解析PDF结构
3. 提取PDF中的表格（可选）
"""

import os
import logging
import pdfplumber
import io
import os
import re
from PIL import Image

# 设置日志
logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path, max_pages=None):
    """
    从PDF文件中提取文本内容
    
    Args:
        pdf_path: PDF文件路径
        max_pages: 最大处理页数，None表示处理所有页面
        
    Returns:
        提取的文本内容字符串
    """
    try:
        text = []
        with pdfplumber.open(pdf_path) as pdf:
            # 确定要处理的页面范围
            pages_to_process = pdf.pages
            if max_pages and max_pages < len(pages_to_process):
                pages_to_process = pages_to_process[:max_pages]
                logger.info(f'限制处理页数为: {max_pages}')
            
            # 提取每一页的文本
            for i, page in enumerate(pages_to_process):
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
                
                # 记录进度
                if (i + 1) % 10 == 0 or (i + 1) == len(pages_to_process):
                    logger.info(f'已处理第 {i+1}/{len(pages_to_process)} 页')
        
        # 将所有页面的文本合并
        full_text = '\n\n'.join(text)
        logger.info(f'从PDF中提取文本完成，总字符数: {len(full_text)}')
        
        return full_text
        
    except Exception as e:
        logger.error(f'提取PDF文本时出错: {str(e)}')
        raise


def extract_tables_from_pdf(pdf_path, pages=None):
    """
    从PDF文件中提取表格
    
    Args:
        pdf_path: PDF文件路径
        pages: 要提取表格的页面列表，None表示所有页面
        
    Returns:
        提取的表格列表，每个表格是二维列表
    """
    try:
        tables = []
        with pdfplumber.open(pdf_path) as pdf:
            # 确定要处理的页面
            pages_to_process = pdf.pages
            if pages:
                pages_to_process = [pdf.pages[i] for i in pages if i < len(pdf.pages)]
            
            # 提取每一页的表格
            for i, page in enumerate(pages_to_process):
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)
                    logger.info(f'从第 {i+1} 页提取到 {len(page_tables)} 个表格')
        
        logger.info(f'总共提取到 {len(tables)} 个表格')
        return tables
        
    except Exception as e:
        logger.error(f'提取PDF表格时出错: {str(e)}')
        raise


def get_pdf_metadata(pdf_path):
    """
    获取PDF文件的元数据
    
    Args:
        pdf_path: PDF文件路径
        
    Returns:
        包含元数据的字典
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            metadata = pdf.metadata or {}
            # 添加一些基本信息
            metadata['num_pages'] = len(pdf.pages)
            metadata['file_size'] = os.path.getsize(pdf_path) / 1024 / 1024  # MB
            
        logger.info(f'获取PDF元数据完成: {metadata}')
        return metadata
        
    except Exception as e:
        logger.error(f'获取PDF元数据时出错: {str(e)}')
        return {}


def extract_images_from_pdf(pdf_path, output_dir=None, fig_patterns=None):
    """
    从PDF文件中提取图片，特别是Fig和Figure字段的图片
    
    Args:
        pdf_path: PDF文件路径
        output_dir: 图片保存目录
        fig_patterns: 用于识别图片的关键词模式列表
        
    Returns:
        提取的图片信息列表，包含图片路径和相关描述
    """
    try:
        # 默认关键词模式
        if fig_patterns is None:
            fig_patterns = [r'Fig\.?\s+\d+', r'Figure\s+\d+', r'图\s*\d+']
        
        # 确保输出目录存在
        if not output_dir:
            # 默认保存在当前目录的images文件夹
            output_dir = 'images'
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        extracted_images = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # 提取页面文本以查找图片描述
                page_text = page.extract_text() or ''
                
                # 查找页面中的图片描述
                fig_matches = []
                for pattern in fig_patterns:
                    matches = re.finditer(pattern, page_text)
                    for match in matches:
                        fig_matches.append(match.group())
                
                # 提取页面中的图片
                images = page.images
                for img_idx, img in enumerate(images):
                    try:
                        # 获取图片对象
                        x0, y0, x1, y1 = img['x0'], img['y0'], img['x1'], img['y1']
                        # 裁剪页面以获取图片区域
                        img_cropped = page.crop((x0, y0, x1, y1))
                        
                        # 获取图片数据
                        img_obj = img_cropped.to_image(resolution=300)
                        
                        # 保存图片
                        img_filename = f"fig_page_{page_num+1}_img_{img_idx+1}.png"
                        img_path = os.path.join(output_dir, img_filename)
                        img_obj.save(img_path)
                        
                        # 获取相对路径，用于markdown引用
                        relative_path = os.path.relpath(img_path)
                        
                        # 查找与图片相关的描述
                        description = "图{}_{}".format(page_num+1, img_idx+1)
                        if fig_matches:
                            description = f"{fig_matches[0]}" if fig_matches else description
                        
                        extracted_images.append({
                            'path': img_path,
                            'relative_path': relative_path,
                            'page': page_num + 1,
                            'description': description
                        })
                    except Exception as e:
                        logger.warning(f'提取第{page_num+1}页第{img_idx+1}张图片时出错: {str(e)}')
        
        logger.info(f'从PDF中提取完成，共提取到{len(extracted_images)}张图片')
        return extracted_images
        
    except Exception as e:
        logger.error(f'提取PDF图片时出错: {str(e)}')
        raise