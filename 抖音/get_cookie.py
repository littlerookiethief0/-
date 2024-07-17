import os
from playwright.sync_api import sync_playwright


class CreatorDouyin:
    def __init__(self, timeout: int):
        """
        初始化
        :param timeout: 等待时间，单位秒
        """
        self.timeout = timeout * 1000  # 转换为毫秒
        self.cookie_dir = self._create_cookie_directory()  # 创建存储 cookies 的目录

    def _create_cookie_directory(self):
        """
        创建用于存储 cookies 的目录
        """
        path = os.path.dirname(__file__) # 获取当前路径
        cookie_dir = os.path.join(path, "cookies")  # 拼接 cookies 目录路径
        os.makedirs(cookie_dir, exist_ok=True)  # 创建目录，若已存在则跳过
        return cookie_dir  # 返回 cookies 目录路径

    def _handle_login(self, playwright, douyin_id):
        """
        处理登录逻辑
        :param playwright: Playwright 实例
        :param douyin_id: 抖音号
        """
        # 启动浏览器并设置参数
        self.browser = playwright.chromium.launch(
            headless=False,
            chromium_sandbox=False,
            channel="chrome",
            ignore_default_args=["--enable-automation"],
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
        )
        # 创建浏览器上下文并设置参数
        self.context = self.browser.new_context(
            no_viewport=True,
            permissions=["geolocation"],  # 设置地理位置权限
            geolocation={"latitude": 30.2741, "longitude": 120.1551},  # 设置地理位置
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        # 创建新页面
        self.page = self.context.new_page()
        # 加载 stealth.min.js 脚本，隐藏自动化特征
        self.page.add_init_script(path=os.path.join(os.path.dirname(__file__), "stealth.min.js"))
        # 打开抖音创作者登录页面
        self.page.goto("https://creator.douyin.com/")

        try:
            # 等待跳转到创作者主页
            self.page.wait_for_url("https://creator.douyin.com/creator-micro/home", timeout=self.timeout)
            # 保存 cookies 到指定文件
            self.context.storage_state(path=os.path.join(self.cookie_dir, f'cookie_{douyin_id}.json'))
        except Exception as e:
            # 处理登录失败的情况
            print(f"{douyin_id} ——> 登录失败，本次操作不保存 cookies", e)

    def run(self):
        """
        运行主程序
        """
        while True:
            # 获取用户输入的抖音号
            douyin_id = input('请输入抖音号(输入 wq 退出):')
            if douyin_id == 'wq':
                break  # 输入 'wq' 退出循环
            with sync_playwright() as playwright:
                # 处理登录操作
                self._handle_login(playwright, douyin_id)


if __name__ == "__main__":
    # 初始化并运行程序
    CreatorDouyin(timeout=60).run()
