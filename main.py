#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DeepSeek论文助手主模块
功能：
1. 论文详细分析及参考文献表格整理
2. 多平台论文检索（网页、Google Scholar、arXiv、dblp）
3. 论文下载
4. 定时发送最新进展报告
5. 批量分析文件夹中的所有论文
6. 通过链接直接分析论文
"""

import os
import sys
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置日志配置
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('paper_assistant.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 确保下载和输出目录存在
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', './downloads')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', './outputs')
for directory in [DOWNLOAD_DIR, OUTPUT_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f'创建目录: {directory}')

def main():
    """主函数，提供命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DeepSeek论文助手')
    subparsers = parser.add_subparsers(dest='command', help='支持的命令')
    
    # 分析论文命令
    analyze_parser = subparsers.add_parser('analyze', help='分析指定论文')
    analyze_parser.add_argument('--paper_path', type=str, required=True, help='论文文件路径')
    analyze_parser.add_argument('--output_path', type=str, help='输出Markdown文件路径')
    
    # 通过链接下载并分析论文命令
    analyze_url_parser = subparsers.add_parser('analyze_from_url_download', help='通过链接下载并分析论文')
    analyze_url_parser.add_argument('--url', type=str, required=True, help='论文URL链接')
    analyze_url_parser.add_argument('--output_dir', type=str, help='分析报告保存目录，默认为outputs')
    analyze_url_parser.add_argument('--overwrite', action='store_true', help='是否覆盖已存在的下载文件')
    
    # 新增：直接从URL分析论文命令（无需下载）
    analyze_from_url_parser = subparsers.add_parser('analyze_from_url', help='直接从URL分析论文，无需下载PDF文件')
    analyze_from_url_parser.add_argument('--url', type=str, required=True, help='论文PDF的URL链接')
    analyze_from_url_parser.add_argument('--output_dir', type=str, help='分析报告保存目录，默认为outputs')
    
    # 批量分析论文命令
    batch_analyze_parser = subparsers.add_parser('batch_analyze', help='批量分析文件夹中的所有论文')
    batch_analyze_parser.add_argument('--folder_path', type=str, required=True, help='包含论文的文件夹路径')
    batch_analyze_parser.add_argument('--output_dir', type=str, help='报告保存根目录，默认为outputs')
    
    # 搜索论文命令
    search_parser = subparsers.add_parser('search', help='搜索指定领域的论文')
    search_parser.add_argument('--query', type=str, required=True, help='搜索关键词')
    search_parser.add_argument('--source', type=str, choices=['google_scholar', 'arxiv', 'dblp', 'all'], 
                              default='all', help='搜索来源')
    search_parser.add_argument('--limit', type=int, default=10, help='返回结果数量')
    
    # 下载论文命令
    download_parser = subparsers.add_parser('download', help='下载指定论文')
    download_parser.add_argument('--url', type=str, help='论文URL')
    download_parser.add_argument('--arxiv_id', type=str, help='arXiv论文ID')
    download_parser.add_argument('--output_dir', type=str, help='下载目录')
    download_parser.add_argument('--no_title_rename', action='store_true', help='禁用使用标题重命名文件')
    
    # 启动定时报告命令
    report_parser = subparsers.add_parser('report', help='启动定时报告服务')
    report_parser.add_argument('--topic', type=str, required=True, help='关注的主题')
    report_parser.add_argument('--frequency', type=str, choices=['daily', 'weekly', 'monthly'], 
                              default='weekly', help='报告频率')
    
    # Notion导入命令
    notion_parser = subparsers.add_parser('notion_import', help='将论文分析报告导入到Notion')
    notion_parser.add_argument('--report_path', type=str, required=True, help='论文分析报告的Markdown文件路径')
    notion_parser.add_argument('--api_key', type=str, help='Notion API密钥（可选，默认从环境变量获取）')
    notion_parser.add_argument('--database_id', type=str, help='Notion数据库ID（可选，默认从环境变量获取）')
    notion_parser.add_argument('--no_proxy', action='store_true', help='禁用代理（解决代理连接问题）')
    notion_parser.add_argument('--as_page', action='store_true', help='创建独立页面而不是数据库条目')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'analyze':
            from paper_analyzer import analyze_paper
            analyze_paper(args.paper_path, args.output_path)
        # 直接从URL分析论文（无需下载）
        elif args.command == 'analyze_from_url':
            from paper_analyzer import analyze_paper_from_url
            print(f'正在直接从URL分析论文: {args.url}')
            result_path = analyze_paper_from_url(args.url, args.output_dir)
            print(f'论文分析完成，报告已保存至: {result_path}')
        # 从URL下载后分析论文
        elif args.command == 'analyze_from_url_download':
            from paper_downloader import paper_downloader
            from paper_analyzer import analyze_paper
            
            print(f'正在从链接下载并分析论文: {args.url}')
            
            # 创建包含URL的论文信息字典
            paper_info = {'url': args.url, 'link': args.url}
            
            # 下载论文 - 移除args.arxiv_id参数
            pdf_path = paper_downloader.download_paper(args.url, output_dir=args.output_dir, overwrite=args.overwrite)
            
            if pdf_path:
                print(f'论文下载成功: {pdf_path}')
                print('开始分析论文...')
                # 分析下载的论文
                result_path = analyze_paper(pdf_path, args.output_dir)
                print(f'论文分析完成，报告已保存至: {result_path}')
            else:
                print('论文下载失败，无法进行分析')
                sys.exit(1)
        elif args.command == 'batch_analyze':
            from paper_analyzer import batch_analyze_papers
            print(f'开始批量分析文件夹: {args.folder_path}')
            result = batch_analyze_papers(args.folder_path, args.output_dir)
            print(f'批量分析完成！总共 {result["total"]} 个文件，成功 {result["successful"]} 个，失败 {result["failed"]} 个')
            if result["failed"] > 0:
                print('以下文件分析失败:')
                for file_path, error in result["failed_files"]:
                    print(f'- {os.path.basename(file_path)}: {error}')
        elif args.command == 'search':
            from paper_searcher import paper_searcher
            papers = paper_searcher.search_papers(
                query=args.query,
                platforms=[args.source] if args.source != 'all' else ['semantic_scholar', 'arxiv', 'dblp'],
                max_results=args.limit
            )
            # 打印搜索结果
            for i, paper in enumerate(papers, 1):
                print(f"{i}. {paper.get('title', 'Untitled')}")
                print(f"   Authors: {paper.get('authors', 'Unknown')}")
                print(f"   Link: {paper.get('link', 'No link')}")
                print()
        elif args.command == 'download':
            from paper_downloader import PaperDownloader
            
            # 设置下载目录
            output_dir = args.output_dir or DOWNLOAD_DIR
            downloader = PaperDownloader(download_dir=output_dir)
            
            # 是否使用标题重命名
            use_title_as_name = not args.no_title_rename
            
            if args.url:
                downloader.download_from_url(args.url, use_title_as_name=use_title_as_name)
            elif args.arxiv_id:
                downloader.download_from_arxiv(args.arxiv_id, use_title_as_name=use_title_as_name)
            else:
                logger.error("请提供--url或--arxiv_id参数")
        elif args.command == 'report':
            from report_scheduler import report_scheduler
            import time
            
            # 创建任务ID
            job_id = f"rl_llm_report_{args.frequency}"
            
            # 根据频率添加定时任务
            if args.frequency == 'daily':
                report_scheduler.add_daily_report_job(
                    job_id=job_id,
                    research_topic=args.topic,
                    max_papers=10,
                    time_window_days=7
                )
            elif args.frequency == 'weekly':
                report_scheduler.add_weekly_report_job(
                    job_id=job_id,
                    research_topic=args.topic,
                    max_papers=20,
                    time_window_days=7,
                    day_of_week='monday'
                )
            elif args.frequency == 'monthly':
                report_scheduler.add_monthly_report_job(
                    job_id=job_id,
                    research_topic=args.topic,
                    max_papers=30,
                    time_window_days=30
                )
            
            print(f"已启动{args.frequency}报告服务，主题: {args.topic}")
            print(f"任务ID: {job_id}")
            print("服务将在后台运行，按Ctrl+C退出...")
            
            # 保持程序运行
            try:
                while True:
                    time.sleep(60)  # 每分钟检查一次
            except KeyboardInterrupt:
                print("正在关闭服务...")
                report_scheduler.remove_job(job_id)
                print("服务已关闭")
        # 添加notion_import命令处理逻辑
        elif args.command == 'notion_import':
            from notion_integration import import_paper_report_to_notion
            try:
                print(f"正在导入论文分析报告到 Notion: {args.report_path}")
                # 调用导入函数
                page_url = import_paper_report_to_notion(
                    markdown_file_path=args.report_path,
                    api_key=args.api_key,
                    database_id=args.database_id,
                    use_proxy=not args.no_proxy,
                    as_page=args.as_page
                )
                print(f"导入成功！页面 URL: {page_url}")
            except Exception as e:
                logger.error(f"执行命令时出错: {str(e)}")
                sys.exit(1)
    except Exception as e:
        logger.error(f'执行命令时出错: {str(e)}')
        sys.exit(1)

if __name__ == '__main__':
    main()