import azure.cognitiveservices.speech as speechsdk
import json
import os

def load_speech_client():
    subscription_key = os.getenv("SUBSCRIPTION")
    service_region = os.getenv("REGION")
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=service_region)

    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio48Khz96KBitRateMonoMp3)
    print('speech client loaded ' + service_region)
    return(speechsdk.SpeechSynthesizer(speech_config=speech_config))

