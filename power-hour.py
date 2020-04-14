import os
import subprocess


def get_video_filename(yt_id, path='.'):
    '''checks occurance in working dir or path and returns filename'''
    for f in os.listdir(path):
        if yt_id in f:
            return f
    return None


def get_yt_id(yt_url):
    '''strips id'''
    if 'youtu.be/' in yt_url:
        return yt_url.split('youtu.be/')[1]
    else:
        return yt_url.split('watch?v=')[1]


def call_yt_dl(yt_url):
    '''downloads m4a to working dir'''
    args = [
        'youtube-dl',
        '-f', 'best[height<=720]', 
	'--id',
        yt_url
    ]
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()

    # fix filename
    filename = get_video_filename(get_yt_id(yt_url))
    if "'" in filename:
        os.rename(filename, filename.replace("'", ""))


def get_index(filename='index.txt'):
    '''yields (url, timestamp) pairs'''
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if line[:4] != 'http':
                continue
            line = line.split('#')[0].strip()
            yt_url, timestamp = line.split()
            if '&' in yt_url:
                yt_url = yt_url.split('&')[0]
            yield yt_url, timestamp


def download_all():
    '''downloads new tracks from index to working dir'''
    for yt_url, _ in get_index():
        if not get_video_filename(get_yt_id(yt_url)):
            print('downloading', yt_url)
            call_yt_dl(yt_url)


def call_ffmpeg_cut(filename, timestamp, separator_track=None):
    '''cuts 1 min of already downloaded file in working dir starting at timestamp and stores it in cut/'''
    args = [
        'ffmpeg',
        '-ss', timestamp,
        '-i', filename,
    ]
    if separator_track is not None:
        args += [
	    '-i', 'airhorn_delayed.m4a',
	    '-filter_complex', 'amix=inputs=2:duration=longest',
            '-c:a', 'aac',
        ]
    args += [
        '-c:v', 'libx264',
        '-t', '60',
        '-y',
        os.path.join('cut', filename)
    ]
    subprocess.check_output(args)


def cut_all(separator_track):
    '''creates cut versions of all index tracks'''
    for yt_url, timestamp in get_index():
        if not get_video_filename(get_yt_id(yt_url), 'cut'):
            filename = get_video_filename(get_yt_id(yt_url))
            print('cutting', yt_url)
            call_ffmpeg_cut(filename, timestamp, separator_track)


def call_ffmpeg_concat(filename_in, filename_out):
    '''creates concatenated mix based on playlist specified by filename_in'''
    args = [
	'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', filename_in,
        '-c', 'copy',
        '-y',
        filename_out
    ]
    subprocess.check_output(args)


def create_mix(filename):
    '''writes playlist.txt and concatenates mix with cut tracks and separator_track'''
    with open('playlist.txt', 'w') as f:
        for basename in os.listdir('cut'):
            path = os.path.join('cut', basename)
            if not os.path.isfile(path):
                continue
            f.write("file '%s'\n" % path)
    print('concatenating to', filename)
    call_ffmpeg_concat('playlist.txt', filename)


if __name__ == '__main__':
    # create cut dir on first run
    if not os.path.isdir('cut'):
        os.mkdir('cut')

    if not os.path.exists('index.txt'):
        exit('missing index.txt')

    download_all()
    cut_all('airhorn.m4a')
    create_mix('POWERHOUR.mp4')
