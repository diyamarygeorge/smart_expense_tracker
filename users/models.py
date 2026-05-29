from django.db import models
from django.contrib.auth.models import User


class Expense(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    item_name = models.CharField(
        max_length=100
    )

    category = models.CharField(
        max_length=50
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    expense_date = models.DateField()

    def __str__(self):
        return self.item_name