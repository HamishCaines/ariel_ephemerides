def simulate(args):
    from os import listdir, mkdir, chdir
    from shutil import rmtree
    import tools
    if args.rp is None:
        runs = 1
    else:
        runs = args.rp
    count = 1
    telescope_file = args.te
    threshold = args.th
    simulation_name = telescope_file.split('.')[0] + '_' + str(threshold)
    simulation_files = listdir('../simulation_data/')
    if simulation_name in simulation_files:
        print('Simulation', simulation_name, 'already exists. Replace?')
        replace = input('Simulation ' + simulation_name + ' already exists. Replace? (y/n) ')
        if replace == 'y':
            replace = True
        else:
            replace = False
        if replace:
            rmtree('../simulation_data/' + simulation_name)
        else:
            raise Exception
    telescopes = tools.load_telescopes('../telescopes/' + telescope_file)

    mkdir('../simulation_data/' + simulation_name)
    chdir('../simulation_data/' + simulation_name)

    with open('results.csv', 'a+') as f:
        f.write('#Run, Performance(%), TotalObservations, TotalObsDays')
        f.close()

    while count <= runs:
        run_name = 'run'+str(count)
        run_sim(args, run_name, telescopes)
        count += 1


def run_sim(args, run_name, telescopes):
    import tools
    from os import mkdir, chdir
    from datetime import timedelta

    start, end = tools.check_input_dates(args)
    threshold = args.th

    infile = '../../starting_data/database.json'
    targets = tools.load_json(infile)
    for target in targets:
        target.calculate_expiry(threshold)
    targets.sort(key=lambda x: x.current_err)

    depth_limit = 10
    interval = timedelta(days=7)

    mkdir(run_name)
    chdir(run_name)
    for telescope in telescopes:
        with open(telescope.name+'.csv', 'a+') as f:  # add header row to new files
            f.write('#Name, Start(UTC), End(UTC)')
            f.close()

    with open('all_telescopes.csv', 'a+') as f:
        f.write('#Name, Site, Start(UTC), End(UTC)')  # add header row to new file
        f.close()
    print('Using', len(telescopes), 'telescopes')
    print('Simulating from', start.date(), 'until', end.date())

    current = start
    tot_obs = 0
    tot_obs_time = timedelta(days=0)
    count, total = 0, 0
    while current < end:
        total = 0
        count = 0
        required_targets = []
        for target in targets:
            if target.depth is not None:  # check for valid depth
                if float(target.depth) > depth_limit:  # check for real target with required depth
                    total += 1
                    if target.check_if_required(current):  # run expiry calculation
                        count += 1
                        required_targets.append(target)  # add to list if required
        print(current, len(required_targets), count/total*100, count, total, tot_obs)
        visible_transits = []
        for target in required_targets:
            visible = target.transit_forecast(current, current + interval, telescopes)
            for single in visible:
                visible_transits.append(single)

        for telescope in telescopes:
            telescope.observations = []
            matching_transits = []
            for transit in visible_transits:
                if transit.telescope == telescope.name:
                    matching_transits.append(transit)

            obs_results = telescope.schedule_observations(matching_transits)
            tot_obs += obs_results[0]
            tot_obs_time += obs_results[1]
            new_data = telescope.simulate_observations()
            for single in new_data:
                for target in targets:
                    if target.name == single[0]:
                        target.observations.append([single[1], single[2], single[3]])
                        target.last_epoch = single[1]
                        target.last_tmid = single[2]
                        target.last_tmid_err = single[3]
                        target.period_fit()
                        target.calculate_expiry(threshold)

        current += interval
    chdir('../')
    percent = 100-(count/total*100)
    with open('results.csv', 'a+') as f:
        f.write('\n'+str(run_name.split('run')[1])+', '+str(percent)+', '+str(tot_obs)+', '+str(tot_obs_time.total_seconds()/86400))
    print(100-(count/total*100))
