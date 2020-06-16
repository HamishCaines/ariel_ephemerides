import random
from datetime import timedelta
import julian
from random import gauss


class Observation:
    def __init__(self, transit, number):
        self.target = transit.name
        self.center = transit.center
        if transit.ingress_visible:
            self.start = transit.ingress - timedelta(minutes=45)
        else:
            self.start = transit.visible_from
        if transit.egress_visible:
            self.end = transit.egress + timedelta(minutes=45)
        else:
            self.end = transit.visible_until
        self.telescope = transit.telescope
        self.duration = self.end - self.start

        self.tmid = None
        self.tmid_err = None
        self.epoch = transit.epoch

        self.telescope_used = number

    def generate_data(self):
        new_tmid_exp = julian.to_jd(self.center, fmt='jd') - 2400000
        new_tmid = gauss(new_tmid_exp, 0.5 / 24 / 60)
        new_tmid_err = abs(gauss(0.5, 0.01) / 24 / 60)
        return self.target, self.epoch, new_tmid, new_tmid_err

    def flip_unfair_coin(self, chance):
        """
        Determines the success of an observation by flipping a weighted coin
        :return: Success: boolean
        """
        return True if random.random() < chance else False
        # return True

    def determine_success(self, total_chance):
        block_chance = total_chance ** (1/4)
        block_success = 0
        fail = False
        while block_success < 4 and not fail:
            if self.flip_unfair_coin(block_chance):
                block_success += 1
            else:
                fail = True
        time_used = self.duration * (block_success/4)
        if fail:
            success = False
        else:
            success = True
        return success, time_used
