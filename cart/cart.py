"""Session cart. Stored as {product_id: quantity}. Prices are always read fresh from the database."""
from catalog.models import Product

SESSION_KEY = "cart"
MAX_QTY = 10


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.data = dict(self.session.get(SESSION_KEY, {}))

    def _save(self):
        self.session[SESSION_KEY] = self.data
        self.session.modified = True

    def add(self, product_id, qty=1):
        key = str(product_id)
        self.data[key] = min(self.data.get(key, 0) + qty, MAX_QTY)
        self._save()

    def set(self, product_id, qty):
        key = str(product_id)
        if qty <= 0:
            self.data.pop(key, None)
        else:
            self.data[key] = min(qty, MAX_QTY)
        self._save()

    def remove(self, product_id):
        self.data.pop(str(product_id), None)
        self._save()

    def clear(self):
        self.data = {}
        self._save()

    def __len__(self):
        return sum(self.data.values())

    def lines(self):
        """List of {product, qty, line_total} for products that are still on sale. Quantity is capped by stock."""
        ids = [int(k) for k in self.data]
        products = Product.objects.visible().filter(pk__in=ids).select_related("shop", "category")
        lines = []
        for p in products:
            qty = min(self.data.get(str(p.pk), 0), p.stock)
            if qty > 0:
                lines.append({"product": p, "qty": qty, "line_total": p.price_minor * qty})
        lines.sort(key=lambda line: line["product"].pk)
        return lines

    @staticmethod
    def subtotal(lines):
        return sum(line["line_total"] for line in lines)
