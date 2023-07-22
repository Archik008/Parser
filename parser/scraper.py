import requests
from bs4 import BeautifulSoup
import csv
import urllib.parse
import re
from time import sleep

failed_urls = ''

def get_html(url):
    global failed_urls
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        sleep(1)
        return response.text
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred for URL: {url}. Error: {err}")
        failed_urls += f'{url}\n'
        print(failed_urls)
    except requests.exceptions.RequestException as err:
        print(f"Request error occurred for URL: {url}. Error: {err}")
        failed_urls += f'{url}\n'
        print(failed_urls)
    return ""


def get_categories(html, url):
    soup = BeautifulSoup(html, 'html.parser')

    categories = soup.find_all('div', class_='category-sidebar__wrap')
    category_data = {}
    for category in categories:
        links = category.find_all('a')
        for link in links:
            category_name = link.find('span').text
            category_url = urllib.parse.urljoin(url, link['href'])
            category_data[category_url] = {'category_name': category_name}
    return category_data


def get_product_ids(url):
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    product_ids = []
    
    product_list = soup.find('div', class_='product-grid__product-list')
    if product_list:
        products = product_list.find_all('div', class_='product-card__wrapper')
        for product in products:
            product_link = product.find('a', class_='link link_wu')
            if product_link:
                product_url = product_link.get('href')
                product_id = re.search(r'/(\d+)/$', product_url)
                if product_id:
                    product_ids.append(product_id.group(1))
    
    return product_ids


def parse_product_details(url):
    html = get_html(url)
    if not html:
        return
    soup = BeautifulSoup(html, 'html.parser')

    product_info = {}

    blocks_property = soup.find_all('section', class_='product-property-list mb-20')
    if len(blocks_property) != 0:
        composition = soup.find('div', class_='product__props-composition p')
        if composition:
            product_info['composition'] = composition.text
        for block in blocks_property:
            title = block.find('h2', class_='product-property-list__title')
            if title:
                if title.text == 'Особенности':
                    features = ""
                    for row in block.find_all('dl', class_='product-property-list__row'):
                        name = row.find('dt', class_='product-property-list__prop').text.strip()
                        value = row.find('dd', class_='product-property-list__value').text.strip()
                        features += f"{name}: {value}\n"
                    product_info['features'] = features
                elif title.text == 'Дополнительно':
                    extra = ""
                    for row in block.find_all('dl', class_='product-property-list__row'):
                        name = row.find('dt', class_='product-property-list__prop').text
                        value = row.find('dd', class_='product-property-list__value').text
                        extra += f"{name}: {value}\n"
                    product_info['extra'] = extra
                elif title.text == 'Общие характеристики':
                    general_info_str = ""
                    for row in block.find_all('dl', class_='product-property-list__row'):
                        name = row.find('dt', class_='product-property-list__prop').text.strip()
                        value = row.find('dd', class_='product-property-list__value').text.strip()
                        general_info_str += f"{name}: {value}\n"
                    product_info['general_info'] = general_info_str.strip()
                
        
    product_photo = soup.find('div', class_='product-slider')
    product_info['image'] = product_photo.find('img', class_='product-slider__photo-img')['src']

    product = soup.find('div', class_='product__info')

    product_info['name'] = product.find('h1', class_='product__title').text.strip()

    product_info['price'] = product.find('div', class_='price__col').text.strip()

    nutrition_info = product.find('div', class_='product__note')
    if nutrition_info:
        nutrition_info_str = ""
        for row in nutrition_info.find_all('div', class_='product__note-row'):
            for col in row.find_all('div', class_='product__note-col'):
                name = col.find('div', class_='product__note-col-name').text.strip()
                value = col.find('div', class_='product__note-col-value').text.strip()
                nutrition_info_str += f"{name}: {value}\n"
        product_info['nutrition_info'] = nutrition_info_str.strip()

    props_info = soup.find('div', class_='product__props')
    if props_info:
        general_info_str = ""
        composition = props_info.find('div', class_='product__props-composition')
        if composition:
            product_info['composition'] = composition.text.strip()
        for row in props_info.find_all('dl', class_='product-property-list__row'):
            name = row.find('dt', class_='product-property-list__prop').text.strip()
            value = row.find('dd', class_='product-property-list__value').text.strip()
            general_info_str += f"{name}: {value}\n"
        product_info['general_info'] = general_info_str.strip()

    return product_info

    


