# 一、项目说明get_info文件夹下

- 1.172号卡平台.py使用requests、pyquery、sqlalchemy、pandas将获取数据，增量爬虫，存储到mysql数据库中。

- 2.gen_markdown.py读取mysql，转存pandas的dataframe，生成markdown文件。

- 3.使用typora将markdwon文件导入typora，导出为pdf。

- 4.pdf_to_imgs.py将pdf转存为图片，并按顺序排列。

# 二、抖音上传:

- 使用tenacity做报错重试
- 使用sqlite3做本地缓存，避免重复上传
- 使用playwright做上传图文
- 支持多账号循环登录上传

- 1.get_cookie.py，通过扫码登录抖音，获取抖音的cookie，存储到cookies目录下。

- 2.deleter.py，删除抖音的视频。删除账号下的所有作品，死循环，直到删除干净，报错退出。

- 3.img_upload.py，上传图片到抖音。

# 三、API：

- file_handle.py，文件处理相关接口
- record.py 使用sqlite3做本地缓存，避免重复上传
- 邮箱接口.py  smtplib发送邮件，有自己的qq邮箱授权码以及邮箱，没有上传。