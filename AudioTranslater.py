import os
from flask import Flask, render_template, request, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip

app = Flask(_name_)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'mp4'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def extract_speech(video_filename):
    # Function to extract speech from video
    video = VideoFileClip(video_filename)
    audio = video.audio
    audio.write_audiofile("extracted_audio.wav")


def transcribe_speech(audio_filename):
    # Function to transcribe speech to text
    recognizer = sr.Recognizer()
    audio_file = sr.AudioFile(audio_filename)

    with audio_file as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        print("Speech Recognition could not understand audio.")
        return ""
    except sr.RequestError as e:
        print(
            "Could not request results from Google Speech Recognition service; {0}".format(e))
        return ""


def translate_text(text, target_language='en'):
    # Function to translate text
    translator = Translator()
    translated_text = translator.translate(text, dest=target_language)
    return translated_text.text


def text_to_speech(text, lang='en', output_filename='translated_audio.mp3'):
    # Function to convert text to speech
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(output_filename)
    print("Translated text saved to '{}'".format(output_filename))
    return output_filename


def select_target_language():
    indian_languages = {
        'Assamese': 'as', 'Bengali': 'bn', 'Bodo': 'brx', 'Dogri': 'doi',
        'Gujarati': 'gu', 'Hindi': 'hi', 'Kannada': 'kn', 'Kashmiri': 'ks',
        'Konkani': 'kok', 'Maithili': 'mai', 'Malayalam': 'ml', 'Manipuri': 'mni',
        'Marathi': 'mr', 'Nepali': 'ne', 'Odia': 'or', 'Punjabi': 'pa',
        'Sanskrit': 'sa', 'Santali': 'sat', 'Sindhi': 'sd', 'Tamil': 'ta',
        'Telugu': 'te', 'Urdu': 'ur'
    }

    print("Select a target language for translation:")
    for idx, lang in enumerate(indian_languages.keys(), start=1):
        print(f"{idx}. {lang}")

    choice = input("Enter the number corresponding to your choice: ")

    try:
        choice_idx = int(choice)
        if 1 <= choice_idx <= len(indian_languages):
            return list(indian_languages.values())[choice_idx - 1]
        else:
            print("Invalid choice. Please try again.")
            return select_target_language()
    except ValueError:
        print("Invalid input. Please enter a number.")
        return select_target_language()


def main(video_filename):
    try:
        extract_speech(video_filename)
        output_audio_filename = 'translated_audio.mp3'

        extracted_text = transcribe_speech("extracted_audio.wav")
        target_language = select_target_language()

        translated_text = translate_text(extracted_text, target_language)
        print("Translated text in {}: {}".format(
            target_language, translated_text))

        translated_audio_filename = text_to_speech(
            translated_text, target_language, output_audio_filename)

        video = VideoFileClip(video_filename)
        translated_audio = AudioFileClip(translated_audio_filename)

        video = video.set_audio(translated_audio)
        output_video_filename = 'static/output_video.mp4'
        video.write_videofile(output_video_filename, fps=24)

        return output_video_filename

    except Exception as e:
        print("An error occurred during the translation and video creation:", str(e))


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'video' not in request.files:
            return redirect(request.url)

        video_file = request.files['video']

        if video_file.filename == '':
            return redirect(request.url)

        if video_file and allowed_file(video_file.filename):
            filename = secure_filename(video_file.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            video_file.save(video_path)

            translated_video_path = main(video_path)

            return redirect(url_for('result', video_path=translated_video_path))

    return render_template('index.html')


@app.route('/result')
def result():
    video_path = request.args.get('video_path')
    return render_template('result.html', video_path=video_path)


@app.route('/video/<filename>')
def video(filename):
    return send_file(f'static/{filename}')


if _name_ == '_main_':
    app.run(debug=True)
