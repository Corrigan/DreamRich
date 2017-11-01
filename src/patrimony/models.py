from django.db import models
from django.db.models import Sum
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
from django.contrib.contenttypes.fields import GenericRelation
import abc
from lib.financial_planning.flow import (
    generic_flow,
    create_array_change_annual,
)
import patrimony.validators as patrimony_validators
from patrimony.choices import AMORTIZATION_CHOICES


class Patrimony(models.Model):
    fgts = models.FloatField(default=0)

    def current_net_investment(self):
        total_active = self.active_set.all().aggregate(Sum('value'))
        total_arrearage = self.arrearage_set.filter(period__lte=2).aggregate(
                                                                Sum('value'))
        total = ((total_active['value__sum'] or 0)
                 - (total_arrearage['value__sum'] or 0))

        return total

    def current_property_investment(self):
        non_salable_total = self.realestate_set.filter(
            salable=False).aggregate(Sum('value'))
        non_salable_total = (non_salable_total['value__sum'] or 0)

        return non_salable_total

    def possible_income_generation(self):
        total_company_participation = self.companyparticipation_set.all(
        ).aggregate(Sum('value'))
        total_equipment = self.equipment_set.all().aggregate(Sum('value'))
        total = (total_company_participation['value__sum'] or 0) + \
            (total_equipment['value__sum'] or 0) + self.fgts

        return total

    def total_annual_income(self):
        total = 0
        incomes = list(self.income_set.all())

        for income in incomes:
            total += income.annual()

        return total

    def income_flow(self):
        income_changes = self.flowunitchange_set.all()
        duration = self.financialplanning.duration()
        array_change = create_array_change_annual(income_changes, duration,
                                                  self.financialplanning.\
                                                        init_year)
        total = self.total_annual_income()
        data = generic_flow(array_change, duration, total)

        return data

    def current_none_investment(self):
        total_movable_property = self.movableproperty_set.all().aggregate(
            Sum('value'))
        total_movable_property = (total_movable_property['value__sum'] or 0)
        salable_total = self.realestate_set.filter(
            salable=True).aggregate(Sum('value'))
        salable_total = (salable_total['value__sum'] or 0)

        total = total_movable_property + salable_total
        return total


class ActiveType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return "{}".format(self.name)


class Active(models.Model):
    name = models.CharField(max_length=100)
    value = models.FloatField(default=0)
    rate = models.FloatField(default=0)

    patrimony = models.ForeignKey(Patrimony, on_delete=models.CASCADE)
    active_type = models.ForeignKey(ActiveType, on_delete=models.CASCADE)

    def __str__(self):
        return "{name} {value}".format(**self.__dict__)


class ArrearageCalculator(models.Model):

    @property
    def calculate_arrearage(self):
        data = []
        outstanding_balance = self.calculate.value
        for period in range(1, self.calculate.period+1):
            outstanding_balance = outstanding_balance - self.calculate_amortization(period)
            parameter_list = {
                'period': period,
                'provision': self.calculate_provision(period),
                'interest': self.calculate_interest(period),
                'amortization': self.calculate_amortization(period),
                'outstanding_balance': outstanding_balance
            }
            data.append(parameter_list)

        return data

    def calculate_interest(self, period):
        interest = 0
        if self.calculate.amortization_system == AMORTIZATION_CHOICES[0][0]:
            interest = (
                (self.calculate.value -
                 (((period - 1)*self.calculate.value)/self.calculate.period)) *
                (self.calculate.rate/100)
            )
        else:
            interest = self.calculate_provision(period) - self.calculate_amortization(period)
        return interest

    def calculate_amortization(self, period):
        amortization = 0
        if self.calculate.amortization_system == AMORTIZATION_CHOICES[0][0]:
            amortization = self.calculate.value/self.calculate.period
        else:
            first_amortization = (
                self.calculate_provision(1) -
                (self.calculate.value*(self.calculate.rate/100))
            )
            amortization = first_amortization * ((1+(self.calculate.rate/100))**(period - 1))
        return amortization

    def calculate_provision(self, period):
        provision = 0
        if self.calculate.amortization_system == AMORTIZATION_CHOICES[0][0]:
            provision = (
                self.calculate_amortization(period) +
                self.calculate_interest(period)
            )
        else:
            provision = (
                self.calculate.value *
                ((self.calculate.rate/100) /
                 (1-(1+(self.calculate.rate/100))**(-self.calculate.period)))
            )
        return provision


