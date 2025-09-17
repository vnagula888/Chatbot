import requests
from bs4 import BeautifulSoup
import json
from difflib import get_close_matches
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time


def load_knowledge_base(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return {"questions": []}
    except Exception as e:
        print(f"Error loading knowledge base: {e}")
        return {"questions": []}


def save_knowledge_base(file_path, data):
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=2)
    except Exception as e:
        print(f"Error saving knowledge base: {e}")


def find_best_match(user_question, questions):
    matches = get_close_matches(user_question.lower(), [q["question"].lower() for q in questions], n=1, cutoff=0.7)
    return matches[0] if matches else None


def parse_event_date(event_date_text):
    date_formats = ['%a %m/%d']
    for date_format in date_formats:
        try:
            return datetime.strptime(event_date_text, date_format).date()
        except ValueError:
            continue
    return None


def scrape_ohsaa_schedules(url, input_date):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        events = []
        for event in soup.find_all('div', class_='event-item'):
            print(event)
            date_text = event.find('span', class_='event-date').get_text(strip=True)
            try:
                event_date = datetime.strptime(date_text, '%a %m/%d').replace(year=input_date.year).date()
            except ValueError:
                continue

            if event_date == input_date:
                event_title = event.find('span', class_='link-highlight').get_text(strip=True)
                participants = event.find('span', class_='event-participants').get_text(strip=True)
                event_time = event.find('span', class_='event-time').get_text(strip=True)
                location = event.find('span', class_='event-location-text').get_text(strip=True)

                event_details = {
                    "title": event_title,
                    "participants": participants,
                    "date": event_date,
                    "time": event_time,
                    "location": location
                }
                events.append(event_details)

        return events
    except Exception as e:
        print(f"Error scraping OHSAA schedules: {e}")
        return []


def find_event_by_date(date_str):
    url = 'https://www.aurora-schools.org/view-all-events'
    response = requests.get(url)

    soup = BeautifulSoup(response.content, 'html.parser')
    results = soup.find(class_='fsCalendarEventGrid fsStyleAutoclear')

    if results:
        event_boxes = results.find_all(class_='fsCalendarDaybox fsStateHasEvents')
        events_found = False
        for event_box in event_boxes:
            date_div = event_box.find('div', class_='fsCalendarDate')
            date_data = f"{date_div['data-year']}-{int(date_div['data-month']) + 1:02d}-{int(date_div['data-day']):02d}"
            if date_data == date_str:
                events_found = True
                titles = event_box.find_all('a', class_='fsCalendarEventTitle fsCalendarEventLink')
                times = event_box.find_all('time', class_='fsStartTime')
                locations = event_box.find_all('div', class_='fsLocation')
                for title, time, location in zip(titles, times, locations):
                    print(f"Title: {title.get_text(strip=True)}")
                    print(f"Time: {time.get_text(strip=True)}")
                    print(f"Location: {location.get_text(strip=True)}")
                    print()
        if not events_found:
            print("No events found for the given date.")
    else:
        print("No events found.")


def get_answer_for_question(question, knowledge_base):
    for q in knowledge_base["questions"]:
        if q["question"].lower() == question.lower():
            return q["answer"]
    return None


# Set Pandas options to display the full content
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.expand_frame_repr', False)

# Initialize the webdriver with ChromeDriverManager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# Open the webpage
driver.get('https://go.dragonflyathletics.com/sites/OHSAA/7VPXNG/about?mode=This%20Season')

# Add a wait to ensure the elements are loaded
wait = WebDriverWait(driver, 10)
actions = ActionChains(driver)

# Scroll to the bottom of the page to load all events
last_height = driver.execute_script("return document.body.scrollHeight")

while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  # Wait for new content to load
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# Find the event blocks
try:
    event_blocks = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="card event-grid"]')))
except Exception as e:
    print(f"An error occurred: {e}")
    driver.quit()
    exit()

# Create lists to store the data
teams_list = []
dates_list = []
times_list = []
locations_list = []
sports_list = []

