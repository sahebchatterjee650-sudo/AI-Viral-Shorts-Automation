
import os
import re
import html
import asyncio
import subprocess
import textwrap
import time
from pathlib import Path

import feedparser
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from google import genai

# =====================================================
# AI VIRAL SHORTS AUTOMATION
# =====================================================

MODEL = "gemini-3.8-flash"
VOICE = "en-US-AndrewNeural"

WIDTH = 1080
HEIGHT = 1920
FPS = 30

OUTPUT_DIR = Path("output_videos")
OUTPUT_DIR.mkdir(exist_ok=True)

SCRIPT_FILE = OUTPUT_DIR / "script.txt"
VIDEO_FILE = OUTPUT_DIR / "viral_short.mp4"
AUDIO_FILE = OUTPUT_DIR / "voice.mp3"
BACKGROUND_FILE = OUTPUT_DIR / "background.png"
CAPTION_FILE = OUTPUT_DIR / "captions.srt"

RSS_FEEDS = [
    "https://www.sciencedaily.com/rss/top/science.xml",
    "https://www.nasa.gov/feed/",
    "https://www.livescience.com/feeds/all",
    "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
]

MAX_STORIES_TO_CHECK = 12


# =====================================================
# LOGGING
# =====================================================

def log(message):
    print(f"[AI SHORTS] {message}", flush=True)


# =====================================================
# API CONFIGURATION
# =====================================================

def get_client():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing from GitHub Secrets."
        )

    return genai.Client(api_key=api_key)


# =====================================================
# RSS NEWS AND TOPIC COLLECTION
# =====================================================

