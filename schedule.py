#################################################################
# Schedules the upcoming observable transits for targets that
# require observation.
# Takes a target list and dataset produced by ETD_query.py to
# make the calculation.
# Transits are calculated for each telescope provided, and each
# gets a list of observable transits.
# Hamish Caines 10/2019
#################################################################


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser(description='Schedule upcoming transits required for ARIEL')
    parser.add_argument('threshold', type=int, help='Accuracy threshold')
    parser.add_argument('telescopes', type=str, help='File containing telescope data')
    parser.add_argument('window_length', type=int, help='Length of window in days')
    args = parser.parse_args()
    telescope_file = args.telescopes
    threshold = args.threshold
    days = args.window_length

    return threshold, telescope_file, days


def load_json(infile):
    """
    Loads database from json output file, created by make_database.py
    :param infile: location of the json file
    :return: list of Target objects containing all the required information
    """
    import json
    import target
    with open(infile) as f:
        data = json.load(f)  # loads a set json outputs into a list
    targets = []
    for single in data:  # create Target object for each json, and load json into it
        new_target = target.Target().init_from_json(single)
        targets.append(new_target)  # add to lis
    return targets


def load_telescopes(filename):
    """
    Loads telescope parameters from a .csv file ans stores as a list of Telescope objects
    :param filename: location of data file to be loaded
    :return: List of Telescope objects
    """
    import numpy as np
    import telescope
    data = np.genfromtxt(filename, dtype=str, skip_header=1, delimiter=',')  # read csv data
    telescopes = []
    for single in data:  # create Telescope object for each row and load data into it
        telescopes.append(telescope.Telescope().gen_from_csv(single))
    return telescopes


def main():
    from datetime import datetime, timedelta
    from os import listdir, remove

    infile = '../starting_data/database.json'
    targets = load_json(infile)
    threshold, telescope_file, window_days = parse_arguments()
    depth_limit = 0.01
    telescopes = load_telescopes('../telescopes/'+telescope_file)

    today = datetime.today()  # start date for calculations
    interval = timedelta(days=window_days)
    print('Using', len(telescopes), 'telescopes')
    print('Forecasting from', today.date(), 'until', (today+interval).date())

    telescope_files = listdir('../scheduling_data/')  # check if output files already exist
    for telescope in telescopes:
        if telescope.name+'.csv' in telescope_files:  # remove output files that exist for telescopes
            remove('../scheduling_data/'+telescope.name+'.csv')
        with open(telescope.name+'.csv', 'a+') as f:  # add header row to new files
            f.write('#Name, Ingress(UTC), Center(UTC), Egress(UTC), PartialTransit')

    if 'all_telescopes.csv' in telescope_files:
        remove('../scheduling_data/all_telescopes.csv')  # remove total output file if exists
    with open('../scheduling_data/all_telescopes.csv', 'a+') as f:
        f.write('#Name, Site, Ingress(UTC), Center(UTC), Egress(UTC), PartialTransit')  # add header row to new file


    # determine which targets require observations
    required_targets = []
    for target in targets:
        if target.depth is not None:  # check for valid depth
            if target.real and float(target.depth) > depth_limit:  # check for real target with required depth
                if target.calculate_expiry(threshold, today):  # run expiry calculation
                    required_targets.append(target)  # add to list if required

    required_targets.sort(key=lambda x: x.current_err, reverse=True)  # prioritise by largest current timing error

    all_transits = []
    for target in required_targets:  # loop through needed targets
        # obtain all visible transits for required targets, with observing site
        visible_transits = target.transit_forecast(today, today + interval, telescopes)
        for visible in visible_transits:  # add to list
            all_transits.append(visible)
    all_transits.sort(key=lambda x: x.center)  # sort by date

    # output required transits
    for single in all_transits:
        # output all to one document, with site data
        with open('../scheduling_data/all_telescopes.csv', 'a+') as f:
            f.write('\n' + single.name + ', ' + single.telescope + ', ' + single.ingress.strftime(
                "%Y-%m-%dT%H:%M:%S") + ', ' + single.center.strftime(
                "%Y-%m-%dT%H:%M:%S") + ', ' + single.egress.strftime("%Y-%m-%dT%H:%M:%S")+', '+str(single.partial))
            f.close()
        # output to individual documents per telescope
        with open('../scheduling_data/'+single.telescope+'.csv', 'a+') as f:
            f.write('\n' + single.name + ', ' + single.ingress.strftime(
                "%Y-%m-%dT%H:%M:%S") + ', ' + single.center.strftime(
                "%Y-%m-%dT%H:%M:%S") + ', ' + single.egress.strftime("%Y-%m-%dT%H:%M:%S")+', '+str(single.partial))
            f.close()

    print('Forecast', len(all_transits), 'visible transits')


if __name__ == '__main__':
    main()
