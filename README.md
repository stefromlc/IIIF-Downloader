# IIIF High-Resolution Image Downloader

A Python utility for downloading and stitching ultra high-resolution images from IIIF-compatible servers.

This project retrieves image metadata from a IIIF endpoint, downloads image tiles in manageable chunks, and reconstructs them into a single full-resolution image. It is designed for archival collections, historical maps, manuscripts, artwork, and other large digital assets hosted using the IIIF standard.

---

## Features

* Download extremely large images from IIIF servers
* Automatic tile/chunk downloading
* Image stitching into a single high-resolution output
* Retry handling for unstable connections and rate limits
* Dynamic tile size detection from `info.json`
* Supports very large image dimensions
* Real-time progress tracking
* JPEG and PNG output support
* Browser-like request headers for improved compatibility
* Works with many IIIF-compatible archives and libraries

---

## What is IIIF?

IIIF (International Image Interoperability Framework) is a standard used by libraries, museums, archives, and universities for serving high-resolution images online.

Many institutions use IIIF to host:

* historical maps
* manuscripts
* books
* artwork
* photographs
* archival scans

This downloader interacts directly with IIIF image servers to retrieve the original high-resolution image data.

---

## Requirements

* Python 3.9+
* Pillow
* Requests
* urllib3

Install dependencies:

```bash
pip install pillow requests urllib3
```

---

## Usage

Run the script:

```bash
python map-downloader.py
```

Enter a supported IIIF image or viewer URL when prompted.

Example:

```text
https://maps.nls.uk/view/245959203
```

The script will:

1. Retrieve image metadata
2. Detect the optimal tile size
3. Download image chunks
4. Stitch the tiles together
5. Save the final high-resolution image

---

## Example Output

```text
Initializing blank canvas of 18000x12000 pixels...
Server preferred tile size is 512x512.
Starting download (840 chunks)...

Downloading chunk 840/840 [100.0%]

Download complete!
Success! Image saved as: output.jpg
```

---

## Supported Sources

This project is intended for use with publicly accessible IIIF-compatible image servers.

Examples include:

* digital libraries
* archival collections
* museums
* university repositories
* historical map collections

Compatibility depends on how each institution implements IIIF.

---

## How It Works

The downloader:

* retrieves image dimensions from `info.json`
* calculates the required tile grid
* downloads each tile individually
* reconstructs the original image using Pillow

It also includes:

* retry logic
* rate-limit handling
* memory cleanup
* fallback compatibility handling for stricter IIIF servers

---

## Project Structure

```text
map-downloader.py
README.md
```

---

## Notes

* Some IIIF servers restrict full-resolution access
* Certain archives may require authentication or special headers
* Extremely large images may require significant RAM and disk space
* Download responsibly and respect archive usage policies

---

## Future Improvements

Planned enhancements:

* Generic IIIF manifest support
* Multi-page document downloading
* Parallel tile downloading
* Resume interrupted downloads
* GUI interface
* Automatic IIIF endpoint discovery
* Metadata export
* TIFF output support

---

## Disclaimer

This tool is intended for educational, archival, and research purposes.

Users are responsible for complying with the terms of service, copyright policies, and access restrictions of the image providers they access.

---

## License

MIT License

Feel free to modify, improve, and share.
