import azure.cognitiveservices.speech as speechsdk
import bs4
import re
import os
import time


def pollytext(content, voice):

    soup = bs4.BeautifulSoup(content, "html")
    hr_tags = soup("hr")
    for hr_tag in hr_tags:
        hr_tag.name = "break"

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
                         <prosody rate="0%" pitch="0%">''' + rest + '<break time="3s"/></prosody></voice></speak>')
    with open("instance/output.txt", "w") as text:
        # Write the response to the output file.
        text.write(str(textBlocks))
    return textBlocks

# Get text from the console and synthesize to the default speaker.


def synthesize_ssml(speech_config, response, voice):
    textBlocks = pollytext(response, voice)
    audio_data_list = []
    for textBlock in textBlocks:
        result = speach_client.speak_ssml_async(textBlock).get()
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

def create_mp3(id, slug, body, voice, client):
    audio_content = synthesize_ssml(speech_config, body, voice, client)
    mp3_name = "instance/" + str(id) + "_" + slug + ".mp3"
    with open(mp3_name, "wb") as out:
    # Write the response to the output file.
        out.write(audio_content)
        print('Audio content written to file' + mp3_name)
    return mp3_name

