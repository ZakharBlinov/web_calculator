from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from rest_framework import status, permissions, generics, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt, csrf_protect, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.middleware.csrf import get_token
from .models import Calculation
from .serializers import UserSerializer, UserSerializerWithToken, CalculationSerializer
import math
from datetime import datetime, timedelta

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        data = request.data
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Имя пользователя и пароль обязательны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Пользователь с таким именем уже существует'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            login(request, user)
            
            refresh = RefreshToken.for_user(user)
            serializer = UserSerializerWithToken(user)
            
            response_data = serializer.data
            
            response = Response(response_data)
            
            response.set_cookie(
                'sessionid',
                request.session.session_key,
                httponly=True,
                max_age=60*60*24*7,
                samesite='Lax'
            )
            
            csrf_token = get_token(request)
            response.set_cookie(
                'csrftoken',
                csrf_token,
                httponly=False,
                max_age=60*60*24*7,
                samesite='Lax'
            )
            
            return response
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            refresh = RefreshToken.for_user(user)
            serializer = UserSerializerWithToken(user)
            
            response_data = serializer.data
            
            response = Response(response_data)
            
            response.set_cookie(
                'sessionid',
                request.session.session_key,
                httponly=True,
                max_age=60*60*24*7,
                samesite='Lax'
            )
            
            csrf_token = get_token(request)
            response.set_cookie(
                'csrftoken',
                csrf_token,
                httponly=False,
                max_age=60*60*24*7,
                samesite='Lax'
            )
            
            return response
        else:
            return Response(
                {'error': 'Неверное имя пользователя или пароль'},
                status=status.HTTP_401_UNAUTHORIZED
            )

@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        logout(request)
        response = Response({'message': 'Успешный выход из системы'})
        response.delete_cookie('sessionid')
        response.delete_cookie('csrftoken')
        return response

@method_decorator(ensure_csrf_cookie, name='dispatch')
class ProfileView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        if request.user.is_authenticated:
            serializer = UserSerializer(request.user, many=False)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Пользователь не авторизован'},
                status=status.HTTP_401_UNAUTHORIZED
            )

@method_decorator(csrf_exempt, name='dispatch')
class CalculateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Требуется авторизация'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            num1 = float(request.data.get('num1', 0))
            num2 = float(request.data.get('num2', 0))
            operation = request.data.get('operation')
            
            if operation == 'add':
                result = num1 + num2
            elif operation == 'subtract':
                result = num1 - num2
            elif operation == 'multiply':
                result = num1 * num2
            elif operation == 'divide':
                if num2 == 0:
                    return Response(
                        {'error': 'Деление на ноль невозможно'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                result = num1 / num2
            elif operation == 'power':
                result = math.pow(num1, num2)
            elif operation == 'sqrt':
                if num1 < 0:
                    return Response(
                        {'error': 'Квадратный корень из отрицательного числа'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                result = math.sqrt(num1)
                num2 = None
            else:
                return Response(
                    {'error': 'Неверная операция'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            calculation = Calculation.objects.create(
                user=request.user,
                num1=num1,
                num2=num2,
                operation=operation,
                result=round(result, 10)
            )
            
            serializer = CalculationSerializer(calculation)
            return Response({
                'result': round(result, 10),
                'calculation': serializer.data
            })
            
        except ValueError:
            return Response(
                {'error': 'Некорректный ввод чисел'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class CalculationListView(generics.ListAPIView):
    serializer_class = CalculationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['expression', 'operation']
    ordering_fields = ['created_at', 'result', 'num1', 'num2']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Calculation.objects.filter(user=user)
        
        operation = self.request.query_params.get('operation', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if operation:
            queryset = queryset.filter(operation=operation)
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(created_at__date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d')
                queryset = queryset.filter(created_at__date__lte=date_to)
            except ValueError:
                pass
        
        return queryset

class CalculationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CalculationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Calculation.objects.all()
        return Calculation.objects.filter(user=user)
    
    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            serializer.save(user=self.request.user)
        else:
            serializer.save()
    
    def perform_destroy(self, instance):
        if self.request.user.is_staff or instance.user == self.request.user:
            instance.delete()
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("У вас нет прав для удаления этой записи")

class AdminCalculationListView(generics.ListAPIView):
    serializer_class = CalculationSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['expression', 'operation', 'user__username']
    ordering_fields = ['created_at', 'result', 'user__username']
    
    def get_queryset(self):
        queryset = Calculation.objects.all()
        
        user_id = self.request.query_params.get('user_id', None)
        username = self.request.query_params.get('username', None)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        if username:
            queryset = queryset.filter(user__username__icontains=username)
        
        return queryset

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def statistics_view(request):
    user = request.user
    if user.is_staff:
        total_calculations = Calculation.objects.count()
        recent_calculations = Calculation.objects.order_by('-created_at')[:5]
    else:
        total_calculations = Calculation.objects.filter(user=user).count()
        recent_calculations = Calculation.objects.filter(user=user).order_by('-created_at')[:5]
    
    return Response({
        'total_calculations': total_calculations,
        'recent_calculations': CalculationSerializer(recent_calculations, many=True).data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_history(request):
    user = request.user
    if user.is_staff and request.data.get('all_users', False):
        Calculation.objects.all().delete()
        message = 'Вся история очищена'
    else:
        Calculation.objects.filter(user=user).delete()
        message = 'Ваша история очищена'
    
    return Response({'message': message})

@api_view(['GET'])
def get_csrf_token(request):
    return Response({'csrfToken': get_token(request)})

def calculator_view(request):
    return render(request, 'calculator/calculator.html')

def history_view(request):
    return render(request, 'calculator/history.html')

def admin_panel_view(request):
    return render(request, 'calculator/admin_panel.html')

def simple_calc_view(request):
    return render(request, 'calculator/simple_calc.html')

def debug_view(request):
    return render(request, 'calculator/debug.html')

def test_csrf_view(request):
    return render(request, 'calculator/test_csrf.html')