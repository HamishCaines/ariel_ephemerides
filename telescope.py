class Telescope:
    """
    Telescope object, contains physical information about the location of the telescope
    """
    def __init__(self):
        """
        Null constructor
        """
        self.name = None
        self.lat = None
        self.lon = None
        self.alt = None
        self.aperture = None
        self.observations = []

    def __str__(self):
        return self.name+' Lat: '+str(self.lat)+' Lon: '+str(self.lon)

    def gen_from_csv(self, row):
        """
        Fills Telescope object with data from .csv file
        :param row: list of values read from .csv file
        :return: Filled object
        """
        self.name = row[0]
        self.lat = float(row[1])
        self.lon = float(row[2])
        self.alt = int(row[3])
        self.aperture = float(row[4])
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
            if ob.flip_unfair_coin():  # simulate random chance of failure
                new_data.append(ob.generate_data())  # generate new data and add to list
        return new_data
