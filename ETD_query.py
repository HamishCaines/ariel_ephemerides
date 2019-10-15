def read_observations(filename):
    import numpy as np
    import re
    import requests
    from os import remove
    outfile = 'ETD_data.csv'
    try:
        remove(outfile)
        with open(outfile, 'a+') as f:
            f.write('#Name, ObNumber, Epoch, Tmid, TmidErr')
    except FileNotFoundError:
        pass
    targets, real = np.genfromtxt(filename, delimiter=',', unpack=True, usecols=(0, 29), dtype=str, skip_header=1)
    url_base = 'http://var2.astro.cz/ETD/etd.php?'
    for i in range(len(targets)):
        if real[i] == '1':
            target = targets[i]
            print('Querying', target)
            url = url_base + 'STARNAME=' + target[:-1] + '&PLANET=' + target[-1]

            web_html = str(requests.get(url).content)  # obtain html from page for target
            obs_data = re.findall(
                "<tr valign=\\\\\\'top\\\\\\'><td>(\d+)<\/td><td class=\\\\\\'right\\\\\\'><b>([\d\.]+)<br\/><\/b>"
                "([\d\s\.\+\/-]+)<\/td><td>(\d+)<\/td><td>([+|\-\d\.\s]+)<\/td><td>([\d\.\s]+)\+\/-([\d\.\s]+)<\/td><td>"
                "([\d\.]+) ([\d\s\.\+\/-]+)<\/td><td>([\w]+)<\/td><td><b><a href=\\\\\\'etd-data\.php\?id=[\d]+\\\\\\' "
                "target=\\\\\\'[\w]+\\\\\\' title=\\\\\\'get data\\\\\\'>(\d)", web_html)

            for single in obs_data:
                try:
                    tmid_err = single[2].split()[1]
                    ob_number = single[0]
                    tmid = single[1]
                    epoch = single[3]
                    quality = int(single[10])
                    if quality >= 3:
                        with open(outfile, 'a+') as f:
                            f.write('\n'+target+','+ob_number+','+epoch+','+tmid+','+tmid_err)
                            f.close()

                except ValueError:
                    pass
                except IndexError:
                    pass


def main():
    read_observations('full_targetlist.csv')


if __name__ == '__main__':
    main()
