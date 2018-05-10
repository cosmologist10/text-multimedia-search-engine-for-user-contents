import os
import time
import re
import exiftool
import hashlib
# import cPickle
# import operator
# import pathlib
# import pprint
# import json
from pathlib import Path
from collections import defaultdict

# import utility function
from text_mod import utils

# Location Library for tracing by 'state', 'city', 'country', 'pin/postal code'
# import geopy
from geopy.geocoders import Nominatim

from text_mod.search_word import SearchWord


class SearchImage(SearchWord):
    """ Image searcher cum indexer using python dictionaries. """

    def __init__(self, searchword, max_size):
        SearchWord.__init__(self, searchword, max_size)
        self.my_extensions = ('.png', '.tif', '.jpg', '.gif', '.JPG')

    def index_img_meta(self, img_flist):
        """
        Return a list the important image metadata along with their source file
        name as key for the given image files.
        """

        filter_set = {'set_1': {'create_date'},
                      'set_2': {'g_p_s_latitude',
                                'g_p_s_longitude'}
                      }

        my_set = []

        target = defaultdict(dict)

        # To flatten the filter_set values into a single list
        for fset in filter_set.values():
            my_set += fset

        with exiftool.ExifTool() as et:

            for fname in img_flist:
                print 'Filename =>', fname
                # get metadata for the file
                metadata = et.get_metadata(fname)

                for key, value in metadata.iteritems():
                    if ':' in key:
                        imp_words = key.split(':')[1]

                    # Constructing my own key
                    split_words = re.findall('[A-Z][a-z]*', imp_words)
                    join_words = "_".join(split_words)
                    final_key = join_words.lower().strip()
                    # print 'Final key',final_key

                    # Check if this is there in my interest set
                    if final_key in my_set:
                        if final_key == 'create_date':
                            modified_value = value.split()[0].split(':')
                            target[fname]['year'] = modified_value[0].encode('utf-8')
                            target[fname]['month'] = modified_value[1].encode('utf-8')
                            target[fname]['day'] = modified_value[2].encode('utf-8')
                        else:
                            target[fname][final_key] = value

        return target

    def add_location_parameters_to_index(self, target):
        """ Find Village, City, State, Country, Postal Code using gps latitude and gps logitude.
        """

        geolocator = Nominatim()

        for filename, data in target.iteritems():
            if 'g_p_s_latitude' in data and 'g_p_s_longitude' in data:
                # using geopy to get location via latitude and longitude.
                location = geolocator.reverse((data['g_p_s_latitude'], data['g_p_s_longitude']))
                # exception handling of KeyError by storing None if not available
                try:
                    target[filename]['village'] = location.raw['address']['village'].encode('utf-8').lower().strip()
                except Exception:
                    target[filename]['village'] = None
                try:
                    target[filename]['city'] = location.raw['address']['city'].encode('utf-8').lower().strip()
                except Exception:
                    target[filename]['city'] = None
                try:
                    target[filename]['state'] = location.raw['address']['state'].encode('utf-8').lower().strip()
                except Exception:
                    target[filename]['state'] = None
                try:
                    target[filename]['country'] = location.raw['address']['country'].encode('utf-8').lower().strip()
                except Exception:
                    target[filename]['country'] = None
                try:
                    target[filename]['postcode'] = str(location.raw['address']['postcode'])
                except KeyError:
                    target[filename]['postcode'] = None

            else:
                target[filename]['state'] = None
                target[filename]['country'] = None
                target[filename]['postcode'] = None

        return target

    def index_image_files(self, loc):
        """
        Return and save the crucial metadata of all image files under
        particular directory.
        """

        fname = hashlib.md5(loc).hexdigest() + '.imgindex'

        complete_name = os.path.join(self.save_path, fname)
        my_file = Path(complete_name)
        rebuild = False

        if my_file.is_file():
            file_last_modify = os.path.getmtime(complete_name)
            print 'File last modified at' + ':' + str(file_last_modify)
            dir_last_modify = os.path.getmtime(loc)
            print 'Directory last modified at' + ':' + str(dir_last_modify)

            comp = dir_last_modify < file_last_modify

            if comp:
                # If index is newer load index
                print 'Loading', complete_name
                index = self.load(complete_name)
                return index
            else:
                # Else rebuild index
                rebuild = True

        if rebuild:
            print 'Directory got modified at ' + time.ctime(dir_last_modify) + ', rebuilding index...'
        else:
            print 'Index not present, building it...'

        with utils.clock_timer():
            index = self.add_location_parameters_to_index(self.index_img_meta(self.file_gen(loc)))

        self.save(index, complete_name)
        print 'Index built at', complete_name

        return index

    def search_filename(self, dic, hits):
        """ Return the filename of respective artist, album, genre, year. """

        final_list = []
        # searching keywords in all files
        for filename, data in dic.iteritems():
            for searchtag in self.searchword:
                if searchtag in data.values():
                    if filename not in final_list:
                        final_list.append(filename)

        print 'Found', str(len(final_list)), 'hits'

        # Filtering Top required number of Hits.
        if len(final_list) >= int(hits):
            print 'Showing top', hits, 'hits', 'out of', str(len(final_list))
            for x in range(int(hits)):
                print final_list[x]
        else:
            print 'Only', str(len(final_list)), 'hits found, showing them:'
            for files in final_list:
                print files


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Folder indexer and searcher. Accepts searchword(village, city, state, country, pin, year, mon, date) \
                     and folder to search for as arguments.')
    parser.add_argument('-village', '--village', help='Name of village')
    parser.add_argument('-city', '--city', help='Name of city')
    parser.add_argument('-state', '--state', help='Name of state')
    parser.add_argument('-country', '--country', help='Name of country')
    parser.add_argument('-pin', '--postal_code', help='Postal code')
    parser.add_argument('-year', '--year', help='Year')
    parser.add_argument('-mon', '--month', help='Month')
    parser.add_argument('-date', '--date', help='Date')
    parser.add_argument('-d', '--dir', required=True, help='Full path of directory you want to index and search')
    parser.add_argument('-s', '--size', required=True, help='Maximum size of the file')
    parser.add_argument('-n', '--num', required=True, help='Number of hits')

    args = parser.parse_args()

    search_path = str(args.dir)
    max_size = str(args.size)
    number_of_hits = str(args.num)

    # Storing and normalisation the union of keywords via which we are looking for files
    if args.village or args.city or args.state or args.country or args.postal_code or args.date or args.month or args.year:
        tags = [args.village, args.city, args.state, args.country, args.postal_code, args.date, args.month, args.year]
        searchtags = [str(tag).lower().strip() for tag in tags if tag is not None]

        searcher = SearchImage(searchtags, max_size)
        indexer = searcher.index_image_files(search_path)

        if indexer is not None:
            searcher.search_filename(indexer, number_of_hits)
        else:
            print 'Error, corrupt or non-existing index!'

    else:
        print ('Need anyone arguments among city, state, country, postal_code, date, month or year')
