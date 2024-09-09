import os
import json
import csv
import time
import signal
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openai import OpenAI
import anthropic

# Load environment variables
load_dotenv()

# Configure API clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Set the model names
OPENAI_MODEL = "gpt-4o-mini"  # DEFINE OAI MODEL HERE
CLAUDE_MODEL = "claude-3-5-sonnet-20240620"  # DEFINE CLAUDE MODEL HERE


class WebScrapingBot:
    def __init__(self, save_format='json', api='openai'):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.dataset = []
        self.questions = []
        self.auth_log = []
        self.running = True
        self.save_format = save_format.lower()
        self.api = api.lower()
        if self.save_format not in ['json', 'csv']:
            raise ValueError("Save format must be either 'json' or 'csv'")
        if self.api not in ['openai', 'claude']:
            raise ValueError("API must be either 'openai' or 'claude'")

    def search_internet(self, query, num_results=10):
        url = f"https://www.google.com/search?q={query}&num={num_results}"
        self.driver.get(url)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        search_results = soup.find_all('div', class_='yuRUbf')
        return [result.find('a')['href'] for result in search_results]

    def scrape_page(self, url):
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            content = self.driver.find_element(By.TAG_NAME, "body").text
            return content
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            if "login" in self.driver.current_url.lower():
                self.auth_log.append(url)
            return None

    def generate_questions(self, content):
        try:
            if self.api == 'openai':
                response = openai_client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system",
                         "content": "You are an expert at analyzing text and generating insightful questions. Aim for diversity in question types and depth of analysis."},
                        {"role": "user", "content": f"""Based on the following content, generate 4-5 key questions that would be useful for understanding and summarizing the main points. 

Content: {content[:2000]}...

Your questions should:
1. Cover different aspects of the content
2. Include a mix of factual, analytical, and interpretive questions
3. Encourage deep thinking about the subject matter
4. Be clearly worded and specific

Format your response as a numbered list of questions."""}
                    ]
                )
                questions = response.choices[0].message.content.split('\n')
            elif self.api == 'claude':
                response = anthropic_client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=300,
                    system="You are an expert at analyzing text and generating insightful questions. Aim for diversity in question types and depth of analysis.",
                    messages=[
                        {
                            "role": "user",
                            "content": f"""Based on the following content, generate 4-5 key questions that would be useful for understanding and summarizing the main points. 

Content: {content[:2000]}...

Your questions should:
1. Cover different aspects of the content
2. Include a mix of factual, analytical, and interpretive questions
3. Encourage deep thinking about the subject matter
4. Be clearly worded and specific

Format your response as a numbered list of questions."""
                        }
                    ]
                )
                questions = response.content[0].text.split('\n')
            return [q.strip() for q in questions if
                    q.strip() and not q.strip().startswith('Human:') and not q.strip().startswith('Assistant:')]
        except Exception as e:
            print(f"Error generating questions: {str(e)}")
            return []

    def process_content(self, content, question):
        try:
            if self.api == 'openai':
                response = openai_client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system",
                         "content": "You are an AI expert with comprehensive knowledge of artificial intelligence. Provide direct, concise answers as if you're explaining from your own knowledge, without referencing any specific source."},
                        {"role": "user", "content": f"""Based on your knowledge of artificial intelligence, answer the following question:

Question: {question}

Your response should be structured as follows:
Instruction: Briefly state what needs to be addressed to answer the question.
Context: Provide a short, relevant background to frame the answer.
Response: Give a detailed, direct answer to the question. Speak confidently as if from your own knowledge, without referencing any specific sources or articles."""}
                    ]
                )
                structured_content = response.choices[0].message.content
            elif self.api == 'claude':
                response = anthropic_client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=1000,
                    system="You are an AI expert with comprehensive knowledge of artificial intelligence. Provide direct, concise answers as if you're explaining from your own knowledge, without referencing any specific source.",
                    messages=[
                        {
                            "role": "user",
                            "content": f"""Based on your knowledge of artificial intelligence, answer the following question:

Question: {question}

Your response should be structured as follows:
Instruction: Briefly state what needs to be addressed to answer the question.
Context: Provide a short, relevant background to frame the answer.
Response: Give a detailed, direct answer to the question. Speak confidently as if from your own knowledge, without referencing any specific sources or articles."""
                        }
                    ]
                )
                structured_content = response.content[0].text

            # Parse the structured content
            sections = structured_content.split('\n\n')
            parsed_content = {}
            current_section = None
            for section in sections:
                if section.startswith('Instruction:'):
                    current_section = 'instruction'
                    parsed_content[current_section] = section.replace('Instruction:', '').strip()
                elif section.startswith('Context:'):
                    current_section = 'context'
                    parsed_content[current_section] = section.replace('Context:', '').strip()
                elif section.startswith('Response:'):
                    current_section = 'response'
                    parsed_content[current_section] = section.replace('Response:', '').strip()
                elif current_section:
                    parsed_content[current_section] += '\n\n' + section.strip()

            return parsed_content
        except Exception as e:
            print(f"Error processing content: {str(e)}")
            return {"instruction": "", "context": "", "response": ""}

    def categorize_data(self, content):
        try:
            if self.api == 'openai':
                response = openai_client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are an expert at categorizing content."},
                        {"role": "user",
                         "content": f"Provide a detailed category, subcategory, and topic for the following content. Format your response as 'Category: X\nSubcategory: Y\nTopic: Z'. Content: {content[:2000]}..."}
                    ]
                )
                categories = response.choices[0].message.content.split('\n')
            elif self.api == 'claude':
                response = anthropic_client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=100,
                    system="You are an expert at categorizing content.",
                    messages=[
                        {
                            "role": "user",
                            "content": f"Provide a detailed category, subcategory, and topic for the following content. Format your response as 'Category: X\nSubcategory: Y\nTopic: Z'. Content: {content[:2000]}..."
                        }
                    ]
                )
                categories = response.content[0].text.split('\n')
            result = {}
            for category in categories:
                if ':' in category:
                    key, value = category.split(':', 1)
                    result[key.strip().lower()] = value.strip()

            return {
                "category": result.get('category', 'Unknown'),
                "subcategory": result.get('subcategory', 'Unknown'),
                "topic": result.get('topic', 'Unknown')
            }
        except Exception as e:
            print(f"Error categorizing data: {str(e)}")
            return {
                "category": "Unknown",
                "subcategory": "Unknown",
                "topic": "Unknown"
            }

    def save_dataset(self):
        if self.save_format == 'json':
            with open('dataset.json', 'w', encoding='utf-8') as f:
                json.dump(self.dataset, f, ensure_ascii=False, indent=2)
        elif self.save_format == 'csv':
            with open('dataset.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['url', 'instruction', 'context', 'response', 'category',
                                                       'subcategory', 'topic'], delimiter='\t')
                writer.writeheader()
                for item in self.dataset:
                    writer.writerow(item)

    def save_questions(self):
        with open('questions.json', 'w', encoding='utf-8') as f:
            json.dump(self.questions, f, ensure_ascii=False, indent=2)

    def save_auth_log(self):
        with open('auth_log.json', 'w', encoding='utf-8') as f:
            json.dump(self.auth_log, f, ensure_ascii=False, indent=2)

    def signal_handler(self, signum, frame):
        print("Interrupt received, stopping...")
        self.running = False

    def run(self, topics, max_pages_per_topic, max_pages_total):
        signal.signal(signal.SIGINT, self.signal_handler)
        total_pages = 0
        try:
            for topic in topics:
                if not self.running or (max_pages_total and total_pages >= max_pages_total):
                    break
                print(f"Searching for topic: {topic}")
                urls = self.search_internet(topic, num_results=max_pages_per_topic)
                for i, url in enumerate(urls):
                    if not self.running or (max_pages_total and total_pages >= max_pages_total):
                        break
                    print(f"Scraping page {i + 1}/{len(urls)}: {url}")
                    content = self.scrape_page(url)
                    if content:
                        questions = self.generate_questions(content)
                        self.questions.append({"url": url, "questions": questions})
                        categories = self.categorize_data(content)
                        for question in questions:
                            processed_content = self.process_content(content, question)
                            self.dataset.append({
                                "url": url,
                                **processed_content,
                                **categories
                            })
                        total_pages += 1
                        if total_pages % 10 == 0:  # Save every 10 pages
                            self.save_dataset()
                            self.save_questions()
                            self.save_auth_log()
                    time.sleep(1)  # Be polite to servers
                print(f"Completed topic: {topic}. Dataset size: {len(self.dataset)}")
        finally:
            self.save_dataset()
            self.save_questions()
            self.save_auth_log()
            print(f"Script stopped. Total pages scraped: {total_pages}")

    def __del__(self):
        self.driver.quit()


# Usage
if __name__ == "__main__":
    save_format = input("Enter save format (json or csv): ").lower()
    api = input("Enter API to use (openai or claude): ").lower()
    max_pages_per_topic = int(input("Enter maximum pages per topic: "))
    max_pages_total = int(input("Enter maximum total pages: "))
    bot = WebScrapingBot(save_format=save_format, api=api)
    topics = ["artificial intelligence", "machine learning", "natural language processing"] # CHANGE TO YOUR TOPICS
    bot.run(topics, max_pages_per_topic, max_pages_total)