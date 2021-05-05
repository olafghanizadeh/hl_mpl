# hl_mpl
A simple implementation of the Holt/Laury(2002) Multiple Price List lottery made in oTree.


1. Clone the repo into your oTree folder
2. Add the following to your `settings.py` file in the oTree root directory. (Add only the dictionary for this project if you have multiple oTree experiments installed.)
```
SESSION_CONFIGS = [
    dict(
        name='hl_mpl',
        display_name='Risk Lottery',
        num_demo_participants=10,
        app_sequence=['hl_mpl'],
        num_choices=8,
        multiplier=10,
    )
]

```
