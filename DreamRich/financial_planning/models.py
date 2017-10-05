from django.db import models
from client.models import ActiveClient
from patrimony.models import Patrimony
from goal.models import GoalManager
from lib.financial_planning.flow import generic_flow
from lib.profit.profit import actual_rate
import datetime
import numpy


class FinancialIndependence(models.Model):
    age = models.PositiveSmallIntegerField()
    duration_of_usufruct = models.PositiveSmallIntegerField()
    remain_patrimony = models.PositiveIntegerField()

    def assets_required(self):
        rate = float(self.financialplanning.real_gain())

        return numpy.pv(rate, self.duration_of_usufruct,
                        -self.remain_patrimony*12)

    def remain_necessary_for_retirement(self):
        assets_required = -self.assets_required()
        rate = 0.0544
        years_for_retirement = self.financialplanning.duration()
        current_net_investment = float(self.financialplanning.patrimony.\
                                      current_net_investment())
        total =  numpy.pmt(rate, years_for_retirement, current_net_investment,
                           assets_required)
        total /= 12
        if total < 0:
            total = 0

        return total


class RegularCost(models.Model):

    home = models.DecimalField(decimal_places=2, max_digits=8, default=0)
    electricity_bill = models.DecimalField(decimal_places=2, max_digits=8,
                                           default=0)
    gym = models.DecimalField(decimal_places=2, max_digits=8, default=0)
    taxes = models.DecimalField(decimal_places=2, max_digits=8, default=0)
    car_gas = models.DecimalField(decimal_places=2, max_digits=8, default=0)

    insurance = models.DecimalField(decimal_places=2, max_digits=8, default=0)
    cellphone = models.DecimalField(decimal_places=2, max_digits=8, default=0)
    health_insurance = models.DecimalField(decimal_places=2, max_digits=8,
                                           default=0)
    supermarket = models.DecimalField(decimal_places=2, max_digits=8,
                                      default=0)
    housekeeper = models.DecimalField(decimal_places=2, max_digits=8,
                                      default=0)
    beauty = models.DecimalField(decimal_places=2, max_digits=8, default=0)
    internet = models.DecimalField(decimal_places=2, max_digits=8, default=0)
    netflix = models.DecimalField(decimal_places=2, max_digits=8, default=0)
    recreation = models.DecimalField(decimal_places=2, max_digits=8, default=0)
    meals = models.DecimalField(decimal_places=2, max_digits=8, default=0)
    appointments = models.DecimalField(
        decimal_places=2, max_digits=8, default=0)  # consultas
    drugstore = models.DecimalField(decimal_places=2, max_digits=8, default=0)
    extras = models.DecimalField(decimal_places=2, max_digits=8, default=0)

    def total(self):
        total = self.home + self.electricity_bill + self.gym + self.taxes \
            + self.car_gas + self.insurance + self.cellphone \
            + self.health_insurance + self.supermarket + self.housekeeper \
            + self.beauty + self.internet + self.netflix + self.recreation \
            + self.meals + self.appointments + self.drugstore + self.extras

        return total

    def flow(self, regular_cost_change):
        duration = self.financialplanning.duration()
        total = self.total()
        data = generic_flow(regular_cost_change, duration, total)

        return data


class FinancialPlanning(models.Model):

    active_client = models.OneToOneField(
        ActiveClient,
        on_delete=models.CASCADE,
        primary_key=True,
    )

    patrimony = models.OneToOneField(
        Patrimony,
        on_delete=models.CASCADE,
    )

    financial_independence = models.OneToOneField(
        FinancialIndependence,
        on_delete=models.CASCADE,
    )

    goal_manager = models.OneToOneField(
        GoalManager,
        on_delete=models.CASCADE,
    )

    regular_cost = models.OneToOneField(
        RegularCost,
        on_delete=models.CASCADE
    )

    cdi = models.DecimalField(max_digits=6, decimal_places=4)

    ipca = models.DecimalField(max_digits=6, decimal_places=4)

    def duration(self):
        age_of_independence = self.financial_independence.age
        actual_year = datetime.datetime.now().year
        birthday_year = self.active_client.birthday.year
        actual_age = actual_year - birthday_year
        duration = age_of_independence - actual_age

        return duration

    def real_gain(self):
        return actual_rate(self.cdi, self.ipca)
