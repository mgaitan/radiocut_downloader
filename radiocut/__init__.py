"""radiocut.fm downloader

Usage:
  radiocut <audiocut_or_podcast> [<output-file-name>] [--verbose] [--background=<path-to-image>] [--join]

Options:
  -h --help                         Show this screen.
  --background=<path-to-image>      If given, produce a video with this image as background
  --join                            Concatenate podcast's cuts as a single file
"""
import re
import sys
import tempfile
from pyquery import PyQuery
import requests
from moviepy.editor import AudioFileClip, ImageClip, concatenate_audioclips

__version__ = '0.3'

AUDIOCUT_PATTERN = re.compile('https?://radiocut\.fm/audiocut/[-\w]+/?')
PODCAST_PATTERN = re.compile('https?://radiocut\.fm/pdc/[-\w]+/[-\w]+/?')


def get_audiocut(url, verbose=False):
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


def get_urls_from_podcast(url, verbose=False):
    """given the url to a podcast, return the list of urls to each audiocut"""
    pq = PyQuery(url)
    pq.make_links_absolute()
    return [PyQuery(a).attr('href') for a in pq('.cut_brief h4 a')]


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


def main():
    from docopt import docopt
    arguments = docopt(__doc__, version=__version__)

    url = arguments['<audiocut_or_podcast>'].partition('#')[0]
    is_audiocut = re.match(AUDIOCUT_PATTERN, url)
    is_podcast = re.match(PODCAST_PATTERN, url)
    if not is_audiocut and not is_podcast:
        print("""The given URL is not a valid audiocut or podcast from radiocut.fm.
Examples:
    - http://radiocut.fm/audiocut/macri-gato/
    - http://radiocut.fm/pdc/tin_nqn_/test
""")
        sys.exit(1)
    if is_audiocut and not url.endswith('/'):
        url += '/'
    verbose = bool(arguments['--verbose'])

    if is_podcast:
        urls = get_urls_from_podcast(url, verbose)

    else:
        urls = [url]

    audioclips = [get_audiocut(url, verbose) for url in urls]
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
            given_filename=arguments['<output-file-name>'],
            extension=extension)

    for clip, filename in zip(audioclips, output_filenames):
        write_output(clip, filename, background, verbose=verbose)



if __name__ == '__main__':
    main()