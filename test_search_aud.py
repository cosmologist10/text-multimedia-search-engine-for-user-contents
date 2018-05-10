"""
Simple unit test for search_audio module.
"""

import unittest
import os
import collections

from search_audio import SearchAudio


class TestSearchAudio(unittest.TestCase):

    """ Unit test class for SearchAudio. """

    def test_index_create(self):
        """ Remove and re-create all indixes from the location. """

        search_audio = SearchAudio('test')

        # clear the location
        os.system('rm -rf ' + search_audio.save_path)

        # Recreate paths
        search_audio = SearchAudio('test')

        index, status = search_audio.index_audio_files('testing/')

        # To assert index was rebuilt
        self.assertTrue(status == True)

        # To assert index was valid
        self.assertTrue(len(index) > 0)

    def test_index_reuse(self):
        """ Reuse bulit index. """

        search_audio = SearchAudio('test')

        index, status = search_audio.index_audio_files('testing/')

        # To assert index was loaded
        self.assertTrue(status == False)

        # To assert index was valid
        self.assertTrue(len(index) > 0)

    def test_index_validity(self):
        """Specific file based testing for specific data."""

        search_audio = SearchAudio('test')
        index, status = search_audio.index_audio_files('testing/')

        print type(index)

        self.assertTrue(type(index) == collections.defaultdict)

        # Test presence of a few keys

        item = index['testing/audio/Dekha Hazaro Dafaa[320]__Raag.Me__.mp3']
        self.assertTrue('artist' in item)
        self.assertTrue('year' in item)

        print item
        print index.keys()


if __name__ == "__main__":

    unittest.main()
