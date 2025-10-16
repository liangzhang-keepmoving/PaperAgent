#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
论文分析模块
功能：
1. 读取论文文件（PDF格式）
2. 提取论文文本内容
3. 调用DeepSeek API进行论文分析
4. 将参考文献整理成表格
5. 输出Markdown格式的分析报告，不要包含任何其他文字或解释
"""

import os
import logging
import re
from datetime import datetime

from utils.pdf_utils import extract_text_from_pdf, extract_text_from_pdf_url  # 导入新函数
from utils.markdown_utils import save_markdown_report
from deepseek_api import deepseek_client

# 设置日志
logger = logging.getLogger(__name__)

def analyze_paper(pdf_path, output_dir=None):
    """
    分析论文并生成报告
    
    Args:
        pdf_path: 论文PDF文件路径
        output_dir: 报告保存目录，默认为outputs/论文标题
    
    Returns:
        保存的报告文件路径
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f'论文文件不存在: {pdf_path}')
        
        # 提取论文文本内容
        logger.info(f'开始提取论文内容: {pdf_path}')
        paper_content = extract_text_from_pdf(pdf_path)
        
        # 提取论文标题
        paper_title = extract_paper_title(paper_content)
        logger.info(f'提取到论文标题: {paper_title}')
        
        # 清理标题中的特殊字符，无论是否提供了output_dir都需要定义clean_title
        clean_title = re.sub(r'[\\/:*?"<>|]', '_', paper_title)[:50]
        
        # 确定输出目录
        if not output_dir:
            output_dir = os.path.join('outputs', clean_title)
        else:
            # 如果提供了output_dir，仍然创建以论文标题命名的子目录
            output_dir = os.path.join(output_dir, clean_title)
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 调用DeepSeek API分析论文
        logger.info('调用DeepSeek API分析论文内容')
        analysis_result = analyze_paper_content(paper_content)
        
        # 构建完整报告
        full_report = analysis_result
        
        # 生成输出文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f'{clean_title}_{timestamp}_分析报告.md')
        
        # 保存报告
        save_path = save_markdown_report(full_report, output_file)
        
        logger.info(f'论文分析完成，报告已保存至: {save_path}')
        return save_path
        
    except Exception as e:
        logger.error(f'分析论文时出错: {str(e)}')
        raise


def batch_analyze_papers(folder_path, output_dir=None):
    """
    批量分析文件夹中的所有PDF论文
    
    Args:
        folder_path: 包含论文的文件夹路径
        output_dir: 报告保存根目录，默认为outputs
    
    Returns:
        分析结果列表，包含每个论文的分析状态和保存路径
    """
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f'文件夹不存在: {folder_path}')
    
    # 确定输出根目录
    if not output_dir:
        output_dir = 'outputs'
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 统计信息
    total_papers = 0
    successful_papers = 0
    failed_papers = []
    
    # 获取文件夹中的所有PDF文件
    pdf_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                pdf_files.append(pdf_path)
    
    total_papers = len(pdf_files)
    logger.info(f'找到 {total_papers} 个PDF文件待分析')
    
    # 逐个分析论文
    for i, pdf_path in enumerate(pdf_files, 1):
        try:
            logger.info(f'正在分析第 {i}/{total_papers} 个文件: {os.path.basename(pdf_path)}')
            # 对每个论文使用独立的子目录
            analyze_paper(pdf_path, output_dir=output_dir)
            successful_papers += 1
        except Exception as e:
            error_msg = f'分析文件 {os.path.basename(pdf_path)} 时出错: {str(e)}'
            logger.error(error_msg)
            failed_papers.append((pdf_path, str(e)))
    
    # 输出统计结果
    logger.info(f'批量分析完成！成功: {successful_papers} 个，失败: {len(failed_papers)} 个')
    
    # 输出失败的文件列表
    if failed_papers:
        logger.warning('以下文件分析失败:')
        for pdf_path, error in failed_papers:
            logger.warning(f'- {os.path.basename(pdf_path)}: {error}')
    
    return {
        'total': total_papers,
        'successful': successful_papers,
        'failed': len(failed_papers),
        'failed_files': failed_papers
    }


