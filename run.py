def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser(description='Run workhouse code in either Scheduler or Simulator mode.'
                                                 'All keywords used for both modes unless specified.')
    parser.add_argument('-mode', choices=['schedule', 'simulate'], help='Operation mode')
    parser.add_argument('-te', help='.csv file containing the telescope network to be used')
    parser.add_argument('-th', type=float, help='Accuracy threshold to be aimed for')
    parser.add_argument('-wl', type=int, required=False, help='Length of window to be scheduled over: Only used by Schedule')
    parser.add_argument('-st', required=False, help='Start date for scheduling or simulation')
    parser.add_argument('-ed', required=False, help='End date for scheduling or simulation')
    parser.add_argument('-rp', type=int, required=False, help='Number of repeats for simulation')
    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()
    if args.mode == 'schedule':  # schedule mode
        import schedule
        schedule.schedule(args)
    if args.mode == 'simulate':  # simulate mode
        import simulate
        simulate.simulate(args)


if __name__ == '__main__':
    main()
