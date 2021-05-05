from otree.api import Currency as c, currency_range
from . import *
from otree.api import Bot



class PlayerBot(Bot):
    def play_round(self):
        yield DecisionPage, dict(choice_1 = 1, choice_2 = 0, choice_3 = 1, choice_4 = 0, choice_5 = 0, choice_6 = 1, choice_7 = 0, choice_8 = 1, choice_9 = 1, choice_10 = 0)
