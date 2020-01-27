class Transit:
    """
    Transit object, contains information of individual transits, can calculate whether it is visible from specified
    telescopes
    """
    def __init__(self):
        """
        Null constructor
        """
        self.date = None
        self.name = None
        self.center = None
        self.ingress = None
        self.egress = None
        self.duration = None
        self.ra = None
        self.dec = None
        self.period = None
        self.epoch = None
        self.ingress_visible = None
        self.egress_visible = None

        self.depth = None

        self.telescope = []
        self.visible_from = None
        self.priority = 0

    def __str__(self):
        """
        Changes string output based on the number of telescopes a transit is observable from
        :return: Output string
        """
        if len(self.telescope) == 1:
            return self.name + ' ' + self.telescope[0] + ' In/Cen/Eg: ' + str(self.ingress) + ' ' + str(
                self.center) + ' ' + str(self.egress)
        elif len(self.telescope) > 3:
            return self.name + ' ' + self.telescope + ' In/Cen/Eg: ' + str(self.ingress) + ' ' + str(
                self.center) + ' ' + str(self.egress)
        else:
            start = self.name+' '
            for single in self.telescope:
                start += single+' '
            start += 'In/Cen/Eg: '+str(self.ingress)+' '+str(self.center)+' '+str(self.egress)
            return start

    def init_for_forecast(self, values_dict, ephemeris, epoch):
        """
        Fills a transit object from the predicted ephemeris and epoch, and target information from a Target object
        :param values_dict: dictionary of variables from Target object: dict
        :param ephemeris: expected ephemeris for the transit: datetime
        :param epoch: epoch of transit being forecast: int
        :return: Filled Transit object
        """
        from datetime import timedelta
        self.name = values_dict['name']
        self.center = ephemeris
        self.duration = timedelta(minutes=values_dict['duration'])
        # calculate ingress and egress from predicted ephemeris and transit duration
        self.ingress = ephemeris - self.duration/2
        self.egress = ephemeris + self.duration/2
        self.epoch = epoch

        self.ra = float(values_dict['ra'])
        self.dec = float(values_dict['dec'])

        self.depth = float(values_dict['depth'])

        return self

    def check_transit_visibility(self, telescopes, observable_from, settings):
        """
        Checks visibility of a Transit object from the set of telescopes provided, adds suitable sites to container
        :param observable_from:
        :param telescopes: List of Telescope objects for the telescopes available
        """
        import mini_staralt
        import datetime
        # loop over all telescopes
        for telescope in telescopes:
            if telescope.name in observable_from:
                # check for night at coordinate
                sunset, sunrise = mini_staralt.sun_set_rise(
                    self.center.replace(hour=0, second=0, minute=0, microsecond=0), lon=telescope.lon, lat=telescope.lat, sundown=-20)
                # if calculation made for wrong day, step back and recalculate
                if sunset > self.center:
                    sunset, sunrise = mini_staralt.sun_set_rise(
                        self.center.replace(hour=0, second=0, minute=0, microsecond=0) - datetime.timedelta(
                            days=1),
                        lon=telescope.lon, lat=telescope.lat, sundown=-20)

                if self.check_rise_set(sunset, sunrise, settings):  # continue only if night at location
                    try:
                        # calculate target rise/set times
                        target_rise, target_set = mini_staralt.target_rise_set(
                            self.center.replace(hour=0, minute=0, second=0, microsecond=0),
                            ra=self.ra, dec=self.dec, mintargetalt=30, lon=telescope.lon, lat=telescope.lat)

                        # if calculation made for wrong day, step back and recalculate
                        if target_rise > self.center:
                            target_rise, target_set = mini_staralt.target_rise_set(
                                self.center.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(
                                    days=1),
                                ra=self.ra, dec=self.dec, mintargetalt=30, lon=telescope.lon, lat=telescope.lat)

                        if self.check_rise_set(target_rise, target_set, settings.partial):  # check if transit is visible
                            self.telescope.append(telescope.name)  # add telescope to Transit object

                    except mini_staralt.NeverVisibleError:
                        pass
                    except mini_staralt.AlwaysVisibleError:
                        # target is always visible
                        self.telescope.append(telescope.name)

    def check_rise_set(self, rise_time, set_time, partial):
        """
        Check if a transit occurs between the two times specified. If it is not, we check for partial transit of
        55% of full duration. Setting rise_time to sunset and set_time to sunrise checks whether the transit happens at
        night for the location the times are computed for
        :param rise_time: Time the target rises calculated from staralt, for a specific date and location: datetime
        :param set_time: Time the target sets calculated from staralt, for a specific date and location: datetime
        :return: Boolean for target visibility
        """
        if self.ingress > rise_time:  # check for visible ingress
            self.ingress_visible = True
            if self.egress < set_time:  # check for visible egress
                self.egress_visible = True
                return True  # visible ingress + visible egress: full transit visible

            elif partial and set_time - self.ingress > 0.55 * self.duration:  # check if visible duration exceeds 55%: partial transit visible
                self.egress_visible = False
                self.egress = set_time  # set egress to be late limit
                return True
        elif partial and self.egress < set_time:  # check for visible egress
            self.egress_visible = True
            if self.egress - rise_time > 0.55 * self.duration:  # check if visible duration exceeds 55%: partial transit visible
                self.ingress_visible = False
                self.ingress = rise_time  # set ingress to be early limit
                return True
        return False  # neither ingress or egress visible

    def calculate_priority(self, target):
        """
        Calculates a priority for a given transit, based on the visibility of the transit, prior observations,
        and the current data
        :param target: Target object
        :return:
        """
        import julian
        from _datetime import datetime, timedelta
        counter = 0
        print(target.name, self.center)
        # only visible from 1 telescope
        if self.visible_from == 1:
            counter += 2
            print('single')
        # last observation is over 2 years old
        if datetime.today() - julian.from_jd(target.last_tmid + 2400000, fmt='jd') > timedelta(days=730):
            counter += 1
            print('old')
        # high current error, currently all targets, as only selecting those that have expired
        #if target.current_err > 10:
        #    counter += 3
        # long period
        if target.period > 30:
            print('long period')
            counter += 2
        self.priority = counter


