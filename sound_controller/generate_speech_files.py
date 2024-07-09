import argparse
import asyncio
import logging
import os
import sys
import json
import soundfile as sf
import librosa

from core.config import HeadConfigs, SegmentLists
from google.cloud import texttospeech

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(asctime)s %(filename)s(%(lineno)d): %(message)s",
    datefmt="%H:%M:%S",
)

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--config", type=argparse.FileType('r'), default="sound_config.json",
                    help="Sound config file")
parser.add_argument("--force_update", action='store_true',
                    help="Forces update of existing speech files.")
parser.add_argument('--samplerate', type=int, default=48000, 
                    help='Desired audio file sample rate.')
parser.add_argument("--base_folder", default='media',
                    help="The base folder for sound files")
args = parser.parse_args()


def synthesize_text(text, output_filename, config):
    """Synthesizes speech from the input string of text."""
    
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=config.language_code,
        name=config.voice_name
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        speaking_rate=config.speaking_rate,
        pitch=config.pitch,
        volume_gain_db=config.volume_gain_db,
        sample_rate_hertz=args.samplerate
    )

    response = client.synthesize_speech(
        request={"input": input_text, "voice": voice,
                 "audio_config": audio_config}
    )

    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    with open(output_filename, "wb") as out:
        out.write(response.audio_content)
        logging.debug('Audio content written to file {output_filename}')


def maybe_resample_audio(filename):
    data, samplerate = sf.read(filename)
    if samplerate == args.samplerate:
        return

    new_data = librosa.resample(data, orig_sr=samplerate, target_sr=args.samplerate)
    sf.write(filename, new_data, args.samplerate)

def process_segment_list(head_configs, segment_lists):
    for segment_list_id, segment_list in segment_lists.lists.items():
        head_id = segment_list.head_id
        logging.info(f"Processing segment list {segment_list_id}")
        for i, segment in enumerate(segment_list.segments):
            if not segment.text:
                continue
            if segment.head_id:
                head_id = segment.head_id()

            assert head_id
            audio_config = head_configs.heads[head_id].audio_config
            text = segment.text
            filename = segment.filename()
            if os.path.exists(filename) and not args.force_update:
                logging.info(f"   Skipping {filename} because it already exists.")
                continue

            logging.info(f"   Generating {filename}")
            synthesize_text(text, filename, audio_config)
            maybe_resample_audio(filename)


async def main(** kwargs):
    config = json.load(args.config)
    head_configs = HeadConfigs(config["heads"])
    process_segment_list(head_configs,
                         SegmentLists(config["monologue_segments"], head_configs))
    process_segment_list(head_configs,
                         SegmentLists(config["dialogue_segments"], head_configs))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit('\nInterrupted by user')
