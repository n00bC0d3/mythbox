#
#  MythBox for XBMC - http://mythbox.googlecode.com
#  Copyright (C) 2009 analogue@yahoo.com
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
import logging
import os
import tempfile
import time
import unittest

from mockito import Mock, verifyZeroInteractions
from mythbox.bus import EventBus
from mythbox.mythtv.conn import Connection
from mythbox.mythtv.db import MythDatabase
from mythbox.mythtv.domain import Channel
from mythbox.mythtv.resolver import MythChannelIconResolver
from mythbox.settings import MythSettings
from mythbox.util import OnDemandConfig
from mythbox.platform import getPlatform

log = logging.getLogger('mythtv.unittest')

# =============================================================================
class MythChannelIconResolverTest(unittest.TestCase):

    def setUp(self):
        self.platform = getPlatform()
        self.translator = Mock()
        self.settings = MythSettings(self.platform, self.translator)
        
        privateConfig = OnDemandConfig()
        self.settings.setMySqlHost(privateConfig.get('mysql_host'))
        self.settings.setMySqlPort(privateConfig.get('mysql_port'))
        self.settings.setMySqlDatabase(privateConfig.get('mysql_database'))
        self.settings.setMySqlUser(privateConfig.get('mysql_user'))  
        self.settings.setMySqlPassword(privateConfig.get('mysql_password'))
        self.settings.setMythTvHost(privateConfig.get('mythtv_host'))
        self.settings.setMythTvPort(int(privateConfig.get('mythtv_port')))
        self.settings.setRecordingDirs(privateConfig.get('paths_recordedprefix'))
        
        log.debug('%s' % self.settings)
        
        self.db = MythDatabase(self.settings, self.translator)
        self.bus = EventBus()
        self.conn = Connection(self.settings, self.translator, self.platform, self.bus, self.db)

    def tearDown(self):
        self.conn.close()

    def test_store_When_channel_has_icon_Then_download_icon(self):
        # Setup
        channels = filter(lambda x: x.getIconPath(), self.conn.getChannels()) # filter out channels that don't have an icon
        self.assertTrue(len(channels) > 0, 'Channels with icon needed in db to run test')
        downloader = MythChannelIconResolver(self.conn)
         
        # Test - download icons for first 5 channels
        for channel in channels[:min(5, len(channels))]:
            if channel.getIconPath():
                log.debug('%s' % channel)
                dest = os.path.sep.join([tempfile.gettempdir(), str(channel.getChannelId()) + channel.getCallSign() + str(time.time()) + ".png"])
                downloader.store(channel, dest)
        
                # Verify
                log.debug('Downloaded %s to %s' % (channel.getIconPath(), dest))
                self.assertTrue(os.path.exists(dest))
                self.assertTrue(os.path.isfile(dest))
                self.assertTrue(os.path.getsize(dest) > 0)
                
                # Cleanup
                os.remove(dest)        
    
    def test_store_When_channel_has_no_icon_Then_do_nothing(self):
        # Setup
        channel = Channel({'name':'Bogus Channel', 'icon':None})
        conn = Mock()
        downloader = MythChannelIconResolver(conn)
         
        # Test 
        downloader.store(channel, 'bogusDestDir')
    
        # Verify
        verifyZeroInteractions(conn)

    def test_store_When_channel_has_icon_but_icon_not_accessible_Then_do_nothing(self):
        pass

# =============================================================================
if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()
