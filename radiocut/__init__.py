"""radiocut.fm downloader

Usage:
  radiocut <audiocut_url>

Options:
  -h --help     Show this screen.
"""

import tempfile
from pyquery import PyQuery
import requests
from moviepy.editor import AudioFileClip, concatenate_audioclips

__version__ = '0.1'


def radiocut(url):
    print('Retrieving {}'.format(url))
    title = url.split('/')[-2] + '.mp3'
    pq = PyQuery(url)
    seconds = pq('li.audio_seconds').text()
    duration = pq('li.audio_duration').text()
    station = pq('li.audio_station').text()
    base_url = pq('li.audio_base_url').text()

    chunks_url = "{}/server/get_chunks/{}/{}/".format(base_url, station, seconds[:6])
    chunks_json = requests.get(chunks_url).json()[seconds[:6]]
    base_url = chunks_json['baseURL']
    chunks = chunks_json['chunks']
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

    audios = [get_mp3(chunk, base_url) for chunk in chunks[first_chunk:last_chunk]]
    start_offset = float(seconds) - chunks[first_chunk]['start']
    cut = concatenate_audioclips(audios)
    cut = cut.subclip(start_offset, start_offset + float(duration))
    cut.write_audiofile(title)


def get_mp3(chunk, base_url=''):
    url = chunk.get('base_url', base_url) + '/' + chunk.get('filename')
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
    print(arguments)
    radiocut(arguments['<audiocut_url>'])

if __name__ == '__main__':
    main()