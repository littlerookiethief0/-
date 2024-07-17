import base64
import re
import json
import requests
import pandas as pd
from pyquery import PyQuery as pq
from sqlalchemy import create_engine, Table, MetaData, select, update
from sqlalchemy.engine.url import URL
import logging
from datetime import datetime


class Programe:
    def __init__(self, db_config):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Content-Type': 'application/json'
        }
        self.db_config = db_config  # 数据库配置
        self.engine = create_engine(URL.create(**db_config))  # 创建数据库引擎

        # 配置日志记录
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def common_verify(self, image, verify_type="10110"):
        _custom_url = "http://api.jfbym.com/api/YmServer/customApi"
        _token = "b-SkqpN3hVoR2syRpa2T_qlcMaFx559kIt3Axyxj158"
        payload = {
            "image": base64.b64encode(image).decode(),
            "token": _token,
            "type": verify_type
        }
        resp = requests.post(_custom_url, headers=self.headers, data=json.dumps(payload))
        return resp.json()['data']['data']

    def get_yzm(self):
        url = 'https://haokaapi.lot-ml.com/api/User/ImgCode'
        response = requests.get(url=url, headers=self.headers)
        img = re.findall(pattern=';base64,(.*?)",', string=response.text)[0]
        yzm = self.common_verify(base64.b64decode(img))
        return yzm

    def login(self, account_row):
        login_url = 'https://haokaapi.lot-ml.com/api/User/Login'
        login_data = {
            'UserName': account_row["账号"],
            'PassWord': account_row["密码"],
            'Code': self.get_yzm()  # 实际情况下这个验证码应该从验证码处理服务获取
        }
        response = requests.post(login_url, headers=self.headers, json=login_data)
        self.headers['Authorization'] = f'bearer {response.json()["data"]["token"]}'

    def get_product_details(self, productID):
        url = f'https://haokawx.lot-ml.com/PackInfo/Detail/{productID}'
        doc = pq(url=url)
        details = {
            "套餐简介": doc('body > div > div.m-1').text().replace('产品套餐：', ''),
            "优惠详情": doc('body > div > div:nth-child(5) > div').text(),
            "快递方式": doc('body > div > div:nth-child(6) > div').text(),
            "激活方式": doc('body > div > div:nth-child(7) > div').text(),
            "办卡年龄": doc('body > div > div:nth-child(9) > div').text(),
            "合约期": doc('body > div > div:nth-child(10) > div').text(),
            "不发货地区": doc('body > div > div:nth-child(11) > div').text(),
            "定向范围": doc('body > div > div:nth-child(12) > div').text(),
            "复机及注销方式": doc('body > div > div.m-5').text()
        }
        return details

    def get_info(self, account_row):
        self.login(account_row)
        url = 'https://haokaapi.lot-ml.com/api/Products/Query'
        params = {
            'page': 1,
            'limit': 500,
            'ProductName': '',
            'CommissionType': '',
            'Operator': '',
            'Area': ''
        }
        response = requests.get(url, headers=self.headers, params=params)
        data = response.json()['data']
        # 获取当前数据库中的 productID 列表
        with self.engine.connect() as connection:
            existing_data = pd.read_sql('SELECT productID FROM 产品信息表_172', connection)
            existing_ids = set(existing_data['productID'])

        # 过滤新增的数据
        new_data = [row for row in data if row["productID"] not in existing_ids]

        # 处理新增的数据
        for index, row in enumerate(new_data):
            try:
                row["详情链接"] = f'https://haokawx.lot-ml.com/PackInfo/Detail/{row["productID"]}'
                row["littlepicture"] = row["littlepicture"].rstrip('|')
                details = self.get_product_details(row["productID"])
                row.update(details)
                self.logger.info(f'一共是{len(new_data)}，正在处理第{index + 1}条数据。')
            except Exception as e:
                self.logger.error(f'处理第{index + 1}条数据时发生错误: {e}')

        # 写入数据库
        if new_data:
            self.write_to_db(new_data)

    def write_to_db(self, data):
        df = pd.DataFrame(data)
        df['插入时间'] = datetime.now().strftime('%Y-%m-%d')
        df.to_sql('产品信息表_172', con=self.engine, if_exists='append', index=False)
        self.logger.info(f'插入了{len(data)}条新数据。')

    def read_accounts_from_db(self):
        query = "SELECT * FROM 用户信息表 where 平台 = 'get_info'"
        df = pd.read_sql(query, self.engine)
        return df

    def run(self):
        df = self.read_accounts_from_db()
        for index, account_row in df.iterrows():
            account_row = dict(account_row)
            self.get_info(account_row)


if __name__ == '__main__':
    db_config = {
        'drivername': 'mysql+mysqlconnector',
        'username': 'root',
        'password': 'lizhuang',
        'host': 'localhost',
        'database': '流量卡推广'
    }
    Programe(db_config=db_config).run()
