# Video Splitter

Video Splitter is a professional web application for splitting large video files into custom duration segments. The application is built as a single Streamlit application and uses FFmpeg for reliable video processing.

## Features

Video Splitter supports video uploads up to 2 GB and allows users to split videos by manually selecting hours, minutes, and seconds.

Key features include:

* Upload a single video up to 2 GB
* Drag and drop video upload
* Support for MP4, MOV, AVI, MKV, WEBM, M4V, WMV, and FLV
* Video metadata display
* Video preview
* Custom split duration using hours, minutes, and seconds
* Automatic video segmentation using FFmpeg
* Individual video part downloads
* Download all generated parts as a ZIP file
* Processing status and progress indication
* Professional dark navy and purple SaaS interface
* Responsive desktop, tablet, and mobile layout
* Error handling for invalid files and processing failures
* Temporary file management and cleanup
* Filename sanitization and upload validation
* Split another video without restarting the application

## Application Flow

The complete workflow is:

Upload Video

The user uploads a supported video file through the upload area. The application validates the file type and confirms that the file does not exceed the 2 GB limit.

Video Information

After uploading, the application displays the filename, file size, duration, resolution, format, codec, frame rate, and a video preview when available.

Split Duration

The user selects the desired segment duration using hours, minutes, and seconds.

For example, selecting 0 hours, 5 minutes, and 0 seconds splits the video into five minute segments.

Video Processing

The application calculates the required number of segments and uses FFmpeg to create the video parts.

Generated Parts

After processing, every generated segment is displayed with its part number, preview, duration, file size, and individual download option.

Download All

Users can download all generated parts together as a ZIP archive.

Split Another Video

The application can be reset so another video can be processed without restarting the server.

## Technology Stack

Python

Streamlit

FFmpeg

FFprobe

HTML

CSS

JavaScript

Python Standard Library

## Project Structure

The project intentionally uses a minimal structure.

```text
Video-Splitter/
│
├── app.py
├── requirements.txt
└── README.md
```

The main application is contained entirely inside `app.py`. The interface, styling, JavaScript, video processing, file handling, validation, and download functionality are implemented from the Streamlit application.

## Requirements

Python 3.10 or later is recommended.

FFmpeg must be available in the system environment.

Required Python packages should be listed in `requirements.txt`.

A typical requirements file can contain:

```text
streamlit
```

Additional packages should only be added if they are actually required by the final implementation.

## FFmpeg Configuration

FFmpeg and FFprobe are required for video processing.

Verify the installation with:

```bash
ffmpeg -version
```

and:

```bash
ffprobe -version
```

If FFmpeg is installed correctly, the commands should return the installed FFmpeg version.

For deployment, FFmpeg must also be available on the server environment.

## Running the Application

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Start the application with:

```bash
streamlit run app.py
```

The application will open in the browser through the Streamlit server.

## Video Splitting Example

Suppose the uploaded video is 23 minutes long and the selected split duration is 5 minutes.

The application generates:

```text
video_part_01.mp4
video_part_02.mp4
video_part_03.mp4
video_part_04.mp4
video_part_05.mp4
```

The final segment contains the remaining three minutes.

## Large File Handling

Video files can be as large as 2 GB. The application is designed to avoid unnecessarily loading complete videos into Python memory.

Temporary directories are used for processing and generated files. FFmpeg performs the actual video operations directly on disk.

Temporary resources should be cleaned when they are no longer required.

## Security

The application validates uploaded files before processing.

Important security practices include:

* Filename sanitization
* Extension validation
* Temporary storage for uploaded files
* Protection against path traversal
* No execution of uploaded files
* FFmpeg-based media validation
* Temporary file cleanup
* No exposure of server filesystem paths

## Error Handling

The application provides user-friendly messages for common problems including unsupported formats, files larger than 2 GB, missing uploads, invalid split durations, split durations longer than the source video, unavailable FFmpeg installations, and video processing failures.

Internal Python exceptions and server filesystem details should not be exposed to normal users.

## User Interface

The application uses a modern dark navy and blue-black interface with purple and indigo accents.

The design includes:

* Premium SaaS-style cards
* Rounded components
* Subtle borders
* Gradient primary buttons
* Responsive layouts
* Professional typography
* Upload animations
* Hover effects
* Processing states
* Success states
* Responsive video cards

The design is inspired by modern video-processing applications while maintaining original Video Splitter branding.

## Production Considerations

For production deployment, ensure that the server has sufficient disk space for uploaded videos, generated segments, and ZIP archives.

Because the application supports files up to 2 GB, the hosting platform must support sufficiently large request and file limits.

FFmpeg must be installed and accessible through the server environment.

Temporary files should be removed after processing whenever they are no longer required.

## Deployment

The application can be deployed on a Streamlit-compatible hosting environment or another server capable of running Python and FFmpeg.

Before deployment, verify:

```text
Python environment
Required Python packages
FFmpeg installation
FFprobe availability
Temporary directory permissions
Maximum upload size
Available disk space
Server resource limits
```

## Project Goal

Video Splitter is designed to provide a simple but professional video segmentation workflow without requiring users to manually enter timestamps for every section.

The primary workflow remains:

Upload Video

Read Video Information

Select Split Duration

Process with FFmpeg

Generate Video Parts

Preview Parts

Download Individual Parts

Download All Parts

Split Another Video

## License

This project can be adapted and extended for personal, educational, or production use according to the license and dependencies selected for the final implementation.
