from rest_framework import serializers
from .models import Refugee

class RefugeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refugee
        fields = '__all__'
