import csv
import os
from venv import logger
from bs4 import BeautifulSoup
import requests
import json
from datetime import datetime, timezone
import dateutil.parser


def main_page_scraper(key, value):
    prod_id = key
    print('product id {}'.format(prod_id))
    prod_name = value['name']
    prod_slug = value['url']  # we do not need to store this in the final csv
    prod_url = 'https://drop.com/buy/' + prod_slug
    print('product url {}'.format(prod_url))
    prod_image = value['thumbImage']
    prod_category_id = value['primaryCategoryId']
    prod_is_active = value['isActive']
    prod_is_best_in_category = value['isBestOf']
    prod_is_custom = value['isCustom']
    prod_is_new = value['isNewArrival']
    prod_max_drop_size = value['maxDropSize']
    prod_num_favourites = value['numFavorites']
    prod_num_reviews = value['numReviews']
    prod_dev_phase = value['developmentPhase']
    print('product dev phase: {}'.format(prod_dev_phase))
    prod_recommended_yes = value['recommendedYesResponses']
    prod_recommended_total = value['recommendedTotalResponses']
    prod_total_sold = value['totalSold']
    prod_average_review_score = value['averageReviewScore']
    prod_collection_ids = value['collections']  # stores the product's collections as a list of IDs, we wont know what these numbers mean until we dig deeper
    prod_is_refundable = value['isReturnable']
    prod_drop_start = value['startAt']
    start_datetime = dateutil.parser.parse(prod_drop_start)
    today_datetime = datetime.now(timezone.utc)
    prod_days_active = abs((today_datetime - start_datetime).days)  # calculates how long a drop has been active by taking the difference between today's date and the startAt date (not including today's date)
    prod_attrs = {'prod_id':prod_id, 'prod_name':prod_name, 'prod_url':prod_url, 'prod_image':prod_image, 'prod_category_id':prod_category_id, 'prod_is_active':prod_is_active,
                  'prod_is_best_in_category':prod_is_best_in_category, 'prod_is_custom':prod_is_custom, 'prod_is_new':prod_is_new, 'prod_max_drop_size':prod_max_drop_size,
                  'prod_num_favourites':prod_num_favourites, 'prod_num_reviews':prod_num_reviews, 'prod_dev_phase':prod_dev_phase, 'prod_recommended_yes':prod_recommended_yes,
                  'prod_recommended_total':prod_recommended_total, 'prod_total_sold':prod_total_sold, 'prod_average_review_score':prod_average_review_score,
                  'prod_collection_ids':prod_collection_ids, 'prod_is_refundable':prod_is_refundable, 'prod_drop_start':prod_drop_start, 'prod_days_active':prod_days_active}
    if prod_attrs['prod_dev_phase'] != 1:
        product_page_scraper(prod_attrs)
        checkout_page_scraper(prod_attrs)

    return prod_attrs


