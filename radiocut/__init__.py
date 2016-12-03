"""radiocut.fm downloader

Usage:
  radiocut <audiocut_url> [<output-file-name>] [--verbose] [--background=<path-to-image>]

Options:
  -h --help     Show this screen.
"""
import re
import sys
import tempfile
from pyquery import PyQuery
import requests
from moviepy.editor import AudioFileClip, ImageClip, concatenate_audioclips

__version__ = '0.2.1'

AUDIOCUT_PATTERN = re.compile('https?://radiocut\.fm/audiocut/[-\w]+/?')


def get_radiocut(url, verbose=False):
    """
    Given an "audio cut" url, return a moviepy's AudioClip instance with the cut
    """

    if verbose:
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
        if verbose:
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

    if verbose:
        print(len(chunks))
        print('Looking for first chunk')
    for i, c in enumerate(chunks):
        if c['start'] + c['length'] > float(seconds):
            first_chunk = i
            break
    if verbose:
        print('Looking for last chunk')
    for i, c in enumerate(chunks[first_chunk:]):
        if c['start'] + c['length'] > float(seconds) + float(duration):
            last_chunk = min(len(chunks), first_chunk + i + 1)
            break

    audios = [get_mp3(chunk, verbose=verbose) for chunk in chunks[first_chunk:last_chunk]]
    start_offset = float(seconds) - chunks[first_chunk]['start']
    cut = concatenate_audioclips(audios)
    cut = cut.subclip(start_offset, start_offset + float(duration))
    return cut


def get_mp3(chunk, verbose=False):
    url = chunk['base_url'] + '/' + chunk['filename']
    if verbose:
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
    url = arguments['<audiocut_url>'].partition('#')[0]
    if not re.match(AUDIOCUT_PATTERN, url):
        print('The given URL is invalid. Example: http://radiocut.fm/audiocut/macri-gato/')
        sys.exit(1)
    if not url.endswith('/'):
        url += '/'
    verbose = bool(arguments['--verbose'])

    audio_clip = get_radiocut(url, verbose)
    background = arguments['--background']
    extension = 'mp4' if background else 'mp3'

    output_file_name = arguments['<output-file-name>']
    if output_file_name is None:
        output_file_name = '{}.{}'.format(url.split('/')[-2], extension)

    if not background:
        audio_clip.write_audiofile(
            str(output_file_name),
            fps=16000,
            nbytes=2,
            bitrate='16k',
            verbose=verbose
        )
    else:
        clip = ImageClip(background, duration=audio_clip.duration)
        clip = clip.set_audio(audio_clip)
        clip.write_videofile(
            str(output_file_name),
            fps=1,
            audio_fps=16000,
            audio_nbytes=2,
            audio_bitrate='16k',
            verbose=verbose
        )


if __name__ == '__main__':
    main()