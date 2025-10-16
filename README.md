# 论文助手
一个简单自用的论文分析助手工具，帮助自动分析学术论文内容并生成结构化报告。

## 功能介绍
### 1. 单篇论文分析 (analyze)
分析指定的单篇PDF论文，提取关键信息并生成结构化的Markdown报告。

**功能特点：**
- 自动提取PDF论文全文内容
- 调用DeepSeek API进行智能分析
- 生成包含论文摘要、主要贡献、技术要点等的结构化报告
- 保存分析结果为Markdown格式

**使用方法：**
```bash
python main.py analyze --paper_path "/path/to/your/paper.pdf"
```

**注意：** 如果文件路径包含空格，请使用双引号括起来。

### 2. 批量论文分析 (batch_analyze)
批量分析指定文件夹中的所有PDF论文，适用于处理多个论文文件。

**功能特点：**
- 递归扫描指定文件夹中的所有PDF文件
- 逐篇自动分析并生成报告
- 提供分析统计信息（总文件数、成功数、失败数）
- 自动记录分析失败的文件列表

**使用方法：**
```bash
python main.py batch_analyze --folder_path "/path/to/papers/folder" --output_dir "/path/to/output/folder"
```

**参数说明：**
- --folder_path : 包含PDF论文的文件夹路径
- --output_dir : 分析结果保存的目录路径

### 3. 从URL直接分析论文 (analyze_from_url)
直接通过论文URL分析论文内容，无需下载PDF文件，特别适用于无法正常下载的情况。

**功能特点：**
- 直接从URL获取并处理PDF内容
- 无需保存中间PDF文件到本地
- 支持各种学术论文URL（如ArXiv）
- 生成与普通分析相同格式的结构化报告

**使用方法：**
```bash
python main.py analyze_from_url --url "https://arxiv.org/pdf/2510.06557v1" --output_dir "./outputs"
```

**参数说明：**
- --url : 论文的PDF URL链接
- --output_dir : 分析结果保存的目录路径（可选，默认为outputs）

### 4. 从URL下载并分析论文 (analyze_from_url_download)
先从URL下载PDF论文，然后进行分析，既保存论文文件又生成分析报告。

**功能特点：**
- 从URL下载PDF论文到本地
- 下载完成后自动进行论文分析
- 同时保存原始PDF文件和分析报告
- 支持各种学术论文URL（如ArXiv）

**使用方法：**
```bash
python main.py analyze_from_url_download --url "https://arxiv.org/pdf/2510.06557v1" --output_dir "./outputs" --overwrite False
```

**参数说明：**
- --url : 论文的PDF URL链接
- --output_dir : 下载文件和分析结果保存的目录路径（可选，默认为outputs）
- --overwrite : 是否覆盖已存在的文件（可选，默认为False）

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
- 优化论文搜索功能
- 完善报告生成功能

希望这个工具能帮助你更高效地阅读和分析学术论文！