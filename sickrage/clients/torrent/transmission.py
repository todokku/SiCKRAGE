# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################

# Author: Mr_Orange <mr_orange@hotmail.it>
# URL: https://sickrage.ca
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import os
from base64 import b64encode

import requests

import sickrage
from sickrage.clients.torrent import GenericClient


class TransmissionAPI(GenericClient):
    def __init__(self, host=None, username=None, password=None):
        super(TransmissionAPI, self).__init__('Transmission', host, username, password)

        if not self.host.endswith('/'):
            self.host += '/'

        if self.rpcurl.startswith('/'):
            self.rpcurl = self.rpcurl[1:]

        if self.rpcurl.endswith('/'):
            self.rpcurl = self.rpcurl[:-1]

        self.url = self.host + self.rpcurl + '/rpc'

    def _get_auth(self):
        try:
            # Triggering HTTP 409 error
            self.response = self.session.post(self.url,
                                              timeout=120,
                                              json={'method': 'session-get'},
                                              auth=(self.username, self.password),
                                              verify=bool(sickrage.app.config.torrent_verify_cert))
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                # Get X-Transmission-Session-Id auth session header
                self.auth = e.response.headers.get('x-transmission-session-id')

                # Validating Transmission authorization
                success = self._request(method='post',
                                        json={'arguments': {}, 'method': 'session-get'},
                                        headers={'x-transmission-session-id': self.auth})

                if not success:
                    self.auth = None

        return self.auth

    def _request(self, *args, **kwargs):
        kwargs.setdefault('headers', {}).update({'x-transmission-session-id': self.auth})
        return super(TransmissionAPI, self)._request(*args, **kwargs)

    def _add_torrent_uri(self, result):
        arguments = {
            'filename': result.url,
            'paused': 1 if sickrage.app.config.torrent_paused else 0,
        }

        if os.path.isabs(sickrage.app.config.torrent_path):
            arguments['download-dir'] = sickrage.app.config.torrent_path

        post_data = {
            'arguments': arguments,
            'method': 'torrent-add'
        }

        if self._request(method='post', json=post_data):
            return self.response.json()['result'] == "success"

    def _add_torrent_file(self, result):
        arguments = {
            'metainfo': b64encode(result.content),
            'paused': 1 if sickrage.app.config.torrent_paused else 0
        }

        if os.path.isabs(sickrage.app.config.torrent_path):
            arguments['download-dir'] = sickrage.app.config.torrent_path

        post_data = {
            'arguments': arguments,
            'method': 'torrent-add'
        }

        if self._request(method='post', json=post_data):
            return self.response.json()['result'] == "success"

    def _set_torrent_ratio(self, result):
        ratio = None
        if isinstance(result.ratio, int):
            ratio = result.ratio

        mode = 0
        if ratio:
            if float(ratio) == -1:
                ratio = 0
                mode = 2
            elif float(ratio) >= 0:
                ratio = float(ratio)
                mode = 1  # Stop seeding at seedRatioLimit

        arguments = {
            'ids': [result.hash],
            'seedRatioLimit': ratio,
            'seedRatioMode': mode
        }

        post_data = {
            'arguments': arguments,
            'method': 'torrent-set'
        }

        if self._request(method='post', json=post_data):
            return self.response.json()['result'] == "success"

    def _set_torrent_seed_time(self, result):
        if sickrage.app.config.torrent_seed_time and sickrage.app.config.torrent_seed_time != -1:
            time = int(60 * float(sickrage.app.config.torrent_seed_time))
            arguments = {
                'ids': [result.hash],
                'seedIdleLimit': time,
                'seedIdleMode': 1
            }

            post_data = {
                'arguments': arguments,
                'method': 'torrent-set'
            }

            if self._request(method='post', json=post_data):
                return self.response.json()['result'] == "success"
        else:
            return True

    def _set_torrent_priority(self, result):
        arguments = {'ids': [result.hash]}

        if result.priority == -1:
            arguments['priority-low'] = []
        elif result.priority == 1:
            # set high priority for all files in torrent
            arguments['priority-high'] = []
            # move torrent to the top if the queue
            arguments['queuePosition'] = 0
            if sickrage.app.config.torrent_high_bandwidth:
                arguments['bandwidthPriority'] = 1
        else:
            arguments['priority-normal'] = []

        post_data = {
            'arguments': arguments,
            'method': 'torrent-set'
        }

        if self._request(method='post', json=post_data):
            return self.response.json()['result'] == "success"

    def remove_torrent(self, info_hash):
        arguments = {
            'ids': [info_hash],
            'delete-local-data': 1,
        }

        post_data = {
            'arguments': arguments,
            'method': 'torrent-remove',
        }

        if self._request(method='post', json=post_data):
            return self.response.json()['result'] == "success"
