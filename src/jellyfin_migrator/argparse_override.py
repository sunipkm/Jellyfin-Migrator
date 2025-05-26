import argparse


def override(func):
    """ returns an argparse action that stops parsing and calls a function
    whenever a particular argument is encountered. The program is then exited """
    class OverrideAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            func(values)
            parser.exit()
    return OverrideAction