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


class Budget(models.Model):

    # One overall monthly budget per user
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    monthly_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"{self.user.username} — ₹{self.monthly_limit}"


class CategoryBudget(models.Model):

    # Optional per-category monthly limit. A user has at most one row per category.
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    category = models.CharField(
        max_length=50
    )

    monthly_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    class Meta:
        # Prevent duplicate category rows for the same user
        unique_together = ('user', 'category')

    def __str__(self):
        return f"{self.user.username} — {self.category}: ₹{self.monthly_limit}"