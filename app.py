import os
import json
import math
import re
import shutil
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Optional

import streamlit as st

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

APP_NAME = "Video Splitter"
MAX_UPLOAD_MB = 2048
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024

SUPPORTED_EXTENSIONS = [
    "mp4", "mov", "avi", "mkv",
    "webm", "m4v", "wmv", "flv"
]

SESSION_ROOT = Path(tempfile.gettempdir()) / "video_splitter_sessions"
SESSION_ROOT.mkdir(parents=True, exist_ok=True)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Video Splitter",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# GLOBAL CSS
# IMPORTANT:
# No custom HTML containers are used around Streamlit widgets.
# This prevents raw <div>/<span> text from appearing.
# ============================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: Inter, sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at 85% 0%, rgba(91, 67, 235, .16), transparent 30%),
            radial-gradient(circle at 0% 45%, rgba(37, 92, 210, .08), transparent 28%),
            linear-gradient(135deg, #050b14 0%, #07111e 52%, #050a12 100%);
        color: #f8fafc;
    }

    [data-testid="stHeader"] {
        background: rgba(5, 11, 20, .78);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #08111f 0%, #091522 100%);
        border-right: 1px solid rgba(148, 163, 184, .13);
    }

    [data-testid="stSidebar"] section {
        padding-top: 1rem;
    }

    .brand-box {
        padding: 8px 4px 18px;
        margin-bottom: 14px;
        border-bottom: 1px solid rgba(148, 163, 184, .13);
    }

    .brand-name {
        color: #ffffff;
        font-size: 20px;
        font-weight: 800;
        letter-spacing: -.5px;
    }

    .brand-accent {
        color: #7c5cff;
    }

    .brand-subtitle {
        color: #8190a5;
        font-size: 11px;
        margin-top: 3px;
    }

    .page-title {
        color: #ffffff;
        font-size: clamp(30px, 4vw, 48px);
        line-height: 1.08;
        font-weight: 800;
        letter-spacing: -1.5px;
        margin: 10px 0 0 0;
    }

    .page-title-accent {
        background: linear-gradient(90deg, #ffffff, #d8ddff 55%, #947dff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .page-subtitle {
        color: #94a3b8;
        font-size: 15px;
        line-height: 1.6;
        margin-top: 9px;
        margin-bottom: 22px;
        max-width: 820px;
    }

    .section-title {
        color: #f8fafc;
        font-size: 20px;
        font-weight: 750;
        margin: 24px 0 12px;
    }

    .section-caption {
        color: #8d9bb0;
        font-size: 13px;
        margin-bottom: 12px;
    }

    .upload-title {
        color: #ffffff;
        font-size: 21px;
        font-weight: 750;
        text-align: center;
        margin-top: 5px;
    }

    .upload-subtitle {
        color: #8fa0b6;
        font-size: 13px;
        text-align: center;
        margin-top: 6px;
    }

    .upload-badge {
        display: inline-block;
        color: #cfc5ff;
        background: rgba(109, 69, 245, .13);
        border: 1px solid rgba(125, 100, 255, .25);
        border-radius: 999px;
        padding: 5px 10px;
        font-size: 11px;
        font-weight: 700;
        margin-top: 10px;
    }

    .success-box {
        border: 1px solid rgba(34, 197, 94, .24);
        background: linear-gradient(145deg, rgba(10, 55, 39, .55), rgba(7, 27, 27, .7));
        border-radius: 14px;
        padding: 16px 18px;
        margin: 12px 0;
    }

    .success-title {
        color: #86efac;
        font-size: 15px;
        font-weight: 750;
    }

    .success-text {
        color: #a7f3d0;
        font-size: 12px;
        margin-top: 4px;
    }

    .info-label {
        color: #8fa0b6;
        font-size: 12px;
    }

    .info-value {
        color: #f8fafc;
        font-size: 13px;
        font-weight: 650;
    }

    .stat-value {
        color: #ffffff;
        font-size: 25px;
        font-weight: 800;
    }

    .stat-label {
        color: #8493aa;
        font-size: 12px;
        margin-top: 3px;
    }

    .part-title {
        color: #ffffff;
        font-size: 14px;
        font-weight: 750;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .part-meta {
        color: #8190a5;
        font-size: 11px;
        margin-top: 4px;
    }

    .footer-text {
        color: #718198;
        text-align: center;
        font-size: 12px;
        padding: 28px 0 8px;
        border-top: 1px solid rgba(148, 163, 184, .11);
        margin-top: 40px;
    }

    /* Streamlit buttons */
    div[data-testid="stButton"] > button,
    div[data-testid="stDownloadButton"] > button {
        border-radius: 10px;
        min-height: 42px;
        font-weight: 700;
        border: 1px solid rgba(148, 163, 184, .15);
        transition: .18s ease;
    }

    div[data-testid="stButton"] > button:hover,
    div[data-testid="stDownloadButton"] > button:hover {
        border-color: rgba(124, 92, 255, .65);
        transform: translateY(-1px);
    }

    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #6d45f5, #4932d2);
        color: #ffffff;
        border: 0;
    }

    div[data-testid="stDownloadButton"] > button {
        background: linear-gradient(135deg, #6d45f5, #4932d2);
        color: #ffffff;
        border: 0;
    }

    /* File uploader */
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(8, 17, 30, .72);
        border: 1px dashed rgba(125, 100, 255, .48);
        border-radius: 15px;
        padding: 18px;
    }

    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: rgba(145, 125, 255, .8);
    }

    [data-testid="stFileUploaderDropzone"] button {
        background: linear-gradient(135deg, #6d45f5, #4932d2) !important;
        color: white !important;
        border: 0 !important;
        border-radius: 9px !important;
    }

    /* Cards using native Streamlit containers */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px;
        border-color: rgba(148, 163, 184, .13);
        background: linear-gradient(145deg, rgba(15, 28, 46, .82), rgba(8, 18, 31, .82));
    }

    /* Progress */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6d45f5, #3d6ae8);
    }

    /* Inputs */
    input, textarea {
        color: #f8fafc !important;
    }

    /* Mobile */
    @media (max-width: 800px) {
        .page-title {
            font-size: 31px;
        }

        .page-subtitle {
            font-size: 13px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

def init_state():
    defaults = {
        "page": "Split Video",
        "session_dir": None,
        "uploaded_path": None,
        "uploaded_name": None,
        "metadata": None,
        "split_seconds": None,
        "parts": [],
        "zip_path": None,
        "history": [],
        "processing": False,
        "uploader_key": 0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_session_dir() -> Path:
    if not st.session_state.session_dir:
        folder = SESSION_ROOT / next(tempfile._get_candidate_names())
        folder.mkdir(parents=True, exist_ok=True)
        st.session_state.session_dir = str(folder)

    return Path(st.session_state.session_dir)


# ============================================================
# UTILITIES
# ============================================================

def safe_name(name: str) -> str:
    path = Path(name)
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", path.stem).strip("._")
    return (stem or "video")[:120]


def format_size(size: int) -> str:
    value = float(size)

    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(value)} B"
            return f"{value:.1f} {unit}"
        value /= 1024

    return f"{value:.1f} TB"


def format_duration(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def parse_fps(value):
    if not value:
        return None

    try:
        if "/" in value:
            a, b = value.split("/", 1)
            if float(b) == 0:
                return None
            return float(a) / float(b)
        return float(value)
    except Exception:
        return None


# ============================================================
# FFMPEG
# ============================================================

def get_ffmpeg() -> Optional[str]:
    system_ffmpeg = shutil.which("ffmpeg")

    if system_ffmpeg:
        return system_ffmpeg

    if imageio_ffmpeg:
        try:
            bundled = imageio_ffmpeg.get_ffmpeg_exe()
            if bundled and Path(bundled).exists():
                return bundled
        except Exception:
            pass

    return None


def get_ffprobe() -> Optional[str]:
    return shutil.which("ffprobe")


def run_command(command, timeout=None):
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Process timed out."
    except OSError as exc:
        return -1, "", str(exc)


# ============================================================
# METADATA
# ============================================================

def get_metadata_ffprobe(path: Path):
    ffprobe = get_ffprobe()

    if not ffprobe:
        return None

    command = [
        ffprobe,
        "-v", "error",
        "-show_entries",
        "format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate",
        "-of", "json",
        str(path),
    ]

    code, stdout, _ = run_command(command, timeout=120)

    if code != 0:
        return None

    try:
        data = json.loads(stdout)
        streams = data.get("streams", [])

        video = next(
            (s for s in streams if s.get("codec_type") == "video"),
            None,
        )

        if not video:
            return None

        fmt = data.get("format", {})

        duration = float(fmt.get("duration") or 0)
        size = int(float(fmt.get("size") or path.stat().st_size))

        fps = parse_fps(
            video.get("avg_frame_rate")
            or video.get("r_frame_rate")
            or ""
        )

        return {
            "duration": duration,
            "size": size,
            "width": int(video.get("width") or 0),
            "height": int(video.get("height") or 0),
            "codec": video.get("codec_name") or "Unknown",
            "fps": fps,
            "format": path.suffix.lstrip(".").upper(),
        }

    except Exception:
        return None


def get_metadata_ffmpeg(path: Path):
    ffmpeg = get_ffmpeg()

    if not ffmpeg:
        return None

    code, _, stderr = run_command(
        [ffmpeg, "-hide_banner", "-i", str(path)],
        timeout=120,
    )

    if code not in (0, 1):
        return None

    duration_match = re.search(
        r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)",
        stderr,
    )

    duration = 0.0

    if duration_match:
        h, m, s = duration_match.groups()
        duration = int(h) * 3600 + int(m) * 60 + float(s)

    video_line = next(
        (line for line in stderr.splitlines() if " Video:" in line),
        "",
    )

    resolution = re.search(r"(\d{2,5})x(\d{2,5})", video_line)
    fps_match = re.search(r"(\d+(?:\.\d+)?)\s*fps", video_line)
    codec_match = re.search(r"Video:\s*([^,\s]+)", video_line)

    if not video_line or not resolution:
        return None

    return {
        "duration": duration,
        "size": path.stat().st_size,
        "width": int(resolution.group(1)),
        "height": int(resolution.group(2)),
        "codec": codec_match.group(1) if codec_match else "Unknown",
        "fps": float(fps_match.group(1)) if fps_match else None,
        "format": path.suffix.lstrip(".").upper(),
    }


def read_video_metadata(path: Path):
    return get_metadata_ffprobe(path) or get_metadata_ffmpeg(path)


# ============================================================
# UPLOAD
# ============================================================

def validate_upload(uploaded):
    if uploaded is None:
        return "Please upload a video before continuing."

    extension = Path(uploaded.name).suffix.lower().lstrip(".")

    if extension not in SUPPORTED_EXTENSIONS:
        return "Unsupported video format."

    if uploaded.size > MAX_FILE_SIZE:
        return "File too large. Maximum supported size is 2 GB."

    return None


def save_uploaded_file(uploaded) -> Path:
    session_dir = get_session_dir()
    input_dir = session_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)

    filename = safe_name(uploaded.name) + Path(uploaded.name).suffix.lower()
    destination = input_dir / filename

    uploaded.seek(0)

    with destination.open("wb") as output:
        shutil.copyfileobj(uploaded, output, length=8 * 1024 * 1024)

    uploaded.seek(0)

    return destination


# ============================================================
# SPLIT VALIDATION
# ============================================================

def validate_duration(hours, minutes, seconds, video_duration):
    if hours < 0:
        return None, "Hours cannot be negative."

    if not 0 <= minutes <= 59:
        return None, "Minutes must be between 0 and 59."

    if not 0 <= seconds <= 59:
        return None, "Seconds must be between 0 and 59."

    total = hours * 3600 + minutes * 60 + seconds

    if total <= 0:
        return None, "Please enter a duration greater than 0 seconds."

    if total > video_duration + 0.01:
        return None, "Split duration cannot be greater than the video duration."

    return total, None


# ============================================================
# FFMPEG PROCESSING
# ============================================================

def run_ffmpeg_part(
    input_path,
    output_path,
    start,
    duration,
    reencode=False,
):
    ffmpeg = get_ffmpeg()

    if not ffmpeg:
        return False

    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-ss", f"{start:.3f}",
        "-i", str(input_path),
        "-t", f"{duration:.3f}",
        "-map", "0:v:0",
        "-map", "0:a?",
    ]

    if reencode:
        command += [
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
        ]
    else:
        command += [
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            "-movflags", "+faststart",
        ]

    command.append(str(output_path))

    code, _, _ = run_command(command, timeout=None)

    return (
        code == 0
        and output_path.exists()
        and output_path.stat().st_size > 0
    )


