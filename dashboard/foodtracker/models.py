from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    def __str__(self):
        return f'{self.username}'

class UserCalories(models.Model):
    username = models.CharField(max_length=200,default="~")
    calories = models.IntegerField(default=0)
    fats = models.IntegerField(default=0)
    carbohydrates = models.IntegerField(default=0)
    proteins = models.IntegerField(default=0)
    def __str__(self):
        return f'{self.calories}'

class FoodCategory(models.Model):
    category_name = models.CharField(max_length=50)

    class Meta:
        verbose_name = 'Food Category'
        verbose_name_plural = 'Food Categories'

    def __str__(self):
        return f'{self.category_name}'

    @property
    def count_food_by_category(self):
        return Food.objects.filter(category=self).count()


class Food(models.Model):
    food_name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=7, decimal_places=2, default=100.00)
    calories = models.IntegerField(default=0)
    fat = models.DecimalField(max_digits=7, decimal_places=2)
    carbohydrates = models.DecimalField(max_digits=7, decimal_places=2)
    protein = models.DecimalField(max_digits=7, decimal_places=2)
    category = models.ForeignKey(FoodCategory, on_delete=models.CASCADE, related_name='food_category')

    def __str__(self):
        return f'{self.food_name} - category: {self.category}'

class Coaches(models.Model):
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=128)
    def __str__(self):
        return f'{self.name} - type : {self.type}'

class CoachDP(models.Model):
    coach = models.ForeignKey(Coaches, on_delete=models.CASCADE,related_name='get_images')
    image = models.ImageField(upload_to='images/coaches')
    def __str__(self):
        return f'{self.image}'

class Image(models.Model):
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='get_images')
    image = models.ImageField(upload_to='images/')

    def __str__(self):
        return f'{self.image}'


class FoodLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food_consumed = models.ForeignKey(Food, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Food Log'
        verbose_name_plural = 'Food Log'

    def __str__(self):
        return f'{self.user.username} - {self.food_consumed.food_name}'


class Weight(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=7, decimal_places=2)
    entry_date = models.DateField()

    class Meta:
        verbose_name = 'Weight'
        verbose_name_plural = 'Weight'

    def __str__(self):
        return f'{self.user.username} - {self.weight} kg on {self.entry_date}'

class Premium(models.Model):
    user = models.CharField(max_length=200,default="~")
    ispremium = models.IntegerField(default=0)
    def __str__(self):
        return f'{self.ispremium}'
