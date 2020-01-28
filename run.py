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
    import settings
    from os import getcwd, chdir
    setting_data = settings.Settings('settings.dat')
    print(vars(setting_data))
    thresholds = setting_data.threshold_value
    networks = setting_data.telescopes
    #args = parse_arguments()
    starting_dir = getcwd()

    for network in networks:
        single_run_settings = setting_data
        single_run_settings.telescopes = network
        for value in thresholds:
            single_run_settings.threshold_value = value
            print(vars(single_run_settings))
            single_run_settings.obtain_directory_name()
            if setting_data.mode == 'SCHEDULE':  # schedule mode
                import schedule
                schedule.schedule(single_run_settings)
            if setting_data.mode == 'SIMULATE':  # simulate mode
                import simulate
                simulate.simulate(single_run_settings)
            chdir(starting_dir)

    # TODO: Need to add the changes discussed with Marco et al, think about how to model amateurs
    # TODO: Think about how many targets are visible from the ground


if __name__ == '__main__':
    main()
