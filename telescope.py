from datetime import timedelta

class Telescope:
    """
    Telescope object, contains physical information about the location of the telescope
    """
    def __init__(self):
        """
        Null constructor
        """
        self.number = None
        self.name = None
        self.lat = None
        self.lon = None
        self.alt = None
        self.aperture = None
        self.observations = []
        self.weather = {}
        self.location = None
        self.cloud_allowed = None
        self.copies = None

    def __str__(self):
        return self.name+' Lat: '+str(self.lat)+' Lon: '+str(self.lon)

    def gen_from_csv(self, row):
        """
        Fills Telescope object with data from .csv file
        :param row: list of values read from .csv file
        :return: Filled object
        """
        from datetime import datetime
        self.number = int(row[0])
        self.name = row[1]
        self.lat = float(row[2])
        self.lon = float(row[3])
        self.alt = int(row[4])
        self.aperture = float(row[5])
        weather = row[6:18]
        for i in range(1, 13):
            month = datetime(year=2019, month=i, day=1).date().strftime('%B')
            self.weather[f'{month}'] = float(weather[i-1])
        self.location = row[18]
        self.cloud_allowed = float(row[19])
        self.copies = int(float(row[21]))

        return self

    def schedule_observations(self, transits):
        """
        Schedules observations of the visible transits given, including baseline time and making sure there
        is no overlap
        :param transits:  List of Transit objects to be scheduled
        :return: Number of observations scheduled, and the total observation time used
        """
        import observation as ob
        from datetime import timedelta
        obs_time = timedelta(days=0)
        self.observations = []
        telescopes_used = 0
        while telescopes_used < self.copies:
            new_observations = []
            telescopes_used += 1
            for transit in transits:  # loop through transits
                if not transit.scheduled:
                    space = True
                    # check for empty schedule
                    if len(new_observations) == 0:
                        new_observations.append(ob.Observation(transit, telescopes_used))
                        transit.scheduled = True
                    # if not empty, check for space against existing observations
                    else:
                        new_ob = ob.Observation(transit, telescopes_used)  # initialise Observation
                        # check for space
                        for scheduled in new_observations:
                            # new observation starts before current one ends
                            if scheduled.start <= new_ob.start <= scheduled.end:
                                space = False
                            # new observation ends after current one starts
                            elif scheduled.start <= new_ob.end <= scheduled.end:
                                space = False
                            # new observation surrounds the current one
                            elif new_ob.start <= scheduled.start and scheduled.end <= new_ob.end:
                                space = False
                        if space:  # add to list if space
                            new_observations.append(new_ob)
                            transit.scheduled = True
            for single in new_observations:
                self.observations.append(single)

        self.observations.sort(key=lambda x: x.start)  # sort by date order
        # write scheduled transits to files
        for single in self.observations:
            obs_time += single.duration
            with open('all_telescopes.csv', 'a+') as f:
                f.write('\n' + single.target + ', ' + single.telescope + ', ' + single.start.strftime(
                    "%Y-%m-%dT%H:%M:%S") + ', ' + single.end.strftime("%Y-%m-%dT%H:%M:%S") + ', ' + str(single.telescope_used))
                f.close()
            # output to individual documents per telescope
            with open(single.telescope+'.csv', 'a+') as f:
                f.write('\n' + single.target + ', ' + single.start.strftime(
                    "%Y-%m-%dT%H:%M:%S") + ', ' + single.end.strftime("%Y-%m-%dT%H:%M:%S") + ', ' + str(single.telescope_used))
                f.close()
        return len(self.observations), obs_time

    def simulate_observations(self):
        """
        Simulate the observation of scheduled observations
        :return: List of new data points generated
        """
        new_data = []
        time = timedelta(minutes=0)
        for ob in self.observations:
            month = ob.center.strftime('%B')
            total_chance = self.weather[month]
            result = ob.determine_success(total_chance)
            time += result[1]
            if result[0]:  # simulate random chance of failure
                new_data.append(ob.generate_data())  # generate new data and add to list
        return new_data, time

