#!/usr/bin/env python3

from pocketsphinx import Endpointer, Decoder, set_loglevel
import argparse
import logging
import os
import paho.mqtt.client as mqtt
import sounddevice
import sys

cli = argparse.ArgumentParser(
        prog='SkeletonAudioCapture',
        description='Records streaming audio from the microphone and publishes mqtt messages as utterances are detected')
subparsers = cli.add_subparsers(dest="subcommand")

# some plumbing so we can create a clean CLI interface
# taken mostly from https://mike.depalatis.net/blog/simplifying-argparse.html
def argument(*name_or_flags, **kwargs):
    return ([*name_or_flags], kwargs)
def subcommand(args=[], parent=subparsers):
    def decorator(func):
        parser = parent.add_parser(func.__name__, description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)
    return decorator

#############################################
# listen will listen on the audio device and 
# emit events as phrases are detected
# largely adapted from https://pocketsphinx.readthedocs.io/en/latest/_modules/pocketsphinx.html
#############################################
@subcommand([
    argument("--sample-rate", "-r", help="The sample rate for the streaming audio", type=int, default=os.environ.get("SAMPLE_RATE", 16000)),
    argument("--mqtt-port", "-p", help="The port for MQTT connections", type=int, default=os.environ.get("MQTT_PORT", 1883)),
    argument("--mqtt-host", help="The hostname for establishing an MQTT connection", type=str, default=os.environ.get("MQTT_HOST", "localhost")),
    argument("--mqtt-topic", help="The topic name to use when publishing captured phrases", type=str, default=os.environ.get("MQTT_TOPIC", "audio/capture/utterance")),
    argument("--log-level", help="The log level to use", type=str, default=os.environ.get("LOG_LEVEL", "WARN")),
])
def listen(args=[], parent=subparsers):
    # process the args
    sampleRate = args.sample_rate
    logLevel = args.log_level
    mqttHost = args.mqtt_host
    mqttPort = args.mqtt_port
    mqttTopic = args.mqtt_topic
    set_loglevel(logLevel)
    logging.basicConfig(handlers=[logging.StreamHandler(sys.stdout)], level=logLevel)
    logging.debug("sample rate: %d" % sampleRate)

    logging.debug("preparing mqtt client (%s:%d)" % (mqttHost, mqttPort))
    client = mqtt.Client()
    client.enable_logger(logging.getLogger())
    client.connect(mqttHost, mqttPort, 60)
    client.loop_start()

    ep = Endpointer()
    bufferSize = ep.frame_bytes
    decoder = Decoder(
        samprate=sampleRate,
    )
    ad = sounddevice.RawInputStream(
        samplerate=sampleRate,
        blocksize=bufferSize // 2,
        dtype="int16",
        channels=1,
    )
    with ad:
        while True:
            frame, _ = ad.read(bufferSize // 2)
            prev_in_speech = ep.in_speech
            speech = ep.process(frame)
            if speech is not None:
                if not prev_in_speech:
                    logging.debug("Speech start at %.2f" % (ep.speech_start))
                    decoder.start_utt()
                decoder.process_raw(speech)
                hyp = decoder.hyp()
                if hyp is not None:
                    logging.debug("PARTIAL RESULT: %s" % hyp.hypstr)
                if not ep.in_speech:
                    logging.debug("Speech end at %.2f" % (ep.speech_end))
                    decoder.end_utt()
                    result = decoder.hyp().hypstr
                    logging.info("Result: %s" % result)
                    client.publish(mqttTopic, result)

def main():
    args = cli.parse_args()
    if args.subcommand is None:
        cli.print_help()
    else:
        args.func(args)

main()
