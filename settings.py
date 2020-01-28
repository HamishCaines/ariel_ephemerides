class Settings:
    def __init__(self, infile):
        from datetime import datetime, timedelta

        self.mode = None
        self.telescopes = []
        self.threshold_mode = None
        self.threshold_value = []
        self.start = None
        self.end = None
        self.window = None
        self.repeats = None
        self.simulation_method = None
        self.partial = False
        self.directory = None

        setting_data = open(infile, 'r')

        while True:
            line = setting_data.readline()
            if line == '':
                break
            if len(line.split()) != 0:
                try:
                    key, val = line.split()[0], line.split()[1]

                    if key == 'MODE':
                        self.mode = val
                    elif key == 'TELESCOPES':
                        self.telescopes.append(val)
                    elif key == 'THRESH_MODE':
                        self.threshold_mode = val
                    elif key == 'THRESH_VALUE':
                        self.threshold_value.append(int(val))
                    elif key == 'START':
                        self.start = datetime.strptime(val, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
                    elif key == 'END':
                        self.end = datetime.strptime(val, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
                    elif key == 'WINDOW':
                        self.window = int(val)
                    elif key == 'REPEATS':
                        self.repeats = int(val)
                    elif key == 'METHOD':
                        self.simulation_method = val
                    elif key == 'PARTIAL':
                        if val == 'Y':
                            self.partial = True
                except IndexError:
                    pass

        if self.mode != 'SCHEDULE' and self.mode != 'SIMULATE':
            print('Invalid mode specified, must be either SCHEDULE or SIMULATE')
            raise Exception
        if self.threshold_mode != 'MINS' and self.threshold_mode != 'SIGMA':
            print('Invalid Threshold Mode, must be either MINS or SIGMA')
            raise Exception
        if self.threshold_value is None:
            print('No Accuracy Threshold value specified')
            raise Exception
        if self.telescopes is None:
            print('No Telescope file specified')
            raise Exception
        if self.partial:
            print('Partial transits allowed')
        else:
            print('Partial transits not allowed')

        if self.mode == 'SCHEDULE':
            if self.start is not None:
                if self.window is not None and self.end is None:
                    self.end = self.start + timedelta(days=int(self.window))
                elif self.window is None and self.end is None:
                    print('Require a way to specify end of scheduling window, either END or WINDOW')
                    raise Exception
                elif self.window is not None and self.end is not None:
                    print('Cannot use START, END, and WINDOW, overdefined scheduling window')
                    raise Exception
                elif self.window is None and self.end is not None:
                    if self.end < self.start:
                        print('Cannot end before we start, END is before START')
                        raise Exception

            if self.start is None:
                if self.window is not None:
                    self.start = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
                    self.end = self.start + timedelta(days=int(self.window))
                else:
                    print('Require at least WINDOW if no dates specified')
                    raise Exception

        if self.mode == 'SIMULATE':

            self.start = datetime(year=2020, month=1, day=1)
            self.end = datetime(year=2030, month=1, day=1)
            if self.start is not None or self.end is not None:
                print('Not using dates given, using fixed dates for simulations')

            #if self.repeats is None:
                #print('Must specify number of REPEATS')
                #raise Exception
            if self.repeats is None:  # if not specified, set to 1
                self.repeats = 1
            if self.simulation_method is None:
                print('Must specify simulation mode to use, can be either INITIAL or SELECTIVE')
                raise Exception

        self.obtain_directory_global()

    def obtain_directory_global(self):
        from datetime import datetime
        #directory_name_base = f'{self.simulation_method}_{self.telescopes.split(".")[0]}TEL_{str(self.threshold_value)}{self.threshold_mode}'
        run_datetime = datetime.today()
        run_datetime_str = f'{run_datetime.date()}T{run_datetime.time()}'
        #directory_name = f'{directory_name_base}_{run_datetime_str.split(".")[0].replace(":", "-")}'
        directory_name = f'{run_datetime_str.split(".")[0].replace(":", "-")}'
        print(directory_name)
        self.directory = directory_name

    def obtain_directory_single(self):
        run_dir = f'{self.simulation_method}_{self.telescopes.split(".")[0]}TEL_{str(self.threshold_value)}{self.threshold_mode}'
        self.directory = run_dir