class Arrearage(models.Model):
    name = models.CharField(max_length=100)
    value = models.FloatField(default=0)
    period = models.PositiveIntegerField(default=0)
    rate = models.FloatField(
        default=0,
        validators=[
            MinValueValidator(
                patrimony_validators.MIN_VALUE_RATE,
                "A taxa de juros não pode ser menor que 0%"
            ),
            MaxValueValidator(
                patrimony_validators.MAX_VALUE_RATE,
                "A taxa de juros não pode ser maior que 100%"
            )
        ]
    )
    amortization_system = models.CharField(
        max_length=5,
        choices=AMORTIZATION_CHOICES,
        default=AMORTIZATION_CHOICES[0][0]
    )
    patrimony = models.ForeignKey(Patrimony, on_delete=models.CASCADE)

    def __str__(self):
        return "{name} {value}".format(**self.__dict__)


class AmortizationStrategy(models.Model):

    arrearage = models.OneToOneField(
        Arrearage,
        related_name="%(class)s",
    )

    @property
    def calculate_arrearage(self):
        data = []
        outstanding_balance = self.calculate.value
        for period in range(1, self.calculate.period+1):
            outstanding_balance = (
                outstanding_balance -
                self.calculate_amortization(period)
            )
            parameter_list = {
                'period': period,
                'provision': self.calculate_provision(period),
                'interest': self.calculate_interest(period),
                'amortization': self.calculate_amortization(period),
                'outstanding_balance': outstanding_balance
            }
            data.append(parameter_list)

        return data

    @abc.abstractmethod
    def calculate_interest(self, period):
        pass

    @abc.abstractmethod
    def calculate_amortization(self, period):
        pass

    @abc.abstractmethod
    def calculate_provision(self, period):
        pass

    class Meta:
        abstract = True


class AmortizationSac(AmortizationStrategy):

    def calculate_interest(self, period):
        interest = (
            (self.calculate.value -
             (((period - 1)*self.calculate.value)/self.calculate.period)) *
            (self.calculate.rate/100)
        )
        return interest

    def calculate_amortization(self, period):
        amortization = self.calculate.value/self.calculate.period

        return amortization

    def calculate_provision(self, period):
        provision = (
            self.calculate_amortization(period) +
            self.calculate_interest(period)
        )
        return provision


class AmortizationPrice(AmortizationStrategy):

    def calculate_interest(self, period):
        interest = (
            self.calculate_provision(period) -
            self.calculate_amortization(period)
        )
        return interest

    def calculate_amortization(self, period):
        first_amortization = (
            self.calculate_provision(1) -
            (self.calculate.value*(self.calculate.rate/100))
        )
        amortization = (
            first_amortization *
            ((1+(self.calculate.rate/100))**(period - 1))
        )
        return amortization

    def calculate_provision(self, period):
        provision = (
            self.calculate.value *
            ((self.calculate.rate/100) /
             (1-(1+(self.calculate.rate/100))**(-self.calculate.period)))
        )
        return provision


class RealEstate(models.Model):
    name = models.CharField(max_length=100)
    value = models.FloatField(default=0)
    salable = models.BooleanField()
    patrimony = models.ForeignKey(Patrimony, on_delete=models.CASCADE)

    def __str__(self):
        return "{name} {value}".format(**self.__dict__)

class CompanyParticipation(models.Model):
    name = models.CharField(max_length=100)
    value = models.FloatField(default=0)
    patrimony = models.ForeignKey(Patrimony, on_delete=models.CASCADE)

    def __str__(self):
        return "{name} {value}".format(**self.__dict__)

class Equipment(models.Model):
    name = models.CharField(max_length=100)
    value = models.FloatField(default=0)
    patrimony = models.ForeignKey(Patrimony, on_delete=models.CASCADE)

    def __str__(self):
        return "{name} {value}".format(**self.__dict__)

class LifeInsurance(models.Model):
    name = models.CharField(max_length=100)
    value = models.FloatField(default=0)
    redeemable = models.BooleanField()
    patrimony = models.ForeignKey(Patrimony, on_delete=models.CASCADE)

    def __str__(self):
        return "{name} {value}".format(**self.__dict__)

class Income(models.Model):
    source = models.CharField(max_length=100)
    value_monthly = models.FloatField(default=0)
    thirteenth = models.BooleanField()
    vacation = models.BooleanField()
    patrimony = models.ForeignKey(Patrimony, on_delete=models.CASCADE)

    def annual(self):
        total = self.value_monthly * 12
        if self.thirteenth:
            total += self.value_monthly
        if self.vacation:
            total += self.value_monthly / 3

        return round(total, 2)

    def __str__(self):
        return "Annual({}) {}".format(self.source, self.annual())