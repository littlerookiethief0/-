import os


def get_files(directory, file_type='json'):
    """
    根据文件类型，获取目录下所有文件，自动排序
    """
    file_list = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(file_type):
                file_list.append(os.path.join(root, file))
    return sorted(file_list)
