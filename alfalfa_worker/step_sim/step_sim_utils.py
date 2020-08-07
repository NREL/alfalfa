import argparse
from datetime import datetime


def valid_date(s):
    """Raise error if datetime string not formatted correctly"""
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        msg = "Not a valid date: '{0}'".format(s)
        raise argparse.ArgumentTypeError(msg)


def step_sim_arg_parser():
    """Argument parser for both OSM and FMU step simulations"""
    parser = argparse.ArgumentParser()
    parser.add_argument('site_id', help="The _id attribute of the record stored in MongoDB")
    parser.add_argument('step_sim_type', help="The type of step simulation to perform.",
                        choices=['timescale', 'realtime', 'external_clock'])
    parser.add_argument('start_datetime', type=valid_date, help="Valid datetime, formatted: %Y-%m-%d %H:%M:%S")
    parser.add_argument('end_datetime', type=valid_date, help="Valid datetime, formatted: %Y-%m-%d %H:%M:%S")

    help_string = ('How quickly the model advances, represented as a '
                   'ratio between model_time:real_time.  1 means the '
                   'model advances 1 minute for every 1 minute in realtime, '
                   'while 5 means the model advances once every 12 seconds in realtime')
    parser.add_argument('--step_sim_value', type=int, choices=range(0, 20), help=help_string)
    args = parser.parse_args()
    if args.step_sim_type == 'timescale' and not args.step_sim_value:
        parser.error('--step_sim_value must be specified if step_sim_type is timescale')
    else:
        print(args)
        return args
