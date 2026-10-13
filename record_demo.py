import os
import shutil
import glob
from playwright.sync_api import sync_playwright

REC_DIR = "/config/Desktop/BuildWithGemini/demo_recording"
if os.path.exists(REC_DIR):
    shutil.rmtree(REC_DIR)
os.makedirs(REC_DIR, exist_ok=True)

def record_session():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-gpu"]
        )
        context = browser.new_context(
            record_video_dir=REC_DIR,
            record_video_size={"width": 1280, "height": 800},
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        print("1. Opening Wanderlust UI...")
        page.goto("http://localhost:8080", wait_until="networkidle")
        page.wait_for_timeout(3000)
        
        # Click on the first example prompt pill to showcase curated UI feature
        print("2. Clicking example prompt pill: '🌊 Ocean Bluffs & Coastal Trips'...")
        pills = page.locator(".example-pill")
        pills.nth(0).click()
        
        # Wait for agent response
        print("3. Waiting for agent recommendations...")
        # Wait until the first agent reply finishes
        page.wait_for_selector(".msg-row.agent .bubble:not(:text-is('…'))", timeout=60000)
        print("   Agent response received! Waiting to let viewer read recommendations...")
        page.wait_for_timeout(9000)
        
        # Second richer action: Ask for live weather and postcard image generation
        print("4. Typing second prompt: 'Can you check the live weather at Muir Woods and generate a vintage postcard for it?'...")
        input_elem = page.locator("#input")
        input_elem.click()
        input_elem.fill("Can you check the live weather at Muir Woods and generate a vintage postcard for it?")
        page.wait_for_timeout(1000)
        page.locator(".send-btn").click()
        
        print("5. Waiting for weather update and AI postcard generation...")
        page.wait_for_selector(".msg-row.agent img", timeout=90000)
        print("   Postcard image loaded! Waiting to showcase the rendered result...")
        page.wait_for_timeout(8000)
        
        print("6. Closing browser context to finalize demo video...")
        context.close()
        browser.close()
        print("Recording completed successfully!")

if __name__ == "__main__":
    record_session()
