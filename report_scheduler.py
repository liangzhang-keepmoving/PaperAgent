#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时报告调度模块
用于定时检索指定领域最新论文并生成进展报告
"""
import os
import time
import logging
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import dotenv

# 导入项目模块
dotenv.load_dotenv()
from deepseek_api import deepseek_api
from paper_searcher import paper_searcher
from paper_downloader import paper_downloader
from utils.markdown_utils import save_markdown_report, format_table, generate_report_title

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ReportScheduler:
    """定时报告调度类，用于管理和执行定时报告任务"""
    
    def __init__(self):
        """初始化报告调度器"""
        # 创建调度器
        self.scheduler = BackgroundScheduler(job_defaults={'max_instances': 3})
        self.scheduler.start()
        
        # 任务存储
        self.jobs = {}
        
        # 读取邮件配置
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'smtp_user': os.getenv('SMTP_USER'),
            'smtp_password': os.getenv('SMTP_PASSWORD'),
            'sender': os.getenv('EMAIL_SENDER'),
            'recipients': os.getenv('EMAIL_RECIPIENTS', '').split(',')
        }
        
        # 检查必要的邮件配置
        if not all([self.email_config['smtp_user'], self.email_config['smtp_password'], self.email_config['sender']]):
            logger.warning("邮件配置不完整，发送邮件功能可能无法正常工作")
        
        # 确保输出目录存在
        self.output_dir = "outputs"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"创建输出目录: {self.output_dir}")
    
    def __del__(self):
        """析构函数，关闭调度器"""
        if hasattr(self, 'scheduler') and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("调度器已关闭")
    
    def create_research_report(self, research_topic, max_papers=10, time_window_days=7):
        """
        创建研究进展报告
        
        Args:
            research_topic: 研究主题
            max_papers: 最多包含的论文数量
            time_window_days: 时间窗口（天）
        
        Returns:
            dict: 报告信息
        """
        try:
            logger.info(f"为主题 '{research_topic}' 创建研究进展报告")
            
            # 计算时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=time_window_days)
            
            # 构建搜索查询
            search_query = research_topic
            # 可以根据需要添加时间范围限制到查询中
            
            # 搜索最新论文
            papers = paper_searcher.search_papers(
                query=search_query,
                platforms=["arxiv", "google_scholar", "dblp"],
                max_results=max_papers,
                sort_by="relevance"
            )
            
            if not papers:
                logger.warning(f"未找到关于 '{research_topic}' 的论文")
                return None
            
            # 为每篇论文获取详细信息
            detailed_papers = []
            for paper in papers:
                detailed = paper_searcher.get_paper_details(paper)
                detailed_papers.append(detailed)
            
            # 准备发送给DeepSeek API的摘要信息
            papers_summary = []
            for i, paper in enumerate(detailed_papers[:5], 1):  # 只取前5篇用于生成总结
                summary_item = {
                    "title": paper.get("title", "Unknown Title"),
                    "authors": paper.get("authors", paper.get("authors_year", "Unknown Authors")),
                    "abstract": paper.get("abstract", "No abstract available"),
                    "source": paper.get("source", "Unknown Source"),
                    "date": paper.get("date", str(datetime.now().year))
                }
                papers_summary.append(summary_item)
            
            # 调用DeepSeek API生成研究进展总结
            prompt = self._generate_summary_prompt(research_topic, papers_summary, start_date, end_date)
            summary = deepseek_api.generate_research_summary(prompt)
            
            if not summary:
                logger.warning("无法生成研究进展总结")
                # 使用默认总结
                summary = f"在过去{time_window_days}天内，关于'{research_topic}'主题有{len(papers)}篇新论文发表。\n"\
                          f"由于API限制，无法生成详细总结。请查看下方论文列表了解更多信息。"
            
            # 生成报告标题
            title = generate_report_title(research_topic, start_date, end_date)
            
            # 准备论文列表表格数据
            table_data = []
            for paper in detailed_papers:
                # 提取论文信息
                title = paper.get("title", "Unknown Title")
                authors = paper.get("authors", paper.get("authors_year", "Unknown Authors"))
                source = paper.get("source", "Unknown Source")
                link = paper.get("link", "")
                citations = paper.get("citations", 0)
                
                # 构建表格行
                table_data.append({
                    "标题": title,
                    "作者": authors,
                    "来源": source,
                    "引用量": citations,
                    "链接": link
                })
            
            # 生成Markdown表格
            paper_table = format_table(table_data)
            
            # 构建完整报告内容
            report_content = f"# {title}\n\n"\
                            f"## 研究进展总结\n\n"\
                            f"{summary}\n\n"\
                            f"## 最新论文列表\n\n"\
                            f"{paper_table}\n"\
                            f"\n## 报告生成信息\n"\
                            f"- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"\
                            f"- 检索平台: arXiv, Google Scholar, dblp\n"\
                            f"- 时间窗口: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}\n"\
                            f"- 论文数量: {len(detailed_papers)}"
            
            # 保存报告到文件
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"{current_time}_{title.replace(' ', '_').replace(':', '')[:50]}.md"
            report_path = os.path.join(self.output_dir, report_filename)
            save_markdown_report(report_content, report_path)
            
            logger.info(f"研究报告已保存: {report_path}")
            
            # 返回报告信息
            return {
                "title": title,
                "content": report_content,
                "path": report_path,
                "papers": detailed_papers,
                "generated_at": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"创建研究报告失败: {str(e)}")
            return None
    
    def _generate_summary_prompt(self, topic, papers, start_date, end_date):
        """
        生成用于DeepSeek API的摘要提示
        
        Args:
            topic: 研究主题
            papers: 论文摘要信息列表
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            str: 完整的提示文本
        """
        prompt = f"你是一名专业的研究助手。请基于以下论文信息，为'{topic}'领域创建一份{start_date.strftime('%Y-%m-%d')}至{end_date.strftime('%Y-%m-%d')}期间的研究进展报告。\n\n"
        prompt += "请按照以下结构撰写报告：\n"
        prompt += "1. 总体趋势概述：总结该领域的最新研究动向和热点\n"
        prompt += "2. 重要founded发现：列出几项最具创新性或影响力的研究成果\n"
        prompt += "3. 技术进展：分析相关技术的最新发展\n"
        prompt += "4. 未来研究方向：基于现有研究，提出可能的未来研究方向\n\n"
        prompt += "请确保报告内容专业、客观，并基于提供的论文信息。\n\n"
        prompt += "论文信息如下：\n"
        
        for i, paper in enumerate(papers, 1):
            prompt += f"\n{i}. 标题：{paper['title']}\n"
            prompt += f"   作者：{paper['authors']}\n"
            prompt += f"   摘要：{paper['abstract'][:300]}...\n"  # 限制摘要长度
            prompt += f"   来源：{paper['source']}\n"  
        
        return prompt
    
    def send_email_report(self, report_info, recipients=None):
        """
        发送邮件报告
        
        Args:
            report_info: 报告信息字典
            recipients: 收件人列表，如果为None则使用配置中的收件人
        
        Returns:
            bool: 是否发送成功
        """
        try:
            # 检查邮件配置
            if not all([self.email_config['smtp_user'], self.email_config['smtp_password'], self.email_config['sender']]):
                logger.error("邮件配置不完整，无法发送邮件")
                return False
            
            # 使用指定的收件人或配置中的收件人
            if recipients is None:
                recipients = self.email_config['recipients']
            
            if not recipients:
                logger.error("没有指定收件人，无法发送邮件")
                return False
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender']
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = report_info['title']
            
            # 添加邮件正文
            body = f"您好！\n\n"
            body += f"这是关于{report_info['title'].replace('研究进展报告：', '')}的最新研究进展报告。\n\n"
            body += "请查看附件获取完整报告内容。\n\n"
            body += "报告生成时间：" + report_info['generated_at'].strftime('%Y-%m-%d %H:%M:%S') + "\n"
            body += "报告包含论文数量：" + str(len(report_info['papers'])) + "\n\n"
            body += "祝您科研顺利！\n"
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 添加报告附件
            if 'path' in report_info and os.path.exists(report_info['path']):
                with open(report_info['path'], 'rb') as file:
                    attachment = MIMEApplication(file.read(), Name=os.path.basename(report_info['path']))
                    attachment['Content-Disposition'] = f'attachment; filename="{os.path.basename(report_info['path'])}"'  
                    msg.attach(attachment)
            
            # 发送邮件
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['smtp_user'], self.email_config['smtp_password'])
                server.send_message(msg)
            
            logger.info(f"邮件报告已发送至: {', '.join(recipients)}")
            return True
            
        except Exception as e:
            logger.error(f"发送邮件失败: {str(e)}")
            return False
    
    def add_daily_report_job(self, job_id, research_topic, max_papers=10, time_window_days=7, hour=9, minute=0, recipients=None):
        """
        添加每日报告任务
        
        Args:
            job_id: 任务ID
            research_topic: 研究主题
            max_papers: 最多包含的论文数量
            time_window_days: 时间窗口（天）
            hour: 执行小时
            minute: 执行分钟
            recipients: 收件人列表
        
        Returns:
            str: 任务ID
        """
        # 定义任务函数
        def daily_report_task():
            logger.info(f"执行每日报告任务: {job_id} - {research_topic}")
            report = self.create_research_report(research_topic, max_papers, time_window_days)
            if report:
                self.send_email_report(report, recipients)
        
        # 创建定时触发器
        trigger = CronTrigger(hour=hour, minute=minute)
        
        # 添加任务到调度器
        job = self.scheduler.add_job(
            daily_report_task,
            trigger=trigger,
            id=job_id,
            name=f"每日报告: {research_topic}",
            replace_existing=True
        )
        
        self.jobs[job_id] = job
        logger.info(f"已添加每日报告任务 '{job_id}'，将在每天 {hour:02d}:{minute:02d} 执行")
        return job_id
    
    def add_weekly_report_job(self, job_id, research_topic, max_papers=20, time_window_days=7, day_of_week='monday', hour=9, minute=0, recipients=None):
        """
        添加每周报告任务
        
        Args:
            job_id: 任务ID
            research_topic: 研究主题
            max_papers: 最多包含的论文数量
            time_window_days: 时间窗口（天）
            day_of_week: 执行星期几
            hour: 执行小时
            minute: 执行分钟
            recipients: 收件人列表
        
        Returns:
            str: 任务ID
        """
        # 定义任务函数
        def weekly_report_task():
            logger.info(f"执行每周报告任务: {job_id} - {research_topic}")
            report = self.create_research_report(research_topic, max_papers, time_window_days)
            if report:
                self.send_email_report(report, recipients)
        
        # 创建定时触发器
        trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
        
        # 添加任务到调度器
        job = self.scheduler.add_job(
            weekly_report_task,
            trigger=trigger,
            id=job_id,
            name=f"每周报告: {research_topic}",
            replace_existing=True
        )
        
        self.jobs[job_id] = job
        logger.info(f"已添加每周报告任务 '{job_id}'，将在每周 {day_of_week} {hour:02d}:{minute:02d} 执行")
        return job_id
    
    def add_monthly_report_job(self, job_id, research_topic, max_papers=30, time_window_days=30, day=1, hour=9, minute=0, recipients=None):
        """
        添加每月报告任务
        
        Args:
            job_id: 任务ID
            research_topic: 研究主题
            max_papers: 最多包含的论文数量
            time_window_days: 时间窗口（天）
            day: 执行日期（1-31）
            hour: 执行小时
            minute: 执行分钟
            recipients: 收件人列表
        
        Returns:
            str: 任务ID
        """
        # 定义任务函数
        def monthly_report_task():
            logger.info(f"执行每月报告任务: {job_id} - {research_topic}")
            report = self.create_research_report(research_topic, max_papers, time_window_days)
            if report:
                self.send_email_report(report, recipients)
        
        # 创建定时触发器
        trigger = CronTrigger(day=day, hour=hour, minute=minute)
        
        # 添加任务到调度器
        job = self.scheduler.add_job(
            monthly_report_task,
            trigger=trigger,
            id=job_id,
            name=f"每月报告: {research_topic}",
            replace_existing=True
        )
        
        self.jobs[job_id] = job
        logger.info(f"已添加每月报告任务 '{job_id}'，将在每月 {day}日 {hour:02d}:{minute:02d} 执行")
        return job_id
    
    def add_interval_report_job(self, job_id, research_topic, seconds=0, minutes=0, hours=0, days=0, weeks=0, max_papers=10, time_window_days=7, recipients=None):
        """
        添加间隔执行的报告任务
        
        Args:
            job_id: 任务ID
            research_topic: 研究主题
            seconds: 秒间隔
            minutes: 分钟间隔
            hours: 小时间隔
            days: 天间隔
            weeks: 周间隔
            max_papers: 最多包含的论文数量
            time_window_days: 时间窗口（天）
            recipients: 收件人列表
        
        Returns:
            str: 任务ID
        """
        # 定义任务函数
        def interval_report_task():
            logger.info(f"执行间隔报告任务: {job_id} - {research_topic}")
            report = self.create_research_report(research_topic, max_papers, time_window_days)
            if report:
                self.send_email_report(report, recipients)
        
        # 创建间隔触发器
        trigger = IntervalTrigger(seconds=seconds, minutes=minutes, hours=hours, days=days, weeks=weeks)
        
        # 添加任务到调度器
        job = self.scheduler.add_job(
            interval_report_task,
            trigger=trigger,
            id=job_id,
            name=f"间隔报告: {research_topic}",
            replace_existing=True
        )
        
        self.jobs[job_id] = job
        logger.info(f"已添加间隔报告任务 '{job_id}'")
        return job_id
    
    def remove_job(self, job_id):
        """
        移除定时任务
        
        Args:
            job_id: 任务ID
        
        Returns:
            bool: 是否移除成功
        """
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]
            logger.info(f"已移除任务: {job_id}")
            return True
        except Exception as e:
            logger.error(f"移除任务失败: {str(e)}")
            return False
    
    def list_jobs(self):
        """
        列出所有定时任务
        
        Returns:
            list: 任务信息列表
        """
        jobs_info = []
        for job in self.scheduler.get_jobs():
            job_info = {
                'id': job.id,
                'name': job.name,
                'next_run_time': str(job.next_run_time) if job.next_run_time else None,
                'trigger': str(job.trigger)
            }
            jobs_info.append(job_info)
        return jobs_info
    
    def run_job_now(self, job_id):
        """
        立即运行指定任务
        
        Args:
            job_id: 任务ID
        
        Returns:
            bool: 是否运行成功
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                logger.info(f"立即运行任务: {job_id}")
                # 获取任务函数
                job_func = job.func
                # 在当前线程中运行任务
                job_func()
                return True
            else:
                logger.error(f"任务不存在: {job_id}")
                return False
        except Exception as e:
            logger.error(f"运行任务失败: {str(e)}")
            return False

# 单例模式实例
report_scheduler = ReportScheduler()

if __name__ == "__main__":
    # 测试代码
    scheduler = ReportScheduler()
    
    # 创建测试报告
    print("测试创建研究报告...")
    report = scheduler.create_research_report("large language models", max_papers=5, time_window_days=30)
    
    if report:
        print(f"报告创建成功: {report['path']}")
        
        # 测试发送邮件（可选）
        # response = input("是否测试发送邮件？(y/n): ")
        # if response.lower() == 'y':
        #     scheduler.send_email_report(report)
    else:
        print("报告创建失败")
        
    # 测试添加定时任务（会在后台运行，不会立即执行）
    scheduler.add_daily_report_job(
        "daily_llm_report", 
        "large language models",
        max_papers=10,
        hour=9,
        minute=0
    )
    
    # 列出所有任务
    print("\n当前任务列表:")
    for job in scheduler.list_jobs():
        print(f"- ID: {job['id']}, 名称: {job['name']}, 下次运行: {job['next_run_time']}")
    
    # 提示用户按Enter退出
    print("\n调度器已启动。按Enter键退出...")
    input()