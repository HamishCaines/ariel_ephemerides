#################################################################
# Schedules the upcoming observable transits for targets that
# require observation.
# Takes a target list and dataset produced by ETD_query.py to
# make the calculation.
# Transits are calculated for each telescope provided, and each
# gets a list of observable transits.
# Hamish Caines 10/2019
#################################################################


def schedule(settings):
    from os import mkdir, chdir
    import tools
    import numpy as np

    # load target and telescope data in objects
    infile = f'{settings.data_root}/starting_data/database_1000_depths.json'
    targets = tools.load_json(infile)
    telescope_file = settings.telescopes
    settings.simulation_method = 'SELECTIVE'
    telescopes = tools.load_telescopes(f'{settings.data_root}/telescopes/' + telescope_file)
    depth_data = np.genfromtxt(f'{settings.data_root}/starting_data/depth_limits_10.csv',
                               delimiter=',')  # load coefficients for depth calculations
    counter = 0
    for target in targets:
        # target.determine_telescope_visibility(telescopes, depth_data)  # obtain usable telescopes for each target
        for telescope in telescopes:
            target.observable_from.append(telescope.name)  # changed: assuming are visible from all telescopes for now
        target.determine_individual_threshold(settings)  # determine individual threshold for target based on settings
        if len(target.observable_from) == 0:
            counter += 1
    print(counter, len(targets), counter/len(targets)*100)
    # threshold = settings.threshold  # extract the accuracy threshold being aimed for

    print('Using', len(telescopes), 'telescopes')
    print('Forecasting from', settings.start, 'until', settings.end)
    settings.obtain_directory_single()
    mkdir(settings.directory)
    chdir(settings.directory)
    for telescope in telescopes:
        with open(telescope.name + '.csv', 'a+') as f:  # add header row to new files
            f.write('#Name, Ingress(UTC), Center(UTC), Egress(UTC), IngressVisible, EgressVisible, Depth(mmag)')
            f.close()
    with open('all_telescopes.csv', 'a+') as f:
        # add header row to new file
        f.write('#Name, Site, Ingress(UTC), Center(UTC), Egress(UTC), IngressVisible, EgressVisible, Depth(mmag)')
        f.close()

    # determine which targets require observations
    required_targets = []
    for target in targets:
        if target.depth is not None:  # check for valid depth
            if target.real and len(target.observable_from) > 0:  # check for real target with required depth
                target.recalculate_parameters(settings.start, settings)
                if target.check_if_required(settings.start, settings):  # run expiry calculation
                    required_targets.append(target)  # add to list if required

    required_targets.sort(key=lambda x: x.current_err, reverse=True)  # prioritise by largest current timing error

    all_transits = []
    for target in required_targets:  # loop through needed targets
        # obtain all visible transits for required targets, with observing site
        visible_transits = target.transit_forecast(settings.start, settings.end, telescopes, settings)
        for visible in visible_transits:  # add to list
            visible.calculate_priority(target)
            all_transits.append(visible)
    all_transits.sort(key=lambda x: x.center)  # sort by date

    # output required transits
    for single in all_transits:
        # output all to one document, with site data
        with open('all_telescopes.csv', 'a+') as f:
            f.write(
                f'\n{single.name}, {single.telescope}, {single.ingress.strftime("%Y-%m-%dT%H:%M:%S")}, '
                f'{single.center.strftime("%Y-%m-%dT%H:%M:%S")}, {single.egress.strftime("%Y-%m-%dT%H:%M:%S")}, '
                f'{single.ingress_visible}, {single.egress_visible}, {single.visible_from}, {single.visible_until}, '
                f'{single.depth}, {single.priority}')
            # f.write('\n' + single.name + ', ' + single.telescope + ', ' + single.ingress.strftime(
            #     "%Y-%m-%dT%H:%M:%S") + ', ' + single.center.strftime(
            #     "%Y-%m-%dT%H:%M:%S") + ', ' + single.egress.strftime("%Y-%m-%dT%H:%M:%S") + ', ' + str(
            #     single.ingress_visible) + ', ' + str(single.egress_visible) + ', ' + str(single.depth) + ', ' + str(
            #     single.priority))
            f.close()
        # output to individual documents per telescope
        with open(f'{single.telescope}.csv', 'a+') as f:
            f.write(
                f'\n{single.name}, {single.ingress.strftime("%Y-%m-%dT%H:%M:%S")}, '
                f'{single.center.strftime("%Y-%m-%dT%H:%M:%S")}, {single.egress.strftime("%Y-%m-%dT%H:%M:%S")}, '
                f'{single.ingress_visible}, {single.egress_visible}, {single.visible_from}, {single.visible_until}, '
                f'{single.depth}, {single.priority}')
            # f.write('\n' + single.name + ', ' + single.ingress.strftime(
            #     "%Y-%m-%dT%H:%M:%S") + ', ' + single.center.strftime(
            #     "%Y-%m-%dT%H:%M:%S") + ', ' + single.egress.strftime("%Y-%m-%dT%H:%M:%S") + ', ' + str(
            #     single.ingress_visible) + ', ' + str(single.egress_visible) + ', ' + str(single.depth) + ', ' + str(
            #     single.priority))
            # f.close()

    print('Forecast', len(all_transits), 'visible transits')
