import asyncio
import aiohttp
import bs4
import csv
import lxml.html
import argparse
from aiofile import AIOFile, LineReader, Reader


class Crawl():
    HEADERS = {
        'accept': '*/*',
        'user-agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    }

    FILE = 'file_name'

    loop = asyncio.get_event_loop()
    SITEMAP = 'https://www.google.com/admob/sitemap.xml'

    def __init__(self, sitemap, format_file="url"):
        self.sitemap = sitemap
        self.format_file = format_file

    def run(self):
        self.loop.run_until_complete(self.fetch_urls())

    async def fetch_urls(self):

        try:
            async with aiohttp.ClientSession() as session:
                if self.format_file == 'url':
                    async with session.get(self.sitemap, allow_redirects=True, headers=self.HEADERS,
                                           timeout=1) as response:
                        raw_content = await response.text()
                        soup = bs4.BeautifulSoup(raw_content, 'html.parser')
                        list_urls_s = [asyncio.ensure_future(self.behavior(i.get_text(), session)) for i in
                                       soup.find_all('loc')]

                        return await asyncio.wait(list_urls_s)

                elif self.format_file == 'txt':
                    async with AIOFile(self.sitemap, 'r') as afp:
                        async for line in Reader(afp):
                            list_urls_s = [asyncio.ensure_future(self.behavior(line, session)) for line in
                                           line.split()]
                        return await asyncio.wait(list_urls_s)

                elif self.format_file == 'xml':
                    async with AIOFile(self.sitemap, 'r') as afp:
                        async for chunk in Reader(afp):
                            soup = bs4.BeautifulSoup(chunk, 'html.parser')
                            list_urls_s = [asyncio.ensure_future(self.behavior(i.get_text(), session)) for i in
                                           soup.find_all('loc')]
                            return await asyncio.wait(list_urls_s)

        except Exception as e:
            return e

    # noinspection PyAttributeOutsideInit
    async def behavior(self, data_urls, session):
        """Поведение(обработка) полученых из data() URL"""

        global urls, status
        try:
            async with session.get(data_urls, allow_redirects=False, headers=self.HEADERS) as response:

                # content = await response.text()
                # soup1 = bs4.BeautifulSoup(content, 'html.parser')
                # lxml_xpath = lxml.html.fromstring(content)
                # description = lxml_xpath.xpath('//meta[@name="description"]/@content')[0]
                # title = lxml_xpath.xpath('//title/text()')[0]
                # h1 = soup1.find('h1').get_text()

                # text = soup1.get_text(strip=False)

                # check status code
                urls = response.url
                status = response.status

                # full check crawl and status code add data dict
                # dicts = {'status': status, 'h1': h1, 'description': description, 'title': title, 'url': urls}
                dicts = {'status': status, 'url': urls}
                print(dicts)

        except Exception as e:

            # dicts = {'status': 'None', 'h1': 'None', 'description': 'None', 'title': 'None', 'url': data_urls,
            #         }
            print('Ошибка: %r' % e)
            dicts = {'status': status, 'url': urls}
            print(dicts)

        self.csv_writer(dicts)
        return None

    # noinspection PyAttributeOutsideInit
    def csv_writer(self, data):
        self.data = data
        """Запись полученых данных из behavior(data_urls)"""
        with open(self.FILE + '.csv', 'a') as f:
            writer = csv.writer(f, delimiter=";", lineterminator="\r")
            # full write data csv crawl and status code and url
            # writer.writerow((self.data['status'], self.data['h1'], self.data['description'], self.data['title'],
            #                  self.data['url']))
            writer.writerow((self.data['status'], self.data['url']))
            f.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-U", "--url", type=str, help="Url")
    parser.add_argument("-F", "--file_name", type=str, help="File_name")
    args = parser.parse_args()

    if args.url:
        crawl = Crawl(args.url)
        crawl.run()

    elif args.file_name:
        format_file_split = args.file_name.split(".")
        crawl = Crawl(args.file_name, format_file=format_file_split[-1])
        crawl.run()

    else:
        parser.print_help()