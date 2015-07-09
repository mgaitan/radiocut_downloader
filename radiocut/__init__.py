"""radiocut.fm downloader

Usage:
  radiocut <audiocut_url> [<output-file-name>]

Options:
  -h --help     Show this screen.
"""

import tempfile
from pyquery import PyQuery
import requests
from moviepy.editor import AudioFileClip, concatenate_audioclips

__version__ = '0.2.1'


def radiocut(url, output_file_name=None):

    print('Retrieving {}'.format(url))


    pq = PyQuery(url)
    seconds = pq('li.audio_seconds').text()

    duration = pq('li.audio_duration').text()
    station = pq('li.audio_station').text()
    base_url = pq('li.audio_base_url').text()

    start_folder = int(seconds[:6])
    chunks = []
    while True:
        chunks_url = "{}/server/get_chunks/{}/{:d}/".format(base_url, station, start_folder)
        print('Getting chunks index {}'.format(chunks_url))
        chunks_json = requests.get(chunks_url).json()[str(start_folder)]
        for chunk_data in chunks_json['chunks']:
            # set the base_url if isnt defined
            chunk_data['base_url'] = chunk_data.get('base_url', chunks_json['baseURL'])
            chunks.append(chunk_data)
        c = chunks[-1]
        if c['start'] + c['length'] > float(seconds) + float(duration):
            break
        # if the last chunk isn't in this index, get the next one
        start_folder += 1

    print(len(chunks))
    print('Looking for first chunk')
    for i, c in enumerate(chunks):
        if c['start'] + c['length'] > float(seconds):
            first_chunk = i
            break
    print('Looking for last chunk')
    for i, c in enumerate(chunks[first_chunk:]):
        if c['start'] + c['length'] > float(seconds) + float(duration):
            last_chunk = min(len(chunks), first_chunk + i + 1)
            break

    audios = [get_mp3(chunk) for chunk in chunks[first_chunk:last_chunk]]
    start_offset = float(seconds) - chunks[first_chunk]['start']
    cut = concatenate_audioclips(audios)
    cut = cut.subclip(start_offset, start_offset + float(duration))
    if output_file_name is None:
        output_file_name = url.split('/')[-2] + '.mp3'
    cut.write_audiofile(str(output_file_name))


def get_mp3(chunk):
    url = chunk['base_url'] + '/' + chunk['filename']
    print('Downloading chunk {}'.format(url))
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        _, p = tempfile.mkstemp('.mp3')
        with open(p, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        return AudioFileClip(p)

def main():
    from docopt import docopt
    arguments = docopt(__doc__, version=__version__)
    radiocut(arguments['<audiocut_url>'], arguments['<output-file-name>'])

if __name__ == '__main__':
    main()