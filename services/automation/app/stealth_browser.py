"""
Enhanced Stealth Browser Configuration
Implements multiple anti-bot detection strategies for WTTJ automation
"""
import asyncio
import random
from typing import Optional, Dict, Any
from playwright.async_api import Page, Browser, BrowserContext, async_playwright
import logging

logger = logging.getLogger(__name__)


class StealthBrowser:
    """
    Browser with advanced anti-detection capabilities
    Implements multiple strategies to bypass bot detection systems
    """
    
    def __init__(self, headless: bool = False, use_residential_proxy: bool = False):
        self.headless = headless
        self.use_residential_proxy = use_residential_proxy
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
    async def launch(self) -> Page:
        """Launch browser with stealth configuration"""
        try:
            self.playwright = await async_playwright().start()
            
            # Browser launch args for maximum stealth
            launch_args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920,1080',
                '--start-maximized',
            ]
            
            # Launch browser
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=launch_args,
                # Use chromium channel for more realistic fingerprint
                channel=None,  # Use default chromium
            )
            
            # Context configuration with realistic fingerprints
            context_options = {
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': self._get_random_user_agent(),
                'locale': 'en-US',
                'timezone_id': 'Europe/Paris',
                'permissions': ['geolocation'],
                'geolocation': {'latitude': 48.8566, 'longitude': 2.3522},  # Paris
                'color_scheme': 'light',
                'device_scale_factor': 1,
                'has_touch': False,
                'is_mobile': False,
            }
            
            # Add proxy if enabled
            if self.use_residential_proxy:
                proxy_config = self._get_proxy_config()
                if proxy_config:
                    context_options['proxy'] = proxy_config
            
            self.context = await self.browser.new_context(**context_options)
            
            # Apply stealth scripts
            await self._apply_stealth_scripts(self.context)
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set longer timeouts
            self.page.set_default_timeout(60000)
            self.page.set_default_navigation_timeout(60000)
            
            logger.info("✅ Stealth browser launched successfully")
            return self.page
            
        except Exception as e:
            logger.error(f"Failed to launch stealth browser: {e}")
            raise
    
    async def _apply_stealth_scripts(self, context: BrowserContext):
        """Apply JavaScript to mask automation"""
        stealth_script = """
        // Overwrite the `navigator.webdriver` property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Overwrite the `plugins` property to mock real plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                },
                {
                    0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                    description: "Portable Document Format", 
                    filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                    length: 1,
                    name: "Chrome PDF Viewer"
                },
                {
                    0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable"},
                    1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable"},
                    description: "Native Client",
                    filename: "internal-nacl-plugin",
                    length: 2,
                    name: "Native Client"
                }
            ],
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en', 'fr'],
        });
        
        // Mock platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32',
        });
        
        // Mock hardware concurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8,
        });
        
        // Mock device memory
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8,
        });
        
        // Mock permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({state: Notification.permission}) :
                originalQuery(parameters)
        );
        
        // Add chrome object for more realistic fingerprint
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        
        // Mock getBattery
        if (!navigator.getBattery) {
            navigator.getBattery = () => Promise.resolve({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 1,
                addEventListener: () => {},
                removeEventListener: () => {},
                dispatchEvent: () => true
            });
        }
        
        // Override toString methods
        const toStringProxy = new Proxy(Function.prototype.toString, {
            apply: function(target, thisArg, argumentsList) {
                if (thisArg === navigator.webdriver) {
                    return 'function get webdriver() { [native code] }';
                }
                return target.apply(thisArg, argumentsList);
            }
        });
        Function.prototype.toString = toStringProxy;
        
        // Remove automation-related properties
        delete navigator.__proto__.webdriver;
        
        console.log('🔒 Stealth mode activated');
        """
        
        await context.add_init_script(stealth_script)
    
    def _get_random_user_agent(self) -> str:
        """Get a random realistic user agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        return random.choice(user_agents)
    
    def _get_proxy_config(self) -> Optional[Dict[str, Any]]:
        """
        Get proxy configuration
        TODO: Configure your residential proxy service here
        """
        # Example proxy configuration (uncomment and configure):
        # return {
        #     'server': 'http://proxy.example.com:8080',
        #     'username': 'your_username',
        #     'password': 'your_password'
        # }
        return None
    
    async def human_like_click(self, selector: str, delay_range: tuple = (0.5, 2.0)):
        """
        Click element with human-like behavior
        
        Args:
            selector: CSS selector for the element
            delay_range: Min and max delay in seconds before clicking
        """
        try:
            # Wait for element
            element = self.page.locator(selector).first
            await element.wait_for(state='visible', timeout=10000)
            
            # Scroll element into view smoothly
            await element.scroll_into_view_if_needed()
            
            # Random delay before interaction
            await asyncio.sleep(random.uniform(0.3, 0.8))
            
            # Move mouse to element (hover)
            await element.hover()
            
            # Random delay before click
            await asyncio.sleep(random.uniform(*delay_range))
            
            # Try click
            await element.click(timeout=5000)
            
            logger.info(f"✅ Human-like click on: {selector}")
            return True
            
        except Exception as e:
            logger.warning(f"Human-like click failed: {e}")
            
            # Try force click as fallback
            try:
                await self.page.locator(selector).first.click(force=True)
                logger.info(f"✅ Force click succeeded: {selector}")
                return True
            except Exception as e2:
                logger.error(f"Force click also failed: {e2}")
                return False
    
    async def human_like_type(self, selector: str, text: str, delay_range: tuple = (0.05, 0.15)):
        """
        Type text with human-like delays between keystrokes
        
        Args:
            selector: CSS selector for input element
            text: Text to type
            delay_range: Min and max delay between keystrokes
        """
        try:
            element = self.page.locator(selector).first
            await element.wait_for(state='visible', timeout=10000)
            
            # Click to focus
            await element.click()
            await asyncio.sleep(random.uniform(0.1, 0.3))
            
            # Clear existing text
            await element.fill('')
            await asyncio.sleep(random.uniform(0.1, 0.2))
            
            # Type with random delays
            for char in text:
                await element.type(char, delay=random.uniform(*delay_range) * 1000)
            
            logger.info(f"✅ Human-like typing completed: {selector}")
            return True
            
        except Exception as e:
            logger.error(f"Human-like typing failed: {e}")
            return False
    
    async def random_mouse_movement(self):
        """Simulate random mouse movements"""
        try:
            # Random movements across the page
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, 1800)
                y = random.randint(100, 900)
                await self.page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.3))
        except Exception as e:
            logger.warning(f"Random mouse movement failed: {e}")
    
    async def random_scroll(self):
        """Simulate random scrolling"""
        try:
            # Scroll down
            for _ in range(random.randint(2, 4)):
                await self.page.mouse.wheel(0, random.randint(100, 500))
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Scroll up a bit
            await self.page.mouse.wheel(0, -random.randint(50, 200))
            await asyncio.sleep(random.uniform(0.3, 0.8))
        except Exception as e:
            logger.warning(f"Random scroll failed: {e}")
    
    async def close(self):
        """Close browser and cleanup"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("✅ Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")


