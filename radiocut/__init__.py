"""radiocut.fm downloader

Usage:
  radiocut <url> [<output-file-name>]
            [--verbose] [--background=<path-to-image>] [--join] [--duration=<duration>]

Options:
  -h --help                         Show this screen.
  --background=<path-to-image>      If given, produce a video with this image as background
  --join                            Concatenate podcast's cuts as a single file
  --duration=<duration>             The length to download (in seconds)
"""
import re
import sys
import tempfile
from dateutil.parser import parse
from pyquery import PyQuery
import requests
from moviepy.editor import AudioFileClip, ImageClip, concatenate_audioclips

__version__ = '0.4'

AUDIOCUT_PATTERN = re.compile('https?://radiocut\.fm/audiocut/[-\w]+/?')
PODCAST_PATTERN = re.compile('https?://radiocut\.fm/pdc/[-\w]+/[-\w]+/?')
RADIOSTATION_PATTERN = re.compile('https?://radiocut\.fm/radiostation/.*')
SHOW_PATTERN = re.compile('https?://radiocut\.fm/radioshow/([-\w]+)/?')

NOT_VALID_MSG = """
The given URL is not a valid audiocut, podcast or timestamp from radiocut.fm.
Examples:
    - http://radiocut.fm/audiocut/macri-gato/
    - http://radiocut.fm/pdc/tin_nqn_/test
    - http://radiocut.fm/radiostation/nacional870/listen/2017/07/01/10/00/00/
    - https://radiocut.fm/radioshow/el-lobby/

"""

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0',
}

def get_audiocut(url, verbose=False, duration=None):
    """
    Given an "audio cut" url, return a moviepy's AudioClip instance with the cut
    """

    if verbose:
        print('Retrieving {}'.format(url))

    pq = PyQuery(url)
    seconds = pq('li.audio_seconds').text()
    if duration is None:
        duration = float(pq('li.audio_duration').text())
    station = pq('li.audio_station').text()
    base_url = pq('li.audio_base_url').text()

    start_folder = int(seconds[:6])
    chunks = []
    while True:
        chunks_url = "{}/server/get_chunks/{}/{:d}/".format(base_url, station, start_folder)
        if verbose:
            print('Getting chunks index {}'.format(chunks_url))
        chunks_json = requests.get(chunks_url, headers=HEADERS).json()[str(start_folder)]
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
        print('Need to download {} chunks'.format(len(chunks)))
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


def get_urls_from_podcast(url, verbose=False):
    """given the url to a podcast, return the list of urls to each audiocut"""
    pq = PyQuery(url)
    pq.make_links_absolute()
    return [PyQuery(a).attr('href') for a in pq('.cut_brief h4 a')]


def get_mp3(chunk, verbose=False):
    url = chunk['base_url'] + '/' + chunk['filename']
    if verbose:
        print('Downloading chunk {}'.format(url))
    r = requests.get(url, stream=True, headers=HEADERS)
    if r.status_code == 200:
        _, p = tempfile.mkstemp('.mp3')
        with open(p, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        return AudioFileClip(p)


def output_file_names(urls, given_filename=None, extension='mp3'):

    filenames = []
    for i, url in enumerate(urls):
        filename = given_filename or url.rstrip('/').split('/')[-1]
        if i and given_filename:
            filename = '{}_{}'.format(filename, i)
        filenames.append('{}.{}'.format(filename, extension))
    return filenames


def write_output(audio_clip, output_filename, background=None, verbose=False):

    if not background:
        audio_clip.write_audiofile(
            output_filename,
            fps=16000,
            nbytes=2,
            bitrate='16k',
            verbose=verbose
        )
    else:
        clip = ImageClip(background, duration=audio_clip.duration)
        clip = clip.set_audio(audio_clip)
        clip.write_videofile(
            output_filename,
            fps=1,
            audio_fps=16000,
            audio_nbytes=2,
            audio_bitrate='16k',
            verbose=verbose
        )


def get_show(url, show, verbose):
    pq = PyQuery(url)
    title = pq('h1:first').text()

    url = 'https://radiocut.fm/api/radioshows/{}/last_recordings/?limit=1&accept=application/json'.format(show)
    if verbose:
        print('Requesting API {}'.format(url))
    data = requests.get(url, headers=HEADERS).json()[0]
    start = parse(data['start'])
    title += '-{}'.format(start.date())
    title = title.lower().replace(' ', '-')
    end = parse(data['end'])
    duration = (end - start).total_seconds()
    return ['https://radiocut.fm{}'.format(data['url'])], duration, title


def main():
    from docopt import docopt
    arguments = docopt(__doc__, version=__version__)

    url = arguments['<url>'].partition('#')[0]
    duration = None
    output_filename = ''
    is_audiocut = re.match(AUDIOCUT_PATTERN, url)
    is_podcast = re.match(PODCAST_PATTERN, url)
    is_radiostation = re.match(RADIOSTATION_PATTERN, url)
    is_show = re.match(SHOW_PATTERN, url)
    if not any([is_audiocut, is_podcast, is_radiostation, is_show]):
        print(NOT_VALID_MSG)
        sys.exit(1)

    if not url.endswith('/'):
        url += '/'
    verbose = bool(arguments['--verbose'])

    if is_podcast:
        urls = get_urls_from_podcast(url, verbose)
    elif is_show:
        urls, duration, output_filename = get_show(url, is_show.group(1), verbose)
    else:
        urls = [url]

    duration = arguments['--duration'] or duration
    if duration is not None:
        duration = int(duration)

    audioclips = [get_audiocut(url, verbose, duration) for url in urls]
    background = arguments['--background']
    extension = 'mp4' if background else 'mp3'

    if arguments['--join'] or is_audiocut:
        audioclips = [concatenate_audioclips(audioclips)]
        output_filenames = output_file_names(
            [url],
            given_filename=arguments['<output-file-name>'],
            extension=extension)
    else:
        output_filenames = output_file_names(
            urls,
            given_filename=arguments['<output-file-name>'] or output_filename,
            extension=extension)

    for clip, filename in zip(audioclips, output_filenames):
        write_output(clip, filename, background, verbose=verbose)


if __name__ == '__main__':
    main()
