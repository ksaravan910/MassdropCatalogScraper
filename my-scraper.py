import csv
import os
import requests
import json
from pprint import pprint

# if a file with this name already exists remove it, otherwise create it and add headers
# to do: fix this so it does return an error on the first run (subsequent runs are fine)
try:
    os.remove('massdrop-products.csv')
except OSError:
    file = csv.writer(open('massdrop-products.csv', 'a'))
    file.writerow(['ID', 'Name', 'Link', 'Image', 'Price', 'PrimaryCategoryId', 'PrimaryCategoryName', 'Custom'])

# increase offset by 20 on each iteration (eg. 20, 40, 60)
# last iteration will have offset=980 (cant go past 1000)
json_url = 'https://drop.com/api/feed;contentTypes=drops;endpoint=dynamicFeed;offset=20;query=*?lang=en-US&returnMeta=true'

# download the raw JSON
raw = requests.get(json_url).text

# parse it into a dict
json_dict = json.loads(raw)
# gets just the items
items_dict = json_dict['data']['contentData']['dropSummaries']
# pprint(items_dict)
# key_list = list(items_dict)
# first_key = key_list[0]
first_item = items_dict[list(items_dict)[0]]
# pprint(first_item)

for key, value in items_dict.items():
    item_id = key
    # print(item_id)
    item_name = value['name']
    # print(item_name)
    item_url = 'https://drop.com/buy/' + value['url']
    print(item_url)
    item_image = value['thumbImage']

    # to do: we will get the item price by following the url and grabbing it from the product page

    item_category_id = value['primaryCategoryId']
    print(item_category_id)

    # to do: find what the category ids correspond to by following the url and grabbing the first category from the product page (eg. 8 = mechnical keyboards)

    # items created by massdrop, store the raw values in the CSV (1 = true, 0 = false)
    item_custom = value['isCustom']
    item_bestInCategory = value['isBestOf']

    # write all item values in the CSV file
    file.writerow([item_id])