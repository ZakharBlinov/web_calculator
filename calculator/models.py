from django.db import models
from django.contrib.auth.models import User
import json

class Calculation(models.Model):
    OPERATION_CHOICES = [
        ('add', 'Сложение'),
        ('subtract', 'Вычитание'),
        ('multiply', 'Умножение'),
        ('divide', 'Деление'),
        ('power', 'Возведение в степень'),
        ('sqrt', 'Квадратный корень'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calculations')
    num1 = models.FloatField()
    num2 = models.FloatField(null=True, blank=True)
    operation = models.CharField(max_length=20, choices=OPERATION_CHOICES)
    result = models.FloatField()
    expression = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.expression} = {self.result}"
    
    def save(self, *args, **kwargs):
        operation_symbols = {
            'add': '+',
            'subtract': '-',
            'multiply': '*',
            'divide': '/',
            'power': '^',
            'sqrt': '√'
        }
        
        symbol = operation_symbols.get(self.operation, '?')
        if self.operation == 'sqrt':
            self.expression = f"{symbol}({self.num1})"
        else:
            self.expression = f"{self.num1} {symbol} {self.num2}"
        
        super().save(*args, **kwargs)