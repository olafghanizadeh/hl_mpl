import random
import numpy as np
from otree.api import *
from gettext import gettext

# Moved index function to separate file to keep this file cleaner
author = 'Olaf Ghanizadeh'
doc = """
A crude and simple implementation of the Holt/Laury(2002) lottery.
"""


def create_index(choices):
    global index
    index = [j for j in range(1, choices + 1)]
    return index


def make_fields(n):
    choice_list = []
    for i in range(1, n + 1):
        locals()['choice_' + str(i)] = models.IntegerField(
            choices=[0, 1], widget=widgets.RadioSelectHorizontal)
    return choice_list


def make_field():
    return models.IntegerField(
        choices=[0, 1],
        label="label",
        widget=widgets.RadioSelect,
    )


class Constants(BaseConstants):
    name_in_url = 'risk_lottery'
    players_per_group = None
    num_rounds = 1
    num_choices = 10
    # Defining Lottery Payoffs in a dict
    payoffs = {"A": [20, 16], "B": [38, 1]}
    index = create_index(num_choices)


class Subsession(BaseSubsession):
    """Creating the lottery subsessions"""


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    """The oTree class that generates the info PER PLAYER"""

    def test_function(self):

        return self.session.vars['num_choices']



    # Initiate fields to be populated by app
    choice_to_pay = models.StringField()
    option_chosen = models.IntegerField()
    option_chosen_letter = models.StringField()
    # Function to set payoffs for each player

    n = len(index)
    # Name Field
    # Generates the fields for the form fields. Necessary to call locals() to access correct scope. This should be
    # put in a function to improve code quality.
    for j in range(1, n + 1):
        locals()['choice_' + str(j)] = make_field()
    # Delete intermediate variables
    del j
    del n


# FUNCTIONS
def creating_session(subsession: Subsession):
    """Method to initiate a session"""
    # Set Constant num.choices to n for easier reuse
    print(subsession.session.config['num_choices'])
    global n
    n = subsession.session.config['num_choices']
    # Multiplier to test for incentive effects
    multiplier = subsession.session.config['multiplier']
    # Multiply payoffs by session.config.multiplier
    payoffs = {
        key: [i * multiplier for i in value]
        for (key, value) in Constants.payoffs.items()
    }
    # Store in session variables
    subsession.session.vars['payoffs'] = payoffs
    subsession.session.vars['index'] = index
    probs = [i / n for i in index]
    inverse_p = [1 - p for p in probs]
    subsession.session.vars['probs'] = probs
    subsession.session.vars['inverse_probs'] = inverse_p
    formatted_p = ["{0:.0f}".format(p * 100) + "%" for p in probs]
    formatted_inverse_p = ["{0:.0f}".format(p * 100) + "%" for p in inverse_p]
    form_fields = ['choice_' + str(k) for k in index]
    print(form_fields)
    choices = list(zip(index, form_fields, formatted_p, formatted_inverse_p))
    subsession.session.vars['choices'] = choices
    # Create lottery for each player
    for p in subsession.get_players():
        # Randomly pick which choice to pay at the end of lottery, and assign to a participant variable
        p.participant.vars['index_to_pay'] = random.randrange(1, len(index))
        # NEEDS COMMENT
        p.participant.vars['choice_to_pay'] = 'choice_' + str(
            p.participant.vars['index_to_pay'])


def set_payoffs(player: Player):
    """When 'set_payoffs' is called, the player's payoff is set"""
    # Call the payoff dictionary, which contains updated values with multiplier
    payoffs = player.session.vars['payoffs']
    # Call the number of choices to create the probability distribution to draw from
    n = player.session.config['num_choices']
    # get the choice that was randomly drawn in 'creating_session'
    player.choice_to_pay = player.participant.vars['choice_to_pay']
    print(player.choice_to_pay)
    print(player.participant.vars['index_to_pay'])

    # Check which option the user selected in the Choice that was selected by app
    player.option_chosen = getattr(player, player.choice_to_pay)
    # Get the index of the Choice that was drawn to create the corresponding probability
    index = player.participant.vars['index_to_pay']
    # Create lists of probability and inverse probability, this could be improved with better code
    i = player.session.vars['probs'][index - 1]
    j = player.session.vars['inverse_probs'][index - 1]
    # store in list for numpy to draw from
    p = [i, j]
    # delete intermediate variables
    del i
    del j
    # Assign the outcomes to lists
    a = [cu(payoffs['A'][0]), cu(payoffs['A'][1])]
    b = [cu(payoffs['B'][0]), cu(payoffs['B'][1])]
    # If the player chose 'A'
    if player.option_chosen == 0:
        # Numpy function that picks an element in a list according to probability distribution, first argument is
        # the list to pick from, second argument is the number of times to run the draw, third argument is list
        # of probabilities
        drawn = np.random.choice(a, 1, p)
        # Run the draw once, numpy creates a list with 1 element, and we access it by getting the 0-index.
        player.payoff = drawn[0]
        player.option_chosen_letter = 'A'
    # If the player chose 'B'
    elif player.option_chosen == 1:
        drawn = np.random.choice(b, 1, p)
        player.payoff = drawn[0]
        player.option_chosen_letter = 'B'


# PAGES
# Expose variables for all templates. Attempted to create this as prettier function, but was not able.
def shared_vars(self):
    return {
        'lottery_a_hi': c(self.session.vars['payoffs']['A'][0]),
        'lottery_a_lo': c(self.session.vars['payoffs']['A'][1]),
        'lottery_b_hi': c(self.session.vars['payoffs']['B'][0]),
        'lottery_b_lo': c(self.session.vars['payoffs']['B'][1]),
        'num_choices': Constants.num_choices,
    }


# Class for the DecisionPage. Inherits attributes from Page Class
class DecisionPage(Page):
    form_model = 'player'
    # Unzip the list of choices, in order to create form fields corresponding to the number of choices
    @staticmethod
    def get_form_fields(player: Player):
        form_fields = [list(t)
                       for t in zip(*player.session.vars['choices'])][1]
        return form_fields

    # Expose variables that will only be available on this page.
    @staticmethod
    def vars_for_template(player: Player):
        return {
            "choices": player.session.vars['choices'],
            'lottery_a_hi': cu(player.session.vars['payoffs']['A'][0]),
            'lottery_a_lo': cu(player.session.vars['payoffs']['A'][1]),
            'lottery_b_hi': cu(player.session.vars['payoffs']['B'][0]),
            'lottery_b_lo': cu(player.session.vars['payoffs']['B'][1]),
            'num_choices': Constants.num_choices,
        }

    # Triggers the function that set draws the payoff of the user before the user is taken to the result page. This
    # should be changed if we were to make a game with several rounds.
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        set_payoffs(player)


# Class for the ResultsPage. Inherits attributes from Page Class
class ResultsPage(Page):
    # Expose variables that will only be available on this page.
    @staticmethod
    def vars_for_template(player: Player):
        return {
            "index_to_pay": player.participant.vars['index_to_pay'],
        }


# The sequence the app will order the pages.
page_sequence = [DecisionPage, ResultsPage]
