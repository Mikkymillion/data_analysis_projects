

import time
import csv 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re

# ======================================================================
# --- Configuration: FILL THESE IN  ---
# ======================================================================

FACEBOOK_CREDENTIAL = "ph.No or email"
FACEBOOK_PASSWORD = "password"
SEARCH_KEYWORD = "search query"

# Use max post to increase to the number you would like
MAX_POSTS_TO_COLLECT = 70

# Use your actual Chrome profile path or leave as is for manual login
CHROME_USER_DATA_PATH = "--- PATH_TO_CHROME_USER_DATA ---"

# ======================================================================
# --- FacebookScraper Class (Internal logic for extraction is improved) ---
# ======================================================================

class FacebookScraper:
    def __init__(self, credential, password, keyword, max_posts, profile_path):
        self.credential = credential
        self.password = password
        self.keyword = keyword
        self.max_posts = max_posts
        self.profile_path = profile_path
        self.scraped_posts = []
        self.seen_post_ids = set()
        self.driver = self._initialize_driver()
        
    def _initialize_driver(self):
        """Initializes the Selenium WebDriver with proper options."""
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        if self.profile_path and self.profile_path != "--- PATH_TO_CHROME_USER_DATA ---":
            options.add_argument(f"user-data-dir={self.profile_path}")
            options.add_argument("profile-directory=Default")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=options
        )
        
        # Execute CDP commands to prevent detection
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("Driver initialized successfully.")
        return driver
    
    def login_if_needed(self):
        """Attempts to load Facebook and performs manual login if needed."""
        print("Attempting to load Facebook to check login status...")
        self.driver.get("https://www.facebook.com/")
        wait = WebDriverWait(self.driver, 10)
        time.sleep(3)
        
        # Try multiple selectors to check if logged in
        logged_in_selectors = [
            (By.XPATH, "//input[@aria-label='Search Facebook']"),
            (By.XPATH, "//div[contains(@aria-label, 'Create a post')]"),
            (By.XPATH, "//span[text()='Home']"),
            (By.XPATH, "//a[@aria-label='Facebook']")
        ]
        
        for selector in logged_in_selectors:
            try:
                wait.until(EC.presence_of_element_located(selector))
                print(f"Already logged in (found {selector[1]}).")
                return True
            except:
                continue
        
        # If not logged in, check for login page
        try:
            email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            print("Login fields found. Performing manual login...")
            return self._perform_login()
        except:
            print("Could not determine login status.")
            return False
    
    def _perform_login(self):
        """Performs a manual login from the login page."""
        wait = WebDriverWait(self.driver, 15)
        
        try:
            # Enter credentials
            email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email_input.send_keys(self.credential)
            
            pass_input = self.driver.find_element(By.NAME, "pass")
            pass_input.send_keys(self.password)
            
            # Click login
            login_button = self.driver.find_element(By.NAME, "login")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Verify login by checking for search bar
            wait.until(EC.presence_of_element_located(
                (By.XPATH, "//input[@aria-label='Search Facebook']")
            ))
            print("Manual login successful.")
            return True
            
        except Exception as e:
            print(f"Manual login failed: {e}")
            return False
    
    def _search_via_input(self):
        """Searches for the keyword using Facebook's search bar."""
        print(f"Searching for keyword: '{self.keyword}'...")
        wait = WebDriverWait(self.driver, 15)
        
        try:
            # Find and use search input
            search_input = wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Search Facebook']"))
            )
            search_input.click()
            time.sleep(1)
            search_input.clear()
            search_input.send_keys(self.keyword)
            time.sleep(2)
            search_input.send_keys(Keys.ENTER)
            
            # Wait for search results
            wait.until(EC.url_contains("/search"))
            print("Search results page loaded.")
            
            # Wait longer for search to fully load
            time.sleep(5)
            
            # Try to switch to Posts tab
            self._switch_to_posts_tab()
            
        except Exception as e:
            print(f"Search failed: {e}")
            raise
    
    def _switch_to_posts_tab(self):
        """Attempts to switch to the Posts tab in search results."""
        print("Looking for 'Posts' tab...")
        wait = WebDriverWait(self.driver, 10)
        
        # Multiple selectors for Posts tab
        posts_tab_selectors = [
            "//span[contains(text(), 'Posts')]/ancestor::a",
            "//span[contains(text(), 'Posts')]/ancestor::div[@role='tab']",
            "//a[contains(@href, 'posts') and contains(@aria-selected, 'false')]",
            "//div[@role='tablist']//span[contains(text(), 'Posts')]"
        ]
        
        for selector in posts_tab_selectors:
            try:
                posts_tab = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                posts_tab.click()
                print("Clicked 'Posts' tab.")
                time.sleep(5)
                return True
            except:
                continue
        
        print("Could not find 'Posts' tab. Proceeding with current view.")
        return False
    
    def _click_see_more(self):
        """
        Clicks 'See More' buttons to expand truncated text using the most 
        robust selector based on role and text content.
        """
        print("Clicking 'See More' buttons...")
        
        # The MOST RELIABLE XPATH: Targets any element with role='button' 
        SEE_MORE_XPATH = "//div[@role='button']//span[contains(text(), 'See more') or contains(text(), 'See More')] | //div[@role='button'][contains(text(), 'See more') or contains(text(), 'See More')]"

        try:
            # Find all potential 'See More' buttons in the visible view
            see_more_buttons = self.driver.find_elements(By.XPATH, SEE_MORE_XPATH)

            print(f"Found {len(see_more_buttons)} 'See More' buttons.")
            
            clicked_count = 0
            for button in see_more_buttons:
                try:
                    # Use JavaScript to click, as it is less likely to be blocked
                    self.driver.execute_script("arguments[0].click();", button)
                    clicked_count += 1
                    time.sleep(0.1) 
                except:
                    continue

            print(f"Successfully clicked {clicked_count} 'See More' links.")
            time.sleep(3) 
            
        except Exception as e:
            print(f"Error during 'See More' click process: {e}")
    
    def _extract_posts_with_multiple_strategies(self):
        """Extracts posts using multiple strategies for maximum coverage."""
        print("Extracting posts with multiple strategies...")
        new_posts = []
        
        # Strategy 1: Look for common post containers
        post_selectors = [
            "//div[@role='article']",
            "//div[contains(@class, 'x1yztbdb')]",
            "//div[contains(@data-ad-preview, 'message')]",
            "//div[@data-pagelet='FeedUnit']",
            "//div[starts-with(@id, 'mount_0_0_')]//div[@role='feed']/div",
        ]
        
        for selector in post_selectors:
            try:
                posts = self.driver.find_elements(By.XPATH, selector)
                print(f"Found {len(posts)} posts with selector: {selector}")
                
                if len(posts) > 0:
                    for post in posts:
                        try:
                            # Extract text using multiple methods
                            post_data = self._extract_post_data(post)
                            if post_data and len(post_data['text']) > 50:
                                post_id = hash(post_data['text'])
                                if post_id not in self.seen_post_ids:
                                    self.seen_post_ids.add(post_id)
                                    new_posts.append(post_data)
                                    print(f"✅ Extracted post {len(new_posts)}: {post_data['text'][:100]}...")
                        except Exception as e:
                            continue
                    
                    if new_posts:
                        break # Stop on the first successful selector to avoid re-parsing
            except:
                continue
        
        # Strategy 2: Fallback to JavaScript extraction
        if not new_posts:
            print("Trying JavaScript extraction...")
            try:
                js_script = """
                var posts = [];
                var elements = document.querySelectorAll("div[role='article'], div[data-pagelet], div[class*='x1yztbdb']");
                
                elements.forEach(function(el) {
                    var text = el.innerText || el.textContent;
                    if (text && text.length > 100 && !text.includes('Sponsored')) {
                        // Attempt to find the specific text container for better isolation
                        var textContainer = el.querySelector("div[style*='text-align:'] > span, div[data-ad-preview='message'], div[dir='auto']:not([role]), div.x1yztbdb");
                        var postText = textContainer ? textContainer.innerText : el.innerText;

                        var cleanText = postText.replace(/\\s+/g, ' ').trim();
                        if (cleanText.length > 50) {
                            posts.push({
                                text: cleanText,
                                html: el.innerHTML.substring(0, 500)
                            });
                        }
                    }
                });
                return posts;
                """
                
                posts_data = self.driver.execute_script(js_script)
                for post_data in posts_data:
                    if 'text' in post_data and len(post_data['text']) > 50:
                        post_id = hash(post_data['text'])
                        if post_id not in self.seen_post_ids:
                            self.seen_post_ids.add(post_id)
                            new_posts.append({
                                'text': post_data['text'],
                                'keyword': self.keyword,
                                'scraped_time': time.strftime("%Y-%m-%d %H:%M:%S")
                            })
            except Exception as e:
                print(f"JavaScript extraction failed: {e}")
        
        return new_posts
    
    def _extract_post_data(self, post_element):
        """
        REVISED: Extracts data from a single post element using BeautifulSoup and Selenium.
        """
        try:
            # 1. Get the raw HTML of the post container
            html_content = post_element.get_attribute("innerHTML")
            
            # 2. Use BeautifulSoup to target common text elements within the post
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Common selectors for the primary post message body
            text_selectors = [
                "div[dir='auto'] > span", 
                "div[data-ad-preview='message']",
                "div[style*='-webkit-box-orient']", 
                "div.x1yztbdb",
                "span.x193iq5w" 
            ]
            
            post_body = None
            
            for selector in text_selectors:
                match = soup.select_one(selector)
                if match and len(match.text.strip()) > 50: 
                    post_body = match
                    break
            
            if post_body:
                raw_text = post_body.text
            else:
                 # Fallback: Use Selenium's innerText on the whole element 
                 raw_text = post_element.text 

            # 3. Clean up the text
            text = raw_text.strip()
            
            # Remove line breaks and normalize spaces
            text = re.sub(r'(\r?\n|\r)+', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Remove common non-content elements
            patterns_to_remove = [
                r'Like Comment Share',
                r'[0-9]+ (comments?|shares?|likes?|views?)\s*',
                r'See more|See More|View more|View More|Read more|Read More',
                r'Sponsored',
                r'Follow|Following|Liked',
                r'\d{1,2}h|\d{1,2}m|\d{1,2}d', # timestamps (e.g., 2h, 10m)
                r'\.\.\.',
                r'Send message|Write a comment'
            ]
            
            for pattern in patterns_to_remove:
                text = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
            
            # Final cleanup
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Check if text is meaningful and contains keyword
            if len(text) > 50 and self.keyword.lower() in text.lower() and "Sponsored" not in text:
                return {
                    'text': text,
                    'keyword': self.keyword,
                    'scraped_time': time.strftime("%Y-%m-%d %H:%M:%S"),
                }
        except Exception as e:
             pass
        
        return None
    
    def _scroll_page(self):
        """Scrolls the page to load more content."""
        print("Scrolling to load more posts...")
        scroll_pause_time = 3
        
        # Get scroll height
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        # Scroll down
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        
        # Calculate new scroll height
        new_height = self.driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            return False  # No more content to load
        
        return True  # More content loaded
    
    def scrape_posts(self):
        """Main scraping function."""
        print("Starting scraping process...")
        
        # Login first
        if not self.login_if_needed():
            print("Login failed. Aborting.")
            return []
        
        # Perform search
        try:
            self._search_via_input()
        except Exception as e:
            print(f"Search failed: {e}")
            return []
        
        # Main scraping loop
        scroll_attempts = 0
        max_scroll_attempts = 20
        
        while len(self.scraped_posts) < self.max_posts and scroll_attempts < max_scroll_attempts:
            print(f"\n--- Iteration {scroll_attempts + 1} ---")
            
            # Click "See More" buttons
            self._click_see_more()
            time.sleep(2)
            
            # Extract posts
            new_posts = self._extract_posts_with_multiple_strategies()
            
            # Add new posts to collection
            for post in new_posts:
                if len(self.scraped_posts) < self.max_posts:
                    self.scraped_posts.append(post)
                    print(f"✅ Total collected: {len(self.scraped_posts)}/{self.max_posts}")
            
            # Break if we have enough posts
            if len(self.scraped_posts) >= self.max_posts:
                break
            
            # Scroll for more content
            if not self._scroll_page():
                print("No more content to load.")
                scroll_attempts += 5  # Force exit soon
            else:
                scroll_attempts += 1
            
            print(f"Scraped {len(self.scraped_posts)} posts so far...")
        
        print(f"\nScraping complete. Collected {len(self.scraped_posts)} posts.")
        return self.scraped_posts
    
    def close(self):
        """Closes the browser."""
        if self.driver:
            self.driver.quit()
            print("Browser closed.")


# ======================================================================
# --- EXECUTION (Modified for CSV output) ---
# ======================================================================

if __name__ == '__main__':
    scraper = FacebookScraper(
        FACEBOOK_CREDENTIAL, 
        FACEBOOK_PASSWORD, 
        SEARCH_KEYWORD, 
        MAX_POSTS_TO_COLLECT,
        CHROME_USER_DATA_PATH
    )

    try:
        # Start scraping
        posts = scraper.scrape_posts()
        
        # Save results to CSV
        if posts:
            filename = f"facebook_posts_{SEARCH_KEYWORD.replace(' ', '_')}_{len(posts)}.csv"
            
            # Define column names based on dictionary keys
            fieldnames = ['scraped_time', 'keyword', 'text']
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                
                # Write header row
                writer.writeheader()
                
                # Write data rows
                writer.writerows(posts)
            
            print(f"\n Successfully saved {len(posts)} posts to {filename}")
            
            # Print sample posts
            print("\n--- Sample Posts ---")
            for i, post in enumerate(posts[:3], 1):
                print(f"\nPost {i} ({len(post['text'])} chars, Keyword: {post['keyword']}):")
                print(post['text'][:200] + "...")
        else:
            print("\n No posts were collected.")
            
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        scraper.close()