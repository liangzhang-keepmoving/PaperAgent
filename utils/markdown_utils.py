#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Markdown处理工具
功能：
1. 生成和格式化Markdown内容
2. 保存Markdown文件
3. 处理表格、列表等Markdown元素
"""

import os
import logging

# 设置日志
logger = logging.getLogger(__name__)


def save_markdown_report(content, file_path):
    """
    保存Markdown格式的报告
    
    Args:
        content: Markdown内容字符串
        file_path: 保存文件路径
    
    Returns:
        保存的文件路径
    """
    try:
        # 确保文件扩展名为.md
        if not file_path.lower().endswith('.md'):
            file_path += '.md'
        
        # 确保保存目录存在
        save_dir = os.path.dirname(file_path)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir)
            logger.info(f'创建保存目录: {save_dir}')
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f'Markdown报告已保存至: {file_path}')
        return file_path
        
    except Exception as e:
        logger.error(f'保存Markdown报告时出错: {str(e)}')
        raise


def format_table(headers, rows):
    """
    格式化表格为Markdown格式
    
    Args:
        headers: 表头列表
        rows: 表格行数据列表，每行是一个列表
        
    Returns:
        格式化后的Markdown表格字符串
    """
    try:
        if not headers or not rows:
            return ""
        
        # 计算每列的最大宽度
        column_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(column_widths):
                    column_widths[i] = max(column_widths[i], len(str(cell)))
        
        # 构建表格
        markdown_table = []
        
        # 添加表头行
        header_line = '| ' + ' | '.join([str(h).ljust(w) for h, w in zip(headers, column_widths)]) + ' |'
        markdown_table.append(header_line)
        
        # 添加分隔线
        separator_line = '| ' + ' | '.join(['-' * w for w in column_widths]) + ' |'
        markdown_table.append(separator_line)
        
        # 添加数据行
        for row in rows:
            row_line = '| ' + ' | '.join([str(cell).ljust(w) for cell, w in zip(row, column_widths)]) + ' |'
            markdown_table.append(row_line)
        
        logger.info(f'生成Markdown表格，{len(rows)}行数据')
        return '\n'.join(markdown_table)
        
    except Exception as e:
        logger.error(f'格式化表格时出错: {str(e)}')
        raise


def generate_title(title, level=1):
    """
    生成Markdown格式的标题
    
    Args:
        title: 标题文本
        level: 标题级别（1-6）
        
    Returns:
        格式化后的Markdown标题字符串
    """
    try:
        level = max(1, min(6, level))  # 确保级别在1-6之间
        prefix = '#' * level
        return f'{prefix} {title}'
    except Exception as e:
        logger.error(f'生成标题时出错: {str(e)}')
        raise


def format_bullet_list(items):
    """
    格式化无序列表为Markdown格式
    
    Args:
        items: 列表项文本列表
        
    Returns:
        格式化后的Markdown无序列表字符串
    """
    try:
        if not items:
            return ""
        
        return '\n'.join([f'- {item}' for item in items])
    except Exception as e:
        logger.error(f'格式化无序列表时出错: {str(e)}')
        raise


def format_numbered_list(items):
    """
    格式化有序列表为Markdown格式
    
    Args:
        items: 列表项文本列表
        
    Returns:
        格式化后的Markdown有序列表字符串
    """
    try:
        if not items:
            return ""
        
        return '\n'.join([f'{i+1}. {item}' for i, item in enumerate(items)])
    except Exception as e:
        logger.error(f'格式化有序列表时出错: {str(e)}')
        raise


def format_blockquote(text):
    """
    格式化引用块为Markdown格式
    
    Args:
        text: 引用文本
        
    Returns:
        格式化后的Markdown引用块字符串
    """
    try:
        lines = text.split('\n')
        return '\n'.join([f'> {line}' for line in lines])
    except Exception as e:
        logger.error(f'格式化引用块时出错: {str(e)}')
        raise