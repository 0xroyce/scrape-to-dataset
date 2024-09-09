# AI-Powered Web Scraping Bot

This project implements an advanced web scraping bot that uses artificial intelligence to gather, process, and categorize information from the internet. It's designed to create datasets for AI training, research, or any application requiring structured web data.

## Features

- **Intelligent Web Scraping**: Utilizes Selenium for dynamic web page scraping.
- **AI-Powered Content Analysis**: Leverages OpenAI's GPT or Anthropic's Claude models to generate questions, process content, and categorize data.
- **Flexible Data Storage**: Supports both JSON and CSV output formats.
- **Customizable Topics**: Allows users to define custom search topics.
- **Polite Scraping**: Implements delays between requests to be respectful to web servers.
- **Interrupt Handling**: Gracefully handles interruptions, saving progress before shutting down.
- **Authentication Logging**: Keeps track of pages requiring login for future reference.

## Prerequisites

- Python 3.10+
- Chrome WebDriver (compatible with your Chrome version)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/0xroyce/scrape-to-dataset.git
   cd scrape-to-dataset
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up your API keys:
   Create a `.env` file in the project root and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

## Usage

Run the script with:

```
python web_scraping_bot.py
```

You will be prompted to enter:
1. Save format (json or csv)
2. API to use (openai or claude)
3. Maximum pages per topic
4. Maximum total pages

The bot will then start scraping based on the predefined topics in the script.

### Customizing Topics

To change the search topics, modify the `topics` list in the `__main__` section of `web_scraping_bot.py`:

```python
topics = ["your", "custom", "topics", "here"]
```

## Output

The script generates three main output files:

1. `dataset.json` or `dataset.csv`: Contains the processed and categorized content.
2. `questions.json`: Stores the AI-generated questions for each URL.
3. `auth_log.json`: Lists URLs that required authentication.

## Configuration

You can customize the AI models used by modifying the following variables in `web_scraping_bot.py`:

```python
OPENAI_MODEL = "gpt-4o-mini"  # or your preferred OpenAI model
CLAUDE_MODEL = "claude-3-5-sonnet-20240620"  # or your preferred Claude model
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This tool is for educational and research purposes only. Always respect websites' terms of service and robots.txt files. The user is responsible for any misuse of this tool.