def get_subcategories(url, category_data):
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')

    subcategories = soup.find_all('div', class_='tag-list')
    subcategory_data = {}
    for subcategory in subcategories:
        subcategory_links = subcategory.find_all('a')

        for subcategory_link in subcategory_links:
            subcategory_name = subcategory_link.text
            subcategory_url = urllib.parse.urljoin(url, subcategory_link['href'])
            subcategory_data[subcategory_url] = {'subcategory_name': subcategory_name, 'category_name': category_data['category_name']}
    return subcategory_data


def check_subsubcategories(url, subcategory_data):
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')

    subsubcategories = soup.find_all('div', class_='tag-list')
    subsubcategory_data = {}
    for subsubcategory in subsubcategories:
        subsubcategory_links = subsubcategory.find_all('a')
        for subsubcategory_link in subsubcategory_links:
            subsubcategory_name = subsubcategory_link.text
            subsubcategory_url = urllib.parse.urljoin(url, subsubcategory_link['href'])
            subsubcategory_data[subsubcategory_url] = {'subsubcategory_name': subsubcategory_name, 'subcategory_name': subcategory_data['subcategory_name'], 'category_name': subcategory_data['category_name']}
    return subsubcategory_data

def check_subsubsucategories(url, subsubcategory_data):
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')

    subsubsubcategories = soup.find_all('div', class_='tag-list')
    subsubsubcategory_data = {}
    for subsubsubcategory in subsubsubcategories:
        subsubsubcategory_links = subsubsubcategory.find_all('a')
        for subsubsubcategory_link in subsubsubcategory_links:
            subsubsubcategory_name = subsubsubcategory_link.text
            subsubsubcategory_url = urllib.parse.urljoin(url, subsubsubcategory_link['href'])
            subsubsubcategory_data[subsubsubcategory_url] = {'subsubsubcategory_name': subsubsubcategory_name, 'subsubcategory_name': subsubcategory_data['subsubcategory_name'], 'subcategory': subsubcategory_data['subcategory_name'], 'category_name': subsubcategory_data['category_name']}
    return subsubsubcategory_data