def output_is_valid(path, expected_duration, final_part=False):
    if not path.exists() or path.stat().st_size < 1024:
        return False

    metadata = read_video_metadata(path)

    if not metadata:
        return False

    actual = metadata.get("duration", 0)
    tolerance = 1.25 if final_part else max(1.25, expected_duration * 0.015)

    return abs(actual - expected_duration) <= tolerance


def split_video(input_path, split_seconds, output_dir, progress_callback):
    if not get_ffmpeg():
        return [], False, (
            "FFmpeg is not available. "
            "Install FFmpeg or keep imageio-ffmpeg in requirements.txt."
        )

    metadata = read_video_metadata(input_path)

    if not metadata:
        return [], False, "We couldn't read this video."

    total_duration = float(metadata["duration"])

    if total_duration <= 0:
        return [], False, "The video duration could not be detected."

    total_parts = math.ceil(total_duration / split_seconds)
    base_name = safe_name(input_path.name)

    def execute(reencode=False):
        for old_file in output_dir.glob("*.mp4"):
            try:
                old_file.unlink()
            except OSError:
                pass

        generated = []

        for index in range(total_parts):
            start = index * split_seconds
            duration = min(split_seconds, total_duration - start)

            if duration <= 0.05:
                continue

            output_path = output_dir / (
                f"{base_name}_part_{index + 1:02d}.mp4"
            )

            if reencode:
                message = "Re-encoding for reliable splitting..."
            else:
                message = "Splitting without re-encoding..."

            progress_callback(
                index / total_parts,
                f"{message} Part {index + 1} of {total_parts}",
            )

            success = run_ffmpeg_part(
                input_path,
                output_path,
                start,
                duration,
                reencode,
            )

            if not success:
                return [], "FFMPEG_FAILED"

            if (
                not reencode
                and not output_is_valid(
                    output_path,
                    duration,
                    index == total_parts - 1,
                )
            ):
                return [], "NEEDS_REENCODE"

            generated.append(output_path)

            progress_callback(
                (index + 1) / total_parts,
                f"Created part {index + 1} of {total_parts}",
            )

        return generated, None

    generated, error = execute(False)

    if error in ("NEEDS_REENCODE", "FFMPEG_FAILED"):
        generated, error = execute(True)

    if error or not generated:
        return [], False, "We couldn't process this video."

    progress_callback(1.0, f"Successfully created {len(generated)} parts.")

    return generated, True, None


