import os
import os.path
import time
import re
import string
import hashlib
import cPickle
import operator
import pathlib
from pathlib import Path

import utils

class SearchWord(object):
    """ Word searcher cum indexer using Python dictionaries """

    def __init__(self, searchword, max_size):

        self.searchword = searchword
        self.max_size = max_size
        self.save_path = os.path.expanduser('~/.indexer/')
        if not os.path.isdir(self.save_path):
            os.makedirs(self.save_path)
        self.word_re = re.compile('[' + re.escape(string.punctuation) + ']+')
        self.numalpha = re.compile(r'[a-zA-Z0-9]+')
        self.my_extensions = ('.py', '.txt',)

    def file_gen(self, loc):
        """ Return a list of text files available the given directory location. """

        for root, dirnames, filenames in os.walk(loc):
            for filename in filenames:
                # Size limit
                if filename.endswith(self.my_extensions):
                    full_filename = os.path.join(root, filename)
                    with utils.ignore_all():
                        if os.path.getsize(full_filename)<=self.max_size:
                            yield full_filename

    def index_files(self, text_flist):
        """ Return a dictionary of occurance of words for a given list of files. """

        dic = {}

        for f in text_flist:
            print 'Processing file',f,'...'
            try:
                for line in open(f):
                    words = line.split()
                    words_punc = [raw_word.lower().strip() for raw_word in words]
                    for words in words_punc:
                        word_group = self.word_re.sub(' ', words)
                        word_list = self.numalpha.findall(word_group)
                        for word in word_list:
                            if (word, f) in dic:
                                dic[word, f] += 1
                            else:
                                dic[word, f] = 1
            except IOError:
                print 'Skipping file',f,'...'

        return dic

    def save(self, dic, filename):
        """ Serialising the dictionary and saves to a file """

        cPickle.dump(dic, file(filename, 'w'))

    def load(self, filename):
        """ Deserialises a previously saved file. """

        try:
            return cPickle.load(open(filename))
        except Exception, e:
            print 'Error loading index file',filename,'=>',e
            print 'Index possibly corrupt, deleting it'
            os.remove(filename)

    def indexFilename(self, loc):
        """ Return an index of words from all text files given under the directory. """

        fname = hashlib.md5(loc).hexdigest() + '.textindex'

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
            index = self.index_files(self.file_gen(loc))

        self.save(index, complete_name)
        print 'Index built at', complete_name

        return index

    def searchWord(self, dic, hits):
        """ Return the occurance of the searchword in sorted order along with
        the associated filename. "
        """

        final_list = []
        for key, value in dic.items():
            if key[0] == self.searchword:
                x = (key[1], value)
                final_list.append(x)

        print 'Found ' + str(len(final_list)) + ' hits'
        result = sorted(final_list, key=operator.itemgetter(1), reverse=True)

        if int(len(final_list)) > int(hits):
            print 'Showing top', hits, 'hits', 'out of', str(len(final_list))
            for i in result[:int(hits)]:
                print i[0],'=>', i[1]
        elif len(final_list)==0:
            print 'Sorry, No such files found!'
        else:
            print 'Only', str(len(final_list)), 'hits found, showing them:'
            for i in result[:int(len(final_list))]:
                print i[0],'=>', i[1]

if __name__ == "__main__":

    import sys
    import argparse

    # no. of hits, we are interested in (n)

    parser = argparse.ArgumentParser(description='Folder indexer and searcher. Accepts searchword and folder to search for as arguments')
    parser.add_argument('-w','--word', help='The searchword which, you are looking for.')
    parser.add_argument('-d', '--dir', required=True, help='Full path of directory you want to index and search')
    parser.add_argument('-s', '--size', required=True, help='Maximum size of the file')
    parser.add_argument('-n', '--num', required=True, help='Number of hits')
    if len(sys.argv)<4:
        sys.argv.append('-h')

    args = parser.parse_args()

    search_word = str(args.word).lower()
    search_path = str(args.dir)
    max_size = str(args.size)
    number_of_hits = str(args.num)

    searcher = SearchWord(search_word, max_size)
    indexer = searcher.indexFilename(search_path)
    if indexer != None:
        searcher.searchWord(indexer, number_of_hits)
    else:
        print 'Error, corrupt or non-existing index!'
