from rest_framework import serializers

from PlanningViewer.models import Werktijd


class WerktijdSerializers(serializers.ModelSerializer):
    class Meta:
        model = Werktijd
        fields = '__all__'