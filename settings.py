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
                        self.threshold = val
                    elif key == 'START':
                        self.start = datetime.strptime(val, '%Y-%m-%d').date()
                    elif key == 'END':
                        self.end = datetime.strptime(val, '%Y-%m-%d').date()
                    elif key == 'WINDOW':
                        self.window = val
                    elif key == 'REPEATS':
                        self.repeats = val
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

            if self.start is None:
                if self.window is not None:
                    self.start = datetime.today().date()
                    self.end = self.start + timedelta(days=int(self.window))
                else:
                    print('Require at least WINDOW if no dates specified')
                    raise Exception

            if self.window is None and self.end is None:
                print('Require a way to specify the end, either with an end date of window length')

            if self.start is None:
                if self.window is None:
                    print('Require either start and end dates, or a window length to run from today')
                    raise Exception
                else:
                    self.start = datetime.today().date()
                    self.end = self.start + timedelta(days=int(self.window))




