from scraper.base import WebScraper
import time

class GoogleAuth(WebScraper):
    def login(self, email: str, password: str = None, cookie_file: str = "cookies/google.json"):
        """
        Attempts to login to Google. 
        If password is not provided, it will wait for manual intervention (VNC).
        """
        self.start()
        context = self.get_context_with_cookies(cookie_file)
        page = context.new_page()
        
        print(f"Navigating to Google Login for {email}...")
        page.goto("https://accounts.google.com/ServiceLogin")
        
        # Check if already logged in
        if "ServiceLogin" not in page.url:
            print("Already logged in or redirected.")
            self.save_cookies(context, cookie_file)
            return context, page

        # Enter Email
        page.fill('input[type="email"]', email)
        page.click('#identifierNext')
        time.sleep(2)
        
        if password:
            print("Entering password...")
            try:
                page.fill('input[type="password"]', password)
                page.click('#passwordNext')
                time.sleep(5)
            except Exception as e:
                print(f"Password field not found or error: {e}. Might need manual intervention.")
        
        # Manual Intervention Check
        print("Checking if manual intervention is needed (2FA/Captcha)...")
        if "challenge" in page.url or "signin/v2/identifier" in page.url:
            print("!!! MANUAL INTERVENTION REQUIRED !!!")
            print("Please connect via VNC to complete the login.")
            # In a real scenario, we would wait here or pulse a status to the UI
            # For now, we'll wait for a timeout or until the URL changes
            page.wait_for_url("https://myaccount.google.com/**", timeout=300000) # 5 min wait
        
        print("Login successful or timed out.")
        self.save_cookies(context, cookie_file)
        return context, page
