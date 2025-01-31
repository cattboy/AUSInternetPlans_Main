from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import os
# Example usage

def save_page_as_single_file(provider, url):   
    try:
        # Create the output directory if it doesn't exist
        print(f"Creating output directory for {provider}...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_path = r"C:\Users\Cursor_VBOX\Downloads\HTML"
        provider_path = os.path.join(base_path, provider.lower(), provider.lower() + " " + timestamp + ".html")
        os.makedirs(os.path.dirname(provider_path), exist_ok=True)


        # Setup Chrome driver
        service = Service()
        driver = webdriver.Chrome(service=service)
        # driver.set_page_load_timeout(180)  # Added 3 minute page load timeout
        # Navigate to page and wait for it to load\
        print(f"Navigating to {provider}'s website via HTMLDownloaderToSingleFile...")
        driver.get(url)
        WebDriverWait(driver, 180).until(  # Already set to 3 minutes
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Execute JavaScript to get complete HTML with inlined resources
        script = """
        return (async () => {
            const getInlineStyles = async () => {
                const styles = document.querySelectorAll('link[rel="stylesheet"]');
                for (const style of styles) {
                    try {
                        const response = await fetch(style.href);
                        const css = await response.text();
                        const newStyle = document.createElement('style');
                        newStyle.textContent = css;
                        style.replaceWith(newStyle);
                    } catch (e) {
                        console.error('Error inlining style:', e);
                    }
                }
            };
            
            const getInlineImages = async () => {
                // Define selectors for plan-related elements
                const planSelectors = [
                    "[class*='plan-card']",
                    "[class*='pricing-table']",
                    "[class*='nbn-plan']",
                    "[data-test*='plan']",
                    "[class*='product-card']"
                ];
                
                // Get all plan-related elements
                const planElements = planSelectors.flatMap(selector => 
                    Array.from(document.querySelectorAll(selector))
                );
                
                // Get all images within or near plan elements
                const relevantImages = new Set();
                planElements.forEach(element => {
                    // Get images within the plan element
                    element.querySelectorAll('img').forEach(img => 
                        relevantImages.add(img)
                    );
                    
                    // Get images in adjacent siblings (for related content)
                    if (element.nextElementSibling) {
                        element.nextElementSibling.querySelectorAll('img').forEach(img => 
                            relevantImages.add(img)
                        );
                    }
                    if (element.previousElementSibling) {
                        element.previousElementSibling.querySelectorAll('img').forEach(img => 
                            relevantImages.add(img)
                        );
                    }
                });

                // Process only the relevant images
                for (const img of relevantImages) {
                    try {
                        if (img.src && !img.src.startsWith('data:')) {
                            const response = await fetch(img.src);
                            const blob = await response.blob();
                            const reader = new FileReader();
                            await new Promise((resolve) => {
                                reader.onload = () => {
                                    img.src = reader.result;
                                    resolve();
                                };
                                reader.readAsDataURL(blob);
                            });
                        }
                    } catch (e) {
                        console.error('Error inlining image:', e);
                    }
                }
            };
            
            await Promise.all([getInlineStyles(), getInlineImages()]);
            return document.documentElement.outerHTML;
        })();
        """
        
        # Get the complete HTML
        complete_html = driver.execute_script(script)
        
        print(f"HTMLDownloaderToSingleFile has finished downloading {provider}'s website...")
        # Save to file
        with open(provider_path, 'w', encoding='utf-8') as f:
            f.write(complete_html)
            
        print(f"Page saved successfully to {provider_path}")
        return provider_path
    finally:
        driver.quit()
