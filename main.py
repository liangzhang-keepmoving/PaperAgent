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
    
    # 启动定时报告命令
    report_parser = subparsers.add_parser('report', help='启动定时报告服务')
    report_parser.add_argument('--topic', type=str, required=True, help='关注的主题')
    report_parser.add_argument('--frequency', type=str, choices=['daily', 'weekly', 'monthly'], 
                              default='weekly', help='报告频率')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'analyze':
            from paper_analyzer import analyze_paper
            analyze_paper(args.paper_path, args.output_path)
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
            from paper_downloader import paper_downloader
            paper_downloader.download_paper(args.url, args.arxiv_id, args.output_dir)
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
    except Exception as e:
        logger.error(f'执行命令时出错: {str(e)}')
        sys.exit(1)


if __name__ == '__main__':
    main()