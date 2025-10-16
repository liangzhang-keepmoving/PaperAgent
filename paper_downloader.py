#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文下载模块
用于从各种来源下载论文PDF文件
"""
import os
import re
import time
import logging
import requests
import shutil
from urllib.parse import urlparse, unquote
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
# 修改导入语句，使用正确的函数名
from utils.web_utils import setup_webdriver, download_file, fetch_url_content

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PaperDownloader:
    """论文下载类，提供从多个来源下载论文的功能"""
    
    def __init__(self, download_dir="downloads"):
        """
        初始化论文下载器
        
        Args:
            download_dir: 论文下载目录
        """
        # 初始化WebDriver
        self.driver = None
        # 设置下载目录
        self.download_dir = os.path.abspath(download_dir)
        
        # 创建下载目录（如果不存在）
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            logger.info(f"创建下载目录: {self.download_dir}")
    
    def __del__(self):
        """析构函数，关闭WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"关闭WebDriver失败: {str(e)}")
    
    def _init_driver(self):
        """初始化Selenium WebDriver"""
        if not self.driver:
            # 使用setup_webdriver替代get_webdriver
            self.driver = setup_webdriver()
    
    def _sanitize_filename(self, filename):
        """
        清理文件名中的非法字符
        
        Args:
            filename: 原始文件名
        
        Returns:
            str: 清理后的文件名
        """
        # 移除非法字符
        filename = re.sub(r'[\\/:*?"<>|]', '_', filename)
        # 限制文件名长度
        max_length = 200
        if len(filename) > max_length:
            # 保留扩展名
            name, ext = os.path.splitext(filename)
            filename = name[:max_length - len(ext)] + ext
        return filename
    
    def download_from_url(self, url, filename=None, overwrite=False, max_retries=3):
        """
        从URL下载论文文件
        
        Args:
            url: 论文下载链接
            filename: 保存的文件名，如果为None则从URL推断
            overwrite: 是否覆盖已存在的文件
            max_retries: 最大重试次数
        
        Returns:
            str: 下载文件的路径，如果下载失败则返回None
        """
        if not url:
            logger.error("下载链接不能为空")
            return None
        
        # 推断文件名
        if filename is None:
            # 从URL路径中提取文件名
            parsed_url = urlparse(url)
            path = unquote(parsed_url.path)
            filename = os.path.basename(path)
            
            # 如果没有文件名或扩展名，使用默认名
            if not filename or '.' not in filename:
                filename = f"paper_{int(time.time())}.pdf"
        
        # 确保文件有.pdf扩展名
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        
        # 清理文件名
        filename = self._sanitize_filename(filename)
        
        # 构建完整的保存路径
        save_path = os.path.join(self.download_dir, filename)
        
        # 检查文件是否已存在
        if os.path.exists(save_path) and not overwrite:
            logger.info(f"文件已存在，跳过下载: {save_path}")
            return save_path
        
        # 尝试下载
        retry_count = 0
        while retry_count < max_retries:
            try:
                logger.info(f"正在下载论文，第{retry_count+1}次尝试: {url}")
                
                # 使用web_utils中的download_file函数
                result = download_file(url, save_path)
                
                if result and os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                    logger.info(f"论文下载成功: {save_path}")
                    return save_path
                else:
                    logger.warning(f"下载失败，文件可能为空: {save_path}")
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.info(f"{retry_count}秒后重试...")
                        time.sleep(retry_count)
            except Exception as e:
                logger.error(f"下载过程中出错: {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"{retry_count}秒后重试...")
                    time.sleep(retry_count)
        
        logger.error(f"达到最大重试次数，下载失败: {url}")
        return None
    
    def download_from_arxiv(self, arxiv_id, overwrite=False):
        """
        从arXiv下载论文
        
        Args:
            arxiv_id: arXiv论文ID
            overwrite: 是否覆盖已存在的文件
        
        Returns:
            str: 下载文件的路径，如果下载失败则返回None
        """
        try:
            # 构建下载链接
            arxiv_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            
            # 构建文件名
            filename = f"arxiv_{arxiv_id}.pdf"
            
            logger.info(f"从arXiv下载论文: {arxiv_id}")
            return self.download_from_url(arxiv_url, filename, overwrite)
            
        except Exception as e:
            logger.error(f"从arXiv下载论文失败: {str(e)}")
            return None
    
    def download_from_google_scholar(self, paper_info, overwrite=False):
        """
        尝试从Google Scholar下载论文
        
        Args:
            paper_info: 论文信息字典
            overwrite: 是否覆盖已存在的文件
        
        Returns:
            str: 下载文件的路径，如果下载失败则返回None
        """
        try:
            self._init_driver()
            
            # 获取论文链接
            paper_url = paper_info.get("link", "")
            if not paper_url:
                logger.error("论文链接为空")
                return None
            
            # 尝试直接访问论文页面
            logger.info(f"尝试从Google Scholar访问论文页面: {paper_url}")
            self.driver.get(paper_url)
            
            # 等待页面加载
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            # 尝试查找PDF链接或下载按钮
            pdf_links = []
            
            # 检查页面上的PDF链接
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in all_links:
                try:
                    href = link.get_attribute("href")
                    if href and (".pdf" in href.lower() or "download" in href.lower()):
                        pdf_links.append(href)
                except:
                    continue
            
            # 从页面内容中提取可能的PDF链接
            page_source = self.driver.page_source
            pdf_pattern = r'href=["\'](.*?\.pdf)["\']'
            pdf_matches = re.findall(pdf_pattern, page_source, re.IGNORECASE)
            for match in pdf_matches:
                if match not in pdf_links:
                    # 处理相对链接
                    if not match.startswith("http"):
                        base_url = f"{urlparse(paper_url).scheme}://{urlparse(paper_url).netloc}"
                        if match.startswith("/"):
                            match = base_url + match
                        else:
                            match = base_url + "/" + match
                    pdf_links.append(match)
            
            # 尝试下载找到的PDF链接
            title = paper_info.get("title", "").replace("/", "_")
            for pdf_link in pdf_links:
                logger.info(f"找到PDF链接: {pdf_link}")
                
                # 构建文件名
                filename = f"gs_{title[:50]}.pdf" if title else None
                
                # 尝试下载
                result = self.download_from_url(pdf_link, filename, overwrite)
                if result:
                    return result
            
            logger.warning(f"未找到可下载的PDF链接: {paper_url}")
            return None
            
        except Exception as e:
            logger.error(f"从Google Scholar下载论文失败: {str(e)}")
            return None
    
    def download_paper(self, paper_info, overwrite=False, prefer_direct=False):
        """
        下载论文，尝试多种方法
        
        Args:
            paper_info: 论文信息字典
            overwrite: 是否覆盖已存在的文件
            prefer_direct: 是否优先使用直接下载链接
        
        Returns:
            str: 下载文件的路径，如果下载失败则返回None
        """
        # 从论文信息中提取关键信息
        title = paper_info.get("title", "")
        link = paper_info.get("link", "")
        source = paper_info.get("source", "")
        
        logger.info(f"尝试下载论文: {title}")
        
        # 根据来源选择不同的下载策略
        if source.lower() == "arxiv" or "arxiv" in link.lower():
            # 从arXiv链接提取ID
            arxiv_match = re.search(r'arxiv\.org/abs/(\d+\.\d+v?\d*)', link)
            if arxiv_match:
                arxiv_id = arxiv_match.group(1)
                result = self.download_from_arxiv(arxiv_id, overwrite)
                if result:
                    return result
        
        # 检查链接是否已经是PDF链接
        if prefer_direct and link and link.lower().endswith('.pdf'):
            # 构建文件名
            filename = None
            if title:
                filename = f"{title[:100]}.pdf"
            
            result = self.download_from_url(link, filename, overwrite)
            if result:
                return result
        
        # 尝试从Google Scholar下载（如果适用）
        if source.lower() == "google scholar" or "scholar.google" in link.lower():
            result = self.download_from_google_scholar(paper_info, overwrite)
            if result:
                return result
        
        # 尝试直接访问链接并查找PDF
        if link:
            try:
                self._init_driver()
                
                logger.info(f"尝试直接访问论文页面查找PDF: {link}")
                self.driver.get(link)
                
                # 等待页面加载
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                
                # 检查页面是否直接显示PDF
                current_url = self.driver.current_url
                if current_url.lower().endswith('.pdf'):
                    filename = None
                    if title:
                        filename = f"{title[:100]}.pdf"
                    return self.download_from_url(current_url, filename, overwrite)
                
                # 查找页面中的PDF链接
                pdf_links = []
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                for a_link in all_links:
                    try:
                        href = a_link.get_attribute("href")
                        if href and (".pdf" in href.lower() or "download" in href.lower()):
                            pdf_links.append(href)
                    except:
                        continue
                
                # 尝试下载找到的PDF链接
                for pdf_link in pdf_links:
                    logger.info(f"找到PDF链接: {pdf_link}")
                    filename = None
                    if title:
                        filename = f"{title[:100]}.pdf"
                    result = self.download_from_url(pdf_link, filename, overwrite)
                    if result:
                        return result
                
            except Exception as e:
                logger.error(f"直接访问链接查找PDF时出错: {str(e)}")
        
        logger.error(f"所有下载方法均失败: {title}")
        return None
    
    def batch_download(self, papers_info, overwrite=False, max_workers=3):
        """
        批量下载论文
        
        Args:
            papers_info: 论文信息列表
            overwrite: 是否覆盖已存在的文件
            max_workers: 最大并发数（目前为串行下载）
        
        Returns:
            list: 下载成功的文件路径列表
        """
        downloaded_files = []
        
        logger.info(f"开始批量下载{len(papers_info)}篇论文")
        
        for i, paper_info in enumerate(papers_info, 1):
            logger.info(f"正在下载第{i}篇论文")
            
            # 下载论文
            file_path = self.download_paper(paper_info, overwrite)
            
            if file_path:
                downloaded_files.append(file_path)
                logger.info(f"已成功下载{len(downloaded_files)}/{i}篇论文")
            
            # 避免请求过于频繁
            time.sleep(2)
        
        logger.info(f"批量下载完成，成功下载{len(downloaded_files)}/{len(papers_info)}篇论文")
        return downloaded_files

# 单例模式实例
paper_downloader = PaperDownloader()

# 在paper_downloader.py文件底部添加一个新方法，以支持main.py中的直接调用

# 在文件末尾添加以下内容
# 下载论文的便捷方法，适配命令行接口
def download_paper(url=None, arxiv_id=None, output_dir=None, overwrite=False):
    """
    下载论文的便捷方法，适配命令行接口
    
    Args:
        url: 论文URL
        arxiv_id: arXiv论文ID
        output_dir: 下载目录
        overwrite: 是否覆盖已存在的文件
        
    Returns:
        str: 下载文件的路径，如果下载失败则返回None
    """
    # 如果提供了output_dir，创建新的下载器实例
    if output_dir:
        downloader = PaperDownloader(download_dir=output_dir)
    else:
        downloader = paper_downloader
    
    # 创建论文信息字典
    paper_info = {}
    
    # 如果提供了URL
    if url:
        paper_info['link'] = url
        paper_info['url'] = url
        if 'arxiv.org' in url:
            paper_info['source'] = 'arxiv'
        
        # 尝试下载
        result = downloader.download_from_url(url, overwrite=overwrite)
        if result:
            return result
        
        # 如果直接URL下载失败，尝试使用完整的download_paper方法
        return downloader.download_paper(paper_info, overwrite=overwrite)
    
    # 如果提供了arXiv ID
    elif arxiv_id:
        return downloader.download_from_arxiv(arxiv_id, overwrite=overwrite)
    
    logger.error("必须提供URL或arXiv ID")
    return None

# 为已有的paper_downloader实例添加这个方法
paper_downloader.download_paper = download_paper

if __name__ == "__main__":
    # 测试代码
    downloader = PaperDownloader()
    
    # 测试从arXiv下载
    print("测试从arXiv下载论文...")
    arxiv_file = downloader.download_from_arxiv("2303.12712")
    print(f"arXiv下载结果: {arxiv_file}")
    
    # 测试从URL直接下载
    print("\n测试从URL直接下载论文...")
    url_file = downloader.download_from_url(
        "https://arxiv.org/pdf/2302.03025.pdf", 
        "example_paper.pdf"
    )
    print(f"URL下载结果: {url_file}")