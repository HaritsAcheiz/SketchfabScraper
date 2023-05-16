import requests
from selectolax.parser import HTMLParser
from dataclasses import dataclass, asdict
import os
import json
import csv
from lxml import html
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

@dataclass
class Item:
    title: str
    source_format: str
    download_size: str
    geometry: str
    vertices: str
    pbr: str
    textures: str
    materials: str
    uv_layers: str
    vertex_colors: str
    animations: str
    rigged_geometries: str
    morph_geometries: str
    scale_transformations: str

@dataclass
class Scraper:

    def fetch(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0'
        }

        with requests.Session() as s:
            r = s.get(url, headers=headers)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            return "Error: " + str(e)
        return r

    # def fetch_view(self, url):
    #     headers = {
    #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0'
    #     }
    #
    #     with requests.Session() as s:
    #         r = s.get(url, headers=headers)
    #         try:
    #             r.raise_for_status()
    #             pid = url.split("/")[-1].split("-")[-1]
    #             s.post(f'https://sketchfab.com/i/models/{pid}/views')
    #             response = s.get(url)
    #         except requests.exceptions.HTTPError as e:
    #             return "Error: " + str(e)
    #     return response

    def webdriver_setup(self):
        # ip, port = proxy.split(sep=':')

        useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0'
        firefox_options = Options()

        firefox_options.add_argument('-headless')
        firefox_options.add_argument('--no-sandbox')
        firefox_options.page_load_strategy = "eager"

        firefox_options.set_preference("general.useragent.override", useragent)
        # firefox_options.set_preference('network.proxy.type', 1)
        # firefox_options.set_preference('network.proxy.socks', ip)
        # firefox_options.set_preference('network.proxy.socks_port', int(port))
        # firefox_options.set_preference('network.proxy.socks_version', 4)
        # firefox_options.set_preference('network.proxy.socks_remote_dns', True)
        # firefox_options.set_preference('network.proxy.http', ip)
        # firefox_options.set_preference('network.proxy.http_port', int(port))
        # firefox_options.set_preference('network.proxy.ssl', ip)
        # firefox_options.set_preference('network.proxy.ssl_port', int(port))

        driver = webdriver.Firefox(options=firefox_options)
        return driver

    def fetch_view(self, url):
        driver = self.webdriver_setup()
        driver.delete_all_cookies()
        driver.get(url)
        driver.maximize_window()
        driver.set_page_load_timeout(20)
        wait = WebDriverWait(driver, 15)
        wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR,'a.stat.skfb-link'))).click()
        items = wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.c-model-3d-information__row')))
        datas = {'Title': None,
             'Source format' : None,
             'Download size' : None,
             'Geometry' : None,
             'Vertices' : None,
             'PBR' : None,
             'Textures' :  None,
             'Materials' : None,
             'UV Layers' : None,
             'Vertex colors' : None,
             'Animations' : None,
             'Rigged geometries' : None,
             'Morph geometries' : None,
             'Scale transformations' : None}
        datas['Title'] = driver.title
        for item in items:
            label = item.find_element(By.CSS_SELECTOR,'div.c-model-3d-information__label').text
            if label in ['Source format', 'Download size']:
                try:
                    datas[label] = (item.find_element(By.CSS_SELECTOR, 'div.c-model-3d-information__value > p > span').text)
                except:
                    datas[label] = None
            elif label == 'Geometry':
                try:
                    datas[label] = (item.find_element(By.CSS_SELECTOR, 'div.c-model-3d-information__value > div').text)
                except:
                    datas[label] = None
            else:
                try:
                    datas[label] = (item.find_element(By.CSS_SELECTOR, 'div.c-model-3d-information__value').text)
                except:
                    datas[label] = None
        print(datas)
        new_item = Item(title = datas['Title'],
             source_format = datas['Source format'],
             download_size = datas['Download size'],
             geometry = datas['Geometry'],
             vertices = datas['Vertices'],
             pbr = datas['PBR'],
             textures =  datas['Textures'],
             materials = datas['Materials'],
             uv_layers = datas['UV Layers'],
             vertex_colors = datas['Vertex colors'],
             animations = datas['Animations'],
             rigged_geometries = datas['Rigged geometries'],
             morph_geometries = datas['Morph geometries'],
             scale_transformations = datas['Scale transformations'])
        driver.close()
        return asdict(new_item)

    def get_detail_url(self, r):
        json_data = r.json()
        json_formatted_str = json.dumps(json_data, indent=2)
        # print(json_formatted_str)
        # print(len(json_data['results']))
        detail = {'cursor_next':None, 'detail_urls':None}
        detail['cursor_next'] = json_data['cursors']['next']
        urls = []
        for i in range(len(json_data['results'])):
            urls.append(json_data['results'][i]['viewerUrl'])
        detail['detail_urls'] = urls
        return detail

    def get_info(self):
        pass

    def download_img(self, img_urls, folder_name):
        for url in img_urls:
            if not os.path.exists(folder_name):
                os.mkdir(folder_name)
            if url != None:
                with requests.Session() as s:
                    r = s.get(url)
                with open(f"{folder_name}/{url.split('/')[-1]}", 'wb') as f:
                    f.write(r.content)
            print('Image downloaded successfully!')

    def to_csv(self, data, filename, headers):
            try:
                file_exists = os.path.isfile(filename)
                with open(filename, 'a', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, delimiter=',', lineterminator='\n', fieldnames=headers)
                    if not file_exists:
                        writer.writeheader()
                    if data != None:
                        writer.writerow(data)
                    else:
                        pass
            except Exception as e:
                print(e)
                pass


if __name__ == '__main__':
    base_url = 'https://sketchfab.com/i/search?q=sofa&sort_by=-relevance&type=models'
    headers = ['title', 'source_format', 'download_size', 'geometry', 'vertices', 'pbr', 'textures', 'materials',
               'uv_layers', 'vertex_colors', 'animations', 'rigged_geometries', 'morph_geometries', 'scale_transformations']
    s=Scraper()
    next_url = base_url
    for i in range(2):
        try:
            url = next_url
            r = s.fetch(url)
            details = s.get_detail_url(r=r)
            print(details)
            for detail_url in details['detail_urls']:
                print(detail_url)
                item = (s.fetch_view(detail_url))
                s.to_csv(data=item, filename='result.csv', headers=headers)
            # result = response.text
            # print(result)
            next_url = f"{base_url}&cursor={details['cursor_next']}"
        except Exception as e:
            print(e)
            break