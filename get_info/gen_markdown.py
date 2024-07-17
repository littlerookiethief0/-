import pandas as pd

from sqlalchemy import create_engine, Table, MetaData, select, update
from sqlalchemy.engine.url import URL

from jinja2 import Environment, FileSystemLoader


def generate_one_markdown(rows, template_path, output_path):
    # 设置Jinja2环境
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template(template_path)

    # 使用模板渲染Markdown内容
    rendered_markdown = template.render(rows=rows)

    # 写入Markdown文件
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(rendered_markdown)


# 数据库配置
db_config = {
    'drivername': 'mysql+mysqlconnector',
    'username': 'root',
    'password': 'lizhuang',
    'host': 'localhost',
    'database': '流量卡推广'
}
db_config = db_config
engine = create_engine(URL.create(**db_config))  # 创建数据库引擎
df = pd.read_sql('SELECT * FROM 产品信息表_172', engine.connect())
rows = df.to_dict(orient='records')[:200]
print(len(rows))
# 定义变量
template_path = '推广模板.md'
output_path = '推广文章.md'
generate_one_markdown(rows, template_path, output_path)
