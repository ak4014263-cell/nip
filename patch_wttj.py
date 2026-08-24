import os

file_path = r"c:\Users\hp\Downloads\IOP\WTJ\services\wttj\app\main.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Imports
content = content.replace(
    "from playwright.async_api import async_playwright",
    "import random\n        from playwright.async_api import async_playwright\n        from playwright_stealth import stealth_async"
)

# 2. Stealth Apply
content = content.replace(
    "page = await ctx.new_page()\n\n            # Track registration API",
    "page = await ctx.new_page()\n            await stealth_async(page)\n\n            # Track registration API"
)

# 3. Random wait on auth URL
content = content.replace(
    'logger.info("Navigate to WTTJ Auth page")\n            await page.goto("https://www.welcometothejungle.com/en/authenticate/signup", wait_until="domcontentloaded")',
    'logger.info("Navigate to WTTJ Auth page")\n            await page.goto("https://www.welcometothejungle.com/en/authenticate/signup", wait_until="domcontentloaded", timeout=60000)\n            await asyncio.sleep(random.uniform(2.5, 4.5))'
)

# 4. Human type delay
content = content.replace(
    'await el.click()\n                            await page.keyboard.type(str(text), delay=50)\n                            await asyncio.sleep(0.3)',
    'await asyncio.sleep(random.uniform(0.5, 1.5))\n                            await el.click()\n                            await asyncio.sleep(random.uniform(0.2, 0.5))\n                            await page.keyboard.type(str(text), delay=random.randint(50, 150))\n                            await asyncio.sleep(random.uniform(0.5, 1.0))'
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched main.py successfully.")
