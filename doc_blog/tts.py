import io
import azure.cognitiveservices.speech as speechsdk

import bs4
import re
import os
import time
import boto3
from botocore.exceptions import ClientError
from flask import current_app, url_for
import os

def get_s3client():
    url = os.getenv("URL")
    aws_access_key_id = os.getenv("ACCESS_KEY_ID")
    print(aws_access_key_id)
    aws_secret_access_key = os.getenv("ACCESS_KEY_SECRET")
    print(aws_secret_access_key)
    s3 = boto3.client('s3',
      endpoint_url = url,
      aws_access_key_id = aws_access_key_id,
      aws_secret_access_key = aws_secret_access_key
    )
    return s3

def pollytext(content, voice):
    text = str(f"<p> {content} </p>")
    text = re.sub('\n+', r'</p>\n<p>', text)
    text = re.sub(u'\xa0', u' ', text)
    text = re.sub(u'&', u'and', text)

    output = re.sub(u'[\u201c\u201d]', '"', text)
    print(len(output))
    sep = '.'
    rest = output

    #remove references
    #Because single invocation of the polly synthesize_speech api can
    # transform text with about 1,500 characters, we are dividing the
    # post into blocks of approximately 1,000 characters.
    textBlocks = []
    while (len(rest) > 5000):
        begin = 0
        end = rest.rfind("</p>", 0, 5000) #rfind looks for the last case of the search term.

        if (end == -1):
            end = rest.rfind(". ", 0, 5000)
            textBlock = rest[begin:end+1]
            rest = rest[end+1:]
            textBlocks.append('''<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">
                     <voice name="'''+ voice + '''">
                         <prosody rate="0%" pitch="0%"><mstts:express-as style="hopeful"">''' + textBlock + "</mstts:express-as></p></prosody></voice></speak>")
            rest = "<p>" + rest

        else:
            textBlock = rest[begin:end+4]
            rest = rest[end+4:] #Remove the annoying "Dot" that otherwise starts each new block since you no longer start on that index.
            textBlocks.append('''<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">
                     <voice name="''' + voice + '''">
                         <prosody rate="0%" pitch="0%"><mstts:express-as style="hopeful">''' + textBlock + "</mstts:express-as></prosody></voice></speak>")
    textBlocks.append('''<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">
                     <voice name="''' + voice + '''">
                         <prosody rate="0%" pitch="0%"><mstts:express-as style="hopeful">''' + rest + '</mstts:express-as></prosody></voice></speak>')
    with open("instance/output.txt", "w") as text:
        # Write the response to the output file.
        text.write(str(textBlocks))
    return textBlocks

# Get text from the console and synthesize to the default speaker.


def synthesize_ssml(speech_client, ssml, voice):
    text_blocks = pollytext(ssml, voice)
    audio_data_list = []
    for text_block in text_blocks:
        result = speech_client.speak_ssml_async(text_block).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(text_block)
            print("Speech synthesized for text")
            audio_data_list.append(result.audio_data)
            time.sleep(2)
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                 if cancellation_details.error_details:
                       print("Error details: {}".format(cancellation_details.error_details))
                       print("Did you set the speech resource key and region values?")
            break
    return b"".join(audio_data_list)

def create_mp3(speech_client, ch_content, voice, mp3_name):
    audio = synthesize_ssml(speech_client, ch_content, voice)
    #file_save = current_app.instance_path, 'files', mp3_name
    s3 = get_s3client()
    bucket = 'archive'
    audiofile = io.BytesIO(audio)
    audio_size = audiofile.getbuffer().nbytes
    s3.upload_fileobj(audiofile, bucket, mp3_name)
    #debug code
    # with open(os.path.join(current_app.static_folder, mp3_name), "wb") as out:
    #  # Write the response to the output file.
    #      out.write(audio)
    return (mp3_name, audio_size)
