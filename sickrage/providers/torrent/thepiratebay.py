# Author: Mr_Orange <mr_orange@hotmail.it>
# URL: https://sickrage.ca
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re
from urlparse import urljoin

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import convert_size, try_int, validate_url, bs4_parser
from sickrage.providers import TorrentProvider


class ThePirateBayProvider(TorrentProvider):
    def __init__(self):
        super(ThePirateBayProvider, self).__init__("ThePirateBay", 'https://thepiratebay.org', False)

        self.urls.update({
            "search": "{base_url}/search/%s/0/3/200".format(**self.urls),
            "rss": "{base_url}/tv/latest".format(**self.urls),
        })

        self.confirmed = True
        self.minseed = None
        self.minleech = None

        self.custom_url = ""

        self.cache = TVCache(self, min_time=20)

    def search(self, search_strings, age=0, ep_obj=None, **kwargs):
        results = []

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: {0}".format(mode))
            for search_string in search_strings[mode]:
                search_url = (self.urls["search"], self.urls["rss"])[mode == "RSS"]
                if self.custom_url:
                    if not validate_url(self.custom_url):
                        sickrage.app.log.warning("Invalid custom url: {0}".format(self.custom_url))
                        return results
                    search_url = urljoin(self.custom_url, search_url.split(self.urls['base_url'])[1])

                if mode != "RSS":
                    search_url = search_url % search_string
                    sickrage.app.log.debug("Search string: {}".format(search_string))

                try:
                    data = self.session.get(search_url).text
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.app.log.debug("No data returned from provider")

        return results

    def parse(self, data, mode, **kwargs):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        def process_column_header(th):
            text = ""
            if th.a:
                text = th.a.get_text(strip=True)
            if not text:
                text = th.get_text(strip=True)
            return text

        with bs4_parser(data) as html:
            torrent_table = html.find("table", id="searchResult")
            torrent_rows = torrent_table("tr") if torrent_table else []

            # Continue only if at least one Release is found
            if len(torrent_rows) < 2:
                sickrage.app.log.debug("Data returned from provider does not contain any torrents")
                return results

            labels = [process_column_header(label) for label in torrent_rows[0]("th")]

            # Skip column headers
            for row in torrent_rows[1:]:
                cells = row('td')
                if len(cells) < len(labels):
                    continue

                try:
                    title = row.find(class_='detName')
                    title = title.get_text(strip=True) if title else None
                    download_url = row.find(title='Download this torrent using magnet')
                    download_url = download_url.get('href') if download_url else None
                    if download_url and 'magnet:?' not in download_url:
                        try:
                            details_url = urljoin(self.custom_url or self.urls['base_url'], download_url)
                            details_data = self.session.get(details_url).text
                        except Exception:
                            sickrage.app.log.debug('Invalid ThePirateBay proxy please try another one')
                            continue

                        with bs4_parser(details_data) as details:
                            download_url = details.find(title='Get this torrent')
                            download_url = download_url.get('href') if download_url else None
                            if download_url and 'magnet:?' not in download_url:
                                sickrage.app.log.debug('Invalid ThePirateBay proxy please try another one')
                                continue
                    if not all([title, download_url]):
                        continue

                    seeders = try_int(cells[labels.index("SE")].get_text(strip=True))
                    leechers = try_int(cells[labels.index("LE")].get_text(strip=True))

                    # Accept Torrent only from Good People for every Episode Search
                    if self.confirmed and not row.find(alt=re.compile(r"VIP|Trusted")):
                        if mode != "RSS":
                            sickrage.app.log.debug(
                                "Found result: {0} but that doesn't seem like a trusted result so I'm "
                                "ignoring it".format(title))
                        continue

                    # Convert size after all possible skip scenarios
                    torrent_size = cells[labels.index('Name')].find(class_='detDesc')
                    torrent_size = torrent_size.get_text(strip=True).split(', ')[1]
                    torrent_size = re.sub(r'Size ([\d.]+).+([KMGT]iB)', r'\1 \2', torrent_size)
                    size = convert_size(torrent_size, -1, ['B', 'KIB', 'MIB', 'GIB', 'TIB', 'PIB'])

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error("Failed parsing provider")

        return results
