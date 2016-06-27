# -*- encoding: utf-8 -*-
import urllib2
from bs4 import BeautifulSoup


class DownloadFile:
    def __init__(self, name, href, size, date, web):
        self.name = name
        self.href = href
        self.size = size
        self.date = date
        self.web = web


def find(keyword, webs):
    files = []

    for web in webs:
        if web == "tokyo":
            # Tokyo Toshokan 0:all 1:Anime 3:Manga 5:Music
            tt_bs = BeautifulSoup(urllib2.urlopen("http://tokyotosho.info/search.php?terms=" + keyword + "&type=0").read())
            # name and torrent file
            tt = tt_bs.find_all(type='application/x-bittorrent')
            tt2 = tt_bs.find_all(class_='desc-bot')

            if len(tt) == len(tt2):
                num = len(tt)-1
                while num >= 0:
                    name = tt[num].text
                    href = tt[num]['href']
                    sd = tt2[num].text.split("|")
                    size = sd[1][6:]
                    date = sd[2][6:17]
                    d = DownloadFile(name, href, size, date, "東京図書館")
                    # print name, href, size, date
                    files.append(d)
                    num -= 1

        if web == "nyaa":
            # nyaa All:0_0, Anime:7_25, Game:7_27,  Manga: 7_26, Doujinshi:7_33
            nyaa_bs = BeautifulSoup(urllib2.urlopen("https://sukebei.nyaa.se/?page=search&cats=0_0&filter=0&term=" + keyword).read())
            nyaa_name = nyaa_bs.find_all(class_='tlistname')
            nyaa_dl = nyaa_bs.find_all(class_='tlistdownload')
            nyaa_size = nyaa_bs.find_all(class_='tlistsize')

            if len(nyaa_name) == len(nyaa_dl) ==len(nyaa_size):
                num = len(nyaa_name)-1
                while num >= 0:
                    name = nyaa_name[num].text
                    href = "http:" + str(BeautifulSoup(str(nyaa_dl[num])).find('a')['href'])
                    size = nyaa_size[num].text
                    d = DownloadFile(name, href, size, '', "nyaa")
                    # print name, href, size
                    files.append(d)
                    num -= 1

    return files
