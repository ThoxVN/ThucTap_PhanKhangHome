class Product:
    product_id = "Unknown"
    support = 0.0
    revenue = 0.0
    type = "Unknown"

    def __int__(self, product_id, support, revenue):
        self.product_id = product_id
        self.support = support
        self.revenue = revenue

    def set_product_id(self, product_id):
        self.product_id = product_id

    def set_support(self, support):
        self.support = support

    def set_revenue(self, revenue):
        self.revenue = revenue

    def set_type(self, type):
        self.type = type



    def to_dict(self):
        return {
            "product_id": self.product_id,
            "support": self.support,
            "revenue": self.revenue,
            "type": self.type
        }
