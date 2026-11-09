
import os
import re
import json
import random
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from shutil import which

import edge_tts

# =========================================
# FREE AI VIRAL REALISTIC SHORTS AUTOMATION
# =========================================

OUTPUT = Path("output_videos")
FOOTAGE = Path("free_footage")

OUTPUT.mkdir(exist_ok=True)

VOICE = os.getenv("TTS_VOICE", "en-US-AndrewNeural")
DAILY_VIDEOS = 4
MAX_SECONDS = 45

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}

IDEAS = [
    {
        "category": "Wildlife",
        "tags": ["fox", "wildlife", "animal", "forest", "nature"],
        "title": "A Fox Discovers a Hidden Garden",
        "script": (
            "Deep inside a snowy forest, a curious red fox "
            "discovers something extraordinary. A beautiful "
            "little garden is hidden between the trees. "
            "Warm golden light shines through the glass as "
            "snowflakes fall silently. Sometimes the most "
            "beautiful discoveries happen when we least expect them."
        )
    },
    {
        "category": "Nature",
        "tags": ["nature", "flower", "rain", "garden", "plant"],
        "title": "The Beauty of Nature After Rain",
        "script": (
            "Have you ever stopped to admire nature after rain? "
            "Tiny water droplets shine like diamonds on every leaf. "
            "The morning sunlight slowly reaches the flowers, "
            "and the entire garden comes alive again. "
            "Sometimes happiness is hidden in the smallest moments."
        )
    },
    {
        "category": "Adventure",
        "tags": ["mountain", "train", "travel", "adventure", "bridge"],
        "title": "The Most Beautiful Train Journey",
        "script": (
            "Imagine travelling through breathtaking mountains "
            "while clouds float beneath your window. "
            "An old railway bridge connects two distant hills. "
            "Golden sunlight touches the landscape, creating "
            "a view you will never forget. "
            "Which destination would you choose?"
        )
    },
    {
        "category": "Satisfying",
        "tags": ["art", "craft", "glass", "satisfying", "making"],
        "title": "The Perfect Creative Transformation",
        "script": (
            "Watch closely as an ordinary material becomes "
            "something extraordinary. Every movement is careful, "
            "every detail matters, and the final result is "
            "incredibly satisfying. It is amazing what patience "
            "and creativity can achieve. "
            "Could you make something like this?"
        )
    },
    {
        "category": "Fantasy",
        "tags": ["ocean", "clouds", "sky", "water", "fantasy"],
        "title": "A World Above the Clouds",
        "script": (
            "What if the sky was hiding an incredible secret? "
            "Imagine floating above endless golden clouds, "
            "watching a magical world unfold beneath you. "
            "The sunlight creates a dreamlike atmosphere. "
            "This is an imaginary world, but just imagine "
            "if something like this really existed."
        )
    },
    {
        "category": "Food Art",
        "tags": ["food", "cooking", "dessert", "chef", "kitchen"],
        "title": "A Food Creation Worth Watching",
        "script": (
            "Some food creations are simply works of art. "
            "Watch how every ingredient comes together "
            "with incredible precision. The textures, colours "
            "and final presentation make this creation "
            "almost too beautiful to eat. "
            "Would you try this delicious masterpiece?"
        )
    },
    {
        "category": "Mystery",
        "tags": ["mystery", "fog", "forest", "abandoned", "door"],
        "title": "Something Hidden in the Forest",
        "script": (
            "Something unusual is hiding deep inside this forest. "
            "A mysterious path disappears into the fog. "
            "Strange shadows move between the trees, "
            "and nobody knows what lies at the end. "
            "Would you continue walking, or turn back?"
        )
    },
    {
        "category": "Dream Places",
        "tags": ["waterfall", "cabin", "lake", "travel", "landscape"],
        "title": "A Dream House in the Mountains",
        "script": (
            "Imagine waking up in a peaceful cabin "
            "surrounded by mountains and flowing waterfalls. "
            "Fresh air fills the room as sunlight enters "
            "through the windows. No traffic, no noise, "
            "just the beauty of nature. "
            "Would you live in a place like this?"
        )
    },
    {
        "category": "Technology",
        "tags": ["technology", "robot", "machine", "computer", "future"],
        "title": "A Glimpse Into the Future",
        "script": (
            "Imagine a future where technology changes "
            "the way we live every single day. Smart machines "
            "help people work, explore and create incredible things. "
            "The future may look very different from today. "
            "What invention would you like to see?"
        )
    },
    {
        "category": "Ocean",
        "tags": ["ocean", "sea", "underwater", "fish", "diving"],
        "title": "Discover the Hidden Ocean World",
        "script": (
            "Beneath the surface of the ocean lies "
            "an extraordinary world. Beautiful underwater "
            "landscapes, colourful marine life and sunlight "
            "moving through crystal clear water create "
            "an unforgettable scene. There is still so much "
            "of our ocean left to discover."
        )
    }
]


