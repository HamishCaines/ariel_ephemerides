#################################################################
# Loads the target list and ETD observations from .csv files
# into Target objects and then outputs in json
# Hamish Caines 10/2019
#################################################################


def collect_data():
    """
    Loads target list and ETD data from csv files, and stores in Target objects
    :return: List of Target objects containing all required information and available observations
    """
    import numpy as np
    import target
    target_list = '../starting_data/full_targetlist.csv'  # target list
    # load required colummns
    target_list_data = np.genfromtxt(target_list, unpack=False, usecols=(0, 1, 2, 3, 4, 5, 16, 17, 20, 6, 29), delimiter=',',
                                     dtype=str, skip_header=1)
    etd_file = '../starting_data/ETD_data.csv'  # ETD data file
    etd_data = np.genfromtxt(etd_file, unpack=False, delimiter=',', dtype=str)  # load data
    # TODO: add TESS data
    targets = []

    for i in range(len(target_list_data)):  # for each target
        # create new Target object and load target list into it
        new_target = target.Target().init_from_list(target_list_data[i])
        if new_target.name in etd_data:  # check if target has ETD data
            # find ETD data for this target
            for j in etd_data:
                if j[0] == new_target.name:
                    # load ETD observation into Target object
                    if float(j[3]) > new_target.last_tmid:  # check for most recent observation
                        # update most recent data
                        new_target.last_epoch = int(j[2])
                        new_target.last_tmid = float(j[3])
                        new_target.last_tmid_err = float(j[4])
                    # add observation to list
                    new_target.observations.append([int(j[2]), float(j[3]), float(j[4])])
        print(new_target.name, new_target.depth)
        targets.append(new_target)  # add new Target object to list

    return targets


def write_json(outfile, data):
    """
    Write data for a list of objects out in json format, one per object
    :param outfile: name and location of output file
    :param data: list of objects to be outputted
    """
    import json
    with open(outfile, 'w') as f:  # dump each object as single json dictionary
        json.dump(data, f)
    f.close()


def main():
    from os import remove
    outfile = '../starting_data/database.json'  # output file
    # check for existing file
    try:
        remove(outfile)
    except FileNotFoundError:
        pass
    targets = collect_data()  # load all available data
    json_out = []
    for target in targets:  # loop through targets and check for None values
        print('Checking', target.name)
        if None in vars(target).values():
            target.find_missing_values()  # attempt to find missing values
        json_out.append(target.__dict__)  # convert to dictionary and add to list
    write_json(outfile, json_out)  # write json output


if __name__ == '__main__':
    main()
