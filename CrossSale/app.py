# app.py
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import webbrowser

from save_load_data import load_from_file, save_to_file, allowed_file, read_data_csv
from algorithmData import (
    convert_to_binary_matrix, apply_apriori, find_association_rules, phanloaiSP)
from product import Product

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}
app.config['TRAINING_FILE'] = 'uploads/delivery_data.csv'
app.config['OLD_DATA'] = 'uploads/old_data.csv'
# Đường dẫn đến các tệp JSON
CURRENT_FREQUENT = 'uploads/current_frequent.json'
RULES_LIST_FILE = 'uploads/rules_list.json'


def frozenset_to_str(x):
    x = list(x)
    x = str(x).lstrip('[').rstrip(']').strip()
    return x


def calculate_revenue_all(frequent, delivery):
    for item in frequent:
        item['itemsets'] = frozenset_to_str(item['itemsets']).replace("'", "")  # Dinh dang lai id
        item['support'] = round(item['support'], 3)  # Lam tron so thap phan
        product_id = item['itemsets']
        item['revenue'] = calculate_revenue_product(delivery, product_id)
    return frequent


def calculate_revenue_product(DELIVERY, idSP):
    # Tính tổng doanh thu
    DELIVERY = DELIVERY[DELIVERY['product_code'] == idSP]
    return (DELIVERY['amount']).sum()


# Xu ly du lieu training
def training_data(delivery_data):
    df_basket = convert_to_binary_matrix(delivery_data)
    frequent_list = apply_apriori(df_basket)
    rules_list = find_association_rules(frequent_list)

    return frequent_list, rules_list


@app.route('/')
def index():
    """Trang chính"""
    frequent_list = load_from_file(CURRENT_FREQUENT)
    sorted_data = sorted(frequent_list, key=lambda x: x['revenue'], reverse=True)

    return render_template('index.html',
                           frequent_list=sorted_data[:15])


@app.route('/upload', methods=['POST'])
def upload_file():
    """Xử lý tệp tải lên và chèn dữ liệu vào cuối tệp hiện có"""
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'new_delivery_data.csv')
        # Mở tệp đích trong chế độ 'append' để chèn thêm dữ liệu
        with open(file_path, 'a') as f:
            f.write(file.stream.read().decode("utf-8"))  # Chèn nội dung của tệp mới vào cuối tệp hiện có
        return redirect(url_for('index'))
    return redirect(request.url)


@app.route('/active_process', methods=['POST'])
def active_process_auto():
    new_delivery = load_from_file('upload/new_delivery_data.csv')
    
    if len(new_delivery) > 2500:
        current_delivery = load_from_file(CURRENT_FREQUENT)
        update_data = pd.concat([current_delivery, new_delivery]) # type: ignore

        save_to_file(update_data, CURRENT_FREQUENT)
        pd.DataFrame().to_csv('upload/new_delivery_data.csv', index=False)

        process_data()
    else:
        return redirect(url_for('index'))  # Redirect to the index route
    
    return 'Process Completed'


@app.route('/process_index')
def open_process_index():
    return render_template('process.html')


