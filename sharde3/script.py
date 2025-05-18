# Imports used in this script
import os
import sys
import time
import smtplib
import logging
import pandas as pd
import schedule
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

sys.stdout.reconfigure(encoding='utf-8')

# Helper function to initialize the WebDriver
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run without UI
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Automatically install and use the correct ChromeDriver version
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    return driver

# Helper function for scraping data
def scrape_books(driver, url):
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'a-offscreen')))
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Extract book titles
        titles = [elem.get_text(strip=True) for elem in soup.find_all('span', class_='a-size-medium')]

        # Extract prices
        prices = [elem.get_text(strip=True) for elem in soup.find_all('span', class_='a-offscreen')]

        books = []
        for i in range(min(len(titles), len(prices) - 1)):  # Ensure proper matching
            title = titles[i]
            discount_price = prices[i]
            original_price = prices[i + 1]

            books.append((title, discount_price, original_price))
            print(f"Título: {title}\nPreço com Desconto: {discount_price}\nPreço Original: {original_price}\n")

        return books
    except Exception as e:
        logging.error(f"Erro durante a extração: {e}")
        return []
    finally:
        driver.quit()


# Helper function to save CSV
def save_to_csv(books, folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    current_date = datetime.now().strftime("%d-%m-%Y")
    file_name = f"Livros em Oferta: {current_date}.csv"
    file_path = os.path.join(folder_path, file_name)

    df = pd.DataFrame(books, columns=['Título', 'Preço com Desconto', 'Preço Original'])
    df.to_csv(file_path, index=False, encoding='utf-8')
    logging.info(f"CSV saved at {file_path}")
    return file_path

# Helper function to send an email
def send_email(file_path, sender_email, receiver_email, password):
    subject = "Relatório Diário de Livros da Amazon"
    body = f"Veja o arquivo em anexo: {file_path}"
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)
        logging.info("Email sent successfully.")
    except smtplib.SMTPException as e:
        logging.error(f"Error sending email: {e}")

# Main function to run the scraping and email task
def scrape_and_send_email():
    url = "https://www.amazon.com.br/Livros/"
    print("hi")
    driver = setup_driver()
    books = scrape_books(driver, url)

    if books:
        folder_path = "C:/Users/Usuario/OneDrive/Web Development/Projects/Amazon_WebScrapper/tabelas"
        file_path = save_to_csv(books, folder_path)

        # Read sensitive info securely
        try:
            with open('info.txt', 'r') as info:
                sender_email = info.readline().strip()
                receiver_email = info.readline().strip()
                password = info.readline().strip()
            send_email(file_path, sender_email, receiver_email, password)
        except FileNotFoundError:
            logging.error("info.txt not found.")
        except Exception as e:
            logging.error(f"Error reading credentials: {e}")

def main():
    schedule.every().day.at("00:56").do(scrape_and_send_email)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
