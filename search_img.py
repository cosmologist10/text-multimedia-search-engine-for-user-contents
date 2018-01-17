import os
import time
import re
import exiftool
import hashlib
import cPickle
import operator
import pathlib
import pprint
import json
from pathlib import Path
from collections import defaultdict

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

        filter_set = {'set_1': {'file_modify_date',
                                'file_inode_change_date',
                                'file_access_date',
                                'file_type',
                                'file_size'},
                      'set_2': {'orientation',
                                'software',
                                'modify_date',
                                'flash',
                                'date_time_original',
                                'create_date',
                                'focal_length',
                                'model',
                                'x_resolution',
                                'y_resolution',
                                'y_resolution'},
                      'set_3': {'g_p_s_latitude',
                                'g_p_s_longitude',
                                'g_p_s_altitude',
                                'g_p_s_time_stamp',
                                'g_p_s_date_stamp'},
                      'set_4': {'image_width',
                                'image_height',
                                'megapixels'}}

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
                        target[fname][final_key] = value

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
            print file_last_modify
            dir_last_modify = os.path.getmtime(loc)
            print dir_last_modify

            comp = dir_last_modify < file_last_modify

            if comp:
                # If index is newer load index
                print 'Loading', complete_name
                index = self.load(complete_name)
                # 2nd argument indicating no index was created
                return index, False
            else:
                # Else rebuild index
                rebuild = True

        if rebuild:
            print 'Directory got modified at ' + time.ctime(dir_last_modify) + ', rebuilding index...'
        else:
            print 'Index not present, building it...'

        files = self.file_gen(loc)

        index = self.index_img_meta(files)
        self.save(index, complete_name)
        print 'Index built at',complete_name

        # 2nd argument indicating index was created
        return index, True

if __name__ == "__main__":

    import sys
    import argparse

    parser = argparse.ArgumentParser(description='It takes searchword as positional argument and locations as optional argument.')
    parser.add_argument('searchword', help='The searchword which, you are looking for.')
    parser.add_argument('-p', dest='loc', required=True, help='Path of directory.')
    parser.add_argument('-s', '--size', required=True, help='Maximum size of the file')
    if len(sys.argv)<3:
        sys.argv.append('-h')

    args = parser.parse_args()

    max_size = str(args.size)

    searcher = SearchImage(args.searchword, max_size)
    index, status = searcher.index_image_files(args.loc)
    print json.dumps(index, indent=4)
