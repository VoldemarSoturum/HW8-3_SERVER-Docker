from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Product, Stock, StockProduct


class ProductAPITests(APITestCase):
    """
    Тесты CRUD и поиска для Product.
    Ожидается, что в проектных urls есть префикс 'api/v1/',
    а router зарегистрирован с basename='product' и 'stock'.
    """

    def setUp(self):
        # немного данных для поиска
        self.tomato = Product.objects.create(title="Помидор черри", description="Свежие мини-помидоры для салатов")
        self.cucumber = Product.objects.create(title="Огурец длинный", description="Хрустящий, отличный для салатов с помидорами")
        self.basil = Product.objects.create(title="Базилик", description="Травяной аромат, сочетается с томатами (помидорами)")

    def test_product_list(self):
        url = reverse("product-list")  # /api/v1/products/
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(res.data["count"], 3)

    def test_product_create_retrieve_update_delete(self):
        # CREATE
        url_list = reverse("product-list")
        payload = {"title": "Помидор", "description": "Лучшие помидоры на рынке"}
        res = self.client.post(url_list, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        pid = res.data["id"]

        # RETRIEVE
        url_detail = reverse("product-detail", args=[pid])
        res = self.client.get(url_detail)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], "Помидор")

        # UPDATE (PATCH)
        res = self.client.patch(url_detail, {"description": "Самые сочные и ароматные помидорки"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("ароматные", res.data["description"])

        # DELETE
        res = self.client.delete(url_detail)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(pk=pid).exists())

    def test_product_search_by_title_and_description(self):
        url = reverse("product-list")
        # ?search=помидор — ожидаем все продукты, где "помидор" встречается в title ИЛИ description
        res = self.client.get(url, {"search": "помидор"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        titles = [item["title"] for item in res.data["results"]]
        # Должно включать "Помидор черри", и другие, где слово в описании
        self.assertIn(self.tomato.title, titles)
        self.assertIn(self.cucumber.title, titles)
        self.assertIn(self.basil.title, titles)


class StockAPITests(APITestCase):
    """
    Тесты для складов: создание с позициями, обновление позиций (upsert), фильтрация по продукту.
    Предполагается сериализатор с:
      - positions = SerializerMethodField() (фильтруется по ?products=...)
      - products  = SerializerMethodField() (фильтруется по ?products=...)
    и вьюха, пробрасывающая filter_product_id через get_serializer_context.
    """

    def setUp(self):
        # Продукты для позиций
        self.p2 = Product.objects.create(title="Помидор черри", description="Свежие мини-помидоры для салатов")
        self.p3 = Product.objects.create(title="Огурец длинный", description="Хрустящий, отличный для салатов с помидорами")

        self.stock_list_url = reverse("stock-list")  # /api/v1/stocks/

    def _create_stock(self):
        payload = {
            "address": "мой адрес не дом и не улица, мой адрес сегодня такой: www.ленинград-спб.ru3",
            "positions": [
                {"product": self.p2.id, "quantity": 250, "price": "120.50"},
                {"product": self.p3.id, "quantity": 100, "price": "180.00"},
            ],
        }
        res = self.client.post(self.stock_list_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        return res.data["id"]

    def test_create_stock_with_positions_and_read(self):
        sid = self._create_stock()

        # Проверим, что склад создан и позиции записаны
        detail_url = reverse("stock-detail", args=[sid])
        res = self.client.get(detail_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # По умолчанию (без ?products=) методные поля могут вернуть все позиции/продукты
        # В зависимости от твоей реализации, здесь может быть либо все позиции,
        # либо только products без positions — адаптируй assert под свою выдачу.
        # Предположим, что без фильтра возвращаем все позиции:
        pos = res.data.get("positions", [])
        self.assertGreaterEqual(len(pos), 2)
        self.assertTrue(StockProduct.objects.filter(stock_id=sid, product=self.p2).exists())
        self.assertTrue(StockProduct.objects.filter(stock_id=sid, product=self.p3).exists())

    def test_update_stock_positions_upsert_and_remove_missing(self):
        sid = self._create_stock()
        detail_url = reverse("stock-detail", args=[sid])

        # PATCH: обновим количество и цену для p2 + заменим p3 на p2/p3 с новыми значениями,
        # и добавим нового здесь не будем; при этом позиции, которых нет в запросе, должны удалиться.
        payload = {
            "positions": [
                {"product": self.p2.id, "quantity": 100, "price": "130.80"},
                {"product": self.p3.id, "quantity": 243, "price": "145.00"},
            ]
        }
        res = self.client.patch(detail_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Проверим upsert
        sp2 = StockProduct.objects.get(stock_id=sid, product=self.p2)
        sp3 = StockProduct.objects.get(stock_id=sid, product=self.p3)
        self.assertEqual(sp2.quantity, 100)
        self.assertEqual(str(sp2.price), "130.80")
        self.assertEqual(sp3.quantity, 243)
        self.assertEqual(str(sp3.price), "145.00")

        # А если теперь отправим только p2 — p3 должна удалиться
        payload2 = {"positions": [{"product": self.p2.id, "quantity": 1, "price": "10.00"}]}
        res2 = self.client.patch(detail_url, payload2, format="json")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

        self.assertTrue(StockProduct.objects.filter(stock_id=sid, product=self.p2).exists())
        self.assertFalse(StockProduct.objects.filter(stock_id=sid, product=self.p3).exists())

    def test_filter_stocks_by_product_and_response_contains_only_that_product(self):
        sid = self._create_stock()

        # Фильтруем списком: ?products=<id>
        res = self.client.get(self.stock_list_url, {"products": self.p2.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        stock = res.data["results"][0]

        # Проверяем, что serializer отфильтровал products и positions по p2
        products = stock.get("products", [])
        positions = stock.get("positions", [])

        # В products — только p2
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["id"], self.p2.id)

        # В positions — только p2
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]["product"], self.p2.id)