# Scrapes info from the product page
## url = https://drop.com/buy/<prod_slug>
## msrp price
## massdrop price
## specs (if available)/details
## discount: calculate as difference between retail price and massdrop price
## image gallery
## description
## recommendation percentage
## color/style options
def product_page_scraper(row_values):
    prod_varieties = []
    prod_gallery = []
    prod_id = row_values['prod_id']
    xhr_url = 'https://drop.com/api/drops;dropUrl={};isPreview=false;noCache=false;withPrices=true?lang=en-US&returnMeta=true'.format(prod_id)
    prod_raw = requests.get(xhr_url).text  # download the raw json
    prod_dict = json.loads(prod_raw)  # parse it into a dict
    prod_msrp_price = prod_dict['data']['msrpPrice']

    prod_massdrop_price = prod_dict.get('data', {}).get('currentPrice')
    prod_category_name = prod_dict['data']['primaryCategoryName']
    prod_is_promo = prod_dict['data']['isPromo']
    content_dict = prod_dict.get('data', {}).get('description', {}).get('content')
    print(prod_dict['data']['description'])

    for dic in content_dict:
        if 'Specs' in dic.values():
            # replace all instances of <li> or </li> with nothing
            dic['copy'] = dic['copy'].replace('\n', '')
            dic['copy'] = dic['copy'].replace('\t', '')
            soup = BeautifulSoup(dic['copy'], features="html.parser")
            text = soup.get_text(',')
            specs_list = [x.strip() for x in text.split(',')]
            for s in specs_list:   # remove blank items from list
                if s == '':
                    specs_list.remove(s)

    if prod_msrp_price and prod_massdrop_price is not None:
        prod_discount = prod_msrp_price - prod_massdrop_price
    else:
        prod_discount = 0

    for list_item in content_dict:
        if 'images' in list_item:
            for image in list_item['images']:
                prod_gallery.append(image['src'])

    soup = BeautifulSoup(content_dict[0]['copy'], features="html.parser")
    prod_description = soup.get_text()
    prod_recommended_total = row_values['prod_recommended_total']
    prod_recommended_yes = row_values['prod_recommended_yes']

    if prod_recommended_total != 0:
        prod_recommended_pc = prod_recommended_yes / prod_recommended_total
    else:
        prod_recommended_pc = 0

    try:
        for i in content_dict:
            if i['layout'] == 'hoverGallery':
                for j in i['images']:
                    prod_varieties.append(j['title'])
    except KeyError as error:
        logger.info(error)

    row_values.update({'prod_msrp_price':prod_msrp_price, 'prod_massdrop_price':prod_massdrop_price, 'prod_category_name':prod_category_name,
                       'prod_is_promo':prod_is_promo, 'prod_discount':prod_discount, 'prod_gallery':prod_gallery, 'prod_description':prod_description,
                       'prod_recommended_pc':prod_recommended_pc, 'prod_varities':prod_varieties})


# Scrapes info from the product checkout page
## url = https://drop.com/payment/<prod_id>
## final price
## shipping cost
## taxes
def checkout_page_scraper(row_values):
    prod_id = row_values['prod_id']
    payment_url = 'https://drop.com/api/orderTotal;commitType=2;country=US;dropId={};' \
                  'orders=%5B%7B%22options%22%3A%5B898470%5D%2C%22customOptions%22%3A%5B%5D%2C%22quantity%22%3A1%7D%5D;' \
                  'postalCode=;state=?lang=en-US&returnMeta=true'.format(prod_id)
    # download the raw json
    payment_raw = requests.get(payment_url).text
    # parse it into a dict
    payment_dict = json.loads(payment_raw)
    prod_total_cost = payment_dict.get('data', {}).get('total')
    prod_taxes = payment_dict.get('data', {}).get('taxRateTotal')
    prod_shipping = payment_dict.get('data', {}).get('shipping')
    row_values.update({'prod_total_cost':prod_total_cost, 'prod_taxes':prod_taxes, 'prod_shipping':prod_shipping})


def write_to_file(prod_attrs):
    output_file = 'massdrop-products.csv'
    # TODO fix the headings so that they match with the data order
    if os.path.exists(output_file):
        file = open(output_file, 'a', newline='', encoding='utf-8')  # append if file already exists
    else:
        file = open(output_file, 'w', newline='', encoding='utf-8')  # make a new file if not
        writer = csv.DictWriter(file, fieldnames=list(prod_attrs.keys()))  # write headers to new file
        writer.writeheader()

    write_outfile = csv.writer(file)
    write_outfile.writerow(list(prod_attrs.values()))
    return file


def main():
    offset_counter = 0  # keeps track of how many dictionaries there are
    if os.path.exists('massdrop-products.csv'):
        os.remove('massdrop-products.csv')  # deletes the file on every run so we have a clean slate
    else:
        print('Nothing to delete')

    for offset in range(20, 1000, 20):
        offset_counter = offset_counter + 1

        search_url = 'https://drop.com/api/feed;contentTypes=drops;endpoint=dynamicFeed;offset={' \
                     '};query=*?lang=en-US&returnMeta=true'.format(offset)
        search_raw = requests.get(search_url).text  # downloads the raw json
        search_dict = json.loads(search_raw)  # converts from json string to python dictionary

        catalog_dict = search_dict['data']['contentData']['dropSummaries']  # stores just the products

        for key, value in catalog_dict.items():  # iterates through key value pairs in the dictionary
            prod_attrs = main_page_scraper(key, value)
            print('Writing to file: {}'.format(prod_attrs))
            outfile = write_to_file(prod_attrs)

    outfile.close()


main()
