#################################################################
# Schedules the upcoming observable transits for targets that
# require observation.
# Takes a target list and dataset produced by ETD_query.py to
# make the calculation.
# Transits are calculated for each telescope provided, and each
# gets a list of observable transits.
# Hamish Caines 10/2019
#################################################################


def schedule(args):
    from os import listdir, remove
    import tools
    import numpy as np

    # load target and telescope data in objects
    infile = '../starting_data/database.json'
    targets = tools.load_json(infile)
    telescope_file = args.te
    telescopes = tools.load_telescopes('../telescopes/' + telescope_file)
    depth_data = np.genfromtxt('../starting_data/depth_limits_10.csv',
                               delimiter=',')  # load coefficients for depth calculations
    counter = 0
    for target in targets:
        target.determine_telescope_visibility(telescopes, depth_data)  # obtain usable telescopes for each target
        if len(target.observable_from) == 0:
            counter += 1
    print(counter, len(targets), counter/len(targets)*100)
    threshold = args.th  # extract the accuracy threshold being aimed for
    start, end = tools.check_input_dates(args)  # determine start and end dates form inputs

    print('Using', len(telescopes), 'telescopes')
    print('Forecasting from', start.date(), 'until', end.date())

    telescope_files = listdir('../scheduling_data/')  # check if output files already exist
    for telescope in telescopes:
        if telescope.name+'.csv' in telescope_files:  # remove output files that exist for telescopes
            remove('../scheduling_data/'+telescope.name+'.csv')
        with open(telescope.name+'.csv', 'a+') as f:  # add header row to new files
            f.write('#Name, Ingress(UTC), Center(UTC), Egress(UTC), IngressVisible, EgressVisible, Depth(mmag)')
            f.close()

    if 'all_telescopes.csv' in telescope_files:
        remove('../scheduling_data/all_telescopes.csv')  # remove total output file if exists
    with open('../scheduling_data/all_telescopes.csv', 'a+') as f:
        f.write('#Name, Site, Ingress(UTC), Center(UTC), Egress(UTC), IngressVisible, EgressVisible, Depth(mmag)')  # add header row to new file
        f.close()

    # determine which targets require observations
    required_targets = []
    for target in targets:
        if target.depth is not None:  # check for valid depth
            if target.real and len(target.observable_from) > 0:  # check for real target with required depth
                target.calculate_expiry(threshold)
                if target.check_if_required(start):  # run expiry calculation
                    required_targets.append(target)  # add to list if required

    required_targets.sort(key=lambda x: x.current_err, reverse=True)  # prioritise by largest current timing error

    all_transits = []
    for target in required_targets:  # loop through needed targets
        # obtain all visible transits for required targets, with observing site
        visible_transits = target.transit_forecast(start, end, telescopes)
        for visible in visible_transits:  # add to list
            visible.calculate_priority(target)
            all_transits.append(visible)
    all_transits.sort(key=lambda x: x.center)  # sort by date

    # output required transits
    for single in all_transits:
        # output all to one document, with site data
        with open('../scheduling_data/all_telescopes.csv', 'a+') as f:
            f.write('\n' + single.name + ', ' + single.telescope + ', ' + single.ingress.strftime(
                "%Y-%m-%dT%H:%M:%S") + ', ' + single.center.strftime(
                "%Y-%m-%dT%H:%M:%S") + ', ' + single.egress.strftime("%Y-%m-%dT%H:%M:%S")+', '+str(single.ingress_visible)+', '+str(single.egress_visible)+', '+str(single.depth)+', '+str(single.priority))
            f.close()
        # output to individual documents per telescope
        with open('../scheduling_data/'+single.telescope+'.csv', 'a+') as f:
            f.write('\n' + single.name + ', ' + single.ingress.strftime(
                "%Y-%m-%dT%H:%M:%S") + ', ' + single.center.strftime(
                "%Y-%m-%dT%H:%M:%S") + ', ' + single.egress.strftime("%Y-%m-%dT%H:%M:%S")+', '+str(single.ingress_visible)+', '+str(single.egress_visible)+', '+str(single.depth)+', '+str(single.priority))
            f.close()

    print('Forecast', len(all_transits), 'visible transits')