def analyze_paper_content(paper_content):
    """
    分析论文内容
    
    Args:
        paper_content: 论文文本内容
        
    Returns:
        论文分析结果
    """

    prompt = f"""请分析以下论文内容，并按照要求生成详细分析报告：

论文内容：
{paper_content}

分析要求：
1. 论文摘要：简明扼要地总结论文的主要内容和贡献
2. 研究背景：介绍论文研究的背景和动机
3. 研究方法：详细描述论文采用的研究方法和技术路线，给出具体的实现步骤和公式
4. 实验设计：描述实验的设置、样本选择、数据采集和处理方法
5. 实验结果：详细分析论文的实验结果，特别是表格中的数据，解释数据含义和趋势，将对应的表格也加入到分析报告中
6. 核心结论：总结论文的主要发现和结论
7. 创新点：分析论文的创新之处
8. 局限性：指出论文的局限性和可能的改进方向
9. 参考文献格式：请将论文中提到的所有参考文献整理成表格形式，包含作者、标题、发表年份、发表的会议/期刊，来源链接等信息

请以Markdown格式输出分析报告，不要包含任何其他文字或解释。"""
    
    result = deepseek_client.generate_text(prompt, max_tokens=6000)
    
    # 删除开头的```markdown标记
    if result.startswith('```markdown'):
        result = result[len('```markdown'):].lstrip()
    
    # 删除结尾的```标记
    if result.endswith('```'):
        result = result[:-len('```')].rstrip()
    
    return result


def extract_paper_title(paper_content):
    """
    从论文内容中提取标题
    
    Args:
        paper_content: 论文文本内容
        
    Returns:
        提取的标题字符串
    """
    try:
        # 尝试通过文本分析提取标题
        lines = paper_content.split('\n')
        # 跳过空行
        lines = [line.strip() for line in lines if line.strip()]
        
        # 尝试使用前几行作为标题候选
        if lines:
            # 检查第一行是否可能是标题
            if len(lines[0]) > 10 and len(lines[0].split()) > 3:
                return lines[0]
            # 检查前几行的组合
            elif len(lines) > 1:
                combined = ' '.join(lines[:2])
                if len(combined) > 10:
                    return combined
        
        # 如果无法提取，返回默认标题
        return '未知论文标题'
        
    except Exception as e:
        logger.error(f'提取论文标题时出错: {str(e)}')
        return '未知论文标题'


# 添加新函数：从URL直接分析论文
def analyze_paper_from_url(pdf_url, output_dir=None):
    """
    从URL直接分析论文并生成报告，无需下载PDF文件
    
    Args:
        pdf_url: 论文PDF的URL链接
        output_dir: 报告保存目录，默认为outputs/论文标题
    
    Returns:
        保存的报告文件路径
    """
    try:
        logger.info(f'开始分析论文URL: {pdf_url}')
        
        # 直接从URL提取论文文本内容
        paper_content = extract_text_from_pdf_url(pdf_url)
        
        # 提取论文标题
        paper_title = extract_paper_title(paper_content)
        logger.info(f'提取到论文标题: {paper_title}')
        
        # 清理标题中的特殊字符
        clean_title = re.sub(r'[\\/:*?"<>|]', '_', paper_title)[:50]
        
        # 确定输出目录
        if not output_dir:
            output_dir = os.path.join('outputs', clean_title)
        else:
            # 如果提供了output_dir，仍然创建以论文标题命名的子目录
            output_dir = os.path.join(output_dir, clean_title)
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 调用DeepSeek API分析论文
        logger.info('调用DeepSeek API分析论文内容')
        analysis_result = analyze_paper_content(paper_content)
        
        # 构建完整报告
        full_report = analysis_result
        
        # 生成输出文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f'{clean_title}_{timestamp}_分析报告.md')
        
        # 保存报告
        save_path = save_markdown_report(full_report, output_file)
        
        logger.info(f'论文分析完成，报告已保存至: {save_path}')
        return save_path
        
    except Exception as e:
        logger.error(f'分析论文URL时出错: {str(e)}')
        raise




if __name__ == '__main__':
    # 示例用法
    import sys
    if len(sys.argv) > 1:
        analyze_paper(sys.argv[1])
    else:
        print("用法: python paper_analyzer.py <论文文件路径>")