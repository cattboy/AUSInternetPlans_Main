import tkinter as tk
from tkinter import ttk
import pandas as pd
from bs4 import BeautifulSoup
import re
import os
import io
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'
import HTMLDownloaderToSingleFile

class InternetPlanScraper:
    def __init__(self):
        self.providers = {
            'Telstra': 'https://www.telstra.com.au/internet/plans'
            # 'Optus': 'https://www.optus.com.au/broadband-nbn/home-broadband/plans',
            # 'TPG': 'https://www.tpg.com.au/nbn',
        }
        self.plans_data = []
        self.nbn_speeds = ["NBN25", "NBN50", "NBN250", "NBN1000", "nbn®50", "nbn®100", "nbn®250", "nbn®1000", "5G Internet"]


    def download_html(self, provider, url):
        try:
            print(f"Navigating to {provider}'s website via HTMLDownloaderToSingleFile...")
            file_path = HTMLDownloaderToSingleFile.save_page_as_single_file(provider, url)
            print(f"Exiting {provider}'s website via HTMLDownloaderToSingleFile...")
            
            # Read the downloaded HTML file
            if file_path and os.path.exists(file_path):
                    return file_path
            return None

        except Exception as e:
            print(f"Error downloading HTML from {provider}: {str(e)}")
            return None

    def extract_plan_details(self, html_content, provider):
        if not html_content:
            print(f"No HTML content found for {provider}")
            return
        
        print(f"\n=== Processing {provider} Plans ===")
        
        # Find plan cards using various possible selectors
        plan_cards = self.driver.find_elements(By.CSS_SELECTOR,
            "[class*='plan-card' i], [class*='planCard' i], [class*='plan' i]")
        
        if not plan_cards:
            print(f"No plan cards found for {provider}")
            return
        
        print(f"Found {len(plan_cards)} plan cards for {provider}")
        
        # Create directories if they don't exist
        base_path = r"C:\Users\Cursor_VBOX\Downloads\HTML"
        provider_path = os.path.join(base_path, provider.lower())
        os.makedirs(provider_path, exist_ok=True)
        
        for index, card in enumerate(plan_cards, 1):
            try:
                print(f"\nProcessing card {index}/{len(plan_cards)}")
                
                # Take screenshot of the card
                print(f"Taking screenshot of card {index}...")
                screenshot = card.screenshot_as_png
                
                # Check image dimensions before proceeding
                image = Image.open(io.BytesIO(screenshot))
                width, height = image.size
                
                if width < 250 or height < 800:
                    print(f"Skipping card {index} - too small (dimensions: {width}x{height})")
                    continue
                
                print(f"Card dimensions: {width}x{height} pixels - processing...")
                
                # Save screenshot with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = os.path.join(provider_path, f"plan_card_{index}_{timestamp}.png")
                with open(screenshot_path, 'wb') as f:
                    f.write(screenshot)
                print(f"Screenshot saved to {screenshot_path}")
                
                # Use OCR to extract text
                print("Performing OCR on card...")
                card_text = pytesseract.image_to_string(image).lower()
                print(f"OCR Text extracted (first 20 chars): {card_text[:20]}...")
                
                speed_found = False
                for speed in self.nbn_speeds:
                    if speed.lower() in card_text:
                        print(f"\nFound speed match: {speed}")
                        # Look for price pattern: $XX/month
                        price_match = re.search(r'\$(\d+)(?:\.?\d*)?/(?:mnth|mth|month)', card_text)
                        if price_match:
                            nbnprice = float(price_match.group(1))
                            nbnmonth = re.search(r'/(\w+)', price_match.group()).group(1)
                            print(f"Found base price: ${nbnprice}/{nbnmonth}")
                            
                            # Check for promotional pricing
                            print("Checking for promotional pricing...")
                            promo_match = re.search(r'for\s+(\d+)\s*(?:mnth|mth|month).*?\$(\d+)', card_text)
                            if promo_match:
                                nbnpromotion = {
                                    'duration': int(promo_match.group(1)),
                                    'price': float(promo_match.group(2))
                                }
                                print(f"Found promotion: ${nbnpromotion['price']} for {nbnpromotion['duration']} {nbnmonth}")
                                
                                self.plans_data.append({
                                    'Provider': provider,
                                    'Speed': int(re.search(r'\d+', speed).group()),
                                    'Price': nbnprice,
                                    'PriceUnit': nbnmonth,
                                    'HasPromotion': True,
                                    'PromotionDuration': nbnpromotion['duration'],
                                    'PromotionPrice': nbnpromotion['price'],
                                    'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                })
                                print("Added plan data with promotion to database")
                            else:
                                print("No promotion found")
                                self.plans_data.append({
                                    'Provider': provider,
                                    'Speed': int(re.search(r'\d+', speed).group()),
                                    'Price': nbnprice,
                                    'PriceUnit': nbnmonth,
                                    'HasPromotion': False,
                                    'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                })
                                print("Added plan data to database")
                            
                            speed_found = True
                            break
                
                if not speed_found:
                    print(f"Warning: No matching NBN speed found in card {index}")
                
            except Exception as e:
                print(f"Error processing card {index}: {str(e)}")
                print(f"Error type: {type(e).__name__}")
                continue
        
        print(f"\n=== Completed processing {provider} Plans ===")
        print(f"Total plans found: {len(self.plans_data)}\n")
        # print(f"Plans Provider: {self.plans_data.Provider} Plans Speed: {self.plans_data.Speed} Plans Price: {self.plans_data.Price}")
        print(f"Plans Provider: {self.plans_data}")

    def scrape_all_providers(self):
        try:
            # Initialize the Chrome driver at the start
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service)
            
            for provider, url in self.providers.items():
                file_path = self.download_html(provider, url)
                if file_path:
                    # Navigate to the downloaded HTML using Selenium
                    temp_html_path = f"file:///{os.path.abspath(file_path)}"
                    self.driver.get(temp_html_path)
                    self.extract_plan_details(file_path, provider)
                else:
                    print(f"Failed to get HTML content for {provider}")
            
            # Create DataFrame from collected data
            df = pd.DataFrame(self.plans_data)
            
            # Cleanup downloaded files and close browser
            self.cleanup_downloads()
            self.cleanup_browser()
            
            # Launch GUI with the data
            self.launch_gui(df)
            
            return df
        except Exception as e:
            print(f"Error scraping all providers: {e}")
            return None
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

    def cleanup_downloads(self):
        print("\nClean up any downloaded files and screenshots")
        try:
            download_dir = r"C:\Users\Cursor_VBOX\Downloads\HTML"
            print("\nCleaning up downloaded files...")
            for filename in os.listdir(download_dir):
                file_path = os.path.join(download_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        print(f"Deleted: {filename}")
                except Exception as e:
                    print(f"Error deleting {filename}: {e}")
            print("\nCleanup downloaded files completed successfully")
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def cleanup_browser(self):
        print("\nClean up WebDriver and Chrome instances")
        try:
            print("\nCleaning up browser resources...")
            if self.driver:
                self.driver.quit()
                print("WebDriver closed successfully")
        except Exception as e:
            print(f"Error during browser cleanup: {e}")
        finally:
            # Force kill any remaining chrome processes if needed
            try:
                if os.name == 'nt':  # Windows
                    os.system('taskkill /f /im chromedriver.exe /T')
                    os.system('taskkill /f /im chrome.exe /T')
                else:  # Linux/Mac
                    os.system('pkill -f chromedriver')
                    os.system('pkill -f chrome')
                print("Chrome processes cleaned up")
            except Exception as e:
                print(f"Error force-closing Chrome processes: {e}")

    def launch_gui(self, df):
        """Launch the GUI with the scraped data"""
        try:
            root = tk.Tk()
            app = InternetPlanGUI(root)
            app.df = df  # Set the DataFrame directly
            app.update_table()  # Update the table with the new data
            root.mainloop()
        except Exception as e:
            print(f"Error launching GUI: {e}")

    def __del__(self):
        print("Cleaning up WebDriver...")
        self.cleanup_browser()
        print("WebDriver cleaned up successfully")

class InternetPlanGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Australian Internet Plans Comparison")
        self.root.geometry("1600x1200")
        
        # Search frame
        search_frame = ttk.Frame(root)
        search_frame.pack(pady=10, padx=10, fill='x')
        
        ttk.Label(search_frame, text="Search:").pack(side='left')
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_table)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side='left', padx=5)
        
        # Create output directory
        self.output_path = os.path.join(r"C:\Users\Cursor_VBOX\Downloads\HTML\Output")
        os.makedirs(self.output_path, exist_ok=True)
        
        # Add export button
        ttk.Button(search_frame, text="Export to HTML", command=self.export_to_html).pack(side='right', padx=5)
        
        # Table
        columns = ('Provider', 'Speed', 'Price', 'HasPromotion', 'PromotionPrice', 'PromotionDuration')
        self.tree = ttk.Treeview(root, columns=columns, show='headings')
        self.tree.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Configure columns
        column_configs = {
            'Provider': ('Provider', 150),
            'Speed': ('Speed (Mbps)', 100),
            'Price': ('Price ($)', 100),
            'HasPromotion': ('Has Promotion', 100),
            'PromotionPrice': ('Promo Price ($)', 100),
            'PromotionDuration': ('Promo Duration (months)', 150)
        }
        
        for col, (heading, width) in column_configs.items():
            self.tree.heading(col, text=heading, command=lambda c=col: self.sort_column(c))
            self.tree.column(col, width=width, anchor='center')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(root, orient='vertical', command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Load data
        self.load_data()

    def load_data(self):
        """Initialize scraper and load data"""
        scraper = InternetPlanScraper()
        self.df = scraper.scrape_all_providers()
        self.update_table()

    def update_table(self, df=None):
        """Update the treeview with current DataFrame"""
        if df is None:
            df = self.df
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Insert new data
        for _, row in df.iterrows():
            values = (
                row['Provider'],
                row['Speed'],
                f"${row['Price']:.2f}",
                'Yes' if row['HasPromotion'] else 'No',
                f"${row['PromotionPrice']:.2f}" if 'PromotionPrice' in row and row['HasPromotion'] else '-',
                f"{row['PromotionDuration']}" if 'PromotionDuration' in row and row['HasPromotion'] else '-'
            )
            self.tree.insert('', 'end', values=values)

    def filter_table(self, *args):
        search_term = self.search_var.get().lower()
        filtered_df = self.df[
            self.df['Provider'].str.lower().str.contains(search_term) |
            self.df['Speed'].astype(str).str.contains(search_term) |
            self.df['Price'].astype(str).str.contains(search_term)
        ]
        self.update_table(filtered_df)

    def sort_column(self, column):
        self.df = self.df.sort_values(by=[column])
        self.update_table()

    def export_to_html(self):
        if hasattr(self, 'df'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_path = os.path.join(self.output_path, f"internet_plans_{timestamp}.html")
            
            # Convert DataFrame to HTML with styling
            html_content = """
            <html>
            <head>
                <style>
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                    tr:nth-child(even) { background-color: #f9f9f9; }
                </style>
            </head>
            <body>
            """
            html_content += "<h2>Australian Internet Plans Comparison</h2>"
            html_content += self.df.to_html(index=False)
            html_content += "</body></html>"
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"Exported data to {html_path}")

def main():
    root = tk.Tk()
    app = InternetPlanGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()