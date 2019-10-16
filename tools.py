def load_json(infile):
    """
    Loads database from json output file, created by make_database.py
    :param infile: location of the json file
    :return: list of Target objects containing all the required information
    """
    import json
    import target
    with open(infile) as f:
        data = json.load(f)  # loads a set json outputs into a list
    targets = []
    for single in data:  # create Target object for each json, and load json into it
        new_target = target.Target().init_from_json(single)
        targets.append(new_target)  # add to list
    return targets


def load_telescopes(filename):
    """
    Loads telescope parameters from a .csv file ans stores as a list of Telescope objects
    :param filename: location of data file to be loaded
    :return: List of Telescope objects
    """
    import numpy as np
    import telescope
    data = np.genfromtxt(filename, dtype=str, skip_header=1, delimiter=',')  # read csv data
    telescopes = []
    for single in data:  # create Telescope object for each row and load data into it
        telescopes.append(telescope.Telescope().gen_from_csv(single))
    return telescopes
