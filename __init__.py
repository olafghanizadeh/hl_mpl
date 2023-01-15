import random
import numpy as np
from otree.api import *
from settings import LANGUAGE_CODE

# Moved index function to separate file to keep this file cleaner

author = 'Olaf Ghanizadeh'
doc = """
A crude and simple implementation of the Holt/Laury(2002) lottery.
"""


def create_index(choices):
    global index
    index = [j for j in range(1, choices + 1)]
    return index


def make_field(name):
    return models.IntegerField(
        choices=[0, 1],
        label=name,
        widget=widgets.RadioSelect,
    )


def draw_prize(payoffs, p, player, letter):
    drawn = np.random.choice(payoffs, 1, p)
    player.option_chosen_letter = letter

    player.participant.drawn[player.round_number] = {letter:drawn[0]}


def subtract(v, i):
    if i == 1:
        return v
    return v - (5 * (i - 1))


def create_payoffs():
    return {
        i: {
            k: ({
                    inner_k: ({
                                  nested_k: (subtract(nested_v, i) if nested_k == 'low' else nested_v) for
                                  nested_k, nested_v in inner_v.items()
                              } if inner_k == 'B' else inner_v) for inner_k, inner_v in v.items()
                } if k == Constants.DECISION_MAKER_ROLE else v) for k, v in Constants.payoffs.items()} for i in
        range(1, Constants.num_rounds + 1)
    }


class Constants(BaseConstants):
    name_in_url = 'risk_lottery'
    BASELINE = 'BASELINE'
    ALIGNED = 'ALIGNED'
    RECEIVER_ROLE = 'Receiver'
    DECISION_MAKER_ROLE = 'Decision Maker'
    players_per_group = 2
    num_rounds = 4
    num_choices = 11
    index = create_index(num_choices)
    payoffs = {
        RECEIVER_ROLE: {
            'A': {'high': 20, 'low': 16},
            'B': {'high': 40, 'low': 1}
        },
        DECISION_MAKER_ROLE: {
            'A': {'high': 20, 'low': 16},
            'B': {'high': 40, 'low': 16}
        }
    }


class Player(BasePlayer):
    """The oTree class that generates the info PER PLAYER"""
    # Initiate fields to be populated by app
    choice_to_pay = models.StringField()
    index_to_pay = models.IntegerField()
    option_chosen = models.IntegerField()
    option_chosen_letter = models.StringField()
    # Function to set payoffs for each player

    n = len(index)
    # Name Field
    # Generates the fields for the form fields. Necessary to call locals() to access correct scope. This should be
    # put in a function to improve code quality.
    for j in range(1, n + 1):
        locals()[f'choice_{str(j)}'] = make_field(f'choice_{str(j)}')
    # Delete intermediate variables
    del j
    del n


def custom_export(players):
    # header row
    yield ['session.code', 'participant.treatment', 'participant.code']
    for p in players:
        participant = p.participant
        session = p.session
        yield [session.code, participant.treatment, participant.code]


class Subsession(BaseSubsession):
    """Creating the lottery subsessions"""


class Group(BaseGroup):
    pass


# FUNCTIONS
def creating_session(subsession: Subsession):
    subsession.group_randomly(fixed_id_in_group=True)
    """Method to initiate a session"""

    # Set Constant num.choices to n for easier reuse
    n = Constants.num_choices

    subsession.session.vars['payoffs'] = create_payoffs()

    # Store in session variables
    subsession.session.vars['index'] = index
    probs = [i / (n - 1) for i in index]
    probs.insert(0, 0)
    inverse_p = [1 - p for p in probs]
    subsession.session.vars['probs'] = probs
    subsession.session.vars['inverse_probs'] = inverse_p
    formatted_p = [f'{p:.1f}' for p in probs]
    formatted_inverse_p = [round(p, 1) for p in inverse_p]
    form_fields = ['choice_' + str(k) for k in index]
    choices = list(zip(index, form_fields, formatted_p, formatted_inverse_p))
    subsession.session.vars['choices'] = choices


def set_payoffs(player: Player):
    """When 'set_payoffs' is called, the player's payoff is set"""
    # Call the payoff dictionary, which contains updated values with multiplier
    # Create lottery for each player
    # for p in player.subsession.get_players():
    # Randomly pick which choice to pay at the end of lottery, and assign to a participant variable
    # p.index_to_pay = random.randrange(1, len(Constants.index))
    # p.choice_to_pay = 'choice_' + str(p.index_to_pay)

    player.index_to_pay = random.randrange(1, len(Constants.index))
    player.choice_to_pay = 'choice_' + str(player.index_to_pay)
    payoffs = player.subsession.session.vars['payoffs']
    # get the choice that was randomly drawn in 'creating_session'
    # player.choice_to_pay = player.participant.vars['choice_to_pay']

    # Check which option the user selected in the Choice that was selected by app
    player.option_chosen = getattr(player, player.choice_to_pay)
    # Get the index of the Choice that was drawn to create the corresponding probability
    index = player.index_to_pay
    # Create lists of probability and inverse probability, this could be improved with better code
    i = player.session.vars['probs'][index - 1]
    j = player.session.vars['inverse_probs'][index - 1]
    # store in list for numpy to draw from
    p = [i, j]
    # delete intermediate variables
    del i
    del j
    # Assign the outcomes to lists
    if player.role == Constants.DECISION_MAKER_ROLE:

        a = [key for key in payoffs[player.round_number][player.role]['A'].keys()]
        b = [key for key in payoffs[player.round_number][player.role]['B'].keys()]
        if 'drawn' not in player.participant.vars:
            player.participant.vars['drawn'] = {}
        # If the player chose 'A'
        if player.option_chosen == 0:
            draw_prize(a, p, player, 'A')
        elif player.option_chosen == 1:
            draw_prize(b, p, player, 'B')



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
        partner = player.get_others_in_group()
        role = partner[0].role

        return {
            "choices": player.session.vars['choices'],
            'num_choices': Constants.num_choices,
            'lang': LANGUAGE_CODE,
            'partner': role,
            'payoffs': player.session.vars['payoffs'][player.round_number][player.role],
            'partner_payoffs': player.session.vars['payoffs'][player.round_number][role]
        }

    # Triggers the function that set draws the payoff of the user before the user is taken to the result page. This
    # should be changed if we were to make a game with several rounds.
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        set_payoffs(player)


# Class for the ResultsPage. Inherits attributes from Page Class
class ResultsPage(Page):
    form_model = 'player'
    form_fields = ['withdraw']

    # Expose variables that will only be available on this page.
    @staticmethod
    def vars_for_template(player: Player):
        return {
            "index_to_pay": player.index_to_pay,
            'lang': LANGUAGE_CODE,
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        pass

    @staticmethod
    def app_after_this_page(player, upcoming_apps):
        pass


# The sequence the app will order the pages.
page_sequence = [DecisionPage]
