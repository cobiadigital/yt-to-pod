

def get_voices(speech_client):
    voices_result = speech_client.get_voices_async().get()
    voices_list = []
    locales = ['en-US', 'en-GB', 'en-AU', 'en-ZN', 'en-IE']
    for voice in voices_result.voices:
        for locale in locales:
            if voice.locale == locale:
                voices_list.append(tuple((voice.short_name, voice.short_name)))
    return(voices_list)


