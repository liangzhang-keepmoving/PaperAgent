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