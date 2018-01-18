import os
import time
import re
import hashlib
import cPickle
import operator
import pathlib
import json
from pathlib import Path
from collections import defaultdict
from text_mod import utils

# metadata extraction library
import exiftool

from text_mod.search_word import SearchWord


class SearchAudio(SearchWord):
    """ Audio searcher cum indexer using python dictionaries. """

    def __init__(self, searchword, max_size):

        SearchWord.__init__(self, searchword, max_size)
        self.my_extensions = ('.mp3', '.ogg', '.wav', '.flac', '.wma')


    def index_audio_meta(self, audio_flist):
        """
        Return a list the important audio metadata using two libraries(exiftool
        & tinytag) along with their source file name as key for the given audio
        files.
        """

        filter_set = {'set_1': {'file_type',
                                'file_size'},
                      'set_2': {'artist',
                                'album',
                                'genre',
                                'year'}}

        my_set = []

        target = defaultdict(dict)

        # To flatten the filter_set values into a single list
        for fset in filter_set.values():
            my_set += fset

        # extract metadata having filter_set tags using pyexiftool library
        with exiftool.ExifTool() as et:

            for fname in audio_flist:
                print 'Filename =>', fname
                # get metadata for the file
                metadata = et.get_metadata(fname)


                for key, value in metadata.iteritems():
                    if ':' in key:
                        imp_words = key.split(':')[1]

                        # Constructing my own key, which will print 'Final key',final_key
                        split_words = re.findall('[A-Z][a-z]*', imp_words)
                        join_words = "_".join(split_words)
                        final_key = join_words.lower().strip()
                        # print 'Final key',final_key

                        # Check if this is there in my filter_set
                        if final_key in my_set:
                            if type(value) == unicode:
                                value = value.encode('utf-8')
                            target[fname][final_key] = str(value).lower().strip()
        return target

    def index_audio_files(self, loc):
        """
        Return and save the crucial metadata of all audio files under
        particular directory.
        """

        fname = hashlib.md5(loc).hexdigest() + '.audioindex'

        complete_name = os.path.join(self.save_path, fname)
        my_file = Path(complete_name)
        rebuild = False

        if my_file.is_file():
            file_last_modify = os.path.getmtime(complete_name)
            print 'File last modified at'+ ':' + str(file_last_modify)
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

        with utils.clock_timer() as timer:
            index = self.index_audio_meta(self.file_gen(loc))

        self.save(index, complete_name)
        print 'Index built at', complete_name

        return index

    def search_filename(self, dic, hits):
        """ Return the filename of respective artist/album/genre/year. """

        final_list = []
        for filename, data in dic.iteritems():
            for searchtag in self.searchword:
                if searchtag in data.values():
                    if filename not in final_list:
                        final_list.append(filename)

        print 'Found', str(len(final_list)), 'hits'

        if len(final_list) >= int(hits):
            print 'Showing top', hits, 'hits', 'out of', str(len(final_list))
            for num in range(int(hits)):
                print final_list[num]
        elif len(final_list)==0:
            print 'Sorry, No such files found!'
        else:
            print 'Only', str(len(final_list)), 'hits found, showing them:'
            for files in final_list:
                print files


if __name__ == "__main__":

    import sys
    import argparse

    parser = argparse.ArgumentParser(description='It takes searchword as positional argument and locations as optional argument.')
    parser.add_argument('-artist', '--artist', help='')
    parser.add_argument('-album', '--album', help ='')
    parser.add_argument('-genre', '--genre', help='')
    parser.add_argument('-y', '--year', help = '')
    parser.add_argument('-d', '--dir', required=True, help='Full path of directory you want to index and search')
    parser.add_argument('-s', '--size', required=True, help='Maximum size of the file')
    parser.add_argument('-n', '--num', required=True, help='Number of hits')

    args = parser.parse_args()

    search_path = str(args.dir)
    max_size = str(args.size)
    number_of_hits = str(args.num)

    if args.artist or args.album or args.genre or args.year:
        tags = [args.artist, args.album, args.genre, args.year]
        searchtags = [str(tag).lower().strip() for tag in tags if tag is not None]

        searcher = SearchAudio(searchtags, max_size)
        indexer = searcher.index_audio_files(search_path)

        if indexer != None:
            searcher.search_filename(indexer, number_of_hits)
        else:
            print 'Error, corrupt or non-existing index!'

    else:
        print ('Need anyone arguments among artist, album, genre, year.')
