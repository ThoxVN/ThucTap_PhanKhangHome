import json
import os
import numpy as np
import pandas as pd
from flask import Flask



app = Flask(__name__)
app.config['ALLOWED_EXTENSIONS'] = {'csv'}
def save_to_file(data, file_path):
    """Lưu dữ liệu vào tệp JSON"""

    def convert_to_serializable(obj):
        """Chuyển đổi đối tượng không serializable thành kiểu dữ liệu chuẩn của JSON"""
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()  # Chuyển đổi NumPy numbers thành Python native types
        elif isinstance(obj, np.ndarray):
            return obj.tolist()  # Chuyển đổi NumPy arrays thành Python lists
        # Xử lý các kiểu dữ liệu khác tại đây nếu cần thiết
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4, default=convert_to_serializable)


def load_from_file(file_path):
    """Đọc dữ liệu từ tệp JSON"""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def read_data_csv(file_path, encoding='cp1252'):
    """Đọc dữ liệu từ file CSV"""
    return pd.read_csv(file_path, encoding=encoding)


def read_data_exl(file_path):
    return pd.read_excel(file_path)


def preprocess_data(df):
    return df[['store_delivery_code', 'product_code']]
