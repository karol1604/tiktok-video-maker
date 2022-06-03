from email.mime import audio
from operator import le
from random import randrange
from turtle import clear, width
import praw
from gtts import gTTS
from mutagen.mp3 import MP3
from playwright.sync_api import sync_playwright
from misc import *
import os
from moviepy.editor import (
  VideoFileClip,
  AudioFileClip,
  ImageClip,
  concatenate_videoclips,
  concatenate_audioclips,
  CompositeVideoClip,
  CompositeAudioClip
)

clear_dir('./assets/audio')
clear_dir('./assets/png')
if(os.path.exists("./assets/final_video.mp4")): os.remove("./assets/final_video.mp4")


reddit = praw.Reddit(
  client_id="aDDFsAo3uSsScUPBBLDLDw",
  client_secret="d1APNBtJRnEaqpd9tvLZajepH4YlpQ",
  user_agent="idk"
)

def get_random_thread(subreddit, limit):
  content = {}
  content["comments"] = []
  rand = randrange(0, limit)
  print(rand)
  thread = list(reddit.subreddit(subreddit).hot(limit=limit))[rand]
  content["thread_title"] = thread.title
  content["thread_url"] = thread.url
  content["thread_id"] = thread
  submission = reddit.submission(thread)
  for i in range(0, 5):
    content["comments"].append({
      "comment_body": submission.comments[i].body,
      "comment_url": submission.comments[i].permalink,
      "comment_id": submission.comments[i]
    })
  
  return content

SUBREDDIT = "AskReddit"

my_thread = get_random_thread(SUBREDDIT, 50)
comments = my_thread["comments"]
tts = gTTS(my_thread["thread_title"])
tts.save(f"assets/audio/title.mp3")
audio_length = MP3(f"assets/audio/title.mp3").info.length

for i in range(0, len(comments)):
  if audio_length > 60: break
  tts = gTTS(comments[i]["comment_body"])
  tts.save(f"assets/audio/{i}.mp3")
  audio_length += MP3(f"assets/audio/{i}.mp3").info.length

print(audio_length)
print(my_thread["thread_url"])


with sync_playwright() as p:
    browser = p.chromium.launch()

    page = browser.new_page()
    page.goto(my_thread["thread_url"])
    print(page.title())
    page.locator('[data-test-id="post-content"]').screenshot(path="assets/png/title.png")

    for i in range(0, len(my_thread["comments"])):
      comment_id = my_thread["comments"][i]["comment_id"]
      print(comment_id)
      comment_url = my_thread["comments"][i]["comment_url"]
      if page.locator('[data-testid="content-gate"]').is_visible():
        page.locator('[data-testid="content-gate"] button').click()
      page.goto(f"https://www.reddit.com{comment_url}")
      page.locator(f"#t1_{comment_id}").screenshot(path=f"assets/png/comment-{i}.png")

    browser.close()

W, H = 1080, 1920

VideoFileClip.reW = lambda clip: clip.resize(width=W)
VideoFileClip.reH = lambda clip: clip.resize(width=H)

background_clip = (
        VideoFileClip("assets/mp4/clip.mp4").set_duration(audio_length + 0.5)
        .without_audio()
        .resize(height=H)
        .crop(x1=1166.6, y1=0, x2=2246.6, y2=1920)
)

audio_clips = []
for i in range(0, len(my_thread["comments"])):
  audio_clips.append(AudioFileClip(f"assets/audio/{i}.mp3"))
audio_clips.insert(0, AudioFileClip("assets/audio/title.mp3"))
audio_concat = concatenate_audioclips(audio_clips)
audio_composite = CompositeAudioClip([audio_concat])

image_clips = []
for i in range(0, len(my_thread["comments"])):
    image_clips.append(
        ImageClip(f"assets/png/comment-{i}.png")
        .set_duration(audio_clips[i + 1].duration)
        .set_position("center")
        .resize(width=W - 100),
    )
image_clips.insert(
    0,
    ImageClip(f"assets/png/title.png")
    .set_duration(audio_clips[0].duration)
    .set_position("center")
    .resize(width=W - 100),
)
image_concat = concatenate_videoclips(image_clips).set_position(
    ("center", "center")
)
image_concat.audio = audio_composite
# final = CompositeVideoClip([background_clip, image_concat])
final = CompositeVideoClip([background_clip, image_concat])
final.write_videofile(
    "assets/final_video.mp4", fps=30, audio_codec="aac", audio_bitrate="192k"
)