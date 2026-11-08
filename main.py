
import os
import re
import asyncio
import subprocess
import textwrap
from pathlib import Path
from io import BytesIO

import feedparser
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from google import genai

# ==========================================
# AI VIRAL SHORTS AUTOMATION
# ==========================================

MODEL = "gemini-2.5-flash"
VOICE = "en-US-AndrewNeural"

WIDTH = 1080
HEIGHT = 1920

OUTPUT = Path("output_videos")
OUTPUT.mkdir(exist_ok=True)

RSS_FEEDS = [
    "https://www.sciencedaily.com/rss/top/science.xml",
    "https://www.nasa.gov/feed/",
    "https://www.livescience.com/feeds/all"
]


def get_font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]

    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


def get_topic():
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)

            if feed.entries:
                for entry in feed.entries:
                    title = entry.get("title", "").strip()
                    summary = entry.get("summary", "").strip()
                    link = entry.get("link", "").strip()

                    if title and summary and link:
                        return title, summary, link

        except Exception as error:
            print("RSS warning:", error)

    raise RuntimeError("No usable RSS story found.")


def generate_script(title, summary, link):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
Create an engaging YouTube Short script for a USA audience.

TOPIC: {title}
SOURCE SUMMARY: {summary}
SOURCE URL: {link}

Rules:
- English language.
- 100 to 120 words.
- Strong curiosity hook in the first sentence.
- Interesting storytelling.
- Short, natural spoken sentences.
- End with a memorable question.
- Use only facts supported by the source.
- Do not invent facts or quotes.
- No headings, labels or hashtags.
- Return only the narration script.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    script = (response.text or "").strip()

    if len(script.split()) < 65:
        raise RuntimeError("AI generated an incomplete script.")

    return script


def create_background(title):
    image = Image.new("RGB", (WIDTH, HEIGHT))
    pixels = image.load()

    for y in range(HEIGHT):
        for x in range(WIDTH):
            ratio = y / HEIGHT
            pixels[x, y] = (
                int(5 + ratio * 12),
                int(12 + ratio * 15),
                int(35 + ratio * 65)
            )

    draw = ImageDraw.Draw(image)

    # Decorative cinematic rings
    for radius in range(150, 850, 130):
        draw.ellipse(
            (
                WIDTH // 2 - radius,
                650 - radius,
                WIDTH // 2 + radius,
                650 + radius
            ),
            outline=(25, 65, 115),
            width=3
        )

    draw.rounded_rectangle(
        (55, 120, 1025, 270),
        radius=30,
        fill=(160, 25, 45)
    )

    draw.text(
        (95, 165),
        "DID YOU KNOW?",
        font=get_font(65, True),
        fill="white"
    )

    draw.text(
        (75, 900),
        "AMAZING FACTS",
        font=get_font(43, True),
        fill=(50, 210, 255)
    )

    font = get_font(66, True)
    words = title.split()
    lines = textwrap.wrap(" ".join(words), width=23)

    y = 1010

    for line in lines[:5]:
        draw.text(
            (75, y),
            line,
            font=font,
            fill="white",
            stroke_width=2,
            stroke_fill=(0, 0, 0)
        )
        y += 100

    draw.text(
        (75, 1750),
        "FOLLOW FOR MORE",
        font=get_font(43, True),
        fill=(255, 205, 65)
    )

    path = OUTPUT / "background.png"
    image.save(path)
    return path


async def create_voice(script):
    path = OUTPUT / "voice.mp3"

    tts = edge_tts.Communicate(
        script,
        VOICE,
        rate="+5%"
    )

    await tts.save(str(path))
    return path


def create_captions(script, duration):
    words = script.split()
    chunks = [
        words[i:i + 4]
        for i in range(0, len(words), 4)
    ]

    path = OUTPUT / "captions.srt"

    def stamp(seconds):
        ms = int(seconds * 1000)
        hours, ms = divmod(ms, 3600000)
        minutes, ms = divmod(ms, 60000)
        secs, ms = divmod(ms, 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"

    with open(path, "w", encoding="utf-8") as file:
        for i, chunk in enumerate(chunks):
            start = duration * i / len(chunks)
            end = duration * (i + 1) / len(chunks)

            file.write(
                f"{i+1}\n"
                f"{stamp(start)} --> {stamp(end)}\n"
                f"{' '.join(chunk)}\n\n"
            )

    return path


def make_video(title, script):
    background = create_background(title)

    audio = asyncio.run(create_voice(script))

    probe = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio)
        ],
        capture_output=True,
        text=True,
        check=True
    )

    duration = float(probe.stdout.strip())

    if not 20 <= duration <= 60:
        raise RuntimeError(
            f"Video duration is {duration:.1f}s; "
            "expected 20–60 seconds."
        )

    captions = create_captions(script, duration)

    video = OUTPUT / "viral_short.mp4"

    subtitle_filter = (
        f"subtitles=filename='{captions.as_posix()}':"
        "force_style='FontName=DejaVu Sans,"
        "FontSize=24,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,Outline=3,"
        "Bold=1,Alignment=2,MarginV=400'"
    )

    video_filter = (
        "zoompan=z='min(zoom+0.0004,1.08)':"
        "d=1:s=1080x1920:fps=30,"
        + subtitle_filter
    )

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-loop", "1",
            "-framerate", "30",
            "-i", str(background),
            "-i", str(audio),
            "-vf", video_filter,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-t", str(duration),
            "-shortest",
            "-movflags", "+faststart",
            str(video)
        ],
        check=True,
        timeout=300
    )

    print("VIDEO CREATED:", video)


def main():
    print("AI VIRAL SHORTS AUTOMATION STARTED")

    title, summary, link = get_topic()

    print("SELECTED TOPIC:", title)
    print("SOURCE:", link)

    script = generate_script(title, summary, link)

    with open(
        OUTPUT / "script.txt",
        "w",
        encoding="utf-8"
    ) as file:
        file.write(
            f"{title}\n\n{script}\n\nSource: {link}"
        )

    print("SCRIPT GENERATED")

    make_video(title, script)

    print("VIDEO GENERATION COMPLETED")


if __name__ == "__main__":
    main()