class HumanBehaviorSimulator:
    """Simulate realistic human behavior patterns"""
    
    @staticmethod
    async def reading_pause(min_seconds: float = 2.0, max_seconds: float = 5.0):
        """Simulate reading time"""
        await asyncio.sleep(random.uniform(min_seconds, max_seconds))
    
    @staticmethod
    async def thinking_pause(min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Simulate thinking time"""
        await asyncio.sleep(random.uniform(min_seconds, max_seconds))
    
    @staticmethod
    async def random_pause(min_seconds: float = 0.5, max_seconds: float = 1.5):
        """Random pause between actions"""
        await asyncio.sleep(random.uniform(min_seconds, max_seconds))
    
    @staticmethod
    def random_typo_and_correction(text: str, typo_probability: float = 0.1) -> list:
        """
        Generate typing sequence with occasional typos and corrections
        
        Returns list of (action, text) tuples: ('type', 'a'), ('backspace', None), etc.
        """
        sequence = []
        for i, char in enumerate(text):
            # Occasionally make a typo
            if random.random() < typo_probability and i > 0:
                # Type wrong character
                wrong_chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
                wrong_char = random.choice([c for c in wrong_chars if c != char.lower()])
                sequence.append(('type', wrong_char))
                # Pause to "notice" mistake
                sequence.append(('pause', random.uniform(0.2, 0.5)))
                # Backspace
                sequence.append(('backspace', None))
                # Pause before typing correct character
                sequence.append(('pause', random.uniform(0.1, 0.3)))
            
            # Type correct character
            sequence.append(('type', char))
            sequence.append(('pause', random.uniform(0.05, 0.15)))
        
        return sequence


# Example usage
async def example_usage():
    """Example of using StealthBrowser"""
    browser = StealthBrowser(headless=False)
    
    try:
        page = await browser.launch()
        
        # Navigate with human-like behavior
        await page.goto('https://www.welcometothejungle.com/en/authenticate/signup')
        
        # Simulate reading the page
        await HumanBehaviorSimulator.reading_pause(3, 5)
        
        # Random mouse movements and scrolling
        await browser.random_mouse_movement()
        await browser.random_scroll()
        
        # Fill form with human-like typing
        await browser.human_like_type('input[type="email"]', 'test@example.com')
        await HumanBehaviorSimulator.thinking_pause()
        
        await browser.human_like_type('input[type="password"]', 'SecurePassword123!')
        await HumanBehaviorSimulator.thinking_pause()
        
        # Click button with human-like behavior
        await browser.human_like_click('button[type="submit"]')
        
        # Wait for result
        await asyncio.sleep(5)
        
    finally:
        await browser.close()


if __name__ == '__main__':
    asyncio.run(example_usage())