def clean_text(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def collect_topics():
    stories = []
    seen = set()

    for rss_url in RSS_FEEDS:
        try:
            log(f"Checking RSS: {rss_url}")

            feed = feedparser.parse(
                rss_url,
                request_headers={
                    "User-Agent": "AI-Viral-Shorts/1.0"
                }
            )

            for entry in feed.entries:
                title = clean_text(entry.get("title"))
                summary = clean_text(
                    entry.get("summary")
                    or entry.get("description")
                )
                link = entry.get("link", "").strip()

                if not title or not summary or not link:
                    continue

                if link in seen:
                    continue

                if len(summary) < 80:
                    continue

                seen.add(link)

                stories.append({
                    "title": title,
                    "summary": summary,
                    "link": link
                })

        except Exception as error:
            log(f"RSS warning: {str(error)[:200]}")
            continue

    log(f"Collected {len(stories)} possible topics.")

    return stories[:MAX_STORIES_TO_CHECK]


# =====================================================
# AI SCRIPT GENERATION
# =====================================================

def generate_script(client, story):

    prompt = f"""
You are an expert short-form video storyteller.

Create an engaging 30-60 second YouTube Short
for an American English-speaking audience.

TOPIC:
{story['title']}

SOURCE INFORMATION:
{story['summary']}

SOURCE:
{story['link']}

STRICT REQUIREMENTS:

1. Write approximately 85-110 spoken words.
2. Start with an extremely interesting curiosity hook.
3. Make the first 2 seconds attention-grabbing.
4. Use simple, natural American English.
5. Use short sentences.
6. Make the story exciting but factual.
7. Use only information supported by the source.
8. Never invent statistics, quotes or facts.
9. Do not present speculation as established fact.
10. End with an interesting question.
11. No headings, no scene directions.
12. Return narration only.

If the source information is insufficient,
return exactly SKIP_STORY.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    script = (response.text or "").strip()

    script = re.sub(
        r"^```(?:text)?|```$",
        "",
        script,
        flags=re.MULTILINE
    ).strip()

    if not script:
        return None

    if "SKIP_STORY" in script.upper():
        return None

    word_count = len(script.split())

    if word_count < 65 or word_count > 130:
        log(f"Invalid script length: {word_count} words.")
        return None

    return script


# =====================================================
# FONT MANAGEMENT
# =====================================================

def get_font(size, bold=False):

    if bold:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
        ]
    else:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"
        ]

    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


# =====================================================
# TEXT WRAPPING
# =====================================================

def wrap_text(draw, text, font, max_width):

    words = text.split()
    lines = []
    current = ""

    for word in words:

        test = (current + " " + word).strip()

        width = draw.textbbox(
            (0, 0),
            test,
            font=font
        )[2]

        if width <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


# =====================================================
# CINEMATIC BACKGROUND DESIGN
# =====================================================

def create_background(title):

    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        (4, 10, 30)
    )

    draw = ImageDraw.Draw(image)

    # Vertical cinematic gradient
    for y in range(HEIGHT):

        ratio = y / HEIGHT

        color = (
            int(5 + ratio * 8),
            int(12 + ratio * 15),
            int(35 + ratio * 65)
        )

        draw.line(
            (0, y, WIDTH, y),
            fill=color
        )

    # Decorative geometric rings
    for radius in range(170, 850, 130):

        draw.ellipse(
            (
                WIDTH // 2 - radius,
                650 - radius,
                WIDTH // 2 + radius,
                650 + radius
            ),
            outline=(22, 55, 100),
            width=3
        )

    # Header
    draw.rounded_rectangle(
        (45, 65, 1035, 245),
        radius=30,
        fill=(135, 20, 45)
    )

    draw.text(
        (85, 112),
        "AMAZING FACTS",
        font=get_font(62, True),
        fill="white"
    )

    draw.text(
        (88, 190),
        "DISCOVER SOMETHING NEW",
        font=get_font(26, True),
        fill=(255, 215, 110)
    )

    # Central title
    draw.rounded_rectangle(
        (45, 350, 1035, 1310),
        radius=35,
        fill=(8, 24, 55),
        outline=(35, 115, 190),
        width=4
    )

    draw.text(
        (85, 415),
        "DID YOU KNOW?",
        font=get_font(44, True),
        fill=(60, 210, 255)
    )

    title_font = get_font(65, True)

    lines = wrap_text(
        draw,
        title.upper(),
        title_font,
        850
    )

    y = 565

    for line in lines[:8]:

        draw.text(
            (85, y),
            line,
            font=title_font,
            fill="white",
            stroke_width=2,
            stroke_fill=(0, 0, 0)
        )

        y += 95

    # Bottom CTA
    draw.rounded_rectangle(
        (65, 1690, 1015, 1820),
        radius=30,
        fill=(175, 25, 48)
    )

    draw.text(
        (WIDTH // 2, 1730),
        "FOLLOW FOR MORE",
        font=get_font(48, True),
        fill="white",
        anchor="mm"
    )

    draw.text(
        (WIDTH // 2, 1790),
        "AMAZING FACTS • SCIENCE • MYSTERY",
        font=get_font(23, True),
        fill=(255, 220, 125),
        anchor="mm"
    )

    image.save(BACKGROUND_FILE)

    return BACKGROUND_FILE


# =====================================================
# AI VOICE GENERATION
# =====================================================

async def generate_voice(script):

    communicator = edge_tts.Communicate(
        script,
        VOICE,
        rate="+3%",
        volume="+0%"
    )

    await communicator.save(str(AUDIO_FILE))

    if not AUDIO_FILE.exists():
        raise RuntimeError("Voice generation failed.")

    if AUDIO_FILE.stat().st_size < 1000:
        raise RuntimeError("Generated audio is too small.")

    log("AI voice generated successfully.")

    return AUDIO_FILE


# =====================================================
# AUDIO DURATION
# =====================================================

def get_audio_duration():

    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(AUDIO_FILE)
        ],
        capture_output=True,
        text=True,
        check=True
    )

    return float(result.stdout.strip())


# =====================================================
# ANIMATED STYLE SUBTITLES
# =====================================================

def make_timestamp(seconds):

    milliseconds = max(
        0,
        int(seconds * 1000)
    )

    hours, milliseconds = divmod(
        milliseconds, 3600000
    )

    minutes, milliseconds = divmod(
        milliseconds, 60000
    )

    secs, milliseconds = divmod(
        milliseconds, 1000
    )

    return (
        f"{hours:02}:"
        f"{minutes:02}:"
        f"{secs:02},"
        f"{milliseconds:03}"
    )


def create_captions(script, duration):

    words = script.split()

    chunks = [
        words[i:i + 4]
        for i in range(0, len(words), 4)
    ]

    total_words = sum(len(chunk) for chunk in chunks)

    current_time = 0.0

    with open(
        CAPTION_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        for index, chunk in enumerate(chunks):

            chunk_duration = (
                duration * len(chunk) / total_words
            )

            start = current_time
            end = current_time + chunk_duration

            file.write(
                f"{index + 1}\n"
                f"{make_timestamp(start)} --> "
                f"{make_timestamp(end)}\n"
                f"{' '.join(chunk)}\n\n"
            )

            current_time = end

    log("Captions generated successfully.")

    return CAPTION_FILE


# =====================================================
# VIDEO CREATION
# =====================================================

def create_video(title, script):

    log("Creating cinematic background...")

    create_background(title)

    log("Generating voice...")

    asyncio.run(generate_voice(script))

    duration = get_audio_duration()

    log(f"Audio duration: {duration:.2f} seconds")

    if duration < 20 or duration > 60:
        raise RuntimeError(
            f"Video duration outside 20-60 seconds: "
            f"{duration:.2f}"
        )

    create_captions(script, duration)

    # Escape file path for FFmpeg
    subtitle_path = CAPTION_FILE.resolve().as_posix()

    subtitle_filter = (
        f"subtitles=filename='{subtitle_path}':"
        "force_style='"
        "FontName=DejaVu Sans,"
        "FontSize=25,"
        "Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "Outline=3,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=380"
        "'"
    )

    video_filter = (
        "zoompan="
        "z='min(zoom+0.00035,1.06)':"
        "d=1:"
        "s=1080x1920:"
        "fps=30,"
        + subtitle_filter
    )

    command = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-framerate", "30",
        "-i", str(BACKGROUND_FILE),
        "-i", str(AUDIO_FILE),
        "-vf", video_filter,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "128k",
        "-t", str(duration),
        "-shortest",
        "-movflags", "+faststart",
        "-metadata", f"title={title}",
        str(VIDEO_FILE)
    ]

    log("Rendering MP4 video...")

    subprocess.run(
        command,
        check=True,
        timeout=300
    )

    if not VIDEO_FILE.exists():
        raise RuntimeError("MP4 file was not created.")

    if VIDEO_FILE.stat().st_size < 10000:
        raise RuntimeError("MP4 file is incomplete.")

    log("VIDEO CREATED SUCCESSFULLY!")
    log(f"Video: {VIDEO_FILE}")
    log(f"Duration: {duration:.2f} seconds")


# =====================================================
# MAIN AUTOMATION
# =====================================================

def main():

    log("====================================")
    log("AI VIRAL SHORTS AUTOMATION STARTED")
    log("====================================")

    if not shutil_which("ffmpeg"):
        raise RuntimeError("FFmpeg is missing.")

    if not shutil_which("ffprobe"):
        raise RuntimeError("FFprobe is missing.")

    client = get_client()

    stories = collect_topics()

    if not stories:
        raise RuntimeError("No usable RSS topics found.")

    video_created = False

    for index, story in enumerate(stories, start=1):

        log(f"Checking story {index}: {story['title']}")

        try:

            script = generate_script(
                client,
                story
            )

            if not script:
                log("Story skipped by quality check.")
                continue

            with open(
                SCRIPT_FILE,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(
                    f"TITLE: {story['title']}\n\n"
                    f"{script}\n\n"
                    f"SOURCE: {story['link']}\n"
                )

            log("AI script created.")

            create_video(
                story["title"],
                script
            )

            video_created = True
            break

        except Exception as error:

            log(
                f"Story processing failed: "
                f"{str(error)[:400]}"
            )

            continue

    if not video_created:
        raise RuntimeError(
            "No video could be created from available stories."
        )

    log("====================================")
    log("AUTOMATION COMPLETED SUCCESSFULLY")
    log("====================================")


# =====================================================
# UTILITY
# =====================================================

def shutil_which(command):

    from shutil import which

    return which(command) is not None


if __name__ == "__main__":

    try:
        main()

    except Exception as error:

        log("FATAL ERROR: " + str(error))

        raise
