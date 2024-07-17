import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Union


class FileUploadTracker:
    def __init__(self, db_name: str = 'file_uploads.db'):
        temp_dir = Path.cwd() / '.tmp'
        temp_dir.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(str(temp_dir / db_name))  # 连接到数据库
        self.cursor = self.conn.cursor()  # 获取游标
        self._create_table()  # 创建表格

    def _create_table(self):
        '''
        创建文件上传表格
        '''
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                upload_time TIMESTAMP NOT NULL,
                status TEXT NOT NULL
            )
        ''')
        self.conn.commit()  # 提交事务

    def add_file(self, filename: str, status: str = 'uploaded') -> int:
        upload_time = datetime.now().isoformat()
        # 向文件上传表格中插入数据
        self.cursor.execute('''
            INSERT INTO file_uploads (filename, upload_time, status)
            VALUES (?, ?, ?)
        ''', (filename, upload_time, status))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_file(self, filename: str) -> Union[Dict, None]:
        '''
        获取文件信息
        '''
        self.cursor.execute('SELECT * FROM file_uploads WHERE filename = ?', (filename,))
        result = self.cursor.fetchone()
        if result:
            return {
                'id': result[0],
                'filename': result[1],
                'upload_time': result[2],
                'status': result[3]
            }
        return None

    def update_file(self, filename: str, status: str) -> bool:
        self.cursor.execute('''
            UPDATE file_uploads
            SET status = ?
            WHERE filename = ?
        ''', (status, filename))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def delete_file(self, filename: str) -> bool:
        self.cursor.execute('DELETE FROM file_uploads WHERE filename = ?', (filename,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def list_files(self) -> List[Dict]:
        self.cursor.execute('SELECT * FROM file_uploads')
        return [
            {
                'id': row[0],
                'filename': row[1],
                'upload_time': row[2],
                'status': row[3]
            }
            for row in self.cursor.fetchall()
        ]

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 使用示例
if __name__ == '__main__':
    with FileUploadTracker() as tracker:
        filename = 'example.txt'
        # 添加文件
        file_id = tracker.add_file(filename)
        print(f"Added file with ID: {file_id}")

        # 获取文件信息
        file_info = tracker.get_file(filename)
        print(f"File info: {file_info}")

        # 更新文件状态
        updated = tracker.update_file(filename, 'processed')
        print(f"File updated: {updated}")

        # 列出所有文件
        all_files = tracker.list_files()
        print(f"All files: {all_files}")

        # 删除文件
        deleted = tracker.delete_file(filename)
        print(f"File deleted: {deleted}")

        # 列出所有文件
        all_files = tracker.list_files()
        print(f"All files: {all_files}")