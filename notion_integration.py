#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Notion 集成模块
功能：
1. 将论文分析报告直接复制到指定的 Notion 页面
2. 处理 Markdown 格式转换为 Notion 块结构
"""

import os
import logging
import re
import requests
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置日志
logger = logging.getLogger(__name__)

class NotionPageCopier:
    """Notion 页面复制类，将内容添加到指定的 Notion 页面"""
    
    def __init__(self, api_key=None, use_proxy=True):
        """
        初始化 Notion 页面复制器
        
        Args:
            api_key: Notion API 密钥
            use_proxy: 是否使用代理（默认为True）
        """
        # 从环境变量或参数获取配置
        self.api_key = api_key or os.getenv('NOTION_API_KEY')
        self.use_proxy = use_proxy
        
        # 验证必要的配置
        if not self.api_key:
            raise ValueError("Notion API 密钥未提供，请设置 NOTION_API_KEY 环境变量")
        
        # 配置代理
        self.proxies = None
        if self.use_proxy:
            http_proxy = os.getenv('HTTP_PROXY')
            https_proxy = os.getenv('HTTPS_PROXY')
            if http_proxy or https_proxy:
                self.proxies = {}
                if http_proxy:
                    self.proxies['http'] = http_proxy
                if https_proxy:
                    self.proxies['https'] = https_proxy
                logger.info(f"配置了代理: {self.proxies}")
            else:
                logger.info("未找到代理配置，将直接连接")
        else:
            logger.info("已禁用代理")
        
        # Notion API 基础 URL
        self.api_base = "https://api.notion.com/v1"
        
        # 请求头
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def extract_page_id_from_url(self, notion_url):
        """
        从 Notion 页面 URL 中提取页面 ID
        
        Args:
            notion_url: Notion 页面 URL
            
        Returns:
            str: 提取的页面 ID
        """
        # 匹配 Notion URL 中的页面 ID 部分
        match = re.search(r'/([0-9a-f]{32})(?:\.|\?|$)', notion_url, re.IGNORECASE)
        if not match:
            raise ValueError(f"无法从 URL 中提取页面 ID: {notion_url}")
        
        page_id = match.group(1)
        # 转换为标准 UUID 格式
        formatted_uuid = f"{page_id[:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:]}"
        return formatted_uuid
    
    def parse_markdown_report(self, markdown_content):
        """
        解析 Markdown 格式的报告，提取关键信息
        
        Args:
            markdown_content: Markdown 格式的报告内容
            
        Returns:
            dict: 提取的论文信息
        """
        try:
            # 提取论文标题
            title_match = re.search(r'^#\s+(.*?)$', markdown_content, re.MULTILINE)
            title = title_match.group(1) if title_match else "未命名论文"
            
            # 提取摘要
            abstract_match = re.search(r'##\s+1\.\s+论文摘要\s+(.*?)(?=##\s+\d+\.|$)', 
                                     markdown_content, re.DOTALL)
            abstract = abstract_match.group(1).strip() if abstract_match else ""
            
            # 提取研究背景
            background_match = re.search(r'##\s+2\.\s+研究背景\s+(.*?)(?=##\s+\d+\.|$)', 
                                       markdown_content, re.DOTALL)
            background = background_match.group(1).strip() if background_match else ""
            
            # 提取研究方法
            method_match = re.search(r'##\s+3\.\s+研究方法\s+(.*?)(?=##\s+\d+\.|$)', 
                                   markdown_content, re.DOTALL)
            method = method_match.group(1).strip() if method_match else ""
            
            # 提取核心结论
            conclusion_match = re.search(r'##\s+6\.\s+核心结论\s+(.*?)(?=##\s+\d+\.|$)', 
                                       markdown_content, re.DOTALL)
            conclusion = conclusion_match.group(1).strip() if conclusion_match else ""
            
            # 提取创新点
            innovation_match = re.search(r'##\s+7\.\s+创新点\s+(.*?)(?=##\s+\d+\.|$)', 
                                      markdown_content, re.DOTALL)
            innovation = innovation_match.group(1).strip() if innovation_match else ""
            
            return {
                "title": title,
                "abstract": abstract,
                "background": background,
                "method": method,
                "conclusion": conclusion,
                "innovation": innovation,
                "full_report": markdown_content
            }
            
        except Exception as e:
            logger.error(f"解析 Markdown 报告时出错: {str(e)}")
            raise
    
    def create_notion_blocks(self, paper_info):
        """
        根据论文信息创建 Notion 块结构
        
        Args:
            paper_info: 论文信息字典
            
        Returns:
            list: Notion 块列表
        """
        blocks = []
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 添加导入标记和时间
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": f"论文分析报告 (导入时间: {timestamp})"}
                }]
            }
        })
        
        # 添加标题
        blocks.append({
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": paper_info["title"]}
                }]
            }
        })
        
        # 添加摘要
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": "论文摘要"}
                }]
            }
        })
        
        # 处理摘要内容，分割为段落
        for para in paper_info["abstract"].split("\n\n"):
            if para.strip():
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": para.strip()}
                        }]
                    }
                })
        
        # 添加研究背景
        if paper_info["background"]:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": "研究背景"}
                    }]
                }
            })
            
            for para in paper_info["background"].split("\n\n"):
                if para.strip():
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": para.strip()}
                            }]
                        }
                    })
        
        # 添加研究方法
        if paper_info["method"]:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": "研究方法"}
                    }]
                }
            })
            
            for para in paper_info["method"].split("\n\n"):
                if para.strip():
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": para.strip()}
                            }]
                        }
                    })
        
        # 添加核心结论
        if paper_info["conclusion"]:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": "核心结论"}
                    }]
                }
            })
            
            for para in paper_info["conclusion"].split("\n\n"):
                if para.strip():
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": para.strip()}
                            }]
                        }
                    })
        
        # 添加创新点
        if paper_info["innovation"]:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": "创新点"}
                    }]
                }
            })
            
            for para in paper_info["innovation"].split("\n\n"):
                if para.strip():
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": para.strip()}
                            }]
                        }
                    })
        
        # 添加分隔线
        blocks.append({
            "object": "block",
            "type": "divider",
            "divider": {}
        })
        
        return blocks
    
    def add_content_to_page(self, page_url, markdown_content):
        """
        将 Markdown 内容添加到指定的 Notion 页面
        
        Args:
            page_url: Notion 页面 URL
            markdown_content: Markdown 格式的内容
            
        Returns:
            str: 更新后的页面 URL
        """
        try:
            # 从 URL 提取页面 ID
            page_id = self.extract_page_id_from_url(page_url)
            logger.info(f"提取到页面 ID: {page_id}")
            
            # 解析 Markdown 内容
            paper_info = self.parse_markdown_report(markdown_content)
            
            # 创建 Notion 块
            blocks = self.create_notion_blocks(paper_info)
            
            # 创建会话并配置超时
            session = requests.Session()
            session.headers.update(self.headers)
            timeout = int(os.getenv('REQUEST_TIMEOUT', 30))
            
            # 获取页面信息，确认页面存在
            response = session.get(
                f"{self.api_base}/blocks/{page_id}/children",
                proxies=self.proxies,
                timeout=timeout
            )
            
            if response.status_code != 200:
                logger.error(f"获取页面信息失败，状态码: {response.status_code}")
                logger.error(f"错误响应内容: {response.text}")
                response.raise_for_status()
            
            # 添加新块到页面末尾
            response = session.patch(
                f"{self.api_base}/blocks/{page_id}/children",
                json={"children": blocks},
                proxies=self.proxies,
                timeout=timeout
            )
            
            if response.status_code != 200:
                logger.error(f"添加内容到页面失败，状态码: {response.status_code}")
                logger.error(f"错误响应内容: {response.text}")
                response.raise_for_status()
            
            logger.info(f"成功将论文分析报告添加到 Notion 页面: {page_url}")
            return page_url
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"添加内容到页面时出现 HTTP 错误: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                error_details = e.response.text
                logger.error(f"错误响应详情: {error_details}")
                
                # 提供更具体的错误提示
                if "object_not_found" in error_details:
                    logger.error("\n====== 错误原因分析 ======")
                    logger.error("1. 页面 URL 可能不正确")
                    logger.error("2. 页面未与您的 Notion 集成共享")
                    logger.error("3. 集成权限可能不足")
                    logger.error("\n====== 解决建议 ======")
                    logger.error("1. 检查页面 URL 是否正确")
                    logger.error("2. 在 Notion 中，确保页面已与集成共享（点击分享按钮，选择您的集成）")
                    logger.error("3. 确保集成有'读取和写入'权限")
            raise
        except requests.exceptions.ProxyError as e:
            logger.error(f"代理连接错误: {str(e)}")
            logger.error("建议: 尝试禁用代理或检查代理配置")
            raise
        except Exception as e:
            logger.error(f"添加内容到页面时出错: {str(e)}")
            raise

def import_paper_report_to_notion(markdown_file_path, api_key=None, database_id=None, use_proxy=True, as_page=False):
    """
    便捷函数：将论文分析报告导入到 Notion 指定页面
    
    Args:
        markdown_file_path: Markdown 文件路径
        api_key: Notion API 密钥（可选）
        database_id: Notion 数据库 ID（可选，此处未使用）
        use_proxy: 是否使用代理（默认为 True）
        as_page: 是否创建独立页面（此处未使用，保持兼容性）
        
    Returns:
        str: 更新后的 Notion 页面 URL
    """
    # 目标 Notion 页面 URL
    TARGET_PAGE_URL = "https://www.notion.so/28e75567538080968739fdab18dfb2d7?pvs=43&qid=&origin="
    
    try:
        # 创建页面复制器实例
        copier = NotionPageCopier(
            api_key=api_key,
            use_proxy=use_proxy
        )
        
        # 读取 Markdown 文件
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # 添加内容到指定页面
        page_url = copier.add_content_to_page(TARGET_PAGE_URL, markdown_content)
        
        return page_url
    except Exception as e:
        logger.error(f"导入论文报告到 Notion 页面时发生错误: {str(e)}")
        raise