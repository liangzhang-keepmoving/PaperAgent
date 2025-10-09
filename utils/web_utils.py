#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
网页爬取工具
功能：
1. 发送HTTP请求获取网页内容
2. 解析HTML内容
3. 设置和管理WebDriver
"""

import os
import logging
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# 设置日志
logger = logging.getLogger(__name__)

# 设置请求头
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}


def fetch_url_content(url, use_selenium=False, timeout=30, proxies=None):
    """
    获取网页内容
    
    Args:
        url: 网页URL
        use_selenium: 是否使用Selenium获取动态内容
        timeout: 请求超时时间（秒）
        proxies: 代理设置
        
    Returns:
        网页HTML内容字符串
    """
    try:
        logger.info(f'开始获取URL内容: {url}')
        
        if use_selenium:
            # 使用Selenium获取动态内容
            driver = setup_webdriver()
            try:
                driver.get(url)
                time.sleep(3)  # 等待页面加载
                html_content = driver.page_source
            finally:
                driver.quit()
        else:
            # 使用requests获取静态内容
            session = requests.Session()
            session.headers.update(DEFAULT_HEADERS)
            response = session.get(url, timeout=timeout, proxies=proxies)
            response.raise_for_status()  # 如果状态码不是200，抛出异常
            html_content = response.text
        
        logger.info(f'成功获取URL内容，长度: {len(html_content)} 字符')
        return html_content
        
    except requests.exceptions.RequestException as e:
        logger.error(f'HTTP请求失败: {str(e)}')
        raise
    except Exception as e:
        logger.error(f'获取URL内容时出错: {str(e)}')
        raise


def setup_webdriver(headless=True):
    """
    设置Chrome WebDriver
    
    Args:
        headless: 是否以无头模式运行
        
    Returns:
        配置好的WebDriver实例
    """
    try:
        chrome_options = Options()
        
        # 配置Chrome选项
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(f'user-agent={DEFAULT_HEADERS["User-Agent"]}')
        
        # 配置下载设置（如果需要）
        prefs = {
            'download.default_directory': os.getenv('DOWNLOAD_DIR', './downloads'),
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'plugins.always_open_pdf_externally': True
        }
        chrome_options.add_experimental_option('prefs', prefs)
        
        # 初始化WebDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 设置隐式等待
        driver.implicitly_wait(10)
        
        logger.info('Chrome WebDriver初始化成功')
        return driver
        
    except Exception as e:
        logger.error(f'WebDriver初始化失败: {str(e)}')
        raise


def parse_html(html_content, selector=None):
    """
    解析HTML内容
    
    Args:
        html_content: HTML内容字符串
        selector: CSS选择器，用于提取特定元素
        
    Returns:
        BeautifulSoup对象或选择器匹配的元素列表
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        if selector:
            # 使用CSS选择器提取特定元素
            elements = soup.select(selector)
            logger.info(f'使用选择器 "{selector}" 找到 {len(elements)} 个元素')
            return elements
        
        logger.info('HTML解析完成')
        return soup
        
    except Exception as e:
        logger.error(f'解析HTML时出错: {str(e)}')
        raise


def download_file(url, save_path, timeout=60, proxies=None):
    """
    下载文件
    
    Args:
        url: 文件URL
        save_path: 保存路径
        timeout: 下载超时时间（秒）
        proxies: 代理设置
        
    Returns:
        下载的文件路径
    """
    try:
        logger.info(f'开始下载文件: {url} 到 {save_path}')
        
        # 确保保存目录存在
        save_dir = os.path.dirname(save_path)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # 发送请求下载文件
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)
        response = session.get(url, timeout=timeout, proxies=proxies, stream=True)
        response.raise_for_status()
        
        # 写入文件
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # 记录下载进度
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        if progress % 20 == 0:  # 每20%记录一次
                            logger.info(f'下载进度: {progress:.1f}% ({downloaded_size/1024/1024:.2f}MB/{total_size/1024/1024:.2f}MB)')
        
        logger.info(f'文件下载完成，保存至: {save_path}，大小: {os.path.getsize(save_path)/1024/1024:.2f}MB')
        return save_path
        
    except requests.exceptions.RequestException as e:
        logger.error(f'文件下载失败: {str(e)}')
        raise
    except Exception as e:
        logger.error(f'下载文件时出错: {str(e)}')
        raise