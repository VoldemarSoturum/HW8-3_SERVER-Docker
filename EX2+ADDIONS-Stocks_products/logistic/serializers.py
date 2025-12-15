from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Product, Stock, StockProduct


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "title", "description"]


class StockProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockProduct
        fields = ["product", "quantity", "price"]


class StockSerializer(serializers.ModelSerializer):
    # В ответе показываем позиции/товары через методы (с возможной фильтрацией ?products=<id>)
    positions = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()

    class Meta:
        model = Stock
        fields = ["id", "address", "positions", "products"]

    # ---------- helpers ----------

    def _resolve_product(self, value: object) -> Product:
        """
        Принимает либо экземпляр Product, либо его id.
        Возвращает Product или бросает ValidationError.
        """
        if isinstance(value, Product):
            return value
        try:
            return Product.objects.get(pk=int(value))
        except (TypeError, ValueError, ObjectDoesNotExist):
            raise ValidationError({"product": f"Invalid product id: {value}"})

    # ---------- read fields ----------

    def get_products(self, obj):
        pid = self.context.get("filter_product_id")
        qs = obj.products.all()  # M2M из модели Stock
        if pid:
            qs = qs.filter(pk=int(pid))
        return ProductSerializer(qs, many=True).data

    def get_positions(self, obj):
        """
        Возвращаем позиции склада. Если передан ?products=<id>,
        оставляем только позиции по этому продукту.
        """
        pid = self.context.get("filter_product_id")
        qs = obj.positions.all()  # related_name='positions' у StockProduct.stock
        if pid:
            qs = qs.filter(product_id=int(pid))
        return StockProductSerializer(qs, many=True).data

    # ---------- write (create/update) ----------

    @transaction.atomic
    def create(self, validated_data):
        # Берём «сырой» список позиций из входящих данных, чтобы стабильно получить id-значения.
        positions_data = self.initial_data.get("positions", [])
        stock = Stock.objects.create(address=validated_data.get("address", ""))

        bulk = []
        for pos in positions_data:
            product = self._resolve_product(pos.get("product"))
            bulk.append(
                StockProduct(
                    stock=stock,
                    product=product,
                    quantity=pos.get("quantity", 0),
                    price=pos.get("price", 0),
                )
            )
        if bulk:
            StockProduct.objects.bulk_create(bulk)
        return stock

    @transaction.atomic
    def update(self, instance, validated_data):
        # Аналогично create — читаем позиции из initial_data.
        positions_data = self.initial_data.get("positions", None)

        # Обновляем простые поля склада
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Если в запросе передали ключ positions — синхронизируем
        if positions_data is not None:
            incoming_ids = set()

            for pos in positions_data:
                product = self._resolve_product(pos.get("product"))
                incoming_ids.add(product.id)

                StockProduct.objects.update_or_create(
                    stock=instance,
                    product=product,
                    defaults={
                        "quantity": pos.get("quantity", 0),
                        "price": pos.get("price", 0),
                    },
                )

            # Удаляем позиции, которых не было в запросе
            StockProduct.objects.filter(stock=instance).exclude(
                product_id__in=incoming_ids
            ).delete()

        return instance