def main():
    url = 'https://darkstore.05.ru'
    html = get_html(url)
    categories = get_categories(html, url)
    print(categories)
    global failed_urls
    print(categories)

    with open('product_data.csv', 'a', newline='', encoding='utf-8-sig') as file:
        fieldnames = ['category_name', 'subcategory_name', 'subsubcategory_name', 'subsubsubcategory_name', 'name', 'price', 'nutrition_info', 'composition', 'general_info',  'image', 'features', 'extra']
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        for category_url, category_data in categories.items():
            print(f'Url category: {category_url}, data category: {category_data}')
            subcategories = get_subcategories(category_url, category_data)
            print(f'Subcategories: {subcategories}')
            for subcategory_url, subcategory_data in subcategories.items():
                subsubcategories = check_subsubcategories(subcategory_url, subcategory_data)
                if len(subsubcategories) != 0:
                    print(f'Subsubcategories: {subsubcategories}')
                    for subsubcategory_url, subsubcategory_data in subsubcategories.items():
                        subsubsubcategories = check_subsubsucategories(subsubcategory_url, subsubcategory_data)
                        print(f'Субсубсубкатегории: {subsubsubcategories}')
                        if len(subsubsubcategories) != 0:
                            for subsubsubcategory_url, subsubsubcategory_data in subsubsubcategories.items():
                                product_ids = get_product_ids(subsubsubcategory_url)
                                print(f'Product_ids: {product_ids}')
                                for product_id in product_ids:
                                    product_url = urllib.parse.urljoin(subsubsubcategory_url, product_id)
                                    product_data = parse_product_details(product_url)
                                    if product_data:
                                        product_data.update(subsubcategory_data)
                                        writer.writerow({'category_name': subcategory_data['category_name'], 
                                        'subcategory_name': subcategory_data['subcategory_name'], 
                                        'subsubcategory_name': subsubcategory_data['subsubcategory_name'] if 'subsubcategory_name' in subsubcategory_data.keys() else '', 
                                        'subsubsubcategory_name': subsubsubcategory_data['subsubsubcategory_name'] if 'subsubcategory_name' in subsubsubcategory_data.keys() else '',
                                        'name': product_data['name'], 'price': product_data['price'], 
                                        'nutrition_info': product_data['nutrition_info'] if 'nutrition' in product_data.keys() else '', 
                                        'composition': product_data['composition'] if 'composition' in product_data.keys() else '', 
                                        'general_info': product_data['general_info'],
                                        'image': product_data['image'],
                                        'features': product_data['features'] if 'features' in product_data.keys() else "",
                                        'extra': product_data['extra'] if 'extra' in product_data.keys() else ""})
                                        print(product_data)
                                        print(subcategory_data)
                        else:
                            product_subsubs_ids = get_product_ids(subsubcategory_url)
                            print(product_subsubs_ids)
                            for id in product_subsubs_ids:
                                product_url = urllib.parse.urljoin(subsubcategory_url, id)
                                product_data = parse_product_details(product_url)
                                if product_data:
                                    product_data.update(subsubcategory_data)
                                    print(subcategory_data)
                                    writer.writerow({'category_name': subcategory_data['category_name'], 
                                        'subcategory_name': subcategory_data['subcategory_name'], 
                                        'subsubcategory_name': subsubcategory_data['subsubcategory_name'] if 'subsubcategory_name' in subsubcategory_data.keys() else '',
                                        'subsubsubcategory_name': "",
                                        'name': product_data['name'], 'price': product_data['price'], 
                                        'nutrition_info': product_data['nutrition_info'] if 'nutrition' in product_data.keys() else '', 
                                        'composition': product_data['composition'] if 'composition' in product_data.keys() else '', 
                                        'general_info': product_data['general_info'],
                                        'image': product_data['image'],
                                        'features': product_data['features'] if 'features' in product_data.keys() else "",
                                        'extra': product_data['extra'] if 'extra' in product_data.keys() else ""})
                                    print(product_data)

                else:
                    product_subs_ids = get_product_ids(subcategory_url)
                    print(product_subs_ids)
                    for id in product_subs_ids:
                        product_url = urllib.parse.urljoin(subcategory_url, id)
                        product_data = parse_product_details(product_url)
                        if product_data:
                            product_data.update(subcategory_data)
                            print(subcategory_data)
                            writer.writerow({'category_name': subcategory_data['category_name'], 
                                'subcategory_name': subcategory_data['subcategory_name'], 
                                'subsubcategory_name': "",
                                'subsubsubcategory_name': "",
                                'name': product_data['name'], 'price': product_data['price'], 
                                'nutrition_info': product_data['nutrition_info'] if 'nutrition' in product_data.keys() else '', 
                                'composition': product_data['composition'] if 'composition' in product_data.keys() else '', 
                                'general_info': product_data['general_info'],
                                'image': product_data['image'],
                                'features': product_data['features'] if 'features' in product_data.keys() else "",
                                'extra': product_data['extra'] if 'extra' in product_data.keys() else ""})
                            print(product_data)
    file.close()
    with open('failed_urls.txt', 'w', encoding='utf-8') as filew:
        filew.write(failed_urls)
    filew.close()
                            
if __name__ == '__main__':
    main()
