class Settings:
    def __init__(self, infile):
        from datetime import datetime, timedelta

        self.mode = None
        self.telescopes = None
        self.threshold = None
        self.start = None
        self.end = None
        self.window = None
        self.repeats = None
        self.simulation_method = None

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
                        self.telescopes = val

                    elif key == 'THRESHOLD':
                        self.threshold = int(val)
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
                except IndexError:
                    pass

        if self.mode != 'SCHEDULE' and self.mode != 'SIMULATE':
            print('Invalid mode specified, must be either SCHEDULE or SIMULATE')
            raise Exception
        if self.threshold is None:
            print('No Accuracy Threshold specified')
            raise Exception
        if self.telescopes is None:
            print('No Telescope file specified')
            raise Exception

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