@app.route('/process', methods=['POST'])
def process_data():
    """Xử lý dữ liệu training và hiển thị kết quả"""
    # Doc du lieu file
    current_data_path = app.config['TRAINING_FILE']
    if not os.path.exists(current_data_path):
        return "Current Delivery file not found!", 404
    current_delivery = read_data_csv(current_data_path)
    old_data_path = app.config['OLD_DATA']
    if not os.path.exists(old_data_path):
        return "Old Delivery file not found!", 404
    old_delivery = read_data_csv(old_data_path)

    # Đọc và xử lý dữ liệu
    current_frequent, current_rule = training_data(current_delivery)
    old_frequent, old_rule = training_data(old_delivery)

    # Convert du lieu Flagship va tinh doanh so tong
    current_frequent['revenue'] = 0
    current_frequent = current_frequent.to_dict(orient='records')
    current_frequent = calculate_revenue_all(current_frequent, current_delivery)

    old_frequent['revenue'] = 0
    old_frequent = old_frequent.to_dict(orient='records')
    old_frequent = calculate_revenue_all(old_frequent, old_delivery)

    # Chuyển đổi old_frequent thành một dictionary để tra cứu nhanh hơn
    old_frequent_dict = {item['itemsets']: item for item in old_frequent}

    # Tính toán và lưu trữ kết quả vào frequentlist
    long_term_weight = float(request.form['long-term-weight']) / 100
    frequentlist = []

    # Tao mang chung cho old_delivery va current_delivery
    for product in current_frequent:
        product_id = product['itemsets']
        if product_id in old_frequent_dict:
            old_product = old_frequent_dict[product_id]
            # Tính toán support và revenue
            support = old_product['support'] * long_term_weight + product['support'] * (1 - long_term_weight)
            revenue = old_product['revenue'] * long_term_weight + product['revenue'] * (1 - long_term_weight)
            # Tạo và thiết lập Product object
            temp = Product()
            temp.set_product_id(product_id)
            temp.set_support(support)
            temp.set_revenue(revenue)
            frequentlist.append(temp)
    # Chuyen du lieu cua mang sang json
    frequentlist_dict = [product.to_dict() for product in frequentlist]

    # Phan loai san pham
    frequentlist_dict = phanloaiSP(frequentlist_dict)
    save_to_file(frequentlist_dict, CURRENT_FREQUENT)
    # Convert du lieu cross sale
    current_rule = current_rule.to_dict(orient='records')
    cross_sale = []
    for rule in current_rule:
        rule['antecedents'] = frozenset_to_str(rule['antecedents']).replace("'", "")
        rule['consequents'] = frozenset_to_str(rule['consequents']).replace("'", "")
        rule['consequent support'] = round(rule['consequent support'], 3)
        rule['support'] = round(rule['support'], 3)
        rule['confidence'] = round(rule['confidence'], 3)

        # Chuyển sang dataframe để dễ tìm kiếm
        item = [i for i in frequentlist_dict if i['product_id'] == rule['consequents']]

        # Chon sanpham vo crosssale
        if item and item[0]['type'] != "A":
            rule['type'] = item[0]['type']
            cross_sale.append(rule)
    # Luu cac ket qua vao file
    save_to_file(cross_sale, RULES_LIST_FILE)
    return render_template('index.html',
                           frequent_list=frequentlist[:15])


@app.route('/cross_sale', methods=['POST'])
def cross_sale():
    product_id = request.form['product_id']
    cross_sale = load_from_file(RULES_LIST_FILE)
    list_product = []
    for product in cross_sale:
        if product_id == product['antecedents']:
            list_product.append(product)

    return render_template('cross_sale.html', cross_sale=list_product, product_id=product_id)


@app.route('/picture/<filename>')
def picture(filename):
    return send_from_directory(os.path.join(app.root_path, 'picture'), filename)


@app.route('/classifi_product', methods=['POST'])
def classifi_product():
    frequent_list = load_from_file(CURRENT_FREQUENT)
    product_type = request.form['product_type']
    arraydisplay = []
    for item in frequent_list:
        if item['type'] == product_type:
            arraydisplay.append(item)

    match product_type:
        case "A":
            type = "A"
            title = " Sản phẩm tần suất mua nhiều, doanh số cao "
        case "B":
            type = "B"
            title = "Sản phẩm tần suất mua ít, doanh số cao"
        case "C":
            type = "C"
            title = "Sản phẩm tần suất mua nhiều, doanh số thấp"
        case "D":
            type = "D"
            title = "Sản phẩm tần suất mua ít, doanh số thấp"
    return render_template('classifi_item.html', title=title, type = type,
                           arraydisplay=arraydisplay)


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    webbrowser.open('http://127.0.0.1:5000')
    app.run(debug=True, use_reloader=False)  # use_reloader=False để tránh mở nhiều tab
