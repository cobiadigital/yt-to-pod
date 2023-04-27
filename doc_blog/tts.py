import io
import azure.cognitiveservices.speech as speechsdk

import bs4
import re
import os
import time
import boto3
import json
from botocore.exceptions import ClientError
from flask import current_app, url_for

def get_keys(path):
        with open(path) as f:
            return json.load(f)
def get_s3client():
    keys = get_keys(".secret/.s3.json")
    url = keys['url']
    bucket = keys['bucket']
    aws_access_key_id = keys['access_key_id']
    aws_secret_access_key = keys['access_key_secret']
    s3 = boto3.client('s3',
      endpoint_url = url,
      aws_access_key_id = aws_access_key_id,
      aws_secret_access_key = aws_secret_access_key
    )
    return s3

def pollytext(body, voice):
    soup = bs4.BeautifulSoup(body, "html.parser")

    hr_tags = soup("hr")
    for epub_h1_tag in soup.find_all("p", class_=re.compile(r"H\d")):
        epub_h1_tag.attrs = {}
        epub_h1_tag.insert_after(hr_tag)

    # remove footnote numbers
    for sup_tag in soup.find_all("sup"):
        sup_tag.decompose()

    for sup_tag in soup.find_all('span', attrs={'class':"superscript"}):
        sup_tag.decompose()

    #Adding pause after headings and lists
    for header_tags in soup.find_all(["h1", "h2", "h3", "h4", "li"]):
        hr_tag = soup.new_tag('hr')
        header_tags.name = "p"
        header_tags.insert_before(hr_tag)
        header_tags.insert_after(hr_tag)

    for hr_tag in hr_tags:
        hr_tag.name = "break"

    for epub_i_tag in soup.find_all('span', attrs={'class':"ePub-I"}):
        epub_i_tag.attrs = {}
        epub_i_tag.name = "emphasis"
        epub_i_tag['level'] = "moderate"

    for epub_i_tag in soup.find_all('span', attrs={'class':"italic"}):
        epub_i_tag.attrs = {}
        epub_i_tag.name = "emphasis"
        epub_i_tag['level'] = "moderate"

    emphasis = soup(["em","i"])
    for emph in emphasis:
        emph.name = "emphasis"
        emph['level'] = "strong"

    text = ""

    for accepted_tag in soup(["p", "break"]):
        text += str(accepted_tag)
    #fix line-break hyphens
    text = re.sub('- \n', '', text)
    text = re.sub('\n', '', text)
    #remove http addresses
    text = re.sub(r'https*? ', '', text)
#     remove page numbers
    text = re.sub(u'\xa0', u' ', text)
    output = re.sub(u'[\u201c\u201d]', '"', text)
    print(len(output))
    sep = '.'
    rest = output

    #remove references
    end = rest.rfind('<p>Reference')
    if (end != -1):

        rest = rest[0:end]
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
                         <prosody rate="0%" pitch="0%">''' + textBlock + "</p></prosody></voice></speak>")
            rest = "<p>" + rest

        else:
            textBlock = rest[begin:end+4]
            rest = rest[end+4:] #Remove the annoying "Dot" that otherwise starts each new block since you no longer start on that index.
            textBlocks.append('''<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">
                     <voice name="''' + voice + '''">
                         <prosody rate="0%" pitch="0%">''' + textBlock + "</prosody></voice></speak>")
    textBlocks.append('''<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">
                     <voice name="''' + voice + '''">
                         <prosody rate="0%" pitch="0%">''' + rest + '</prosody></voice></speak>')
    with open("instance/output.txt", "w") as text:
        # Write the response to the output file.
        text.write(str(textBlocks))
    return textBlocks

# Get text from the console and synthesize to the default speaker.


def synthesize_ssml(speech_client, ssml, voice):
    textBlocks = pollytext(ssml, voice)
    audio_data_list = []
    for textBlock in textBlocks:
        result = speech_client.speak_ssml_async(textBlock).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(textBlock)
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
    bucket = 'docs-pod'
    audiofile = io.BytesIO(audio)
    audio_size = audiofile.getbuffer().nbytes
    s3.upload_fileobj(audiofile, bucket, mp3_name)
    #debug code
    # with open(os.path.join(current_app.static_folder, mp3_name), "wb") as out:
    #  # Write the response to the output file.
    #     out.write(audio)
    return (mp3_name, audio_size)
