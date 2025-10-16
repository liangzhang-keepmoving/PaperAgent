#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
论文检索模块
用于从网页/Semantic Scholar/arXiv/dblp检索指定领域热门高引用高质量论文
支持调用大模型进行搜索结果分析和处理
"""

import os
import re
import time
import logging
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
# 修改导入语句
from utils.web_utils import setup_webdriver, download_file, fetch_url_content
# 导入大模型API模块
from deepseek_api import DeepSeekAPI

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PaperSearcher:
    """论文检索类，提供多种平台的论文检索功能，并支持调用大模型处理结果"""
    
    def __init__(self, api_key=None, api_base=None):
        """
        初始化论文检索器
        
        Args:
            api_key: DeepSeek API密钥，默认为None（从环境变量获取）
            api_base: DeepSeek API基础URL，默认为None（从环境变量获取）
        """
        # 初始化WebDriver
        self.driver = None
        # 论文数据库URL
        self.arxiv_url = "https://arxiv.org"
        self.semantic_scholar_url = "https://api.semanticscholar.org"
        self.dblp_url = "https://dblp.org"
        
        # 获取Semantic Scholar API密钥
        self.semantic_scholar_api_key = os.getenv('SEMANTIC_SCHOLAR_API_KEY')
        
        # 初始化大模型客户端
        self.api_key = api_key
        self.api_base = api_base
        self.deepseek_client = None
        self._init_deepseek_client()
        
    def __del__(self):
        """析构函数，关闭WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"关闭WebDriver失败: {str(e)}")
    
    # 在PaperSearcher类中修改_init_driver方法
    def _init_driver(self):
        """初始化Selenium WebDriver"""
        if not self.driver:
            self.driver = setup_webdriver()  # 从get_webdriver改为setup_webdriver
    
    def _init_deepseek_client(self):
        """初始化DeepSeek API客户端"""
        try:
            # 如果提供了API密钥，则使用提供的密钥，否则从环境变量获取
            if self.api_key or os.getenv('DEEPSEEK_API_KEY'):
                self.deepseek_client = DeepSeekAPI()
                logger.info("DeepSeek API客户端初始化成功")
            else:
                logger.warning("未设置DeepSeek API密钥，无法使用大模型功能")
        except Exception as e:
            logger.error(f"DeepSeek API客户端初始化失败: {str(e)}")
    
    def search_semantic_scholar(self, query, max_results=20, sort_by="citations"):
        """
        使用Semantic Scholar API搜索论文
        
        Args:
            query: 搜索关键词
            max_results: 最大返回结果数
            sort_by: 排序方式，支持'citations'（引用量）或'relevance'（相关性）
        
        Returns:
            list: 论文信息列表
        """
        try:
            if not self.semantic_scholar_api_key:
                logger.error("未设置Semantic Scholar API密钥，请在.env文件中配置SEMANTIC_SCHOLAR_API_KEY")
                return []
            
            # 构建搜索URL
            search_params = {
                "query": query,
                "limit": max_results,
                "fields": "title,abstract,authors,venue,year,citationCount,url,externalIds"
            }
            
            headers = {
                "x-api-key": self.semantic_scholar_api_key,
                "Content-Type": "application/json"
            }
            
            # 根据排序方式设置排序参数
            if sort_by == "citations":
                search_params["sort"] = "citationCount:desc"
            else:
                search_params["sort"] = "relevance"
            
            logger.info(f"使用Semantic Scholar API搜索: {query}")
            
            # 发送API请求
            response = requests.get(
                f"{self.semantic_scholar_url}/graph/v1/paper/search",
                params=search_params,
                headers=headers
            )
            
            # 检查响应状态
            if response.status_code != 200:
                logger.error(f"Semantic Scholar API请求失败: {response.status_code}, {response.text}")
                return []
            
            # 解析响应
            data = response.json()
            papers = []
            
            for paper in data.get("data", []):
                try:
                    # 处理作者信息
                    authors = ", ".join([author.get("name", "Unknown") for author in paper.get("authors", [])])
                    
                    # 提取DOI或其他标识符用于构建完整链接
                    external_ids = paper.get("externalIds", {})
                    url = paper.get("url", "")
                    
                    papers.append({
                        "title": paper.get("title", "Untitled"),
                        "link": url,
                        "abstract": paper.get("abstract", ""),
                        "authors": authors,
                        "year": paper.get("year", ""),
                        "venue": paper.get("venue", ""),
                        "citations": paper.get("citationCount", 0),
                        "source": "Semantic Scholar"
                    })
                    
                except Exception as e:
                    logger.warning(f"解析Semantic Scholar结果时出错: {str(e)}")
                    continue
            
            logger.info(f"从Semantic Scholar获取了{len(papers)}篇论文")
            return papers
            
        except Exception as e:
            logger.error(f"Semantic Scholar搜索失败: {str(e)}")
            return []
    
    # 修改arXiv搜索函数中的get_page_content调用
    def search_arxiv(self, query, max_results=20, sort_by="relevance"):
        """
        在arXiv上搜索论文
        
        Args:
            query: 搜索关键词
            max_results: 最大返回结果数
            sort_by: 排序方式，支持'relevance'（相关性）或'newest'（最新）
        
        Returns:
            list: 论文信息列表
        """
        try:
            # 使用arXiv标准搜索路径格式
            search_url = f"{self.arxiv_url}/search_query?searchtype=all&query={requests.utils.quote(query)}"
            
            logger.info(f"在arXiv上搜索: {query}")
            
            # 尝试使用Selenium获取页面内容，以避免被阻止
            content = fetch_url_content(search_url, use_selenium=True)  # 启用Selenium
            if not content:
                return []
            
            # 解析页面
            soup = BeautifulSoup(content, "html.parser")
            papers = []
            
            # 查找所有论文条目
            entries = soup.select(".arxiv-result")
            
            for entry in entries[:max_results]:
                try:
                    # 标题
                    title = entry.select_one(".title").text.strip()
                    
                    # 链接
                    link = entry.select_one(".title a")['href']
                    if not link.startswith("http"):
                        link = self.arxiv_url + link
                    
                    # 作者
                    authors = entry.select_one(".authors").text.strip().replace("Authors:", "").strip()
                    
                    # 摘要
                    abstract = entry.select_one(".abstract").text.strip().replace("Abstract:", "").strip()
                    
                    # 发表日期
                    date = entry.select_one(".is-size-7").text.strip()
                    
                    papers.append({
                        "title": title,
                        "link": link,
                        "abstract": abstract,
                        "authors": authors,
                        "date": date,
                        "source": "arXiv"
                    })
                    
                except Exception as e:
                    logger.warning(f"解析arXiv结果时出错: {str(e)}")
                    continue
            
            logger.info(f"从arXiv获取了{len(papers)}篇论文")
            return papers
            
        except Exception as e:
            logger.error(f"arXiv搜索失败: {str(e)}")
            return []
    
    # 修改dblp搜索函数中的get_page_content调用
    def search_dblp(self, query, max_results=20, sort_by="relevance"):
        """
        在dblp上搜索论文
        
        Args:
            query: 搜索关键词
            max_results: 最大返回结果数
            sort_by: 排序方式（dblp主要按相关性排序）
        
        Returns:
            list: 论文信息列表
        """
        try:
            # 构建搜索URL
            search_url = f"{self.dblp_url}/search?q={requests.utils.quote(query)}"
            
            logger.info(f"在dblp上搜索: {query}")
            
            # 获取页面内容
            content = fetch_url_content(search_url)  # 从get_page_content改为fetch_url_content
            if not content:
                return []
            
            # 解析页面
            soup = BeautifulSoup(content, "html.parser")
            papers = []
            
            # 查找所有论文条目
            entries = soup.select(".entry")
            
            for entry in entries[:max_results]:
                try:
                    # 标题和链接
                    title_link = entry.select_one(".title a")
                    title = title_link.text.strip()
                    link = title_link['href']
                    
                    # 作者
                    authors = ", ".join([a.text for a in entry.select(".authors a")])
                    
                    # 发表信息
                    venue_info = entry.select_one(".data").text.strip()
                    
                    papers.append({
                        "title": title,
                        "link": link,
                        "authors": authors,
                        "venue_info": venue_info,
                        "source": "dblp"
                    })
                    
                except Exception as e:
                    logger.warning(f"解析dblp结果时出错: {str(e)}")
                    continue
            
            logger.info(f"从dblp获取了{len(papers)}篇论文")
            return papers
            
        except Exception as e:
            logger.error(f"dblp搜索失败: {str(e)}")
            return []
    
    def search_papers(self, query, platforms=None, max_results=20, sort_by="relevance"):
        """
        从多个平台搜索论文
        
        Args:
            query: 搜索关键词
            platforms: 搜索平台列表，默认包括所有支持的平台
            max_results: 每个平台的最大返回结果数
            sort_by: 排序方式
        
        Returns:
            list: 合并后的论文信息列表
        """
        # 默认平台，已替换为Semantic Scholar替代Google Scholar
        if platforms is None:
            platforms = ["semantic_scholar", "arxiv", "dblp"]
        
        all_papers = []
        
        # 执行各平台搜索
        for platform in platforms:
            if platform == "semantic_scholar":
                papers = self.search_semantic_scholar(query, max_results, sort_by)
            elif platform == "arxiv":
                papers = self.search_arxiv(query, max_results, sort_by)
            elif platform == "dblp":
                papers = self.search_dblp(query, max_results, sort_by)
            else:
                logger.warning(f"不支持的搜索平台: {platform}")
                continue
            
            all_papers.extend(papers)
        
        # 去重（基于标题）
        seen_titles = set()
        unique_papers = []
        
        for paper in all_papers:
            title = paper["title"].lower().strip()
            if title not in seen_titles:
                seen_titles.add(title)
                unique_papers.append(paper)
        
        # 如果按引用量排序，合并后再排序
        if sort_by == "citations":
            unique_papers.sort(key=lambda x: x.get("citations", 0), reverse=True)
        
        logger.info(f"总共获取了{len(unique_papers)}篇唯一论文")
        return unique_papers
    
    def get_paper_details(self, paper_info):
        """
        获取论文的详细信息
        
        Args:
            paper_info: 论文基本信息
        
        Returns:
            dict: 包含详细信息的论文字典
        """
        try:
            # 基于来源不同处理
            source = paper_info.get("source", "")
            link = paper_info.get("link", "")
            
            if not link:
                return paper_info
            
            # 可以根据不同来源实现不同的详细信息获取逻辑
            logger.info(f"获取论文详细信息: {paper_info.get('title', 'Unknown')}")
            
            # 这里可以添加更多的详细信息获取逻辑
            # 例如从论文页面提取引用格式、下载链接等
            
            return paper_info
            
        except Exception as e:
            logger.error(f"获取论文详细信息失败: {str(e)}")
            return paper_info
    
    def analyze_search_results(self, papers, analysis_type="summary"):
        """
        使用大模型分析搜索结果
        
        Args:
            papers: 论文列表
            analysis_type: 分析类型，支持'summary'(总结)、'topics'(主题分析)、'trends'(趋势分析)
        
        Returns:
            str: 分析结果文本
        """
        try:
            # 检查大模型客户端是否初始化成功
            if not self.deepseek_client:
                logger.error("DeepSeek API客户端未初始化，无法分析搜索结果")
                return "错误：DeepSeek API客户端未初始化，无法分析搜索结果"
            
            # 准备论文信息文本
            papers_text = "\n".join([f"标题: {paper.get('title', '未知')}\n摘要: {paper.get('abstract', '未知')}\n作者: {paper.get('authors', paper.get('authors_year', '未知'))}\n来源: {paper.get('source', '未知')}\n" for paper in papers[:10]])  # 限制分析论文数量
            
            # 根据分析类型构建不同的提示词
            if analysis_type == "summary":
                prompt = f"""请分析以下学术论文搜索结果，生成一份综合总结：

论文列表：
{papers_text}

总结要求：
1. 概述：简要总结搜索结果的整体内容和主题分布
2. 主要研究方向：归纳出主要的研究方向和每个方向的核心观点
3. 热点话题：指出搜索结果中出现的热点话题和研究趋势
4. 推荐阅读：基于引用量、相关性或创新性，推荐2-3篇值得深入阅读的论文

请以Markdown格式输出总结报告。"""
            elif analysis_type == "topics":
                prompt = f"""请分析以下学术论文搜索结果，进行主题分析：

论文列表：
{papers_text}

分析要求：
1. 识别主要研究主题：从搜索结果中识别出3-5个主要研究主题
2. 主题描述：对每个主题进行简要描述，说明其核心内容
3. 主题分布：分析每个主题在搜索结果中的分布情况
4. 主题间关系：简要分析不同主题之间的关联和区别

请以Markdown格式输出主题分析报告。"""
            elif analysis_type == "trends":
                prompt = f"""请分析以下学术论文搜索结果，进行研究趋势分析：

论文列表：
{papers_text}

分析要求：
1. 时间分布：分析论文的发表时间分布，识别研究活跃度变化
2. 研究重点演变：分析研究重点的变化和发展趋势
3. 新兴方向：识别可能的新兴研究方向和增长点
4. 未来展望：基于当前趋势，对未来研究方向进行简要展望

请以Markdown格式输出趋势分析报告。"""
            else:
                logger.warning(f"不支持的分析类型: {analysis_type}")
                return f"错误：不支持的分析类型 '{analysis_type}'"
            
            logger.info(f"使用大模型进行搜索结果分析，类型: {analysis_type}")
            result = self.deepseek_client.generate_text(prompt, max_tokens=3000)
            
            return result
            
        except Exception as e:
            logger.error(f"分析搜索结果时出错: {str(e)}")
            return f"分析失败: {str(e)}"
    
    def refine_search_query(self, initial_query):
        """
        使用大模型优化搜索查询
        
        Args:
            initial_query: 初始搜索查询
        
        Returns:
            str: 优化后的搜索查询
        """
        try:
            # 检查大模型客户端是否初始化成功
            if not self.deepseek_client:
                logger.error("DeepSeek API客户端未初始化，无法优化搜索查询")
                return initial_query
            
            prompt = f"""你是一个学术搜索专家，请优化以下初始搜索查询，使其更准确、更专业地表达搜索意图：

初始查询：{initial_query}

优化要求：
1. 使用更专业的学术术语
2. 添加相关的同义词或上位词，扩大搜索范围
3. 保持原始搜索意图不变
4. 优化后的查询应适合在Semantic Scholar、arXiv等学术平台使用
5. 只返回优化后的查询，不要添加任何解释或说明

示例：
初始查询：人工智能应用
优化后的查询：人工智能应用 机器学习 深度学习 自然语言处理 计算机视觉
"""
            
            logger.info(f"使用大模型优化搜索查询")
            result = self.deepseek_client.generate_text(prompt, max_tokens=200)
            
            return result.strip() if result else initial_query
            
        except Exception as e:
            logger.error(f"优化搜索查询时出错: {str(e)}")
            return initial_query

# 单例模式实例
paper_searcher = PaperSearcher()

if __name__ == "__main__":
    # 测试代码
    searcher = PaperSearcher()
    
    # 测试搜索
    query = "large language models"
    papers = searcher.search_papers(query, max_results=5)
    
    print(f"搜索 '{query}' 得到 {len(papers)} 篇论文:")
    for i, paper in enumerate(papers, 1):
        print(f"{i}. {paper['title']} ({paper['source']})")
        if paper.get('citations'):
            print(f"   引用量: {paper['citations']}")
        print(f"   链接: {paper.get('link', 'N/A')}")
        print()
    
    # 测试大模型分析功能（如果API可用）
    if searcher.deepseek_client:
        print("\n正在使用大模型分析搜索结果...\n")
        summary = searcher.analyze_search_results(papers)
        print("搜索结果总结：")
        print(summary)
        
        # 测试查询优化
        optimized_query = searcher.refine_search_query(query)
        print(f"\n优化后的查询：{optimized_query}")