def log(message):
    print("[AI VIRAL SHORTS] " + str(message), flush=True)


def run(command, timeout=900):
    subprocess.run(
        command,
        check=True,
        timeout=timeout
    )


def check_tools():
    for tool in ["ffmpeg", "ffprobe"]:
        if not which(tool):
            raise RuntimeError(f"{tool} is not installed.")


# =========================================
# DAILY IDEA SELECTION
# =========================================

def select_ideas():

    today = datetime.now(timezone.utc).strftime("%Y%m%d")

    rng = random.Random(int(today))

    return rng.sample(
        IDEAS,
        DAILY_VIDEOS
    )


# =========================================
# FREE FOOTAGE LIBRARY
# =========================================

def get_footage(idea, used):

    files = [
        p for p in FOOTAGE.rglob("*")
        if p.is_file()
        and p.suffix.lower() in VIDEO_EXTENSIONS
    ]

    if not files:
        raise RuntimeError(
            "No footage found. Add free videos "
            "inside the free_footage folder."
        )

    tags = idea["tags"]

    matching = [
        p for p in files
        if any(tag in p.stem.lower() for tag in tags)
    ]

    candidates = matching if matching else files

    unused = [
        p for p in candidates
        if p not in used
    ]

    rng = random.Random(
        datetime.now(timezone.utc).strftime("%Y%m%d")
        + idea["title"]
    )

    selected = rng.choice(unused or candidates)

    used.add(selected)

    log(f"Footage selected: {selected.name}")

    return selected


# =========================================
# FREE EDGE TTS VOICE
# =========================================

async def create_edge_voice(script, output):

    communicator = edge_tts.Communicate(
        script,
        VOICE,
        rate="+2%",
        volume="+0%"
    )

    await communicator.save(str(output))


def generate_voice(script, output):

    try:
        log("Generating English AI voice...")

        asyncio.run(
            create_edge_voice(script, output)
        )

        if output.exists() and output.stat().st_size > 1000:
            return output

        raise RuntimeError("Empty Edge TTS audio.")

    except Exception as error:

        log(f"Edge TTS failed: {error}")

        if not which("espeak-ng"):
            raise RuntimeError(
                "No working voice engine available."
            )

        wav = output.with_suffix(".wav")

        run([
            "espeak-ng",
            "-v", "en-us",
            "-s", "150",
            "-w", str(wav),
            script
        ])

        run([
            "ffmpeg", "-y",
            "-i", str(wav),
            "-codec:a", "libmp3lame",
            "-q:a", "3",
            str(output)
        ])

        wav.unlink(missing_ok=True)

        return output


# =========================================
# AUDIO DURATION
# =========================================

def audio_duration(audio):

    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio)
        ],
        capture_output=True,
        text=True,
        check=True
    )

    return float(result.stdout.strip())


# =========================================
# AUTOMATIC SUBTITLES
# =========================================

