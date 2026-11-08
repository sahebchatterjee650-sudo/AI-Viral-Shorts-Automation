
import os
import json
import random
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime, timezone

import edge_tts
from huggingface_hub import InferenceClient

# ==========================================
# AI VIRAL REALISTIC SHORTS AUTOMATION
# ==========================================

OUTPUT = Path("output_videos")
OUTPUT.mkdir(exist_ok=True)

MODEL = os.getenv(
    "HF_VIDEO_MODEL",
    "Wan-AI/Wan2.2-TI2V-5B"
)

VOICE = os.getenv(
    "TTS_VOICE",
    "en-US-AndrewNeural"
)

MAX_SECONDS = 45

# Original fictional concepts. No news/RSS.
IDEAS = [
    {
        "category": "Wildlife",
        "title": "A Fox Discovers a Hidden Garden",
        "prompt": (
            "Ultra photorealistic wildlife documentary footage "
            "of a beautiful red fox discovering a tiny warm "
            "greenhouse inside a snowy pine forest at sunrise. "
            "Realistic fur, visible breath, falling snow, "
            "natural animal movements, cinematic long lens, "
            "real camera footage, vertical 9:16, no text."
        ),
        "script": (
            "Imagine walking through a frozen forest and "
            "discovering a secret garden. A curious red fox "
            "slowly approaches a warm greenhouse surrounded "
            "by snow. Golden light shines through the glass "
            "as tiny snowflakes fall around it. "
            "Would you explore this magical place?"
        )
    },
    {
        "category": "Impossible Realism",
        "title": "An Ocean Inside a Glass Room",
        "prompt": (
            "Hyper realistic cinematic footage of an enormous "
            "glass room containing a miniature living ocean, "
            "clear moving waves, realistic fish, sunlight "
            "caustics, physically accurate water simulation, "
            "smooth camera movement, photorealistic, vertical 9:16."
        ),
        "script": (
            "What if an entire ocean could fit inside one room? "
            "Imagine watching tiny waves move beneath a glass "
            "ceiling while colorful fish swim through sunlight. "
            "This is an imaginary architectural concept, "
            "but it looks almost real. Would you live here?"
        )
    },
    {
        "category": "Satisfying",
        "title": "The Perfect Glass Sculpture",
        "prompt": (
            "Ultra realistic macro cinematic video of an expert "
            "glass artist shaping glowing molten orange glass "
            "into a perfectly smooth transparent sculpture. "
            "Realistic heat shimmer, precise tools, detailed "
            "reflections, satisfying movements, vertical 9:16."
        ),
        "script": (
            "Watch closely as glowing molten glass slowly "
            "becomes a beautiful transparent sculpture. "
            "The artist carefully shapes the hot material "
            "with incredible precision. The glowing orange "
            "surface gradually becomes crystal clear. "
            "Could you create something this beautiful?"
        )
    },
    {
        "category": "Mystery",
        "title": "The Mysterious Door in the Forest",
        "prompt": (
            "Photorealistic cinematic mystery scene showing "
            "a tiny ancient wooden door inside a giant tree "
            "in a foggy forest. Wet autumn leaves, realistic "
            "mist, natural wind moving branches, slow camera "
            "approach, atmospheric lighting, vertical 9:16."
        ),
        "script": (
            "Deep inside a quiet forest, something unusual "
            "appears. A tiny wooden door is built into the "
            "trunk of an enormous tree. Fresh footprints "
            "stop right in front of it. The forest is silent. "
            "Would you have the courage to open that door?"
        )
    },
    {
        "category": "Miniature World",
        "title": "A City Inside a Teacup",
        "prompt": (
            "Photorealistic macro tilt shift footage of a "
            "detailed miniature city built inside a white "
            "ceramic teacup. Tiny moving trains, glowing "
            "apartment windows, miniature trees, rising steam, "
            "realistic materials, cinematic camera orbit, vertical 9:16."
        ),
        "script": (
            "Look carefully. Inside this ordinary teacup "
            "is an entire miniature city. Tiny trains move "
            "between buildings while warm lights glow "
            "through the windows. Steam rises above the "
            "rooftops like morning fog. What would you "
            "build inside a teacup?"
        )
    },
    {
        "category": "Fantasy",
        "title": "A Giant Whale Above the Clouds",
        "prompt": (
            "Photorealistic magical realism cinematic footage "
            "of a gigantic gentle blue whale swimming above "
            "golden clouds at sunrise. Realistic whale skin, "
            "beautiful atmospheric lighting, distant birds, "
            "smooth aerial camera tracking, vertical 9:16."
        ),
        "script": (
            "Imagine looking out of an airplane window "
            "and seeing a giant whale swimming above the clouds. "
            "Its movement is peaceful as golden sunlight "
            "fills the sky. This is an imaginary fantasy scene "
            "made to look like a real discovery. What would "
            "you name this incredible creature?"
        )
    },
    {
        "category": "Nature",
        "title": "A Flower After the Rain",
        "prompt": (
            "Ultra photorealistic macro nature video of a "
            "beautiful purple flower opening after rainfall. "
            "Individual water droplets rolling from petals, "
            "soft morning sunlight, gentle breeze, detailed "
            "pollen, cinematic macro camera, vertical 9:16."
        ),
        "script": (
            "Sometimes nature creates the most beautiful "
            "moments. After the rain, a tiny flower slowly "
            "opens toward the morning sunlight. Water droplets "
            "slide across its delicate petals. Every little "
            "detail tells a beautiful story. What is your "
            "favorite thing about nature?"
        )
    },
    {
        "category": "Dream Places",
        "title": "A Cabin Behind a Waterfall",
        "prompt": (
            "Photorealistic cinematic travel footage of a "
            "beautiful wooden cabin hidden behind a powerful "
            "forest waterfall. Real flowing water, drifting "
            "mist, lush green plants, warm glowing windows, "
            "slow cinematic camera movement, vertical 9:16."
        ),
        "script": (
            "Imagine discovering a beautiful wooden cabin "
            "hidden behind a waterfall. Water rushes past "
            "the entrance while soft golden light shines "
            "through the windows. Mist fills the surrounding "
            "forest. It looks like the perfect escape. "
            "Would you spend a weekend here?"
        )
    },
    {
        "category": "Food Art",
        "title": "A Dessert That Looks Like a Planet",
        "prompt": (
            "Ultra photorealistic luxury food macro video "
            "of a pastry chef creating a glossy spherical "
            "blue planet dessert. Mirror glaze, delicate "
            "edible details, precision tools, studio lighting, "
            "slow cinematic close-up, vertical 9:16."
        ),
        "script": (
            "At first glance, this looks like a tiny planet. "
            "But it is actually an imaginative dessert. "
            "A chef carefully adds the final details to "
            "its glossy blue surface. It looks almost too "
            "beautiful to eat. Would you taste this creation?"
        )
    },
    {
        "category": "Adventure",
        "title": "A Train Above the Clouds",
        "prompt": (
            "Ultra photorealistic cinematic travel footage "
            "of a red passenger train crossing an old stone "
            "railway bridge above a misty mountain valley "
            "at sunrise. Realistic moving train, pine forests, "
            "golden atmospheric lighting, aerial camera, vertical 9:16."
        ),
        "script": (
            "A red train slowly appears through the morning "
            "mist and crosses an ancient stone bridge. "
            "Far below, a mountain valley disappears beneath "
            "the clouds. Golden sunlight touches the hills. "
            "It feels like the beginning of an unforgettable "
            "journey. Where would you travel by train?"
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


def check_program(name):
    from shutil import which
    return which(name) is not None


def timestamp(seconds):
    milliseconds = int(seconds * 1000)

    hours, milliseconds = divmod(
        milliseconds, 3600000
    )

    minutes, milliseconds = divmod(
        milliseconds, 60000
    )

    seconds, milliseconds = divmod(
        milliseconds, 1000
    )

    return (
        f"{hours:02}:"
        f"{minutes:02}:"
        f"{seconds:02},"
        f"{milliseconds:03}"
    )


# ==========================================
# SELECT ORIGINAL VIDEO IDEA
# ==========================================

def select_idea():

    seed = int(
        datetime.now(timezone.utc).strftime("%Y%m%d")
    )

    rng = random.Random(seed)

    return rng.choice(IDEAS)


# ==========================================
# GENERATE REAL AI VIDEO
# ==========================================

def generate_video(prompt):

    token = os.getenv("HF_TOKEN", "").strip()

    if not token:
        raise RuntimeError(
            "HF_TOKEN missing. Add Hugging Face token "
            "in GitHub Actions Secrets."
        )

    log("Connecting to Hugging Face Inference...")

    client = InferenceClient(
        api_key=token,
        timeout=900
    )

    log("Requesting one AI video generation...")

    video_bytes = client.text_to_video(
        prompt=prompt,
        model=MODEL,
        num_frames=49,
        num_inference_steps=20,
        guidance_scale=6.0,
        negative_prompt=[
            "blurry",
            "low quality",
            "distorted objects",
            "bad anatomy",
            "watermark",
            "text",
            "flickering"
        ]
    )

    if not video_bytes or len(video_bytes) < 10000:
        raise RuntimeError(
            "AI provider returned an invalid video."
        )

    video_path = OUTPUT / "ai_source.mp4"

    video_path.write_bytes(video_bytes)

    log(
        f"AI video downloaded: "
        f"{len(video_bytes):,} bytes"
    )

    return video_path


# ==========================================
# GENERATE ENGLISH AI VOICE
# ==========================================

async def edge_voice(script, output):

    communicator = edge_tts.Communicate(
        script,
        VOICE,
        rate="+2%",
        volume="+0%"
    )

    await communicator.save(str(output))


def generate_voice(script):

    audio = OUTPUT / "voice.mp3"

    try:
        log("Generating natural English voice...")

        asyncio.run(edge_voice(script, audio))

        if audio.exists() and audio.stat().st_size > 1000:
            return audio

        raise RuntimeError("Edge TTS returned empty audio.")

    except Exception as error:

        log(f"Edge TTS unavailable: {error}")

        # Offline fallback
        if not check_program("espeak-ng"):
            raise RuntimeError(
                "Both Edge TTS and offline TTS are unavailable."
            )

        wav = OUTPUT / "voice_fallback.wav"

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
            str(audio)
        ])

        if not audio.exists() or audio.stat().st_size < 1000:
            raise RuntimeError("Offline voice generation failed.")

        return audio


# ==========================================
# AUDIO DURATION
# ==========================================

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


# ==========================================
# CAPTION GENERATION
# ==========================================

def generate_captions(script, duration):

    words = script.split()

    chunks = [
        words[i:i + 5]
        for i in range(0, len(words), 5)
    ]

    total_words = sum(
        len(chunk) for chunk in chunks
    )

    current = 0.0

    caption_file = OUTPUT / "captions.srt"

    with open(
        caption_file,
        "w",
        encoding="utf-8"
    ) as file:

        for index, chunk in enumerate(chunks, 1):

            part = duration * len(chunk) / total_words

            start = current
            end = current + part

            file.write(
                f"{index}\n"
                f"{timestamp(start)} --> "
                f"{timestamp(end)}\n"
                f"{' '.join(chunk)}\n\n"
            )

            current = end

    return caption_file


# ==========================================
# VIDEO RENDERING
# ==========================================

def render_video(source, audio, captions, output, duration):

    log("Rendering vertical 1080x1920 video...")

    subtitle_path = (
        captions.resolve().as_posix()
        .replace(":", r"\:")
        .replace("'", r"\'")
    )

    video_filter = (
        "scale=1080:1920:"
        "force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "setsar=1,"
        "fps=30,"
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
        "ffmpeg",
        "-y",
        "-stream_loop", "-1",
        "-i", str(source),
        "-i", str(audio),
        "-vf", video_filter,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(output)
    ])

    if not output.exists() or output.stat().st_size < 50000:
        raise RuntimeError("Final video creation failed.")

    log("Final MP4 successfully created.")