# ============================================================
# ZIP
# ============================================================

def create_zip(parts, source_name, progress_callback):
    if not parts:
        return None

    zip_path = get_session_dir() / (
        f"{safe_name(source_name)}_Split.zip"
    )

    try:
        with zipfile.ZipFile(
            zip_path,
            "w",
            compression=zipfile.ZIP_STORED,
            allowZip64=True,
        ) as archive:
            total = len(parts)

            for index, part in enumerate(parts, start=1):
                archive.write(part, arcname=part.name)

                progress_callback(
                    index / total,
                    f"Preparing ZIP: {index} of {total}",
                )

        return zip_path

    except Exception:
        return None


# ============================================================
# RESET
# ============================================================

def reset_project():
    session_dir = st.session_state.get("session_dir")

    if session_dir:
        shutil.rmtree(session_dir, ignore_errors=True)

    st.session_state.session_dir = None
    st.session_state.uploaded_path = None
    st.session_state.uploaded_name = None
    st.session_state.metadata = None
    st.session_state.split_seconds = None
    st.session_state.parts = []
    st.session_state.zip_path = None
    st.session_state.processing = False
    st.session_state.uploader_key += 1


# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar():
    st.sidebar.markdown(
        """
        <div class="brand-box">
            <div class="brand-name">
                ✂️ Video<span class="brand-accent">Splitter</span>
            </div>
            <div class="brand-subtitle">
                Fast • Secure • Professional
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    navigation = [
        ("🏠", "Dashboard"),
        ("✂️", "Split Video"),
        ("🕘", "Recent Splits"),
        ("⚙️", "Settings"),
        ("❓", "Help & Support"),
    ]

    for icon, label in navigation:
        if st.sidebar.button(
            f"{icon}  {label}",
            use_container_width=True,
            key=f"nav_{label}",
        ):
            st.session_state.page = label
            st.rerun()

    st.sidebar.divider()

    with st.sidebar.container(border=True):
        st.markdown("### 🎬 Split in high quality")
        st.caption(
            "Upload up to 2 GB and split videos "
            "by hours, minutes and seconds."
        )
        st.caption("MP4 • MOV • AVI • MKV • WEBM")


# ============================================================
# HEADER
# ============================================================

def page_header(title, subtitle):
    st.markdown(
        f'<div class="page-title">'
        f'<span class="page-title-accent">{title}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="page-subtitle">{subtitle}</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# UPLOAD SECTION
# ============================================================

def upload_section():
    st.markdown(
        '<div class="section-title">Upload Your Video</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(
            '<div class="upload-title">'
            '⬆️ Drag & Drop your video here'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="upload-subtitle">'
            'or use Browse Files below'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div style="text-align:center;">'
            '<span class="upload-badge">Maximum file size: 2 GB</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.write("")

        uploaded = st.file_uploader(
            "Browse Files",
            type=SUPPORTED_EXTENSIONS,
            accept_multiple_files=False,
            max_upload_size=MAX_UPLOAD_MB,
            key=f"video_uploader_{st.session_state.uploader_key}",
            help=(
                "MP4, MOV, AVI, MKV, WEBM, M4V, WMV, FLV. "
                "Maximum 2 GB."
            ),
        )

    if uploaded is None:
        return

    is_new_file = (
        st.session_state.uploaded_name != uploaded.name
        or st.session_state.uploaded_path is None
    )

    if not is_new_file:
        return

    error = validate_upload(uploaded)

    if error:
        st.error(error)
        return

    with st.spinner("Saving and reading video information..."):
        try:
            path = save_uploaded_file(uploaded)
            metadata = read_video_metadata(path)
        except Exception:
            path = None
            metadata = None

    if not path or not metadata:
        st.error(
            "We couldn't read this video. "
            "Please check the file and try again."
        )
        return

    if metadata["duration"] <= 0:
        st.error("We couldn't detect the video duration.")
        return

    output_dir = get_session_dir() / "outputs"
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    st.session_state.uploaded_path = str(path)
    st.session_state.uploaded_name = uploaded.name
    st.session_state.metadata = metadata
    st.session_state.parts = []
    st.session_state.zip_path = None

    st.rerun()


# ============================================================
# VIDEO INFORMATION
# ============================================================

def video_information():
    metadata = st.session_state.metadata

    if not metadata:
        return

    st.markdown(
        '<div class="section-title">Video Information</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.15, 1], gap="large")

    with left:
        with st.container(border=True):
            rows = [
                ("File Name", st.session_state.uploaded_name),
                ("Duration", format_duration(metadata["duration"])),
                (
                    "Resolution",
                    f'{metadata["width"]} × {metadata["height"]}',
                ),
                ("Size", format_size(metadata["size"])),
                ("Format", metadata["format"]),
                ("Video Codec", str(metadata["codec"]).upper()),
                (
                    "Frame Rate",
                    f'{metadata["fps"]:.2f} FPS'
                    if metadata.get("fps")
                    else "Unknown",
                ),
            ]

            for label, value in rows:
                c1, c2 = st.columns([1, 1.4])

                with c1:
                    st.markdown(
                        f'<span class="info-label">{label}</span>',
                        unsafe_allow_html=True,
                    )

                with c2:
                    st.markdown(
                        f'<span class="info-value">{value}</span>',
                        unsafe_allow_html=True,
                    )

                st.divider()

    with right:
        with st.container(border=True):
            st.markdown("### 🎥 Video Preview")

            try:
                st.video(st.session_state.uploaded_path)
            except Exception:
                st.info("Preview is unavailable for this file.")


# ============================================================
# DURATION SECTION
# ============================================================

def duration_section():
    metadata = st.session_state.metadata

    if not metadata:
        return

    st.markdown(
        '<div class="section-title">Split Video By Duration</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.caption(
            "Choose how long each generated video part should be. "
            "The final part automatically contains the remaining video."
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            hours = st.number_input(
                "Hours",
                min_value=0,
                max_value=999,
                value=0,
                step=1,
            )

        with c2:
            minutes = st.number_input(
                "Minutes",
                min_value=0,
                max_value=59,
                value=5,
                step=1,
            )

        with c3:
            seconds = st.number_input(
                "Seconds",
                min_value=0,
                max_value=59,
                value=0,
                step=1,
            )

        total_seconds, error = validate_duration(
            int(hours),
            int(minutes),
            int(seconds),
            float(metadata["duration"]),
        )

        if error:
            st.warning(error)
            valid = False
        else:
            valid = True
            estimated_parts = math.ceil(
                metadata["duration"] / total_seconds
            )
            st.info(
                f"Split every {format_duration(total_seconds)} "
                f"• Estimated parts: {estimated_parts}"
            )

        if st.button(
            "✂️  Split Video",
            type="primary",
            disabled=not valid or st.session_state.processing,
            use_container_width=True,
            key="split_button",
        ):
            process_video(int(total_seconds))


# ============================================================
# PROCESS VIDEO
# ============================================================

def process_video(split_seconds):
    if not st.session_state.uploaded_path:
        st.error("Please upload a video first.")
        return

    st.session_state.processing = True
    st.session_state.split_seconds = split_seconds
    st.session_state.parts = []
    st.session_state.zip_path = None

    output_dir = get_session_dir() / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    progress = st.progress(0, text="Preparing video processing...")
    status = st.empty()

    def update_progress(value, message):
        progress.progress(
            min(max(value, 0), 1),
            text=message,
        )
        status.caption(message)

    try:
        parts, success, error = split_video(
            Path(st.session_state.uploaded_path),
            split_seconds,
            output_dir,
            update_progress,
        )

        if not success:
            st.error(error or "We couldn't process this video.")
            return

        st.session_state.parts = [str(p) for p in parts]

        progress.progress(1.0, text="Splitting complete")
        status.success(f"Created {len(parts)} video parts.")

        zip_progress = st.progress(
            0,
            text="Preparing Download All ZIP...",
        )

        def zip_callback(value, message):
            zip_progress.progress(
                min(max(value, 0), 1),
                text=message,
            )

        zip_path = create_zip(
            [Path(p) for p in st.session_state.parts],
            st.session_state.uploaded_name,
            zip_callback,
        )

        if zip_path:
            st.session_state.zip_path = str(zip_path)

        history_item = {
            "name": st.session_state.uploaded_name,
            "parts": len(parts),
            "duration": st.session_state.metadata["duration"],
            "split": split_seconds,
            "time": time.strftime("%d %b %Y, %I:%M %p"),
        }

        st.session_state.history.insert(0, history_item)
        st.session_state.history = st.session_state.history[:20]

        st.success("Video splitting completed successfully.")

    except Exception:
        st.error(
            "We couldn't process this video. "
            "Please check the video file and try again."
        )

    finally:
        st.session_state.processing = False


# ============================================================
# RESULTS
# ============================================================

def results_section():
    if not st.session_state.parts:
        return

    parts = [
        Path(p)
        for p in st.session_state.parts
        if Path(p).exists()
    ]

    if not parts:
        return

    metadata = st.session_state.metadata or {}

    st.markdown(
        '<div class="section-title">Split Complete ✓</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="success-box">
            <div class="success-title">
                Your video has been successfully split.
            </div>
            <div class="success-text">
                The generated parts are ready to preview and download.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    stats = [
        (str(len(parts)), "Total Parts"),
        (
            format_duration(metadata.get("duration", 0)),
            "Original Duration",
        ),
        (
            format_duration(st.session_state.split_seconds or 0),
            "Split Duration",
        ),
        ("MP4", "Output Format"),
    ]

    for column, (value, label) in zip([c1, c2, c3, c4], stats):
        with column:
            with st.container(border=True):
                st.markdown(
                    f'<div class="stat-value">{value}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="stat-label">{label}</div>',
                    unsafe_allow_html=True,
                )

    st.markdown(
        '<div class="section-title">Generated Parts</div>',
        unsafe_allow_html=True,
    )

    for start in range(0, len(parts), 3):
        row = parts[start:start + 3]
        columns = st.columns(3)

        for index, part in enumerate(row):
            with columns[index]:
                with st.container(border=True):
                    number = start + index + 1

                    st.markdown(
                        f"### Part {number:02d}"
                    )

                    try:
                        st.video(str(part))
                    except Exception:
                        st.info("Preview unavailable.")

                    part_metadata = read_video_metadata(part) or {}
                    duration = part_metadata.get("duration", 0)
                    size = part.stat().st_size

                    st.markdown(
                        f'<div class="part-title">{part.name}</div>',
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        f'<div class="part-meta">'
                        f'Duration: {format_duration(duration)} '
                        f'• Size: {format_size(size)}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                    st.write("")

                    try:
                        with part.open("rb") as file:
                            data = file.read()

                        st.download_button(
                            "⬇️ Download",
                            data=data,
                            file_name=part.name,
                            mime="video/mp4",
                            use_container_width=True,
                            key=f"download_{number}",
                        )
                    except OSError:
                        st.error("Download unavailable.")

    st.write("")

    left, right = st.columns(2)

    with left:
        zip_path = (
            Path(st.session_state.zip_path)
            if st.session_state.zip_path
            else None
        )

        if zip_path and zip_path.exists():
            try:
                with zip_path.open("rb") as file:
                    zip_data = file.read()

                st.download_button(
                    "📦  Download All Parts",
                    data=zip_data,
                    file_name=zip_path.name,
                    mime="application/zip",
                    use_container_width=True,
                    key="download_all",
                )
            except OSError:
                st.error("ZIP download is unavailable.")

    with right:
        if st.button(
            "＋  Split Another Video",
            use_container_width=True,
            key="split_another",
        ):
            reset_project()
            st.rerun()


# ============================================================
# SPLIT PAGE
# ============================================================

def split_page():
    page_header(
        "Split Your Video",
        "Upload one video, choose a custom duration, "
        "and generate clean video segments automatically.",
    )

    upload_section()

    if st.session_state.metadata:
        video_information()
        duration_section()
        results_section()


# ============================================================
# DASHBOARD
# ============================================================

def dashboard_page():
    page_header(
        "Dashboard",
        "A professional workspace for splitting videos "
        "into custom duration segments.",
    )

    c1, c2, c3 = st.columns(3)

    dashboard_stats = [
        ("2 GB", "Maximum Upload"),
        ("8", "Supported Formats"),
        ("FFmpeg", "Processing Engine"),
    ]

    for column, (value, label) in zip(
        [c1, c2, c3],
        dashboard_stats,
    ):
        with column:
            with st.container(border=True):
                st.markdown(
                    f'<div class="stat-value">{value}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="stat-label">{label}</div>',
                    unsafe_allow_html=True,
                )

    st.markdown(
        '<div class="section-title">How It Works</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(
            "### Upload → Choose Duration → Split → Download"
        )
        st.caption(
            "The application validates the file, reads its metadata, "
            "uses FFmpeg for real video processing, creates MP4 parts, "
            "and provides individual or ZIP downloads."
        )

    st.write("")

    if st.button(
        "✂️  Start Splitting",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.page = "Split Video"
        st.rerun()


# ============================================================
# RECENT SPLITS
# ============================================================

def recent_splits_page():
    page_header(
        "Recent Splits",
        "Your completed split operations from this browser session.",
    )

    if not st.session_state.history:
        with st.container(border=True):
            st.markdown("### 🕘 No recent splits")
            st.caption(
                "Completed split jobs will appear here during this session."
            )
        return

    for item in st.session_state.history:
        with st.container(border=True):
            c1, c2 = st.columns([1.4, 1])

            with c1:
                st.markdown(f"### {item['name']}")
                st.caption(item["time"])

            with c2:
                st.write(
                    f"**{item['parts']} parts**  •  "
                    f"Every {format_duration(item['split'])}"
                )


# ============================================================
# SETTINGS
# ============================================================

def settings_page():
    page_header(
        "Settings",
        "Application limits and processing configuration.",
    )

    with st.container(border=True):
        settings = [
            ("Maximum upload size", "2 GB"),
            ("Streamlit uploader limit", "2048 MB"),
            (
                "Supported formats",
                ", ".join(x.upper() for x in SUPPORTED_EXTENSIONS),
            ),
            ("Output format", "MP4"),
            ("Processing engine", "FFmpeg"),
            (
                "Processing mode",
                "Stream copy first, automatic re-encode fallback",
            ),
            ("Storage", "Temporary server-side session storage"),
        ]

        for label, value in settings:
            c1, c2 = st.columns([1, 2])

            with c1:
                st.markdown(
                    f'<span class="info-label">{label}</span>',
                    unsafe_allow_html=True,
                )

            with c2:
                st.markdown(
                    f'<span class="info-value">{value}</span>',
                    unsafe_allow_html=True,
                )

            st.divider()

    st.markdown(
        '<div class="section-title">Session Storage</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        "🗑️  Clear Current Session Files",
        use_container_width=True,
    ):
        reset_project()
        st.success("Current uploaded and generated files were cleared.")


# ============================================================
# HELP
# ============================================================

def help_page():
    page_header(
        "Help & Support",
        "Everything you need to use Video Splitter.",
    )

    questions = [
        (
            "What is the maximum upload size?",
            "The application supports video files up to 2 GB.",
        ),
        (
            "Which formats are supported?",
            "MP4, MOV, AVI, MKV, WEBM, M4V, WMV and FLV.",
        ),
        (
            "Can I choose hours, minutes and seconds?",
            "Yes. You can manually enter all three values. "
            "Minutes and seconds must be between 0 and 59.",
        ),
        (
            "What happens to the remaining duration?",
            "If the duration is not exactly divisible, "
            "the final part contains the remaining video.",
        ),
        (
            "Does it use FFmpeg?",
            "Yes. FFmpeg performs the actual video splitting. "
            "The application first tries stream copying and "
            "automatically falls back to H.264/AAC re-encoding "
            "when required.",
        ),
        (
            "Are uploaded files permanent?",
            "No. Files are stored in temporary session storage.",
        ),
    ]

    for question, answer in questions:
        with st.expander(question):
            st.write(answer)

    st.markdown(
        '<div class="section-title">FFmpeg Status</div>',
        unsafe_allow_html=True,
    )

    if get_ffmpeg():
        st.success("FFmpeg is available and ready.")
    else:
        st.error(
            "FFmpeg is not available. Video processing cannot start."
        )

    if get_ffprobe():
        st.info("FFprobe is available for metadata extraction.")
    else:
        st.caption(
            "FFprobe is unavailable. FFmpeg metadata fallback will be used."
        )


# ============================================================
# FOOTER
# ============================================================

def footer():
    st.markdown(
        """
        <div class="footer-text">
            Video Splitter • Fast, secure and easy to use
            <br>
            © 2026 Video Splitter
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# MAIN
# ============================================================

init_state()
render_sidebar()

page = st.session_state.page

if page == "Dashboard":
    dashboard_page()
elif page == "Split Video":
    split_page()
elif page == "Recent Splits":
    recent_splits_page()
elif page == "Settings":
    settings_page()
elif page == "Help & Support":
    help_page()
else:
    st.session_state.page = "Split Video"
    split_page()

footer()