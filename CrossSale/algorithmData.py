from mlxtend.frequent_patterns import apriori, association_rules
import pandas as pd


def convert_to_binary_matrix(df_filtered):
    """Chuyển đổi dữ liệu thành bảng nhị phân"""
    df_basket = df_filtered.groupby(['store_delivery_code', 'product_code'])[
        'product_code'].count().unstack().reset_index().fillna(0).set_index('store_delivery_code')
    return df_basket.applymap(lambda x: 1 if x > 0 else 0)


def apply_apriori(df_basket, min_support=0.01):
    """Áp dụng thuật toán Apriori và trả về top N itemsets phổ biến nhất"""
    frequent_itemsets = apriori(df_basket, min_support=min_support, use_colnames=True)
    sorted_itemsets = frequent_itemsets.sort_values(by='support', ascending=False)
    return sorted_itemsets


def find_association_rules(frequent_itemsets, metric="lift", min_threshold=0):
    """Tìm các luật kết hợp và loại bỏ các dòng có support trùng nhau, giữ lại dòng có lift cao nhất"""
    # Tìm các luật kết hợp
    rules = association_rules(frequent_itemsets, metric=metric, min_threshold=min_threshold)
    sorted_rules = rules.sort_values(by='antecedent support', ascending=False)
    # unique_support_rules = sorted_rules.drop_duplicates(subset='support', keep='first')
    return sorted_rules.sort_values(by='confidence', ascending=False)


def count_products(df):
    df = pd.DataFrame(df)
    product_list = df.drop_duplicates(subset='product_code', keep='first')
    return len(product_list)


def tinhDoanhThuTB(FREQUENT_LIST):
    tongDoanhThu = 0.0
    total_product = 0
    for item in FREQUENT_LIST:
        if item['revenue'] > 1:
            total_product += 1
            tongDoanhThu += item['revenue']
    return tongDoanhThu / total_product


def tinhTanSuatTB(FREQUENT_LIST):
    tongTanSuat = 0.0
    total_product = 0
    for item in FREQUENT_LIST:
        if item['revenue'] > 1:
            total_product += 1
            tongTanSuat += item['support']
    return tongTanSuat / total_product


def phanloaiSP(FREQUENT_LIST):
    doanhthuTB = tinhDoanhThuTB(FREQUENT_LIST)
    tansuatTB = tinhTanSuatTB(FREQUENT_LIST)
    for product in FREQUENT_LIST:
        if (product['revenue'] > 0):
            if (product['revenue'] > doanhthuTB):
                if (product['support'] > tansuatTB):
                    product['type'] = "A"
                else:
                    product['type'] = "B"
            else:
                if (product['support'] > tansuatTB):
                    product['type'] = "C"
                else:
                    product['type'] = "D"

    return FREQUENT_LIST
