import azure.cognitiveservices.speech as speechsdk
import json

def get_keys(path):
        with open(path) as f:
            return json.load(f)

def load_speech_client():
    keys = get_keys(".secret/azure.json")
    subscription_key = keys['subscription']
    service_region = keys['region']
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=service_region)

    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio24Khz96KBitRateMonoMp3)
    print('speech client loaded' + service_region)
    return(speechsdk.SpeechSynthesizer(speech_config=speech_config))

