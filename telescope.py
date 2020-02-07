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
        for transit in transits:  # loop through transits
            space = True
            # check for empty schedule
            if len(self.observations) == 0:
                self.observations.append(ob.Observation(transit))
            # if not empty, check for space against existing observations
            else:
                new_ob = ob.Observation(transit)  # initialise Observation
                # check for space
                for scheduled in self.observations:
                    # new observation starts before current one ends
                    if scheduled.start < new_ob.start < scheduled.end:
                        space = False
                    # new observation ends after current one starts
                    elif scheduled.start < new_ob.end < scheduled.end:
                        space = False
                    # new observation surrounds the current one
                    elif new_ob.start < scheduled.start and scheduled.end < new_ob.end:
                        space = False
                if space:  # add to list if space
                    self.observations.append(new_ob)

        self.observations.sort(key=lambda x: x.start)  # sort by date order
        # write scheduled transits to files
        for single in self.observations:
            obs_time += single.duration
            with open('all_telescopes.csv', 'a+') as f:
                f.write('\n' + single.target + ', ' + single.telescope + ', ' + single.start.strftime(
                    "%Y-%m-%dT%H:%M:%S") + ', ' + single.end.strftime("%Y-%m-%dT%H:%M:%S"))
                f.close()
            # output to individual documents per telescope
            with open(single.telescope+'.csv', 'a+') as f:
                f.write('\n' + single.target + ', ' + single.start.strftime(
                    "%Y-%m-%dT%H:%M:%S") + ', ' + single.end.strftime("%Y-%m-%dT%H:%M:%S"))
                f.close()
        return len(self.observations), obs_time

    def simulate_observations(self):
        """
        Simulate the observation of scheduled observations
        :return: List of new data points generated
        """
        new_data = []
        for ob in self.observations:
            month = ob.center.strftime('%B')
            chance = self.weather[month]
            if ob.flip_unfair_coin(chance):  # simulate random chance of failure
                new_data.append(ob.generate_data())  # generate new data and add to list
        return new_data
