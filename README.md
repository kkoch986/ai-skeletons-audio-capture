# Audio Capture

This is a module of my AI powered animatronics pipeline.
It's core responsibility is to capture audio input from a microphone
and transcribe it to utterances which can be used later on in the pipeline.

## Running the Listener

To run it, you can use the provided docker compose file but essentially it boils down
to running `./main.py listener`. This will kick off a process that will listen on the
microphone and emit messages to an MQTT server as it recognizes phrases.

The messages are currently just the raw text that was received.
Later I would like to structure it and also include the timestamps of the words
(which I think can be provided by the pocketsphinx output) in case its useful for
the output generation.
