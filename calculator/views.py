from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
import json
import math
from django.core.cache import cache

OPERATIONS = {
    'add': '+',
    'subtract': '-',
    'multiply': '*',
    'divide': '/',
    'power': '^',
    'sqrt': '√'
}

def get_history():
    history = cache.get('calculator_history')
    if not history:
        history = []
        cache.set('calculator_history', history)
    return history

def add_to_history(operation):
    history = get_history()
    history.insert(0, operation)
    if len(history) > 10:
        history = history[:10]
    cache.set('calculator_history', history)

def calculator_view(request):
    return render(request, 'calculator/calculator.html')

def calculate(request):
    if request.method == 'POST':
        try:
            num1 = float(request.POST.get('num1', 0))
            num2 = float(request.POST.get('num2', 0))
            operation = request.POST.get('operation')
            
            if operation == 'add':
                result = num1 + num2
                operation_symbol = '+'
            elif operation == 'subtract':
                result = num1 - num2
                operation_symbol = '-'
            elif operation == 'multiply':
                result = num1 * num2
                operation_symbol = '*'
            elif operation == 'divide':
                if num2 == 0:
                    return JsonResponse({'error': 'Деление на ноль невозможно'})
                result = num1 / num2
                operation_symbol = '/'
            elif operation == 'power':
                result = math.pow(num1, num2)
                operation_symbol = '^'
            elif operation == 'sqrt':
                if num1 < 0:
                    return JsonResponse({'error': 'Квадратный корень из отрицательного числа'})
                result = math.sqrt(num1)
                operation_symbol = '√'
            else:
                return JsonResponse({'error': 'Неверная операция'})
            
            history_entry = {
                'num1': num1,
                'num2': num2 if operation != 'sqrt' else None,
                'operation': operation_symbol,
                'result': round(result, 10),
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            add_to_history(history_entry)
            
            return JsonResponse({
                'result': round(result, 10),
                'operation': f"{num1} {operation_symbol} {num2 if operation != 'sqrt' else ''} = {round(result, 10)}"
            })
            
        except ValueError:
            return JsonResponse({'error': 'Некорректный ввод чисел'})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    
    return JsonResponse({'error': 'Метод не разрешен'})

def history_view(request):
    history = get_history()
    return render(request, 'calculator/history.html', {'history': history})

def clear_history(request):
    if request.method == 'POST':
        cache.set('calculator_history', [])
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Метод не разрешен'})