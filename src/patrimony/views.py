from rest_framework import viewsets
from patrimony.serializers import (
    PatrimonySerializer,
    ActiveSerializer,
    ActiveManagerSerializer,
    ActiveTypeSerializer,
    ArrearageSerializer,
    RealEstateSerializer,
    CompanyParticipationSerializer,
    EquipmentSerializer,
    LifeInsuranceSerializer,
    IncomeSerializer,
)

from patrimony.models import (
    Patrimony,
    ActiveType,
    Active,
    ActiveManager,
    Arrearage,
    RealEstate,
    CompanyParticipation,
    Equipment,
    LifeInsurance,
    Income,
)


class PatrimonyViewSet(viewsets.ModelViewSet):
    serializer_class = PatrimonySerializer
    queryset = Patrimony.objects.all()


class ActiveManagerViewSet(viewsets.ModelViewSet):
    serializer_class = ActiveManagerSerializer
    queryset = ActiveManager.objects.all()


class ActiveTypeViewSet(viewsets.ModelViewSet):
    serializer_class = ActiveTypeSerializer
    queryset = ActiveType.objects.all()


class ActiveViewSet(viewsets.ModelViewSet):
    serializer_class = ActiveSerializer
    queryset = Active.objects.all()


class ArrearageViewSet(viewsets.ModelViewSet):
    serializer_class = ArrearageSerializer
    queryset = Arrearage.objects.all()


class RealEstateViewSet(viewsets.ModelViewSet):
    serializer_class = RealEstateSerializer
    queryset = RealEstate.objects.all()


class CompanyParticipationViewSet(viewsets.ModelViewSet):
    serializer_class = CompanyParticipationSerializer
    queryset = CompanyParticipation.objects.all()


class EquipmentViewSet(viewsets.ModelViewSet):
    serializer_class = EquipmentSerializer
    queryset = Equipment.objects.all()


class LifeInsuranceViewSet(viewsets.ModelViewSet):
    serializer_class = LifeInsuranceSerializer
    queryset = LifeInsurance.objects.all()


class IncomeViewSet(viewsets.ModelViewSet):
    serializer_class = IncomeSerializer
    queryset = Income.objects.all()
