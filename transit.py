import mini_staralt
import datetime
import numpy as np
from datetime import timedelta

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
        self.visible_fraction = None
        self.visible_from = None
        self.visible_until = None
        self.scheduled = False
        self.magnitude = None

        self.depth = None

        self.telescope = []
        self.visible_tels = None
        self.priority = 0

        self.target_rise = None
        self.target_set = None

        self.sunset = None
        self.sunrise = None
        self.visible = None

        self.moon_phase = None
        self.moon_alt = None
        self.cheap_moon = None

        self.days_to_next_visible = None
        self.days_to_next_full = None
        self.visible_in_next_30 = 0

        self.run_start = None
        self.run_end = None
        self.series = {}

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
        self.period = float(values_dict['period'])

        self.magnitude = float(values_dict['star_mag'])

        return self

    def obtain_sun_set_rise(self, telescope):
        self.sunset, self.sunrise = mini_staralt.sun_set_rise(
            self.center.replace(hour=0, second=0, minute=0, microsecond=0), lon=telescope.lon, lat=telescope.lat,
            sundown=-20)
        #self.sunset, self.sunrise = sunset, sunrise
        # if calculation made for wrong day, step back and recalculate
        if self.sunset > self.center:
            self.sunset, self.sunrise = mini_staralt.sun_set_rise(
                self.center.replace(hour=0, second=0, minute=0, microsecond=0) - datetime.timedelta(
                    days=1),
                lon=telescope.lon, lat=telescope.lat, sundown=-20)
        #return sunset, sunrise

    def obtain_target_rise_set(self, telescope):
        try:
            # calculate target rise/set times
            self.target_rise, self.target_set = mini_staralt.target_rise_set(
                self.center.replace(hour=0, minute=0, second=0, microsecond=0),
                ra=self.ra, dec=self.dec, mintargetalt=30, lon=telescope.lon, lat=telescope.lat)

            # if calculation made for wrong day, step back and recalculate
            if self.target_rise > self.center:
                self.target_rise, self.target_set = mini_staralt.target_rise_set(
                    self.center.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(
                        days=1),
                    ra=self.ra, dec=self.dec, mintargetalt=30, lon=telescope.lon, lat=telescope.lat)

        except mini_staralt.NeverVisibleError:
            self.target_rise = datetime.datetime(year=1, month=1, day=1, hour=0, minute=0, second=0)
            self.target_set = datetime.datetime(year=1, month=1, day=1, hour=0, minute=0, second=1)
        except mini_staralt.AlwaysVisibleError:
            # target is always visible
            self.target_rise = self.sunset
            self.target_set = self.sunrise
            # self.telescope.append(telescope.name)

        #return target_rise, target_set

    def check_visibility_limits(self):
        if self.sunset >= self.target_rise:
            self.visible_from = self.sunset
        else:
            self.visible_from = self.target_rise

        if self.sunrise <= self.target_set:
            self.visible_until = self.sunrise
        else:
            self.visible_until = self.target_set

    def check_gress_visible(self, partial):
        if self.visible_from < self.ingress < self.visible_until:
            self.ingress_visible = True
        else:
            self.ingress_visible = False
        if self.visible_from < self.egress < self.visible_until:
            self.egress_visible = True
        else:
            self.egress_visible = False

        if self.ingress_visible and self.egress_visible:
            self.visible_fraction = 1
            self.visible = True
        elif partial and self.ingress_visible and not self.egress_visible:
            self.visible_fraction = np.round((self.visible_until - self.ingress)/self.duration, 2)
            if self.visible_fraction > 0.55:
                self.visible = True
        elif partial and not self.ingress_visible and self.egress_visible:
            self.visible_fraction = np.round((self.egress - self.visible_from)/self.duration, 2)
            if self.visible_fraction > 0.55:
                self.visible = True
        else:
            self.visible = False

    def check_transit_visibility(self, telescope, settings):
        """
        Checks visibility of a Transit object from the Telescope, adds suitable sites to container
        :param telescope: Telescope object for telescope being tested
        """
        self.obtain_sun_set_rise(telescope)
        self.obtain_target_rise_set(telescope)
        self.check_visibility_limits()
        self.check_gress_visible(settings.partial)
        self.check_moon(telescope)
        if self.moon_phase > settings.moon_phase and self.moon_alt > settings.moon_alt:
            self.cheap_moon = True

        if self.visible and self.cheap_moon:
            self.telescope = telescope.name
        if 'HIP41378' in self.name:
            self.telescope = telescope.name

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
        if self.visible_tels == 1:
            counter += 2
            # print('single')
        # last observation is over 2 years old
        if datetime.today() - julian.from_jd(target.last_tmid + 2400000, fmt='jd') > timedelta(days=730):
            counter += 1
            # print('old')
        # high current error, currently all targets, as only selecting those that have expired
        #if target.current_err > 10:
        #    counter += 3
        # long period
        if target.period > 30:
            print('long period')
            counter += 2
        self.priority = counter

    def check_moon(self, telescope):
        self.moon_phase = round(mini_staralt.get_moon_phase(self.center), 3)
        self.moon_alt = mini_staralt.get_moon_alt(self.center, telescope)

    def determine_strategy(self, strategy_data):
        telescope = None
        if self.telescope == 'Spain':
            telescope = 'SPA-2'
        elif self.telescope == 'ElSauce':
            telescope = 'CHI-1'
        if telescope is not None:
            try:

                strategy = strategy_data[f'{self.name}_{telescope}']
                self.run_start = self.center + timedelta(minutes=strategy['start_time'])
                self.run_end = self.center + timedelta(minutes=strategy['end_time'])
                self.series = strategy['series']
            except KeyError:
                pass






