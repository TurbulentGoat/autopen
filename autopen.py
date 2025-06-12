import time
import random
import csv
import os
from faker import Faker
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth

# --- PHONE NUMBER GENERATOR ---
def generate_random_us_phone_number():
    area_code = random.randint(200, 999)
    exchange_code = random.randint(200, 999)
    line_number = random.randint(0, 9999)
    return "{:03d}-{:03d}-{:04d}".format(area_code, exchange_code, line_number)

# --- INITIALISE FAKER ---
fake = Faker('en_US')
FORM_URL = "https://events.america250.org/events/250th-anniversary-of-the-us-army-grand-military-parade-and-celebration"

# --- SAVE DATA TO CSV ---
def save_to_csv(data_list, filename="successful_submission_records.csv"):
    """
    Appends a list of dictionaries to a CSV file.
    If the file doesn't exist, it's created with a header row.
    """
    if not data_list:
        print("No new data was recorded, so the CSV was not updated.")
        return

    # 1. Check if the file already exists to determine if we need a header
    file_exists = os.path.exists(filename)

    # Get the headers from the keys of the first dictionary
    headers = data_list[0].keys()

    # 2. Open the file in 'a' (append) mode
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)

        # 3. Write the header only if the file is new (did not exist before)
        if not file_exists:
            writer.writeheader()

        # Write all the new data rows
        writer.writerows(data_list)

    print(f"\nSuccessfully appended {len(data_list)} new records to {filename}")

def fill_out_form(driver):
    """
    Fills out the form, clicks through, and if successful,
    returns a dictionary containing the data that was used.
    """
    print("Filling out the form...")
    try:
        # --- 1. Capture data in a dictionary ---
        form_data = {}

        # --- Form Filling (and data capture) ---
        form_data['first_name'] = fake.first_name()
        driver.find_element(By.NAME, "first_name").send_keys(form_data['first_name'])

        form_data['last_name'] = fake.last_name()
        driver.find_element(By.NAME, "last_name").send_keys(form_data['last_name'])

        form_data['email'] = fake.email()
        driver.find_element(By.NAME, "email").send_keys(form_data['email'])

        mobile_input = driver.find_element(By.NAME, "phone")
        while True:
            phone_with_dashes = generate_random_us_phone_number()
            area_code_str = phone_with_dashes.split('-')[0]
            if not area_code_str.endswith('11'):
                break
        ten_digit_number = phone_with_dashes.replace('-', '')
        final_phone_number = f"+1{ten_digit_number}"
        form_data['phone'] = final_phone_number # Capture the phone number
        print(f"Generated phone number: {form_data['phone']}")
        mobile_input.send_keys(form_data['phone'])

        form_data['zip_code'] = fake.zipcode()
        driver.find_element(By.NAME, "zip").send_keys(form_data['zip_code'])

        form_data['state'] = fake.state_abbr()
        Select(driver.find_element(By.NAME, "state")).select_by_value(form_data['state'])
        
        form_data['tickets'] = "1"
        Select(driver.find_element(By.NAME, "ticket")).select_by_value(form_data['tickets'])

# --- RECAPTCHA CHECKBOX TICK ---
        print("Locating the reCAPTCHA checkbox...")
        try:
            recaptcha_checkbox = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "recaptcha-anchor"))
            )
            print("Executing JavaScript to set aria-checked='true'...")
            driver.execute_script("arguments[0].setAttribute('aria-checked', 'true')", recaptcha_checkbox)
            print("Attribute successfully changed.")
            time.sleep(1)
        except Exception as e:
            print(f"Could not find or modify the reCAPTCHA element: {e}")

# --- CLICKING 'Continue' ---
        print("Clicking 'Continue'...")
        continue_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[data-test='ticket-selection-continue']"))
        )
        continue_button.click()

# --- CLICKING 'Save' PG.2---
        print("Waiting for the second page and clicking 'Save'...")
        save_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='Save']"))
        )
        save_button.click()

        print("Form submission fully attempted!")
        time.sleep(4)

# --- 2. RETURN THE CAPTURED DATA ON SUCCESS ---
        # This line is only reached if all the steps above succeed
        return form_data

    except Exception as e:
        print(f"An error occurred during the submission process: {e}")
        print("NOTE: This failure is expected if the reCAPTCHA was not solved correctly by a human.")
# --- RETURN NOTHING ON FAILURE ---
        return None


def main():
    """
    Main function to run the submission loop. It now collects data from
    successful submissions and saves it to a CSV at the end.
    """
    while True:
        try:
            num_submissions = int(input("How many times do you want to fill out the form? "))
            if num_submissions > 0:
                break
            else:
                print("Please enter a number greater than 0.")
        except ValueError:
            print("Invalid input. Please enter a whole number.")
            
# --- LIST TO HOLD ALL THE RECORDED DATA ---
    all_submissions_data = []

    for i in range(num_submissions):
        print(f"\n--- Starting submission {i + 1} of {num_submissions} in a NEW browser session ---")

        driver = None
        try:
            print("Setting up the stealth browser...")
            chrome_options = Options()
            chrome_options.add_argument("start-maximized")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

            stealth(driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                    )

            driver.get(FORM_URL)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "first_name")))
            
# --- CATCH THE RETURNED DATA ---
            submitted_data = fill_out_form(driver)
            
# --- IF DATA WAS RETURNED (i.e., submission was successful), ADD IT TO THE LIST ---
            if submitted_data:
                all_submissions_data.append(submitted_data)
                print(f"Data for submission {i + 1} recorded successfully.")
            else:
                print(f"Submission {i + 1} failed or was incomplete. No data recorded for this attempt.")


        except Exception as e:
            print(f"A critical error occurred during submission {i + 1}. Error: {e}")
        finally:
            if driver:
                print("Closing browser session...")
                driver.quit()

    print("\nAll submission attempts completed.")
    
# --- AFTER THE LOOP, SAVE ALL COLLECTED DATA TO THE CSV FILE ---
    save_to_csv(all_submissions_data)


if __name__ == "__main__":
    main()
