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

## Environment Requirements
- Python 3.7+
- Install dependencies: `pip install -r requirements.txt`
- DeepSeek API key (needs to be configured in the .env file)

## Notes
- Ensure the DeepSeek API key is correctly configured
- Use quotes when handling file paths containing spaces
- The batch analysis feature will create a separate output directory for each paper
- Analysis results are saved in the outputs directory by default

## Future Plans
- Add paper search functionality
- Implement paper download functionality
- Add report generation functionality

Hope this tool helps you read and analyze academic papers more efficiently!