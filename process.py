"""Runs the feature extraction on the waveforms and binarises the label files.

Usage:
    python process.py [--lab_dir DIR] [--state_level] [--wav_dir DIR] [--id_list FILE] --out_dir DIR"""

import argparse
import os

import file_io
import label_io
import feature_io


def add_arguments(parser):
    parser.add_argument("--lab_dir", action="store", dest="lab_dir", type=str, default=None,
                        help="Directory of the label files to be converted.")
    parser.add_argument("--wav_dir", action="store", dest="wav_dir", type=str, default=None,
                        help="Directory of the wave files to be converted.")
    parser.add_argument("--id_list", action="store", dest="id_list", type=str, default=None,
                        help="List of file ids to process (must be contained in lab_dir).")
    parser.add_argument("--out_dir", action="store", dest="out_dir", type=str, required=True, default=None,
                        help="Directory to save the output to.")
    file_io.add_arguments(parser)
    label_io.add_arguments(parser)


def get_file_ids(dir, id_list=None):
    """Determines the basenames of all files to be processed, using id_list of os.listdir.

    Args:
        dir (str): Directory where the basenames would exist.
        id_list (str): File containing a list of basenames, if not given `os.listdir(dir)` is used instead.

    Returns:
        file_ids (list<str>): Basenames of files in dir or id_list"""
    if id_list is None:
        file_ids = filter(lambda f: f.endswith('.lab'), os.listdir(dir))
        file_ids = map(lambda x: x[:-len('.lab')], file_ids)
    else:
        file_ids = label_io.load_txt(id_list)

    return file_ids


def process_files(lab_dir, wav_dir, id_list, out_dir, state_level):
    """Processes label and wave files in id_list, saves the binarised labels and vocoder features to a protobuffer.

    Args:
        lab_dir (str): Directory containing the label files.
        wav_dir (str): Directory containing the wave files.
        id_list (str): List of file basenames to process.
        out_dir (str): Directory to save the output to.
        state_level (bool): Indicates that label files are state level if True, otherwise they are frame level.
        """
    file_ids = get_file_ids(lab_dir, id_list)
    _file_ids = get_file_ids(wav_dir, id_list)

    if file_ids != _file_ids:
        raise ValueError("Please provide id_list, or ensure that wav_dir and lab_dir contain the same files.")

    for file_id in file_ids:
        lab_path = os.path.join(lab_dir, '{}.lab'.format(file_id))
        label = label_io.Label(lab_path, state_level)

        wav_path = os.path.join(wav_dir, '{}.wav'.format(file_id))
        wav = feature_io.Wav(wav_path)

        binary_label = label.binarise('')
        duration = label.count_frames()
        f0, mgc, bap = wav.extract_features()

        features = {
            'lab': binary_label,
            'duration': duration,
            'f0': f0,
            'mgc': mgc,
            'bap': bap
        }

        feature_path = os.path.join(out_dir, '{}.proto'.format(file_id))
        file_io.save_proto(features, feature_path)


def process_lab_files(lab_dir, id_list, out_dir, state_level):
    """Processes label files in id_list, saves the binarised labels and durations.

    Args:
        lab_dir (str): Directory containing the label files.
        id_list (str): List of file basenames to process.
        out_dir (str): Directory to save the output to.
        state_level (bool): Indicates that the label files are state level if True, otherwise they are frame level.
        """
    file_ids = get_file_ids(lab_dir, id_list)

    for file_id in file_ids:
        lab_path = os.path.join(lab_dir, '{}.lab'.format(file_id))
        label = label_io.Label(lab_path, state_level)

        duration = label.count_frames()
        duration_path = os.path.join(out_dir, '{}.dur'.format(file_id))
        file_io.save_txt(duration, duration_path)

        binary_label = label.binarise('')
        binary_label_path = os.path.join(out_dir, '{}.lab'.format(file_id))
        file_io.save_bin(binary_label, binary_label_path)


def process_wav_files(wav_dir, id_list, out_dir):
    """Processes wave files in id_list, saves the vocoder features to binary numpy files.

    Args:
        wav_dir (str): Directory containing the wave files.
        id_list (str): List of file basenames to process.
        out_dir (str): Directory to save the output to.
        """
    file_ids = get_file_ids(wav_dir, id_list)

    for file_id in file_ids:
        wav_path = os.path.join(wav_dir, '{}.wav'.format(file_id))
        wav = feature_io.Wav(wav_path)

        f0, mgc, bap = wav.extract_features()

        feature_path = os.path.join(out_dir, file_id)
        file_io.save_bin(f0, '{}.f0'.format(feature_path))
        file_io.save_bin(mgc, '{}.mgc'.format(feature_path))
        file_io.save_bin(bap, '{}.bap'.format(feature_path))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to extract duration information from forced alignment label files.")
    add_arguments(parser)
    args = parser.parse_args()

    if args.lab_dir and args.wav_dir:
        process_files(args.lab_dir, args.wav_dir, args.id_list, args.out_dir, args.state_level)

    elif args.lab_dir:
        process_lab_files(args.lab_dir, args.id_list, args.out_dir, args.state_level)

    elif args.wav_dir:
        process_wav_files(args.wav_dir, args.id_list, args.out_dir)

