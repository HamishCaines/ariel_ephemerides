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
