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

### 5. 论文下载功能 (download)
下载指定的学术论文到本地，支持通过URL或arXiv ID下载。

**功能特点：**
- 支持通过URL下载论文
- 支持通过arXiv ID下载论文
- 可选择性使用论文标题自动重命名下载的文件
- 支持自定义下载目录

**使用方法：**
```bash
# 通过URL下载
python main.py download --url "https://arxiv.org/pdf/2510.06557v1"

# 通过arXiv ID下载
python main.py download --arxiv_id "2510.06557"

# 禁用使用标题重命名
python main.py download --url "https://arxiv.org/pdf/2510.06557v1" --no_title_rename

# 指定下载目录
python main.py download --url "https://arxiv.org/pdf/2510.06557v1" --output_dir "./my_papers"
```

**参数说明：**
- --url : 论文的URL链接（与--arxiv_id二选一）
- --arxiv_id : arXiv论文ID（与--url二选一）
- --output_dir : 下载目录路径（可选，默认为downloads）
- --no_title_rename : 禁用使用标题重命名下载的文件

### 6. Notion导入功能 (notion_import)
将论文分析报告导入到指定的Notion页面，方便整理和查阅论文分析结果。

**功能特点：**
- 读取本地Markdown格式的论文分析报告
- 将报告内容转换为Notion格式并添加到指定页面
- 自动解析论文标题、摘要、研究背景等结构化内容
- 支持配置代理设置以解决连接问题

**使用方法：**
```bash
# 基本使用
python main.py notion_import --report_path "/path/to/report.md"

# 禁用代理
python main.py notion_import --report_path "/path/to/report.md" --no_proxy
```

**参数说明：**
- --report_path : 论文分析报告的Markdown文件路径（必需）
- --api_key : Notion API密钥（可选，默认从环境变量获取）
- --database_id : Notion数据库ID（可选，默认从环境变量获取）
- --no_proxy : 禁用代理（解决代理连接问题）
- --as_page : 创建独立页面而不是数据库条目

## 环境要求
- Python 3.7+
- 安装依赖： pip install -r requirements.txt
- DeepSeek API密钥（需配置在.env文件中）
- Notion API密钥（如需使用Notion导入功能）

## 注意事项
- 确保已正确配置DeepSeek API密钥
- 处理包含空格的文件路径时请使用引号
- 批量分析功能会为每个论文创建单独的输出目录
- 分析结果默认保存在outputs目录下
- 使用Notion导入功能时，确保API密钥有效且已正确共享相关页面

## 未来计划
- 优化论文搜索功能
- 完善报告生成功能

希望这个工具能帮助你更高效地阅读和分析学术论文！