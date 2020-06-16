#################################################################
# Schedules the upcoming observable transits for targets that
# require observation.
# Takes a target list and dataset produced by ETD_query.py to
# make the calculation.
# Transits are calculated for each telescope provided, and each
# gets a list of observable transits.
# Hamish Caines 10/2019
#################################################################
import json
from os import getcwd


def load_exoclock_latest(targets):
    import exoclock_database as exo
    exoclock_data = exo.ExoClock().database
    print(exoclock_data)
    for target in targets:
        if target.real:
            try:
                latest_data = exoclock_data[target.name]
                target.last_tmid, target.last_tmid_err = latest_data['mid_time'] - 2400000, latest_data['mid_time_error']
                target.period, target.period_error = latest_data['period'], latest_data['period_error']
            except KeyError:
                pass


def find_required_targets(targets, date, settings):
    required_targets = []
    for target in targets:
        if target.depth is not None:  # check for valid depth
            if target.real and len(target.observable_from) > 0:  # check for real target with required depth
                target.recalculate_parameters(date, settings)
                if target.check_if_required(date, settings):  # run expiry calculation
                    required_targets.append(target)  # add to list if required

    required_targets.sort(key=lambda x: x.current_err, reverse=True)  # prioritise by largest current timing error
    return required_targets


def schedule(settings):
    from os import mkdir, chdir
    import tools
    import numpy as np
    from datetime import timedelta

    # load target and telescope data in objects
    infile = f'{settings.data_root}/starting_data/database_HIP.json'
    targets = tools.load_json(infile)
    interval = timedelta(days=7)
    with open('../../../observations/strategies3.json', 'r') as f:
        strategy_data = json.load(f)

    telescope_file = settings.telescopes
    settings.simulation_method = 'SELECTIVE'
    telescopes = tools.load_telescopes(f'{settings.data_root}/telescopes/' + telescope_file)
    if settings.use_exoclock:
        load_exoclock_latest(targets)

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

    all_transits = []
    current_date = settings.start
    while current_date < settings.end:
        required_targets = find_required_targets(targets, current_date, settings)
        print(current_date, len(required_targets))
        for target in required_targets:  # loop through needed targets
            # obtain all visible transits for required targets, with observing site
            visible_transits = target.transit_forecast(current_date, current_date + interval, telescopes, settings)
            for visible in visible_transits:  # add to list
                if 'HIP41378' in visible.name:
                    print('HIP FOUND')
                all_transits.append(visible)
        current_date += interval


    # determine which targets require observations
    # required_targets = []
    # for target in targets:
    #     if target.depth is not None:  # check for valid depth
    #         if target.real and len(target.observable_from) > 0:  # check for real target with required depth
    #             target.recalculate_parameters(settings.start, settings)
    #             if target.check_if_required(settings.start, settings):  # run expiry calculation
    #                 required_targets.append(target)  # add to list if required
    #
    # required_targets.sort(key=lambda x: x.current_err, reverse=True)  # prioritise by largest current timing error
    #
    # for target in required_targets:  # loop through needed targets
    #     # obtain all visible transits for required targets, with observing site
    #     visible_transits = target.transit_forecast(settings.start, settings.end, telescopes, settings)
    #     for visible in visible_transits:  # add to list
    #         visible.calculate_priority(target)
    #         all_transits.append(visible)
    all_transits.sort(key=lambda x: x.center)  # sort by date

    names = []
    for transit in all_transits:
        if transit.name not in names:
            names.append(transit.name)

    print('Names: ', len(names))
    for name in names:
        transits = [single for single in all_transits if single.name == name]
        for i in range(0, len(transits) - 1):
            first_date = transits[i].center
            next_date = transits[i + 1].center
            days_to_next = round((next_date - first_date).total_seconds()/86400)
            transits[i].days_to_next_visible = days_to_next

            found = False
            j = i
            while j < len(transits) - 1 and not found:
                j += 1
                if transits[j].ingress_visible and transits[j].egress_visible:
                    next_full = transits[j].center
                    found = True

            if found:
                days_to_next_full = round((next_full - first_date).total_seconds()/86400)
                transits[i].days_to_next_full = days_to_next_full
            else:
                transits[i].days_to_next_full = 999

            k = i
            found = False
            while k < len(transits) - 1 and not found:
                k += 1
                if (transits[k].center - transits[i].center) < timedelta(days=30):
                    transits[i].visible_in_next_30 += 1
                else:
                    found = True






        transits[-1].days_to_next_visible = 999
        transits[-1].days_to_next_full = 999

    # output required transits
    for single in all_transits:
        single.determine_strategy(strategy_data)
        print('series', single.series)
        # output all to one document, with site data
        with open('all_telescopes.csv', 'a+') as f:
            try:
                f.write(
                f'\n{single.name}, {single.magnitude}, {single.telescope}, {single.ingress.strftime("%Y-%m-%d, %H:%M:%S")}, '
                f'{single.center.strftime("%Y-%m-%d, %H:%M:%S")}, {single.egress.strftime("%Y-%m-%d, %H:%M:%S")}, '
                f'{single.ingress_visible}, {single.egress_visible}, {single.visible_from}, {single.visible_until}, {single.run_start}, {single.run_end}, '
                f'{single.series["bin1"]["exp_time"]}, {single.series["bin1"]["images"]}, {single.series["bin2"]["exp_time"]}, {single.series["bin2"]["images"]}, {single.visible_fraction}, {single.depth}, {single.priority}, {single.moon_phase}, {single.moon_alt}, '
                f'{single.period}, {single.days_to_next_visible}, {single.days_to_next_full}, {single.visible_in_next_30}')
            except KeyError:
                f.write(
                    f'\n{single.name}, {single.magnitude}, {single.telescope}, {single.ingress.strftime("%Y-%m-%d, %H:%M:%S")}, '
                    f'{single.center.strftime("%Y-%m-%d, %H:%M:%S")}, {single.egress.strftime("%Y-%m-%d, %H:%M:%S")}, '
                    f'{single.ingress_visible}, {single.egress_visible}, {single.visible_from}, {single.visible_until}, {single.run_start}, {single.run_end}, '
                    f'{None}, {None}, {None}, {None}, {single.visible_fraction}, {single.depth}, {single.priority}, {single.moon_phase}, {single.moon_alt}, '
                    f'{single.period}, {single.days_to_next_visible}, {single.days_to_next_full}, {single.visible_in_next_30}')
            # f.write('\n' + single.name + ', ' + single.telescope + ', ' + single.ingress.strftime(
            #     "%Y-%m-%dT%H:%M:%S") + ', ' + single.center.strftime(
            #     "%Y-%m-%dT%H:%M:%S") + ', ' + single.egress.strftime("%Y-%m-%dT%H:%M:%S") + ', ' + str(
            #     single.ingress_visible) + ', ' + str(single.egress_visible) + ', ' + str(single.depth) + ', ' + str(
            #     single.priority))
            f.close()
        # output to individual documents per telescope
        with open(f'{single.telescope}.csv', 'a+') as f:
            try:
                f.write(
                    f'\n{single.name}, {single.magnitude}, {single.ingress.strftime("%Y-%m-%d, %H:%M:%S")}, '
                    f'{single.center.strftime("%Y-%m-%d, %H:%M:%S")}, {single.egress.strftime("%Y-%m-%d, %H:%M:%S")}, '
                    f'{single.ingress_visible}, {single.egress_visible}, {single.visible_from}, {single.visible_until}, {single.run_start}, {single.run_end}, '
                    f'{single.series["bin1"]["exp_time"]}, {single.series["bin1"]["images"]}, {single.series["bin2"]["exp_time"]}, {single.series["bin2"]["images"]}, {single.visible_fraction}, {single.depth}, {single.moon_phase}, {single.moon_alt}, '
                    f'{single.period}, {single.days_to_next_visible}, {single.days_to_next_full}, {single.visible_in_next_30}')
            except KeyError:
                f.write(
                    f'\n{single.name}, {single.magnitude}, {single.ingress.strftime("%Y-%m-%d, %H:%M:%S")}, '
                    f'{single.center.strftime("%Y-%m-%d, %H:%M:%S")}, {single.egress.strftime("%Y-%m-%d, %H:%M:%S")}, '
                    f'{single.ingress_visible}, {single.egress_visible}, {single.visible_from}, {single.visible_until}, {single.run_start}, {single.run_end}, '
                    f'{None}, {None}, {None}, {None}, {single.visible_fraction}, {single.depth}, {single.moon_phase}, {single.moon_alt}, '
                    f'{single.period}, {single.days_to_next_visible}, {single.days_to_next_full}, {single.visible_in_next_30}')

    print('Forecast', len(all_transits), 'visible transits')
