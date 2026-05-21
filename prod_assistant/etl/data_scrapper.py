import csv
import time
import re
import os
from bs4 import BeautifulSoup
from pandas import options
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class FlipkartScraper:
    def __init__(self, output_dir="data"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def get_top_reviews(self, product_url, count=2):
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        driver = uc.Chrome(options=options, version_main=145)

        driver.get(product_url)
        time.sleep(4)

        # scroll
        for _ in range(5):
            driver.execute_script("window.scrollBy(0, 1500);")
            time.sleep(1)

        reviews_data = []

        # each review block
        review_items = driver.find_elements(By.XPATH, "//div[contains(@class,'col') and contains(@class,'x_CUu6')]")

        for item in review_items[:count]:

            try:
                rating = item.find_element(By.XPATH, ".//div[contains(@class,'MKiFS6')]").text.strip()
            except:
                rating = ""

            try:
                title = item.find_element(By.XPATH, ".//p[contains(@class,'qW2QI1')]").text.strip()
            except:
                title = ""

            try:
                description = item.find_element(By.XPATH, ".//div[contains(@class,'G4PxIA')]//div[1]").text.strip()
            except:
                description = ""

            try:
                reviewer = item.find_element(By.XPATH, ".//p[contains(@class,'zJ1ZGa')][1]").text.strip()
            except:
                reviewer = ""

            try:
                location = item.find_element(By.XPATH, ".//p[contains(@id,'review-')]").text.strip()
            except:
                location = ""

            try:
                time_ago = item.find_element(By.XPATH, ".//p[contains(@class,'zJ1ZGa')][last()]").text.strip()
            except:
                time_ago = ""

            try:
                likes = item.find_element(By.XPATH, "(.//span[@class='Fp3hrV'])[1]").text.strip()
            except:
                likes = "0"

            try:
                dislikes = item.find_element(By.XPATH, "(.//span[@class='Fp3hrV'])[2]").text.strip()
            except:
                dislikes = "0"

            try:
                permalink = item.find_element(By.XPATH, ".//a[contains(@href,'reviewId')]").get_attribute("href")
            except:
                permalink = ""

            full_review = f"{rating} | {title} | {description} | {reviewer} | {location} | {time_ago} | {likes} | {dislikes} | {permalink}"

            reviews_data.append(full_review)

        driver.quit()

        return " || ".join(reviews_data) if reviews_data else "No reviews found"


    # def get_top_reviews(self,product_url,count=2):
    #     """Get the top reviews for a product.
    #     """
    #     options = uc.ChromeOptions()
    #     options.add_argument("--no-sandbox")
    #     options.add_argument("--disable-blink-features=AutomationControlled")
    #     driver = uc.Chrome(options=options,version_main=137)

    #     if not product_url.startswith("http"):
    #         driver.quit()
    #         return "No reviews found"

    #     try:
    #         driver.get(product_url)
    #         time.sleep(4)
    #         try:
    #             driver.find_element(By.XPATH, "//button[contains(text(), '✕')]").click()
    #             time.sleep(1)
    #         except Exception as e:
    #             print(f"Error occurred while closing popup: {e}")

    #         for _ in range(4):
    #             ActionChains(driver).send_keys(Keys.END).perform()
    #             time.sleep(1.5)

    #         soup = BeautifulSoup(driver.page_source, "html.parser")
    #         review_blocks = soup.select("div._27M-vq, div.col.EPCmJX, div._6K-7Co")
    #         seen = set()
    #         reviews = []

    #         for block in review_blocks:
    #             text = block.get_text(separator=" ", strip=True)
    #             if text and text not in seen:
    #                 reviews.append(text)
    #                 seen.add(text)
    #             if len(reviews) >= count:
    #                 break
    #     except Exception:
    #         reviews = []

    #     driver.quit()
    #     return " || ".join(reviews) if reviews else "No reviews found"
    
    def scrape_flipkart_products(self, query, max_products=1, review_count=2):
        """Scrape Flipkart products based on a search query.
        """
        options = uc.ChromeOptions()
        driver = uc.Chrome(options=options, version_main=145)
        search_url = f"https://www.flipkart.com/search?q={query.replace(' ', '+')}"
        driver.get(search_url)
        time.sleep(4)

        # try:
        #     driver.find_element(By.XPATH, "//button[contains(text(), '✕')]").click()
        # except Exception as e:
        #     print(f"Error occurred while closing popup: {e}")

        try:
            popup_close = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '✕')]"))
                )
            popup_close.click()
        except:
            print("No popup found")

        time.sleep(2)
        products = []

        items = driver.find_elements(By.CSS_SELECTOR, "div[data-id]")[:max_products]
        for item in items:
            try:
                title = item.find_element(By.CSS_SELECTOR, "div.RG5Slk").text.strip()
                price = item.find_element(By.CSS_SELECTOR, "div.hZ3P6w.DeU9vF").text.strip()
                rating = item.find_element(By.CSS_SELECTOR, "div.MKiFS6").text.strip()
                # reviews_text = item.find_element(By.CSS_SELECTOR, ".G4PxIA > div > div").text.strip()
                reviews_text = item.find_element(
    By.XPATH,
    ".//div[normalize-space() and not(descendant::span[contains(text(),'READ')])]"
).text.strip()

                match = re.search(r"\d+(,\d+)?(?=\s+Reviews)", reviews_text)
                total_reviews = match.group(0) if match else "N/A"

                link_el = item.find_element(By.CSS_SELECTOR, "a[href*='/p/']")
                href = link_el.get_attribute("href")
                product_link = href if href.startswith("http") else "https://www.flipkart.com" + href
                match = re.findall(r"/p/(itm[0-9A-Za-z]+)", href)
                product_id = match[0] if match else "N/A"
            except Exception as e:
                print(f"Error occurred while processing item: {e}")
                continue

            top_reviews = self.get_top_reviews(product_link, count=review_count) if "flipkart.com" in product_link else "Invalid product URL"
            products.append([product_id, title, rating, total_reviews, price, top_reviews])

        driver.quit()
        return products
    
    def save_to_csv(self, data, filename="product_reviews.csv"):
        """Save the scraped product reviews to a CSV file."""
        if os.path.isabs(filename):
            path = filename
        elif os.path.dirname(filename):  # filename includes subfolder like 'data/product_reviews.csv'
            path = filename
            os.makedirs(os.path.dirname(path), exist_ok=True)
        else:
            # plain filename like 'output.csv'
            path = os.path.join(self.output_dir, filename)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["product_id", "product_title", "rating", "total_reviews", "price", "top_reviews"])
            writer.writerows(data)
        