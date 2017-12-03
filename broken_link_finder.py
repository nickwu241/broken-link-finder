#!/usr/bin/env python3
import argparse
import os
import re
import ssl
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

# https://regexr.com/3e6m0
# URL_PATTERN = re.compile(r'((http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*))')

# https://stackoverflow.com/questions/6883049/regex-to-find-urls-in-string-in-python
URL_PATTERN = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
TIMEOUT = 10


def good_link(link):
    if not link.startswith('http'):
        print(f'-> prepend "http://" to "{link}"')
        link = 'http://' + link

    try:
        r = urlopen(link, timeout=TIMEOUT)
        print(f'-> [SUCCESS] status={r.getcode()}')
        return True
    except URLError as e:
        print(f'-> [ERROR] e={e}')
        return False
    except HTTPError as e:
        print(f'-> [ERROR] e={e}')
        return False
    except ssl.CertificateError as e:
        print('-> [ERROR] SSL Certificate, retrying wtih http...')
        return good_link(link.replace('https://', 'http://'))


def process_file(fh):
    print(f'Processing file "{fh.name}..."')
    print('-------------------------------')
    bad_links = []
    for i, line in enumerate(fh):
        for m in URL_PATTERN.findall(line):
            link = str(m)
            print(f'GET "{link}" from line {i+1}...')
            if not good_link(link):
                bad_links.append((link, i+1, fh.name)) 
    print('-------------------------------')
    return bad_links


def main():
    parser = argparse.ArgumentParser(description='Check for broken links in files.')
    parser.add_argument('path', metavar='file | directory',
                        help='file or directory to check')
    parser.add_argument('--recursive', '-r', action='store_true',
                        help='recursively check directory')

    args = parser.parse_args()
    path = args.path

    bad_links = []
    if not os.path.exists(path):
        print(f'{path} does not exist. Make sure the path exist.')
        exit(1)
    elif os.path.isfile(path):
        with open(path, 'r') as f:
            bad_links += process_file(f)
    elif os.path.isdir(path):
        if not args.recursive:
            print(f'{path} is a directory. Specify --recursive flag to check directories.')
            exit(1)

        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filename = os.path.join(dirpath, filename)
                with open(filename, 'r') as f:
                    bad_links += process_file(f)
    else:
        raise Exception(f'{path} is not a file or directory...?')

    if bad_links:
        print('Potential broken links:')
        for link, line_number, filename in bad_links:
            print(f'    {link} from line {line_number} in {filename}')
    else:
        print('All links look fine :)')


if __name__ == '__main__':
    main()

