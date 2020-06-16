import tools
from os import mkdir, chdir
from datetime import timedelta
import numpy as np
import json


def simulate(settings):
    from os import mkdir, chdir
    import tools

    count = 1  # run count
    # obtain telescope and threshold to use
    telescope_file = settings.telescopes
    # check existing simulations for this one
    #simulation_files = listdir('../simulation_data/')
    telescopes = tools.load_telescopes(f'{settings.data_root}/telescopes/' + telescope_file)
    settings.obtain_directory_single()
    # make new directory for simulation and cd into it
    mkdir(settings.directory)
    chdir(settings.directory)

    # initialise results file
    with open('results.csv', 'a+') as f:
        f.write(
            '#Run, Performance(%), TotalObservations, TotalObsDays, TotalNightDays, PercentNightUsed, PercentClearUsed')
        f.close()

    required_targets = []
    # loop for number of runs specified
    while count <= settings.repeats:
        run_name = 'run'+str(count)  # increment run number
        required_targets_run = run_sim(settings, run_name, telescopes, settings)  # new simulation run
        for target in required_targets_run:
            required_targets.append(target)
        count += 1
    with open('missing_targets', 'a+') as f:
        f.write('Target, Duration(mins), Depth')
        for target in required_targets:
            f.write('\n'+target.name+' '+str(target.period)+' '+str(target.duration)+' '+str(target.depth))
        f.close()


def find_required_targets(current, targets, settings):
    """
    For a given list of exoplanets, checks which require observations based on the current ephemeris error
    :param current: Current date that the simulation is running at: datetime
    :param targets: List of targets in our data set: List of Target objects
    :param settings: Settings object for the current simulation
    :return: List of Targets that require observation, the length of the list, and total Targets
    """
    count = 0
    total = 0
    required_targets = []
    for target in targets:
        if target.depth is not None:  # check for valid depth
            if len(target.observable_from) > 0:  # check for real target with observable
                total += 1
                if target.check_if_required(current, settings):  # run check if target is required
                    count += 1
                    required_targets.append(target)  # add to list if required

    return required_targets, count, total


def find_visible_transits(req_targets, current, interval, telescopes, settings):
    """
    Forecasts transits for a list of Targets that are visible from at least one Telescope
    :param req_targets: List of Targets that require observation
    :param current: Current date for the simulation: datetime
    :param interval: Length of time to forecast transits over: timedelta
    :param telescopes: List of Telescope objects for the network being testes
    :param settings: Settings object for the current simulation
    :return: List of Transit objects for visible transits across the network
    """
    visible_transits = []
    for target in req_targets:
        # obtain visible transits
        visible = target.transit_forecast(current, current + interval, telescopes, settings)
        for single in visible:
            visible_transits.append(single)
    return visible_transits


def match_transit_to_telescope(transits, telescope):
    """
    Obtain the visible Transits for a given Telescope
    :param transits: List of Transits to be checked
    :param telescope: Telescope object currently being checked
    :return: List of Transit objects for transits visible from the given Telescope
    """
    matching_transits = []
    for transit in transits:
        if transit.telescope == telescope.name:
            matching_transits.append(transit)
    return matching_transits


def handle_new_data(new_data, targets, current, settings):
    """
    Handles newly generated obsservation data, stores in the relevant Target object and recalculates key parameters
    :param new_data: List of new observation data
    :param targets: List of all Targets being tested
    :param current: Current date for the simulation: datetime
    :param settings: Settings object for the current simulation
    """
    for single in new_data:
        for target in targets:
            if target.name == single[0]:
                target.observations.append([single[1], single[2], single[3]])  # add new data point to target
                # reset values to latest observation
                target.last_epoch = single[1]
                target.last_tmid = single[2]
                target.last_tmid_err = single[3]
                target.period_fit_poly()  # run period fit to refine the period error
                # target.period_fit_deeg()
                target.recalculate_parameters(current,
                                              settings)  # recalculate the selection parameters based on the new data


def run_sim(args, run_name, telescopes, settings):

    # load targets from database into objects
    infile = f'{settings.data_root}/starting_data/database_60_50.json'
    targets = tools.load_json(infile)

    # depth_data = np.genfromtxt(f'{settings.data_root}/starting_data/depth_limits_10.csv',
    #                           delimiter=',')  # load coefficients for depth calculations
    for target in targets:
        target.determine_individual_threshold(settings)  # calculate individual threshold based on settings
        target.recalculate_parameters(settings.start, settings)  # calculate selection parameters for target
        # target.determine_telescope_visibility(telescopes, depth_data)
        # Changed to make all targets visible depth-wise from all telescopes for now
        for telescope in telescopes:
            target.observable_from.append(telescope.name)

    targets.sort(key=lambda x: x.current_err)  # sort by current timing error

    interval = timedelta(days=7)  # length of individual time blocks

    # made directory for current run and cd into it
    mkdir(run_name)
    chdir(run_name)
    # initialise files for scheduled observations
    for telescope in telescopes:
        with open(telescope.name+'.csv', 'a+') as f:  # add header row to new files
            f.write('#Name, Start(UTC), End(UTC)')
            f.close()

    with open('all_telescopes.csv', 'a+') as f:
        f.write('#Name, Site, Start(UTC), End(UTC)')  # add header row to new file
        f.close()
    print('Using', len(telescopes), 'telescopes')
    print('Simulating from', args.start.date(), 'until', args.end.date())

    # initialise counters
    current = args.start
    tot_obs = 0
    tot_obs_time = timedelta(days=0)
    tot_night_time = timedelta(days=0)
    tot_clear_time = timedelta(days=0)
    count, total = 0, 0
    required_targets = []

    while current < args.end:
        required_targets, count, total = find_required_targets(current, targets, settings)

        print(current.date(), len(required_targets), np.round(count/total*100, 1), count, total, tot_obs)
        # obtain visible transits for the required targets
        visible_transits = find_visible_transits(required_targets, current, interval, telescopes, settings)

        # match transits to telescopes
        for telescope in telescopes:
            matching_transits = match_transit_to_telescope(visible_transits, telescope)
            matching_transits.sort(key=lambda x: x.visible_from)
            obs_results = telescope.schedule_observations(
                matching_transits)  # schedule matching transits and count time used
            # increment counters
            tot_obs += obs_results[0]

            new_data, obs_time = telescope.simulate_observations()  # simulate the scheduled observations
            tot_obs_time += obs_time
            # add new data
            handle_new_data(new_data, targets, current, settings)

        time_increments = tools.increment_total_night(current, interval, telescopes)
        tot_night_time += time_increments[0]
        tot_clear_time += time_increments[1]

        current += interval  # increment time block

    with open('required_targets.json', 'a+') as f:
        for target in required_targets:
            json.dump(vars(target), f)
        f.close()
    chdir('../')  # change out of run folder
    percent = 100-(count/total*100)
    # write results for this run to results file
    tot_obs_days = tot_obs_time.total_seconds()/86400
    tot_night_days = tot_night_time.total_seconds()/86400
    tot_clear_days = tot_clear_time.total_seconds()/86400
    with open('results.csv', 'a+') as f:
        f.write('\n' + str(run_name.split('run')[1]) + ', ' + str(percent) + ', ' + str(tot_obs) + ', ' + str(
            tot_obs_days) + ', ' + str(tot_night_days) + ', ' + str(tot_obs_days / tot_night_days * 100) + ', ' + str(
            tot_obs_days / tot_clear_days * 100))
    print(100-(count/total*100))

    return required_targets
