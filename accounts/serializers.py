from rest_framework import serializers
from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'phone',
            'nom',
            'alias',
            'email',
            'option',
            'is_super_admin',
            'is_staff',
        ]

