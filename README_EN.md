# Paper Assistant
A simple personal paper analysis assistant tool that helps automatically analyze academic paper content and generate structured reports.

## Features
### 1. Single Paper Analysis (analyze)
Analyze a specific PDF paper, extract key information, and generate a structured Markdown report.

**Features:**
- Automatically extract full text content from PDF papers
- Use DeepSeek API for intelligent analysis
- Generate structured reports containing paper summary, main contributions, technical highlights, etc.
- Save analysis results in Markdown format

**Usage:**
```bash
python main.py analyze --paper_path "/path/to/your/paper.pdf"
```

**Note:** If the file path contains spaces, please enclose it in double quotes.

### 2. Batch Paper Analysis (batch_analyze)
Batch analyze all PDF papers in a specified folder, suitable for processing multiple paper files.

**Features:**
- Recursively scan all PDF files in the specified folder
- Automatically analyze and generate reports for each paper
- Provide analysis statistics (total files, successful, failed)
- Automatically record the list of files that failed to analyze

**Usage:**
```bash
python main.py batch_analyze --folder_path "/path/to/papers/folder" --output_dir "/path/to/output/folder"
```

**Parameter Description:**
- --folder_path: Path to the folder containing PDF papers
- --output_dir: Path to the directory where analysis results will be saved

### 3. Direct Analysis from URL (analyze_from_url)
Analyze paper content directly from a URL without downloading the PDF file, especially useful when normal downloads fail.

**Features:**
- Fetch and process PDF content directly from URL
- No need to save intermediate PDF files locally
- Support various academic paper URLs (such as ArXiv)
- Generate structured reports in the same format as normal analysis

**Usage:**
```bash
python main.py analyze_from_url --url "https://arxiv.org/pdf/2510.06557v1" --output_dir "./outputs"
```

**Parameter Description:**
- --url: The PDF URL link of the paper
- --output_dir: Path to the directory where analysis results will be saved (optional, defaults to outputs)

### 4. Download and Analyze from URL (analyze_from_url_download)
Download the PDF paper from URL first, then analyze it, saving both the paper file and the analysis report.

**Features:**
- Download PDF papers from URL to local storage
- Automatically analyze papers after download
- Save both the original PDF file and analysis report
- Support various academic paper URLs (such as ArXiv)

**Usage:**
```bash
python main.py analyze_from_url_download --url "https://arxiv.org/pdf/2510.06557v1" --output_dir "./outputs" --overwrite False
```

**Parameter Description:**
- --url: The PDF URL link of the paper
- --output_dir: Path to the directory where downloaded files and analysis results will be saved (optional, defaults to outputs)
- --overwrite: Whether to overwrite existing files (optional, defaults to False)

### 5. Paper Download (download)
Download specified academic papers to local storage, supporting downloads via URL or arXiv ID.

**Features:**
- Support downloading papers via URL
- Support downloading papers via arXiv ID
- Optionally automatically rename downloaded files using paper titles
- Support custom download directories

**Usage:**
```bash
# Download via URL
python main.py download --url "https://arxiv.org/pdf/2510.06557v1"

# Download via arXiv ID
python main.py download --arxiv_id "2510.06557"

# Disable title renaming
python main.py download --url "https://arxiv.org/pdf/2510.06557v1" --no_title_rename

# Specify download directory
python main.py download --url "https://arxiv.org/pdf/2510.06557v1" --output_dir "./my_papers"
```

**Parameter Description:**
- --url: URL link to the paper (either --url or --arxiv_id is required)
- --arxiv_id: arXiv paper ID (either --url or --arxiv_id is required)
- --output_dir: Path to the download directory (optional, defaults to downloads)
- --no_title_rename: Disable automatic renaming of downloaded files using paper titles

### 6. Notion Import (notion_import)
Import paper analysis reports to a specified Notion page for easy organization and reference of paper analysis results.

**Features:**
- Read local Markdown format paper analysis reports
- Convert report content to Notion format and add to the specified page
- Automatically parse structured content such as paper title, abstract, research background, etc.
- Support proxy configuration to solve connection issues

**Usage:**
```bash
# Basic usage
python main.py notion_import --report_path "/path/to/report.md"

# Disable proxy
python main.py notion_import --report_path "/path/to/report.md" --no_proxy
```

**Parameter Description:**
- --report_path: Path to the paper analysis report in Markdown format (required)
- --api_key: Notion API key (optional, defaults to value from environment variables)
- --database_id: Notion database ID (optional, defaults to value from environment variables)
- --no_proxy: Disable proxy (to resolve proxy connection issues)
- --as_page: Create a standalone page instead of a database entry

## Environment Requirements
- Python 3.7+
- Install dependencies: `pip install -r requirements.txt`
- DeepSeek API key (needs to be configured in the .env file)
- Notion API key (for using Notion import functionality)

## Notes
- Ensure the DeepSeek API key is correctly configured
- Use quotes when handling file paths containing spaces
- The batch analysis feature will create a separate output directory for each paper
- Analysis results are saved in the outputs directory by default
- When using the Notion import functionality, ensure the API key is valid and has been correctly shared with relevant pages

## Future Plans
- Optimize paper search functionality
- Improve report generation functionality

Hope this tool helps you read and analyze academic papers more efficiently!