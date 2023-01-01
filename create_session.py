import pickle
import time
import json
from selenium import webdriver
import requests
import concurrent.futures


def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.zomato.com/")
    time.sleep(1)
    return driver


def login(driver, phone_num):
    driver.find_element_by_css_selector("ul[role='menu'] li:nth-last-child(2)").click()
    time.sleep(5)
    driver.switch_to.frame("auth-login-ui")
    driver.find_element_by_css_selector("input[type='number']").send_keys(
        f"{phone_num}"
    )
    send_otp = driver.find_elements_by_css_selector("button")[0]
    send_otp.click()
    time.sleep(1)
    if driver.find_element_by_tag_name("p").text == "OTP sent successfully.":
        print("OTP sent successfully.")
        return driver

    else:
        print("OTP not sent.")
        driver.quit()
        return None


def fill_otp_submit(driver, otp):
    driver.find_element_by_css_selector("input[type='text']").send_keys(f"{otp}")
    # TODO : Check if otp auth was successful or not
    time.sleep(5)
    for element in driver.find_elements_by_tag_name("p"):
        if element.text == "The OTP entered is invalid/incorrect. Please try again.":
            print("The OTP entered is invalid/incorrect. Please try again.")
            return (False, driver)
        else:
            continue
    driver.find_elements_by_css_selector("button")[0].click()
    time.sleep(5)
    return (True, driver)


def get_otp():
    return input("Enter OTP: ")


def get_page_json(page, req_session):
    time.sleep(0.5)
    print(f"Page {page} started")
    r = req_session.get(
        "https://www.zomato.com/webroutes/user/orders?page={}".format(page)
    )
    print(f"Page {page} done")
    return r.json()


def get_order_json(phone_number):
    with open(f"sessions/{phone_number}_session.pkl", "rb") as f:
        req_session = pickle.load(f)
    orders = req_session.get("https://www.zomato.com/webroutes/user/orders")
    page_count = orders.json()["sections"]["SECTION_USER_ORDER_HISTORY"]["totalPages"]
    all_pages = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for page in range(1, page_count + 1):
            all_pages.append(executor.submit(get_page_json, page, req_session))
    all_pages = [page.result() for page in all_pages]

    # for page in range(1, page_count + 1):
    #     r = req_session.get(
    #         "https://www.zomato.com/webroutes/user/orders?page={}".format(page)
    #     )
    #     all_pages.append(r.json())
    #     print(f"Page {page} done")
    #     print(f"Length of curr_page: {len(r.json())}")
    #     time.sleep(0.3)

    with open(f"order_data/{phone_number}_orders.json", "w") as f:
        json.dump(all_pages, f)
    return all_pages


def create_req_session(driver):
    cookies = driver.get_cookies()
    req_session = requests.Session()
    for cookie in cookies:
        req_session.cookies.set(cookie["name"], cookie["value"])
    user_agent = driver.execute_script("return navigator.userAgent;")
    req_session.headers.update({"User-Agent": user_agent})
    print("session_req created")
    return req_session


def run(phone_num):
    driver = create_driver()
    driver = login(driver, phone_num)
    otp = get_otp()
    is_valid, driver = fill_otp_submit(driver, otp)
    if not is_valid:
        print("Invalid OTP, Try again.")
        otp = get_otp()
        is_valid, driver = fill_otp_submit(driver, otp)
        if not is_valid:
            print("Invalid OTP, Try again.")
            driver.quit()
            print("Exiting...")
            return None
        else:
            print("OTP valid.")
    else:
        print("OTP valid.")
    req_session = create_req_session(driver)
    # create pickle
    with open(f"sessions/{phone_num}_session.pkl", "wb") as f:
        pickle.dump(req_session, f)

    orders = req_session.get("https://www.zomato.com/webroutes/user/orders")
    print(orders.json())
    time.sleep(5)
    driver.quit()


if __name__ == "__main__":
    phone_number = input("Enter phone number: ")
    run(phone_number)
