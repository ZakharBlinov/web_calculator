from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Calculation
from rest_framework_simplejwt.tokens import RefreshToken

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

class UserSerializerWithToken(UserSerializer):
    token = serializers.SerializerMethodField(read_only=True)
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['token']
    
    def get_token(self, obj):
        refresh = RefreshToken.for_user(obj)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

class CalculationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    operation_display = serializers.CharField(source='get_operation_display', read_only=True)
    
    class Meta:
        model = Calculation
        fields = ['id', 'user', 'username', 'num1', 'num2', 'operation', 
                  'operation_display', 'result', 'expression', 'created_at']
        read_only_fields = ['user', 'result', 'expression', 'created_at']
    
    def validate(self, data):
        operation = data.get('operation')
        num2 = data.get('num2')
        
        if operation != 'sqrt' and num2 is None:
            raise serializers.ValidationError(
                {"num2": "Это поле обязательно для данной операции"})
        
        if operation == 'divide' and num2 == 0:
            raise serializers.ValidationError(
                {"num2": "Деление на ноль невозможно"})
        
        if operation == 'sqrt' and data.get('num1', 0) < 0:
            raise serializers.ValidationError(
                {"num1": "Квадратный корень из отрицательного числа невозможен"})
        
        return data