from rest_framework import serializers
from .models import Company, Role, User

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    # write-only: never serialized back out (would otherwise expose the hash via
    # fields='__all__'-style introspection); required only on create, so existing staff
    # can be edited (role/name/etc.) without needing to resupply a password each time.
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'company', 'role', 'role_name',
            'is_active', 'is_staff', 'is_superuser', 'date_joined', 'password',
        ]
        read_only_fields = ('date_joined', 'is_superuser')

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        if not password:
            raise serializers.ValidationError({'password': 'This field is required when creating a user.'})
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user 