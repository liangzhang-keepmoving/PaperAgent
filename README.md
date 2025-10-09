# 论文助手
一个简单自用的论文分析助手工具，帮助自动分析学术论文内容并生成结构化报告。

## 功能介绍
### 1. 单篇论文分析 (analyze)
分析指定的单篇PDF论文，提取关键信息并生成结构化的Markdown报告。
 功能特点
- 自动提取PDF论文全文内容
- 调用DeepSeek API进行智能分析
- 生成包含论文摘要、主要贡献、技术要点等的结构化报告
- 保存分析结果为Markdown格式 使用方法
```
python main.py analyze --paper_path 
"/path/to/your/paper.pdf"
```
注意： 如果文件路径包含空格，请使用双引号括起来。

### 2. 批量论文分析 (batch_analyze)
批量分析指定文件夹中的所有PDF论文，适用于处理多个论文文件。
 功能特点
- 递归扫描指定文件夹中的所有PDF文件
- 逐篇自动分析并生成报告
- 提供分析统计信息（总文件数、成功数、失败数）
- 自动记录分析失败的文件列表 使用方法
```
python main.py batch_analyze --
folder_path "/path/to/papers/folder" --
output_dir "/path/to/output/folder"
```
参数说明：

- --folder_path : 包含PDF论文的文件夹路径
- --output_dir : 分析结果保存的目录路径

## 环境要求
- Python 3.7+
- 安装依赖： pip install -r requirements.txt
- DeepSeek API密钥（需配置在.env文件中）
## 注意事项
- 确保已正确配置DeepSeek API密钥
- 处理包含空格的文件路径时请使用引号
- 批量分析功能会为每个论文创建单独的输出目录
- 分析结果默认保存在outputs目录下

## 未来计划
- 增加论文搜索功能
- 实现论文下载功能
- 添加报告生成功能
希望这个工具能帮助你更高效地阅读和分析学术论文