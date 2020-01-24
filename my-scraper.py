import csv
import os

from html.parser import HTMLParser
import requests
import json
from pprint import pprint
from datetime import datetime, timezone
import dateutil.parser



# increase offset by 20 on each iteration (eg. 20, 40, 60)
# last iteration will have offset=980 (cant go past 1000)
search_url = 'https://drop.com/api/feed;contentTypes=drops;endpoint=dynamicFeed;offset=20;query=*?lang=en-US&returnMeta=true'

# download the raw JSON
search_raw = requests.get(search_url).text

# parse it into a dict
search_dict = json.loads(search_raw)
# gets just the prods
catalog_dict = search_dict['data']['contentData']['dropSummaries']
# pprint(prods_dict)
# key_list = list(prods_dict)
# first_key = key_list[0]
# first_prod = prods_dict[list(prods_dict)[0]]
# pprint(first_prod)

for key, value in catalog_dict.items():
    prod_id = key
    # print(value)
    print('prod_id {}'.format(prod_id))
    prod_name = value['name']
    # print(prod_name)
    prod_slug = value['url']
    # print(prod_slug)
    prod_url = 'https://drop.com/buy/' + prod_slug
    print(prod_url)
    prod_image = value['thumbImage']
    # print(prod_image)

    # to do: we will get the prod price by following the url and grabbing it from the product page
    # to do: we will get the prod gallery by following the url and grabbing it from the product page

    prod_category_id = value['primaryCategoryId']
    #  print(prod_category_id)

    # to do: find what the category ids correspond to by following the url and grabbing the first category from the product page (eg. 8 = mechnical keyboards)

    # prods created by massdrop, store the raw values in the CSV (1 = true, 0 = false)
    prod_active = value['isActive']
    prod_bestInCategory = value['isBestOf']
    prod_custom = value['isCustom']
    prod_new = value['isNewArrival']
    prod_maxDropSize = value['maxDropSize']
    prod_numFavourites = value['numFavorites']
    prod_numReviews = value['numReviews']
    prod_recommendedYes = value['recommendedYesResponses']
    prod_recommendedTotal = value['recommendedTotalResponses']

    try:
        prod_freeShipping = value['badges'][1]['type']
    except:
        prod_freeShipping = 'paidShipping'
    # print(prod_freeShipping)

    prod_totalSold = value['totalSold']
    prod_averageReviewScore = value['averageReviewScore']
    # stores the product's collections as a list of IDs, we wont know what these numbers mean until we dig deeper
    # to do: find where these collections are stored on the site
    prod_collections = value['collections']

    # this feature is useless to us since its not fixed, will change at some point in the future
    # prod_developmentPhase = value['developmentPhase']
    prod_refundable = value['isReturnable']
    prod_dropStart = value['startAt']
    start_datetime = dateutil.parser.parse(prod_dropStart)
    today_datetime = datetime.now(timezone.utc)
    # calculates how long a drop has been active by taking the difference between today's date and the startAt date (not including today's date)
    prod_daysActive = abs((today_datetime - start_datetime).days)
    # print(prod_daysActive)

    #####################################################
    # this section scrapes info from the product page
    # info we will collect
        # msrp price
        # massdrop price
        # specs (if available)/details
        # discount: calculate as difference between retail price and massdrop price
        # image gallery
        # full description
        # recommendation percentage (previously recommendation ratio)
        # color/style options: check if key called layout with value hoverGallery exists, grab the titles in the images array 
        # scrape this url: https://drop.com/api/drops;dropUrl=<prod_id>;isPreview=false;noCache=false;withPrices=true?lang=en-US&returnMeta=true
    prod_url = 'https://drop.com/api/drops;dropUrl={};isPreview=false;noCache=false;withPrices=true?lang=en-US&returnMeta=true'.format(prod_id)
    # print(prod_url)
    # download the raw JSON
    prod_raw = requests.get(prod_url).text
    # parse it into a dict
    prod_dict = json.loads(prod_raw)
    # print(prod_dict)
    # note that any custom massdrop products wont have an msrp price since theyre only sold on the massdrop site (you are already getting the best price)
    prod_msrpPrice = prod_dict['data']['msrpPrice']
    # print('prod_msrpPrice {}'.format(prod_msrpPrice))
    prod_massdropPrice = prod_dict['data']['currentPrice']
    # print('prod_massdropPrice {}'.format(prod_massdropPrice))

    content_dict = prod_dict['data']['description']['content']
    # prints the dict that contains specs as heading
    for dic in content_dict:
        if 'Specs' in dic.values():
            # replace all instances of <li> or </li> with nothing
            dic['copy'] = dic['copy'].replace('\n', '')
            dic['copy'] = dic['copy'].replace('\t', '')
            print('specs ' + dic['copy'])
    ##########################################
    # this sections scrapes info from the product shipping page
    # follow this url: https://drop.com/payment/<prod_id> and scrape this XHR file https://drop.com/api/orderTotal;commitType=2;country=US;dropId=<prod_id>;orders=%5B%7B%22options%22%3A%5B898470%5D%2C%22customOptions%22%3A%5B%5D%2C%22quantity%22%3A1%7D%5D;postalCode=;state=?lang=en-US&returnMeta=true
    # info to collect
        # final price
    payment_url = 'https://drop.com/api/orderTotal;commitType=2;country=US;dropId={};' \
                  'orders=%5B%7B%22options%22%3A%5B898470%5D%2C%22customOptions%22%3A%5B%5D%2C%22quantity%22%3A1%7D%5D;' \
                  'postalCode=;state=?lang=en-US&returnMeta=true'.format(prod_id)
    # print(payment_url)
    # download the raw JSON
    payment_raw = requests.get(payment_url).text
    # parse it into a dict
    payment_dict = json.loads(payment_raw)
    # print(payment_dict)
    prod_totalCost = payment_dict['data']['total']
    # print('prod_totalCost {}'.format(prod_totalCost))
# if a file with this name already exists remove it, otherwise create it and add headers and write to it
try:
    os.remove('massdrop-products.csv')
except OSError:
    file = csv.writer(open('massdrop-products.csv', 'a'))
    # to do: update this line
    file.writerow(['ID', 'Name', 'Link', 'Image', 'Price', 'PrimaryCategoryId', 'PrimaryCategoryName', 'Custom'])
    # to do: update this line
    file.writerow([prod_id])
