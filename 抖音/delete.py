import os
import re
import time
import logging
import random
from typing import Optional, List
from playwright.async_api import async_playwright, Browser, Page, Playwright, BrowserContext
import pandas as pd
import asyncio


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            chromium_sandbox=False,
            ignore_default_args=["--enable-automation"],
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
        )

        # 创建新的浏览器上下文
        context = await browser.new_context(
            no_viewport=True,
            storage_state=path,
            permissions=["geolocation"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

        page = await context.new_page()
        await page.goto(url)
        await page.wait_for_load_state()

        while True:
            await page.locator('//div[@class="content-body--29zhI"]/div[1]').hover()
            await page.locator("div:nth-child(4) > span").first.click()
            await page.get_by_role("button", name="确定").click()

        # 关闭浏览器上下文
        await context.close()
        await browser.close()

url='https://netbanking.hdfcbank.com/netbanking/'
url = 'https://creator.douyin.com/creator-micro/content/manage'
path = '/抖音/cookie_小菜鸟贼菜48089699093.json'
# 运行异步主函数
asyncio.run(main())
