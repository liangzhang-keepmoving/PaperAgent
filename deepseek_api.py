#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DeepSeek API封装模块
提供与DeepSeek大模型交互的接口
"""

import os
import logging
from openai import OpenAI

# 设置日志
logger = logging.getLogger(__name__)


class DeepSeekAPI:
    """DeepSeek API封装类"""
    
    def __init__(self):
        """初始化DeepSeek API客户端"""
        api_key = os.getenv('DEEPSEEK_API_KEY')
        api_base = os.getenv('DEEPSEEK_API_BASE', 'https://api.deepseek.com')
        
        if not api_key:
            raise ValueError('DeepSeek API密钥未设置，请在.env文件中配置DEEPSEEK_API_KEY')
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base
        )
        self.model = "deepseek-chat"
        
    def generate_text(self, prompt, model=None, max_tokens=2000, temperature=0.7):
        """
        生成文本回复
        
        Args:
            prompt: 提示词
            model: 模型名称，默认为deepseek-chat
            max_tokens: 最大生成 tokens 数
            temperature: 生成温度，控制随机性
        
        Returns:
            生成的文本字符串
        """
        try:
            response = self.client.chat.completions.create(
                model=model or self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的学术论文助手，擅长分析和总结学术论文。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f'调用DeepSeek API失败: {str(e)}')
            raise
    

    
    def summarize_research_progress(self, paper_list):
        """
        总结研究进展
        
        Args:
            paper_list: 论文列表，每个元素包含标题、摘要、作者等信息
        
        Returns:
            研究进展总结报告
        """
        papers_text = "\n".join([f"标题: {paper.get('title', '未知')}\n摘要: {paper.get('abstract', '未知')}\n作者: {paper.get('authors', '未知')}\n来源: {paper.get('source', '未知')}\n" for paper in paper_list])
        
        prompt = f"""请根据以下最近发表的论文，生成一份研究领域最新进展报告：

论文列表：
{papers_text}

报告要求：
1. 概述：总结该领域的最新研究动态和趋势
2. 主要研究方向：分类整理主要的研究方向和每个方向的进展
3. 关键技术进展：分析最新的技术突破和创新点
4. 未来研究展望：预测该领域未来的研究方向和可能的发展趋势

请以Markdown格式输出报告。"""
        
        return self.generate_text(prompt, max_tokens=4000)


# 创建全局实例，方便其他模块直接导入使用
deepseek_client = DeepSeekAPI()