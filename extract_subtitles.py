#!/usr/bin/env python3
import argparse
import subprocess
import shutil
import sys
import json
import re

from os import path


class SubtitleStream:
    def __init__(self, index: int, basename_no_ext: str, folder: str, language: str = None, title: str = None):
        self.index = index
        self.language = language
        self.title = title
        self.basename_no_ext = basename_no_ext
        self.folder = folder
        self.filename = None

    def get_filename(self) -> str:
        if self.filename:
            return self.filename
        elif self.language and self.title:
            return '{}.{}.{}.srt'.format(self.basename_no_ext, self.language, self.title)
        elif self.language:
            return '{}.{}.srt'.format(self.basename_no_ext, self.language)
        elif self.title:
            return '{}.{}.srt'.format(self.basename_no_ext, self.title)
        else:
            return '{}.{}.srt'.format(self.basename_no_ext, str(self.index).zfill(3))

    def get_path(self) -> str:
        return path.join(self.folder, self.get_filename())

    def __str__(self) -> str:
        return 'SubtitleStream \033[1m{}\033[0m: language: {}, title: {}'.format(self.index, self.language, self.title)

    def __repr__(self) -> str:
        return str(self)

    @staticmethod
    def from_json(data: json, basename_no_ext: str, folder: str) -> 'SubtitleStream':
        subtitle = SubtitleStream(int(data['index']), basename_no_ext, folder, None, None)
        try:
            subtitle.language = data['tags']['language']
        except KeyError as e:
            pass

        try:
            subtitle.title = data['tags']['title']
        except KeyError as e:
            pass

        return subtitle


pattern = re.compile('([\d\s,]*)')
def parse_input(valid_indexes: [int], input: str) -> []:
    if input == '':
        return valid_indexes

    if not pattern.fullmatch(input):
        return None

    input_sanitized = re.sub(r'\s+', '', input)

    indexes = [int(i) for i in input_sanitized.split(',')]
    if set(indexes).issubset(valid_indexes):
        return indexes
    else:
        return None


def extract_subtitle(ffmpeg_executable: str, video_file_path: str, index: int, subtitle_out_path: str, log_level: str):
    ffmpeg_result = subprocess.run(
        [
            ffmpeg_executable,
            '-hide_banner',
            '-loglevel',
            log_level,
            '-i',
            video_file_path,
            '-map',
            '0:{}'.format(index),
            subtitle_out_path
        ]
    )

    if ffmpeg_result.returncode != 0:
        print('ffmpeg process did not exit cleanly, subtitle {} might not have been extracted'.format(index))
        return

    print('Extracted subtitle to file {}'.format(subtitle_out_path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract subrip (*.srt) subtitles from video files using ffprobe '
                                                 'and ffmpeg')
    parser.add_argument('-a',
                        '--autoconfirm',
                        action='store_true',
                        dest='autoconfirm',
                        help='Autoconfirm choices. Extracts all found subtitles using a generated name. Names are '
                             'generated using language tag, if available. If the language tag is not set the index of '
                             'the subtitle is appended to its name')
    parser.add_argument('--ffmpeg-loglevel',
                        '--fl',
                        type=str,
                        dest='ffmpeg_loglevel',
                        choices=['debug', 'verbose', 'info', 'warning'],
                        default='warning',
                        help='Log level used for ffmpeg / ffprobe commands. Default "warning", info shows progress')
    parser.add_argument(type=str,
                        dest='file',
                        help='Video file containing the subtitles. Subtitles will be saved to the directory of the '
                             'video file')
    args = parser.parse_args()
    autocomplete = args.autoconfirm
    ffmpeg_loglevel = args.ffmpeg_loglevel
    file = args.file

    if path.exists(file) and path.isfile(file):
        file = path.abspath(file)
    else:
        sys.exit('Specified file does not exist')

    ffprobe = shutil.which('ffprobe')
    if not ffprobe:
        sys.exit("Missing tool ffprobe")

    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        sys.exit("Missing tool ffmpeg")

    # Get subtitle streams
    ffprobe_result = subprocess.run(
        [
            ffprobe,
            '-loglevel',
            ffmpeg_loglevel,
            '-print_format',
            'json',
            '-show_streams',
            '-select_streams',
            's',
            file
        ],
        capture_output=True)

    if ffprobe_result.returncode != 0:
        sys.exit("ffprobe process did not exit cleanly")

    folder = path.dirname(file)
    filename = path.basename(file)
    filename_no_ext = path.splitext(filename)[0]
    #print('folder: {}\nfilename: {}\nfilename_no_ext: {}'.format(folder, filename, filename_no_ext))

    input_data = json.loads(ffprobe_result.stdout)
    subtitle_streams = []
    for item in input_data['streams']:
        if item['codec_name'] == 'subrip':
            tmp_subtitle_stream = SubtitleStream.from_json(item, filename_no_ext, folder)
            subtitle_streams.append(tmp_subtitle_stream)

    amount_subtitle_streams = len(subtitle_streams)
    if amount_subtitle_streams == 0:
        print('No subrip subtitles found in file')
        sys.exit(0)

    print('Found {} subtitles in file {}:'.format(amount_subtitle_streams, file))
    for subtitle_stream in subtitle_streams:
        print('\t{}'.format(subtitle_stream))

    valid_indexes = [s.index for s in subtitle_streams]
    if autocomplete:
        chosen_indexes = valid_indexes
    else:
        input_str = input('Limit which subtitles should be extracted by entering their respective '
                          'indexes (for example: {}). Leave empty to extract all: '
                          .format(','.join([str(i) for i in valid_indexes[:3]])))
        chosen_indexes = parse_input(valid_indexes, input_str)
        while not chosen_indexes:
            print('Invalid input "{}": '.format(input_str))
            input_str = input()
            chosen_indexes = parse_input(valid_indexes, input_str)

    for index in chosen_indexes:
        subtitle_stream = [s for s in subtitle_streams if s.index == index][0]
        print('Extracting subtitle {} to file: \033[1m{}\033[0m.'.format(index, subtitle_stream.get_filename()))

        if not autocomplete:
            name = input('Press enter to continue, else type in a different name (must end with extension ".srt"): '
                         .format(index, subtitle_stream.get_filename()))

            while name and not name.endswith('.srt'):
                name = input('Invalid name. Names must end with extension ".srt": ')

            if name:
                subtitle_stream.filename = name

        # call extract process
        print('Starting extraction, might take some time. Please wait...')
        extract_subtitle(ffmpeg, file, subtitle_stream.index, subtitle_stream.get_path(), ffmpeg_loglevel)