def timestamp(seconds):

    ms = int(seconds * 1000)

    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)

    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def generate_captions(script, duration, output):

    words = script.split()

    chunks = [
        words[i:i + 5]
        for i in range(0, len(words), 5)
    ]

    total = len(words)
    current = 0.0

    with open(output, "w", encoding="utf-8") as f:

        for index, chunk in enumerate(chunks, 1):

            part = duration * len(chunk) / total

            start = current
            end = current + part

            f.write(
                f"{index}\n"
                f"{timestamp(start)} --> "
                f"{timestamp(end)}\n"
                f"{' '.join(chunk)}\n\n"
            )

            current = end

    return output


# =========================================
# CINEMATIC VIDEO EDITING
# =========================================

def render_video(source, audio, captions, output, duration):

    log("Creating cinematic vertical video...")

    subtitle_path = (
        captions.resolve().as_posix()
        .replace(":", r"\:")
        .replace("'", r"\'")
    )

    video_filter = (
        "scale=1080:1920:"
        "force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "zoompan="
        "z='min(zoom+0.0004,1.08)':"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        "d=1:s=1080x1920:fps=30,"
        f"subtitles='{subtitle_path}':"
        "force_style='"
        "FontName=DejaVu Sans,"
        "FontSize=17,"
        "Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "Outline=3,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=260"
        "'"
    )

    run([
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", str(source),
        "-i", str(audio),
        "-vf", video_filter,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "24",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(output)
    ])

    if not output.exists() or output.stat().st_size < 50000:
        raise RuntimeError("Video rendering failed.")

    log(f"Created: {output.name}")


# =========================================
# GENERATE ONE SHORT
# =========================================

def generate_short(idea, index, used):

    title = idea["title"]
    script = idea["script"]

    log("--------------------------------")
    log(f"SHORT {index}: {title}")
    log(f"Category: {idea['category']}")

    source = get_footage(idea, used)

    audio = OUTPUT / f"voice_{index}.mp3"

    generate_voice(script, audio)

    duration = audio_duration(audio)

    if duration < 8:
        raise RuntimeError("Voice duration too short.")

    if duration > MAX_SECONDS:
        raise RuntimeError(
            f"Voice duration exceeds {MAX_SECONDS} seconds."
        )

    captions = OUTPUT / f"captions_{index}.srt"

    generate_captions(
        script,
        duration,
        captions
    )

    safe_title = re.sub(
        r"[^a-zA-Z0-9_-]",
        "_",
        title
    )[:50]

    final = OUTPUT / (
        f"{index:02d}_{safe_title}.mp4"
    )

    render_video(
        source,
        audio,
        captions,
        final,
        duration
    )

    metadata = {
        "title": title,
        "category": idea["category"],
        "description": (
            script
            + "\n\nVisual footage used under its applicable license. "
            + "Original narration and editing."
        ),
        "source_footage": source.name,
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat()
    }

    (OUTPUT / f"{index:02d}_metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8"
    )

    audio.unlink(missing_ok=True)
    captions.unlink(missing_ok=True)

    log(f"SHORT {index} COMPLETED")

    return final


# =========================================
# MAIN AUTOMATION
# =========================================

def main():

    log("================================")
    log("FREE AI VIRAL SHORTS STARTED")
    log("================================")

    check_tools()

    if not FOOTAGE.exists():
        raise RuntimeError(
            "Create the free_footage folder first."
        )

    # Remove previous outputs
    for item in OUTPUT.iterdir():
        if item.is_file():
            item.unlink()

    ideas = select_ideas()

    used = set()
    completed = []

    for index, idea in enumerate(ideas, 1):

        try:
            video = generate_short(
                idea,
                index,
                used
            )

            completed.append(video)

        except Exception as error:
            log(f"SHORT {index} FAILED: {error}")

    log("================================")
    log(f"VIDEOS CREATED: {len(completed)}/4")
    log("================================")

    if not completed:
        raise RuntimeError(
            "No Shorts could be generated."
        )

    if len(completed) < DAILY_VIDEOS:
        raise RuntimeError(
            f"Only {len(completed)} of 4 videos created."
        )

    log("ALL FOUR SHORTS COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()
