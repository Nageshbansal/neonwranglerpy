import re
import os.path
from urllib.request import urlretrieve
from urllib.error import HTTPError
from neonwranglerpy.utilities.tools import get_api, get_month_year_urls, create_temp
from neonwranglerpy.utilities.defaults import NEON_API_BASE_URL
from neonwranglerpy.utilities.getzipurls import get_zip_urls

DATE_PATTERN = re.compile('20[0-9]{2}-[0-9]{2}')


def zips_by_product(dpID,
                    site='all',
                    start_date='',
                    end_date='',
                    package="basic",
                    release="current",
                    savepath='',
                    token=None):
    """Download the data files from NEON API."""
    if dpID[4:5] == 3 and dpID != "DP1.30012.001":
        return f'{dpID}, "is a remote sensing data product and cannot be loaded' \
               f'directly to R with this function.Use the byFileAOP() or ' \
               f'byTileAOP() function to download locally." '

    global zip_dir_path

    if not re.match("DP[1-4]{1}.[0-9]{5}.00[0-9]{1}", dpID):
        return f"{dpID} is not a properly formatted data product ID. The correct format" \
               f" is DP#.#####.00#, where the first placeholder must be between 1 and 4."

    if len(start_date):
        if not re.match(DATE_PATTERN, start_date):
            return 'startdate and enddate must be either NA or valid dates in the form '\
                   'YYYY-MM'

    if len(end_date):
        if not re.match(DATE_PATTERN, end_date):
            return 'startdate and enddate must be either NA or valid dates in the form '\
                   'YYYY-MM'

    if release == 'current':
        api_url = NEON_API_BASE_URL + 'products/' + dpID
        product_req = get_api(api_url, token)
    else:
        api_url = NEON_API_BASE_URL + 'products/' + dpID + '?release' + release
        product_req = get_api(api_url, token).json()

    api_response = product_req.json()

    # if api_response['error']['status']:
    #     print('No data found for product')

    # TODO: check for rate-limit

    # extracting URLs for specific sites
    month_urls = []
    all_urls = []
    for i in range(len(api_response['data']['siteCodes'])):
        all_urls.extend(api_response['data']['siteCodes'][i]['availableDataUrls'])

    if site == 'all':
        month_urls = all_urls
    else:
        if isinstance(site, str):
            site = list(site.split(' '))
        for package in site:
            month_site = [x for x in all_urls if re.search(package, x)]
            month_urls.extend(month_site)

    if not len(month_urls):
        print(f"There is no data for site {site}")

    # extracting urls for specified start and end dates
    if len(start_date):
        month_urls = get_month_year_urls(start_date, month_urls, 'start')

    if not len(month_urls):
        print("There is no data for selected dates")

    if len(end_date):
        month_urls = get_month_year_urls(end_date, month_urls, 'end')

    if not len(month_urls):
        print("There is no data for selected dates")

    # list of all the urls of the files
    temp = get_zip_urls(month_urls, package, dpID, release, token)

    # TODO: calculate download size
    # TODO: user input for downloading or not
    if not len(savepath):
        savepath = "."
        tempdir = create_temp(os.path.abspath(savepath))
        dir_path = os.path.join(tempdir, "filesToStack")
        os.mkdir(dir_path)

    else:
        dir_path = os.path.join(savepath, "filesToStack")
        os.mkdir(dir_path)

    # TODO: add progress bar

    if dir_path:
        for zips in temp:
            dirname = '.'.join([
                'NEON', zips['productCode'], zips['siteCode'], zips['month'],
                zips['release']
            ])
            zip_dir_path = os.path.join(dir_path, f'{dirname}')
            os.mkdir(zip_dir_path)
            for file in zips['files']:
                try:
                    save_path = os.path.join(zip_dir_path, f"{file['name']}")
                    file_path, _ = urlretrieve(file['url'], save_path)

                except HTTPError as e:
                    print("HTTPError :", e)
                    return None
    # returns the path to /filestostack directory
    return dir_path
