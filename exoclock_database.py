from urllib.request import urlopen
import pylightcurve as plc
import numpy as np
from PyAstronomy import pyasl


class ExoClock:
    def __init__(self):
        import ssl
        import urllib
        from urllib.request import urlretrieve

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        self.database_url = 'https://exoclock.space/database/request'
        # with urllib.request.urlopen(self.database_url, context=ctx) as u, open(…local_file_path…., 'wb') as f:
        #     f.write(u.read())
        online_list = str(urlopen(self.database_url, context=ctx).read()).replace('\\n', '')[2:-1].split('<br>')[:-1]
        online_list = [ff.split(',') for ff in online_list]
        # {print(ff) for ff in online_list}

        self.database = {ff[0]: {'mid_time': float(ff[7]),
                                 'mid_time_error': float(ff[8]),
                                 'period': float(ff[9]),
                                 'period_error': float(ff[10]),
                                 'ra_deg': pyasl.coordsSexaToDeg(f'{ff[1]} {ff[2]}')[0],
                                 'dec_deg': pyasl.coordsSexaToDeg(f'{ff[1]} {ff[2]}')[1],
                                 'mag_v': float(ff[4]),
                                 'depth_mmag': float(ff[5]),
                                 'duration': float(ff[6]) / 24.0,
                                 } for ff in online_list}

    def get_transits(self, planet, start_day, end_day):
        start_bjd = plc.utc_to_bjd_tdb(self.database[planet]['ra_deg'], self.database[planet]['dec_deg'],
                                       '{0} 00:00:00'.format(start_day))
        end_bjd = plc.utc_to_bjd_tdb(self.database[planet]['ra_deg'], self.database[planet]['dec_deg'],
                                     '{0} 23:59:59'.format(end_day))

        start_epoch = int(1 + (start_bjd - self.database[planet]['mid_time']) / self.database[planet]['period'])
        end_epoch = int((end_bjd - self.database[planet]['mid_time']) / self.database[planet]['period'])

        final_list = []
        for epoch in range(start_epoch, end_epoch + 1):
            bjd = self.database[planet]['mid_time'] + epoch * self.database[planet]['period']
            jd = plc.bjd_tdb_to_jd_utc(self.database[planet]['ra_deg'], self.database[planet]['dec_deg'], bjd)
            jd1 = plc.astrotime(jd - self.database[planet]['duration'] / 2, format='jd')
            jd2 = plc.astrotime(jd, format='jd')
            jd3 = plc.astrotime(jd + self.database[planet]['duration'] / 2, format='jd')
            error = np.sqrt(
                self.database[planet]['mid_time_error'] ** 2 + (epoch * self.database[planet]['period_error']) ** 2)
            final_list.append(
                [epoch, jd1.iso.split('.')[0], jd2.iso.split('.')[0], jd3.iso.split('.')[0], round(error * 24 * 60, 1)])

        return final_list
