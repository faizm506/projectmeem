from .cart import Cart


def cart(request):
    try:
        return {"cart_count": len(Cart(request))}
    except Exception:
        return {"cart_count": 0}