# ==========================================
# MAIN
# ==========================================

def main():

    log("================================")
    log("AI REALISTIC SHORTS STARTED")
    log("================================")

    if not check_program("ffmpeg"):
        raise RuntimeError("FFmpeg is missing.")

    if not check_program("ffprobe"):
        raise RuntimeError("FFprobe is missing.")

    idea = select_idea()

    category = idea["category"]
    title = idea["title"]
    prompt = idea["prompt"]
    script = idea["script"]

    log(f"Category: {category}")
    log(f"Title: {title}")

    (OUTPUT / "script.txt").write_text(
        script,
        encoding="utf-8"
    )

    (OUTPUT / "video_prompt.txt").write_text(
        prompt,
        encoding="utf-8"
    )

    metadata = {
        "title": title,
        "category": category,
        "description": (
            script
            + "\n\nAI-generated fictional visual."
        ),
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat()
    }

    (OUTPUT / "metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8"
    )

    # One real AI video generation attempt
    source = generate_video(prompt)

    # Narration
    audio = generate_voice(script)

    duration = audio_duration(audio)

    if duration < 10 or duration > MAX_SECONDS:
        raise RuntimeError(
            f"Invalid audio duration: {duration:.2f}"
        )

    # Captions
    captions = generate_captions(
        script,
        duration
    )

    # Final rendering
    final = OUTPUT / "viral_short.mp4"

    render_video(
        source,
        audio,
        captions,
        final,
        duration
    )

    log("================================")
    log("AUTOMATION COMPLETED")
    log(f"OUTPUT: {final}")
    log("================================")


if __name__ == "__main__":
    main()
