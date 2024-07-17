import logging
import os
import re
import time
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type, before_sleep_log
from playwright.sync_api import sync_playwright
from API.file_handle import get_files
from API.record import FileUploadTracker

script_name = os.path.basename(__file__).split('.')[0]
logging.basicConfig(level=logging.INFO, format=f'%(asctime)s-{script_name}-%(levelname)s-%(message)s')
logger = logging.getLogger(script_name)


class Program:
    def __init__(self, cookie_dir=None, file_dir=None):
        self.p: Optional[sync_playwright] = None
        self.browser: Optional[sync_playwright.Browser] = None
        self.context: Optional[sync_playwright.BrowserContext] = None
        self.page: Optional[sync_playwright.Page] = None
        self.url = 'https://creator.douyin.com/creator-micro/content/upload?default-tab=3'
        self.cookie_dir = cookie_dir
        self.file_dir = file_dir
        self.file_tracker = FileUploadTracker()  # 添加文件上传记录器
        self.upload = retry(
            stop=stop_after_attempt(3),
            wait=wait_fixed(2),
            retry=retry_if_exception_type(Exception),
            before_sleep=self.custom_before_sleep,
            reraise=True,
        )(self.upload)

    def custom_before_sleep(self, retry_state):
        attempt_number = retry_state.attempt_number
        wait = retry_state.next_action.sleep
        logger.info(f"Attempt {attempt_number} failed. Retrying in {wait} seconds.")
        self.init_browser()

    def init_browser(self):
        if self.p:
            self.context.close() or self.p.stop()
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch(headless=False,
                                              chromium_sandbox=False,
                                              # channel="chrome",
                                              ignore_default_args=["--enable-automation"],
                                              args=["--disable-blink-features=AutomationControlled",
                                                    "--start-maximized"]
                                              )
        self.context = self.browser.new_context(
            no_viewport=True,
            storage_state=self.cookie_file,
            permissions=["geolocation"],
            geolocation={"latitude": 30.2741, "longitude": 120.1551},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.page = self.context.new_page()
        self.page.add_init_script(path=os.path.join(os.path.dirname(__file__), "stealth.min.js"))

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(2), retry=retry_if_exception_type(Exception))
    def perform_upload(self):
        # self.page.locator('//span[text()="抱歉，今天投稿次数已达到上限，请明天再试"]').wait_for()
        self.page.locator('//button[text()="发布"]').click()
        self.page.locator('//span[text()="发布成功"]').wait_for(state='visible')

    def upload(self, dir_name, dir_path, account, index):
        start_time = time.time()  # 开始时间
        key_id = account + '-' + dir_name
        if self.file_tracker.get_file(key_id):
            return logger.info(f"已经上传序号:{index},账号:{account},上传目录:{dir_name},跳过······")
        self.page.goto(self.url)
        # 处理弹窗,是否处于上次上传没有上传成功，处于编辑状态
        if (dismiss_button := self.page.locator('span:has-text("放弃")')).is_visible(timeout=5000):
            dismiss_button.click()
        logger.info(f"正在上传序号:{index},账号:{account},上传目录:{dir_name}")
        self.page.locator('input[accept*="image/png"]').set_input_files(dir_path)
        self.page.wait_for_url(
            "https://creator.douyin.com/creator-micro/content/publish-media/image-text?default-tab=3&enter_from=publish_page&media_type=image&type=new",
            timeout=2000)
        self.page.locator('//input[@placeholder="添加作品标题"]').fill(dir_name)
        self.page.focus('//div[@data-placeholder="添加作品描述..."]')
        self.page.keyboard.type("简介信息")
        for text in ['流量卡推荐', '流量卡', '流量卡怎么选', '流量卡避坑指南', '流量卡官方正品']:
            self.page.keyboard.down('Shift')
            self.page.keyboard.press('#')
            self.page.keyboard.up('Shift')
            self.page.keyboard.type(text)
            self.page.keyboard.press('Space')

        self.page.locator('//span[text()="选择音乐"]').click()
        self.page.locator('//input[@placeholder="搜索音乐"]').fill('young for you (抒情版)\n')
        self.page.hover('//div[text()="young for you (抒情版)"]')
        self.page.locator("div").filter(has_text=re.compile(r"^01:57使用$")).get_by_role("button").click()
        self.page.locator('//span[text()="编辑封面"]').click()
        self.page.locator(
            '//button[text()="确定" and @class="button--1SZwR submit--1rTdk primary--1AMXd large--84z2d"]').wait_for()
        self.page.locator('//div[text()="设置封面"]/..//div[@class="resize-drag-rotate "]').click()
        self.page.locator(
            '//button[text()="确定" and @class="button--1SZwR submit--1rTdk primary--1AMXd large--84z2d"]').click()
        self.page.locator('//button[text()="确定"]').wait_for(state='hidden')
        self.perform_upload()
        self.file_tracker.add_file(key_id)  # 记录上传文件
        end_time = time.time()  # 结束时间
        logger.info(f"上传成功序号:{index},账号:{account},上传目录:{dir_name},总用时:{end_time - start_time:.2f}秒")

    def __del__(self):
        self.file_tracker.close()

    def run(self):
        accounts = get_files(self.cookie_dir, file_type='json')
        file_dirs = {dir_name: get_files(os.path.join(self.file_dir, dir_name), file_type='jpeg') for dir_name in
                     os.listdir(self.file_dir)}
        for cookie_file in accounts:
            account = os.path.basename(cookie_file).split('.')[0]
            self.cookie_file = cookie_file
            self.init_browser()
            for index, (dir_name, dir_path) in enumerate(file_dirs.items(), start=1):
                if index > 75: break  # 每个账号每天上传有限制
                try:
                    self.upload(dir_name, dir_path, account, index)
                except Exception as e:
                    logger.error(f"上传失败序号{index}：账号{account},上传目录{dir_name},错误信息{e}")
            logger.info(f"账号{account}上传完成")
            self.p.stop()


if __name__ == '__main__':
    Program(
        cookie_dir=os.path.join(os.path.dirname(__file__), 'cookies'),
        file_dir=os.path.join(os.path.dirname(__file__), '图文汇总'),
    ).run()
