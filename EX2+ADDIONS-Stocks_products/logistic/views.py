from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, Stock
from .serializers import ProductSerializer, StockSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    Полный CRUD по товарам + поиск по названию и описанию.
    """
    queryset = Product.objects.all().order_by("id")
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "description"]  # ?search=карандаш


class StockViewSet(viewsets.ModelViewSet):
    """
    Полный CRUD по складам.
    Поиск складов, на которых есть конкретный продукт, по его id:
    ?products=<id>
    (работает благодаря filterset_fields=['products'] и M2M Stock.products)
    Дополнительно оставим поиск по адресу и названию товара.
    """
    queryset = Stock.objects.all().order_by("id")
    serializer_class = StockSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # поиск складов по продукту (id)
    filterset_fields = ["products"]        # /api/stocks/?products=1

    # удобный поиск
    search_fields = ["address", "products__title"]  # /api/stocks/?search=карандаш

    # сортировка (опционально)
    ordering_fields = ["id", "address"]
    ordering = ["id"]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["filter_product_id"] = self.request.query_params.get("products")
        return ctx