"""
Simple unit test for search_img module
"""

import unittest
import os
import collections

from search_img import SearchImage


class TestSearchImage(unittest.TestCase):
    """ Unit test class for SearchImage """

    def test_index_create(self):
        """ Remove and re-create all indixes from the location. """

        search_img = SearchImage('test')

        # Clear the location
        os.system('rm -rf ' + search_img.save_path)

        # Have to do this again to recreate paths
        search_img = SearchImage('test')

        index, status = search_img.index_image_files('testing/')

        # To assert index was rebuilt
        self.assertTrue(status == True)

        # To assert index was valid
        self.assertTrue(len(index) > 0)

    def test_index_reuse(self):
        """ Reuse bulit index. """

        search_img = SearchImage('test')
        index, status = search_img.index_image_files('testing/')

        # To assert index was loaded
        self.assertTrue(status == False)

        # To assert index was valid
        self.assertTrue(len(index) > 0)

    def test_index_validity(self):
        """Specific file based testing for specific data."""

        search_img = SearchImage('test')
        index, status = search_img.index_image_files('testing/')

        print type(index)

        self.assertTrue(type(index) == collections.defaultdict)

        item = index['testing/image/insta_pic.jpg']

        # Test presence of a few keys
        self.assertTrue('megapixels' in item)
        self.assertTrue('image_height' in item)

        item = index['testing/image/samsung.jpg']

        self.assertTrue('g_p_s_longitude' in item)

        print index.keys()

        # Like this pick specific keys to specific files
        # and write assertions

        item = index['testing/image/filter_lenovo.jpg']
        print item
        self.assertTrue('model' in item)


if __name__ == "__main__":

    unittest.main()