# Extract data from each event block
for event in event_blocks:
    try:
        teams = event.find_elements(By.XPATH, './/div[@class="event-title-container roboto-font"]/h2')
        date = event.find_element(By.XPATH,
                                  './/div[@class="event-sport roboto-font"]/span/span[@style="font-weight: 700; font-size: 20px;"]')
        time = event.find_element(By.XPATH,
                                  './/div[@class="event-sport roboto-font"]/span/span[not(@style="font-weight: 700; font-size: 20px;")]')
        location = event.find_element(By.XPATH, './/div[@class="event-location"]/span[@class="event-location-text"]')
        sport = event.find_element(By.XPATH, './/div[@class="event-sport roboto-font"]/span[@class="link-highlight"]')

        teams_list.append(' vs '.join([team.text for team in teams]))
        dates_list.append(date.text)
        times_list.append(time.text)
        locations_list.append(location.get_attribute("title"))
        sports_list.append(sport.text)
    except Exception as e:
        print(f"Error extracting event details: {e}")

# Ensure all lists have the same length by trimming to the shortest length
min_length = min(len(teams_list), len(dates_list), len(times_list), len(locations_list), len(sports_list))

teams_list = teams_list[:min_length]
dates_list = dates_list[:min_length]
times_list = times_list[:min_length]
locations_list = locations_list[:min_length]
sports_list = sports_list[:min_length]

# Create a DataFrame
data = {
    'Teams': teams_list,
    'Date': dates_list,
    'Time': times_list,
    'Location': locations_list,
    'Sport': sports_list
}
df = pd.DataFrame(data)

# Filter rows containing "Aurora City Schools", using case-insensitive matching
df_aurora = df[df['Teams'].str.contains('Aurora City Schools', case=False, na=False)]

# Close the webdriver
driver.quit()

# Save the DataFrame to a CSV file for better visualization
df_aurora.to_csv('aurora_city_schools_events.csv', index=False)


def chat_bot():
    knowledge_base = load_knowledge_base('General_Information.json')
    print("Hi! This is the Greenmen chatbot! Enter 1-4 for the options:")
    print("1. General Events")
    print("2. Athletics Schedule")
    print("3. Other")
    print("Type 'quit', 'exit', or 'bye' to end the chat.")

    while True:
        user_input = input('You: ')
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Bot: Goodbye!")
            break

        if user_input == '1':
            user_date = input("Enter the date (YYYY-MM-DD): ")
            find_event_by_date(user_date)

        elif user_input == '2':
            # Prompt the user to enter a date
            user_date = input("Enter a date (e.g., 4/11): ")

            # Find events matching the entered date
            matching_events = df_aurora[df_aurora['Date'].str.contains(user_date)]

            # Print the matching events
            if not matching_events.empty:
                print(matching_events.to_string(index=False))
            else:
                print(f"No events found for the date: {user_date}")

        elif user_input == '3':
            while True:
                user_question = input("Please enter your question using 2 words (or type 'back' to return to the main menu): ")
                if user_question.lower() in ['back', 'quit', 'exit', 'bye']:
                    if user_question.lower() in ['quit', 'exit', 'bye']:
                        print("Bot: Goodbye!")
                        return
                    break
                best_match = find_best_match(user_question, knowledge_base["questions"])
                if best_match:
                    answer = get_answer_for_question(best_match, knowledge_base)
                    print(f'Bot: {answer}')
                else:
                    print('Bot: I don\'t know the answer, can you teach me please?')
                    new_answer = input('Type the answer or "skip" to skip: ')
                    if new_answer.lower() != 'skip':
                        knowledge_base["questions"].append({"question": user_question, "answer": new_answer})
                        save_knowledge_base('General_Information.json', knowledge_base)
                        print('Bot: Thank you! I learned a new response!')
        else:
            print("Bot: Invalid option. Please enter a number between 1 and 3.")


# Call the chat_bot function
if __name__ == "__main__":
    chat_bot()
