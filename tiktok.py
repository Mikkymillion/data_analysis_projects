from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import pandas as pd
import json
from datetime import datetime
import random
import re

class TikTokScraper:
    def __init__(self, headless=False):
        """
        Initialize the TikTok scraper
        """
        self.headless = headless
        self.driver = None
        self.wait = None
        self.data = []
        
    def setup_driver(self):
        """Set up Chrome driver with anti-detection options"""
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Anti-detection settings
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Mimic real user
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        # Optional: Use webdriver-manager to automatically handle ChromeDriver
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except:
            # Fallback to system ChromeDriver
            self.driver = webdriver.Chrome(options=chrome_options)
        
        # Hide WebDriver detection
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            '''
        })
        
        self.wait = WebDriverWait(self.driver, 15)
    
    def search_query(self, query):
        """Search for a query on TikTok"""
        try:
            print(f"🔍 Searching for: '{query}'")
            
            # Go to TikTok homepage
            self.driver.get("https://www.tiktok.com")
            time.sleep(random.uniform(1, 3))
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Find search box
            search_box = None
            search_selectors = [
                'input[placeholder="Search accounts and videos"]',
                'input[placeholder*="Search"]',
                '[data-e2e="search-input"]',
                'input[type="search"]',
                'input.search-input',
                '.search-input',
                '#search-box-input'
            ]
            
            for selector in search_selectors:
                try:
                    search_box = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if search_box and search_box.is_displayed():
                        break
                except:
                    continue
            
            if not search_box:
                # Direct URL fallback
                search_url = f"https://www.tiktok.com/search?q={query.replace(' ', '%20')}"
                self.driver.get(search_url)
                print(f"📡 Navigated directly to search URL")
                time.sleep(random.uniform(2, 4))
                return
            
            # Clear and type query
            search_box.clear()
            time.sleep(random.uniform(0.5, 1.5))
            
            # Type slowly
            for char in query:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            time.sleep(random.uniform(0.5, 1))
            search_box.send_keys(Keys.RETURN)
            print(f"✅ Search initiated")
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            search_url = f"https://www.tiktok.com/search?q={query.replace(' ', '%20')}"
            self.driver.get(search_url)
            time.sleep(random.uniform(2, 4))
    
    def scroll_and_collect(self, max_videos=50, fetch_comments=False):
        """Scroll through search results and collect video data"""
        print(f"📥 Starting to collect data (target: {max_videos} videos)")
        
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        videos_collected = 0
        scroll_attempts = 0
        max_scroll_attempts = 20
        
        while videos_collected < max_videos and scroll_attempts < max_scroll_attempts:
            try:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 4))
                scroll_attempts += 1
                
                # ==================== PAUSE AUTOPLAY VIDEOS ====================
                try:
                    self.pause_autoplay_videos()
                except:
                    pass
                # ==============================================================
                
                # Find video elements
                video_containers = []
                selectors_to_try = [
                    'div[data-e2e="search-card"]',
                    'div[class*="DivItemContainer"]',
                    'div[class*="video-card"]',
                    'div[class*="tiktok-"]',
                    'div[class*="ItemContainer"]',
                    'div.search-card'
                ]
                
                for selector in selectors_to_try:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            video_containers.extend(elements)
                    except:
                        continue
                
                # Remove duplicates
                unique_videos = []
                seen_positions = set()
                for video in video_containers:
                    try:
                        location = video.location
                        position_key = f"{location['x']}_{location['y']}"
                        if position_key not in seen_positions:
                            seen_positions.add(position_key)
                            unique_videos.append(video)
                    except:
                        unique_videos.append(video)
                
                print(f"👀 Found {len(unique_videos)} unique video containers")
                
                # Extract data from newly loaded videos
                new_videos_collected = 0
                for i, video in enumerate(unique_videos[-10:]):
                    if videos_collected >= max_videos:
                        break
                    
                    try:
                        # Scroll to view video
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", video)
                        time.sleep(0.5)
                        
                        video_data = self.extract_video_data(video, videos_collected + 1)
                        
                        if video_data and video_data.get('video_url'):
                            # Check for duplicates
                            existing_urls = [item.get('video_url') for item in self.data if 'video_url' in item]
                            if video_data['video_url'] not in existing_urls:
                                
                                # Fetch comments if requested
                                if fetch_comments:
                                    print(f"💬 Fetching comments for video {videos_collected + 1}...")
                                    comments = self.fetch_comments(video_data['video_url'])
                                    video_data['all_comments'] = comments
                                    print(f"   Found {len(comments)} comments")
                                
                                self.data.append(video_data)
                                videos_collected += 1
                                new_videos_collected += 1
                                
                                caption_preview = video_data.get('caption', '')[:50]
                                if len(video_data.get('caption', '')) > 50:
                                    caption_preview += "..."
                                    
                                print(f"✅ Collected video {videos_collected}: {video_data.get('username', 'Unknown')} - {caption_preview}")
                    except Exception as e:
                        print(f"⚠️ Error processing video: {e}")
                        continue
                
                if new_videos_collected == 0 and scroll_attempts > 5:
                    print("🔄 No new videos found, trying alternative scroll...")
                    self.driver.execute_script("window.scrollBy(0, 500);")
                    time.sleep(2)
                
                # Check if we've reached the end
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print("🏁 Reached end of page or content not loading")
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(1)
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    
                    if new_height == last_height:
                        break
                
                last_height = new_height
                
            except Exception as e:
                print(f"❌ Scroll error: {e}")
                break
        
        print(f"🎯 Total videos collected: {len(self.data)}")
    
    def fetch_comments(self, video_url, max_comments=100):
        """
        Fetch all comments from a video
        Returns: List of dictionaries with 'date' and 'text' only
        """
        comments = []
        
        try:
            # Open video in new tab
            original_window = self.driver.current_window_handle
            
            # Open new tab
            self.driver.execute_script("window.open('');")
            time.sleep(1)
            
            # Switch to new tab
            new_window = [window for window in self.driver.window_handles if window != original_window][0]
            self.driver.switch_to.window(new_window)
            
            # Navigate to video
            print(f"   Opening: {video_url}")
            self.driver.get(video_url)
            time.sleep(random.uniform(2, 4))
            
            # ==================== PAUSE THE VIDEO ====================
            self.pause_video()
            # ========================================================
            
            # Scroll to comments section
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(2)
            
            # Try to find and click "View more comments" if exists
            try:
                view_more_selectors = [
                    'div[data-e2e="view-more-1"]',
                    'div[class*="ViewMore"]',
                    'div[class*="view-more"]',
                    'button:contains("View more comments")',
                    'div:contains("View more comments")'
                ]
                
                for selector in view_more_selectors:
                    try:
                        if 'contains' in selector:
                            element = self.driver.find_element(By.XPATH, f"//*[contains(text(), 'View more comments')]")
                        else:
                            element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                        if element and element.is_displayed():
                            self.driver.execute_script("arguments[0].scrollIntoView();", element)
                            time.sleep(1)
                            element.click()
                            print(f"   Clicked 'View more comments'")
                            time.sleep(2)
                            break
                    except:
                        continue
            except:
                pass  # Continue without clicking
            
            # Scroll and collect comments
            comments_collected = 0
            last_comment_count = 0
            scroll_attempts = 0
            
            while comments_collected < max_comments and scroll_attempts < 10:
                try:
                    # Find comment containers
                    comment_elements = []
                    
                    # Try multiple selectors for comments
                    comment_selectors = [
                        'div[data-e2e="comment-level-1"]',
                        'div[class*="CommentItem"]',
                        'div[class*="comment-item"]',
                        'div[class*="commentContainer"]',
                        'div[class*="CommentList"] div[class*="DivCommentItemContainer"]'
                    ]
                    
                    for selector in comment_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if elements:
                                comment_elements.extend(elements)
                        except:
                            continue
                    
                    # If no specific selectors work, try generic approach
                    if not comment_elements:
                        try:
                            # Look for divs that likely contain comments
                            all_divs = self.driver.find_elements(By.CSS_SELECTOR, 'div')
                            for div in all_divs:
                                try:
                                    text = div.text.strip()
                                    if text and len(text) > 10 and len(text) < 500:
                                        # Check if it looks like a comment (has some text)
                                        comment_elements.append(div)
                                except:
                                    continue
                        except:
                            pass
                    
                    # Process new comments
                    for element in comment_elements[comments_collected:]:
                        if comments_collected >= max_comments:
                            break
                        
                        try:
                            comment_data = self.extract_comment_data(element)
                            if comment_data:
                                comments.append(comment_data)
                                comments_collected += 1
                        except:
                            continue
                    
                    # Check if we got new comments
                    if comments_collected == last_comment_count:
                        scroll_attempts += 1
                    else:
                        scroll_attempts = 0
                    
                    last_comment_count = comments_collected
                    
                    # Scroll within comments section
                    print(f"   Found {comments_collected} comments so far...")
                    self.driver.execute_script("window.scrollBy(0, 800);")
                    time.sleep(random.uniform(2, 3))
                    
                except Exception as e:
                    print(f"   ⚠️ Comment collection error: {e}")
                    break
            
            # Close the tab and return to original window
            self.driver.close()
            self.driver.switch_to.window(original_window)
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Failed to fetch comments: {e}")
            # Try to return to original window
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(original_window)
            except:
                pass
        
        return comments
    
    def pause_video(self):
        """Pause the video on the current page"""
        try:
            print("   ⏸️ Attempting to pause video...")
            
            # Method 1: Direct video element control via JavaScript
            pause_scripts = [
                # Pause all video elements
                """
                var videos = document.querySelectorAll('video');
                for(var i=0; i<videos.length; i++) {
                    videos[i].pause();
                    videos[i].currentTime = 0;
                    videos[i].muted = true;
                }
                return videos.length;
                """,
                
                # Click play/pause buttons
                """
                var buttons = document.querySelectorAll('button[data-e2e="video-play"], button[aria-label*="pause" i], button[aria-label*="play" i]');
                for(var i=0; i<buttons.length; i++) {
                    if(buttons[i].offsetParent !== null) {
                        buttons[i].click();
                    }
                }
                return buttons.length;
                """,
                
                # Click on video container
                """
                var containers = document.querySelectorAll('div[data-e2e="browse-video"], div[class*="DivPlayerContainer"], div[class*="VideoPlayer"]');
                for(var i=0; i<containers.length; i++) {
                    if(containers[i].offsetParent !== null) {
                        containers[i].click();
                    }
                }
                return containers.length;
                """
            ]
            
            for script in pause_scripts:
                try:
                    result = self.driver.execute_script(script)
                    if result:
                        print(f"   ✅ Video paused via script (elements: {result})")
                        time.sleep(0.5)
                except:
                    continue
            
            # Method 2: Try clicking on the center of the screen
            try:
                actions = ActionChains(self.driver)
                
                # Get screen size
                width = self.driver.execute_script("return window.innerWidth")
                height = self.driver.execute_script("return window.innerHeight")
                
                # Click in the center (where video likely is)
                actions.move_by_offset(width//2, height//2).click().perform()
                print("   ✅ Clicked center of screen to pause video")
                time.sleep(0.5)
            except:
                pass
            
            # Method 3: Emergency mute all media
            try:
                self.driver.execute_script("""
                    // Mute all audio
                    var videos = document.querySelectorAll('video, audio');
                    for(var v of videos) {
                        v.muted = true;
                        v.volume = 0;
                        v.pause();
                    }
                """)
                print("   🔇 All media muted and paused")
            except:
                pass
            
            # Verify video is paused
            time.sleep(1)
            try:
                is_paused = self.driver.execute_script("""
                    var videos = document.querySelectorAll('video');
                    if(videos.length === 0) return true;
                    
                    var allPaused = true;
                    for(var v of videos) {
                        if(!v.paused) {
                            allPaused = false;
                            break;
                        }
                    }
                    return allPaused;
                """)
                
                if is_paused:
                    print("   ✅ Video successfully paused")
                else:
                    print("   ⚠️ Video may still be playing")
                    
            except:
                print("   ⚠️ Could not verify pause status")
            
            return True
            
        except Exception as e:
            print(f"   ⚠️ Error pausing video: {e}")
            return False
    
    def pause_autoplay_videos(self):
        """Pause any autoplaying videos in search results"""
        try:
            self.driver.execute_script("""
                // Pause all videos
                document.querySelectorAll('video').forEach(v => {
                    v.pause();
                    v.currentTime = 0;
                    v.muted = true;
                });
                
                // Click any visible play/pause buttons
                document.querySelectorAll('button[data-e2e*="play"], button[aria-label*="pause" i], button[aria-label*="play" i]').forEach(btn => {
                    if(btn.offsetParent !== null) btn.click();
                });
            """)
        except:
            pass
    
    def extract_comment_data(self, comment_element):
        """
        Extract date and text from a comment element
        Returns: dict with 'date' and 'text' keys
        """
        try:
            comment_text = ""
            comment_date = ""
            
            # Try to get text content
            try:
                # Get all text from element
                comment_text = comment_element.text.strip()
                
                # Try to separate date from text
                # Look for patterns like "2d", "3w", "2024-01-15", etc.
                date_patterns = [
                    r'(\d+\s*(?:d|day|days|h|hour|hours|w|week|weeks|m|month|months|y|year|years|ago))',
                    r'(\d{1,2}/\d{1,2}/\d{2,4})',
                    r'(\d{4}-\d{1,2}-\d{1,2})',
                    r'(\d+\s*(?:minutes?|hours?|days?|weeks?|months?|years?)\s*ago)'
                ]
                
                # Try to extract date
                for pattern in date_patterns:
                    match = re.search(pattern, comment_text, re.IGNORECASE)
                    if match:
                        # Extract date part
                        date_part = match.group(1)
                        comment_date = date_part.strip()
                        
                        # Remove date from text if it's at the end
                        text_without_date = comment_text.replace(date_part, '').strip()
                        
                        # Clean up: remove extra punctuation
                        if text_without_date.endswith('·') or text_without_date.endswith('-'):
                            text_without_date = text_without_date[:-1].strip()
                        
                        comment_text = text_without_date
                        break
                
                # If no pattern matched, try splitting by newlines
                if not comment_date and '\n' in comment_text:
                    lines = comment_text.split('\n')
                    # Usually last line might be date
                    potential_date = lines[-1].strip()
                    if re.search(r'\d+[dhwmy]', potential_date.lower()) or re.search(r'\d+ \s*ago', potential_date.lower()):
                        comment_date = potential_date
                        comment_text = '\n'.join(lines[:-1]).strip()
            
            except:
                pass
            
            # If we couldn't parse date, set a default
            if not comment_date:
                comment_date = "Unknown date"
            
            # Clean the text
            if comment_text:
                # Remove any remaining metadata-like patterns
                comment_text = re.sub(r'@\w+\s*', '', comment_text)  # Remove @mentions if present
                comment_text = re.sub(r'#\w+\s*', '', comment_text)  # Remove hashtags if present
                comment_text = comment_text.strip()
            
            # Only return if we have some text
            if comment_text and len(comment_text) > 1:
                return {
                    'date': comment_date,
                    'text': comment_text
                }
            else:
                return None
                
        except Exception as e:
            print(f"      Comment extraction error: {e}")
            return None
    
    def extract_video_data(self, video_element, index):
        """Extract basic video data"""
        try:
            data = {
                'index': index,
                'collected_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'video_url': '',
                'caption': '',
                'post_date': ''
            }
            
            # Get video URL
            try:
                links = video_element.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    href = link.get_attribute('href')
                    if href and '/video/' in href and 'tiktok.com' in href:
                        data['video_url'] = href
                        break
            except:
                pass
            
            # Get caption
            try:
                caption_selectors = [
                    'div[data-e2e="search-card-desc"]',
                    'div[class*="VideoDesc"]',
                    'div[class*="caption"]',
                    'p', 'span',
                    'div[class*="content"]'
                ]
                
                for selector in caption_selectors:
                    try:
                        element = video_element.find_element(By.CSS_SELECTOR, selector)
                        text = element.text.strip()
                        if text and len(text) > 3:
                            data['caption'] = text
                            break
                    except:
                        continue
            except:
                pass
            
            # Try to get post date
            try:
                # Look for date patterns in the text
                all_text = video_element.text
                date_patterns = [
                    r'(\d+\s*(?:d|day|days|h|hour|hours|w|week|weeks|m|month|months|y|year|years|ago))',
                    r'(\d{1,2}/\d{1,2}/\d{2,4})',
                    r'(\d{4}-\d{1,2}-\d{1,2})'
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, all_text, re.IGNORECASE)
                    if match:
                        data['post_date'] = match.group(1)
                        break
            except:
                pass
            
            return data if data['video_url'] or data['caption'] else None
                
        except Exception as e:
            print(f"⚠️ Video extraction error: {e}")
            return None
    
    def save_data(self, query, format='csv'):
        """Save collected data to file"""
        if not self.data:
            print("📭 No data to save")
            return
        
        # Create flat structure for saving
        flat_data = []
        
        for video in self.data:
            # Video/post entry
            flat_data.append({
                'type': 'post',
                'video_index': video.get('index', ''),
                'video_url': video.get('video_url', ''),
                'date': video.get('post_date', video.get('collected_at', '')),
                'text': video.get('caption', ''),
                'has_comments': 'all_comments' in video
            })
            
            # Comments entries
            if 'all_comments' in video and video['all_comments']:
                for comment in video['all_comments']:
                    flat_data.append({
                        'type': 'comment',
                        'video_index': video.get('index', ''),
                        'video_url': video.get('video_url', ''),
                        'date': comment.get('date', ''),
                        'text': comment.get('text', ''),
                        'has_comments': ''
                    })
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '_')).rstrip()
        base_filename = f"tiktok_{safe_query}_{timestamp}"
        
        if format.lower() == 'csv':
            filename = f"{base_filename}.csv"
            df = pd.DataFrame(flat_data)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"💾 Data saved to {filename}")
            
            # Also save a summary
            summary_file = f"{base_filename}_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"TikTok Scraper Results\n")
                f.write(f"Query: {query}\n")
                f.write(f"Collection time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total posts collected: {len(self.data)}\n")
                f.write(f"Total entries (posts + comments): {len(flat_data)}\n")
                f.write(f"Posts with comments: {sum(1 for v in self.data if 'all_comments' in v and v['all_comments'])}\n")
                f.write(f"Total comments: {sum(len(v.get('all_comments', [])) for v in self.data)}\n")
            
        elif format.lower() == 'json':
            filename = f"{base_filename}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'query': query,
                    'collection_time': datetime.now().isoformat(),
                    'posts': self.data
                }, f, ensure_ascii=False, indent=2)
            print(f"💾 Data saved to {filename}")
        
        elif format.lower() == 'txt':
            # Simple text format
            filename = f"{base_filename}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                for item in flat_data:
                    f.write(f"Type: {item['type']}\n")
                    f.write(f"Date: {item['date']}\n")
                    f.write(f"Text: {item['text']}\n")
                    f.write(f"{'-'*50}\n\n")
            print(f"💾 Data saved to {filename}")
        
        # Print summary
        total_comments = sum(len(v.get('all_comments', [])) for v in self.data)
        print(f"\n📊 Final Summary:")
        print(f"   • Posts collected: {len(self.data)}")
        print(f"   • Total comments fetched: {total_comments}")
        print(f"   • Total text entries: {len(flat_data)}")
    
    def run(self, query, max_videos=20, fetch_comments=False, save_format='csv'):
        """Main method to run the scraper"""
        print(f"🚀 Starting TikTok Scraper for: '{query}'")
        print(f"📊 Target: {max_videos} videos")
        if fetch_comments:
            print(f"💬 Comments collection: ENABLED")
        print("=" * 50)
        
        try:
            # Setup browser
            self.setup_driver()
            
            # Perform search
            self.search_query(query)
            
            # Scroll and collect data
            self.scroll_and_collect(max_videos=max_videos, fetch_comments=fetch_comments)
            
            # Save results
            if self.data:
                self.save_data(query, format=save_format)
            else:
                print("❌ No data was collected.")
            
            print("=" * 50)
            print("🏁 Scraping completed!")
            
        except Exception as e:
            print(f"💥 Critical error: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            if self.driver:
                print("🛑 Closing browser...")
                self.driver.quit()

# Simple usage with comments
if __name__ == "__main__":
    # Create scraper instance
    scraper = TikTokScraper(headless=False)  # Set headless=True for background
    
    # Run with comments fetching
    scraper.run(
        query="Nelfund",  # Your search term
        max_videos=30,               # Number of videos to collect
        fetch_comments=True,        # Set to True to fetch comments
        save_format='csv'           # Options: 'csv', 'json', 'txt'
    )