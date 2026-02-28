"""
mediachdl_core.py — download logic for Media Downloader
"""

import os
import re
import time
import random
import threading
import urllib3
import warnings
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Callable, List, Optional

from language_en import LANG

warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)


def t(key: str, **kwargs) -> str:
    s = LANG.get(key, key)
    return s.format(**kwargs) if kwargs else s


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.2739.42",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.2792.52",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 OPR/114.0.0.0",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 OPR/115.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
]

VALID_HOSTS = ("2ch.su", "arhivach.vc", "4chan.org", "boards.4chan.org")

IMAGE_EXTS = ["png", "jpg", "jpeg", "webp"]
VIDEO_EXTS = ["mp4", "webm"]


def is_valid_url(url: str) -> bool:
    return url.startswith("https://") and any(h in url for h in VALID_HOSTS)


def get_thread_id(url: str) -> str:
    match = re.search(r"(?:res/|thread/)(\d+)", url)
    if match:
        return match.group(1)
    return "unknown"


def get_source_name(url: str) -> str:
    if "4chan.org" in url:
        return "4chan"
    if "arhivach.vc" in url:
        return "arhivach"
    return "2ch"


def _sort_links_by_post_order(links: List[str]) -> List[str]:
    """
    Sort links so files appear in the order they were posted.
    Works by extracting the numeric part of the filename.
    For 2ch/arhivach filenames are typically Unix timestamps;
    for 4chan they follow the pattern <board>/<timestamp><random>.ext.
    Sorting lexicographically by the numeric stem preserves post order.
    """
    def _key(url: str) -> str:
        name = url.split("/")[-1]
        stem = re.sub(r"\.[^.]+$", "", name)   # strip extension
        digits = re.sub(r"\D", "", stem)         # keep only digits
        return digits.zfill(30)                  # zero-pad for stable sort

    return sorted(links, key=_key)


# ── Callbacks type alias ──────────────────────────────────────────────────────
LogCb    = Callable[[str], None]
ProgCb   = Callable[[int, int], None]   # (done, total)
StatusCb = Callable[[str], None]


class MediaDownloaderCore:
    def __init__(self):
        self.stop_requested = False
        self._lock = threading.Lock()

    def request_stop(self):
        with self._lock:
            self.stop_requested = True

    def _is_stopped(self) -> bool:
        with self._lock:
            return self.stop_requested

    def reset(self):
        with self._lock:
            self.stop_requested = False

    # ── Public API ────────────────────────────────────────────────────────────

    def check_url(
        self,
        url: str,
        log_cb: LogCb,
        done_cb: Callable[[int, int], None],
        error_cb: Callable[[str], None],
    ):
        """Fetch link counts without downloading. Runs in calling thread."""
        try:
            log_cb(t('log_checking_url', url=url))
            images = self.get_media_links(url, IMAGE_EXTS, log_cb)
            videos = self.get_media_links(url, VIDEO_EXTS, log_cb)
            done_cb(len(images), len(videos))
        except Exception as e:
            error_cb(t('log_check_error', error=e))

    def download(
        self,
        url: str,
        base_folder: str,
        media_type: str,
        skip_existing: bool,
        max_workers: int,
        sequential: bool,
        log_cb: LogCb,
        progress_cb: ProgCb,
        status_cb: StatusCb,
        done_cb: Callable[[], None],
    ):
        """Main download entry point. Runs in calling thread (use threading externally)."""
        self.reset()
        try:
            ua = random.choice(USER_AGENTS)
            log_cb(t('log_start_ua', ua=ua))

            thread_id  = get_thread_id(url)
            source     = get_source_name(url)
            log_cb(t('log_source', source=source, thread_id=thread_id))

            thread_folder = os.path.join(base_folder, thread_id)
            os.makedirs(thread_folder, exist_ok=True)

            if media_type == "all_media":
                image_links = self.get_media_links(url, IMAGE_EXTS, log_cb)
                video_links = self.get_media_links(url, VIDEO_EXTS, log_cb)
                log_cb(t('log_found_images', count=len(image_links)))
                log_cb(t('log_found_videos', count=len(video_links)))

                if image_links:
                    self._download_files(image_links, thread_folder, "images",
                                         skip_existing, max_workers, sequential,
                                         log_cb, progress_cb, status_cb)
                if video_links and not self._is_stopped():
                    self._download_files(video_links, thread_folder, "videos",
                                         skip_existing, max_workers, sequential,
                                         log_cb, progress_cb, status_cb)

            elif media_type == "all_images":
                links = self.get_media_links(url, IMAGE_EXTS, log_cb)
                log_cb(t('log_found_images', count=len(links)))
                self._download_files(links, thread_folder, "images",
                                     skip_existing, max_workers, sequential,
                                     log_cb, progress_cb, status_cb)

            elif media_type == "all_videos":
                links = self.get_media_links(url, VIDEO_EXTS, log_cb)
                log_cb(t('log_found_videos', count=len(links)))
                self._download_files(links, thread_folder, "videos",
                                     skip_existing, max_workers, sequential,
                                     log_cb, progress_cb, status_cb)

            else:
                links = self.get_media_links(url, [media_type], log_cb)
                log_cb(t('log_found_files', subfolder=media_type, count=len(links)))
                if links:
                    self._download_files(links, thread_folder, media_type,
                                         skip_existing, max_workers, sequential,
                                         log_cb, progress_cb, status_cb)
                else:
                    log_cb(t('log_no_ext_files'))

        except Exception as e:
            log_cb(t('log_general_error', error=e))
        finally:
            done_cb()

    # ── Link fetching ─────────────────────────────────────────────────────────

    def get_media_links(
        self,
        url: str,
        media_types: List[str],
        log_cb: Optional[LogCb] = None,
    ) -> List[str]:
        def _log(msg):
            if log_cb:
                log_cb(msg)

        try:
            _log(t('log_fetching_links', types=', '.join(media_types)))
            headers  = {"User-Agent": random.choice(USER_AGENTS)}
            response = requests.get(url, headers=headers, verify=False, timeout=15)

            if response.status_code != 200:
                _log(t('log_page_error', code=response.status_code))
                return []

            soup        = BeautifulSoup(response.text, "html.parser")
            media_links = set()

            if "4chan.org" in url:
                for thumb in soup.find_all("a", class_="fileThumb"):
                    href = thumb.get("href", "")
                    if any(href.endswith(f".{ext}") for ext in media_types):
                        if href.startswith("//"):
                            full_url = "https:" + href
                        elif href.startswith("/"):
                            full_url = "https://boards.4chan.org" + href
                        else:
                            full_url = href
                        media_links.add(full_url)
            else:
                for tag in soup.find_all("a", href=True):
                    href = tag["href"]
                    if any(href.endswith(f".{ext}") for ext in media_types):
                        media_links.add(urljoin(url, href))

                for file_elem in soup.find_all(class_="file"):
                    for a_tag in file_elem.find_all("a", href=True):
                        href = a_tag["href"]
                        if any(href.endswith(f".{ext}") for ext in media_types):
                            media_links.add(urljoin(url, href))

            return list(media_links)

        except Exception as e:
            _log(t('log_link_error', error=e))
            return []

    # ── Downloading ───────────────────────────────────────────────────────────

    def _download_files(
        self,
        links: List[str],
        thread_folder: str,
        subfolder: str,
        skip_existing: bool,
        max_workers: int,
        sequential: bool,
        log_cb: LogCb,
        progress_cb: ProgCb,
        status_cb: StatusCb,
    ):
        if not links:
            return

        # ── Sort by post order (chronological by filename numeric part) ──
        sorted_links = _sort_links_by_post_order(links)
        log_cb(t('log_sequential'))

        folder = os.path.join(thread_folder, subfolder)
        os.makedirs(folder, exist_ok=True)

        total     = len(sorted_links)
        completed = 0
        errors    = 0
        progress_cb(0, total)

        if sequential or max_workers == 1:
            # ── Sequential: one file at a time, strictly in order ──
            for link in sorted_links:
                if self._is_stopped():
                    break
                result, ok = self._download_single_file(link, folder, skip_existing)
                log_cb(result)
                completed += 1
                if not ok:
                    errors += 1
                progress_cb(completed, total)
                status_cb(t('status_downloading', done=completed, total=total))
        else:
            # ── Parallel: submit in sorted order, collect results ──
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit in post order so executor picks them up in order when possible
                futures = [
                    executor.submit(self._download_single_file, link, folder, skip_existing)
                    for link in sorted_links
                ]

                for future in futures:
                    if self._is_stopped():
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
                    try:
                        result, ok = future.result()
                        log_cb(result)
                        completed += 1
                        if not ok:
                            errors += 1
                    except Exception as e:
                        log_cb(t('log_download_error', link='?', error=e))
                        errors += 1
                        completed += 1

                    progress_cb(completed, total)
                    status_cb(t('status_downloading', done=completed, total=total))

    def _download_single_file(
        self,
        link: str,
        folder: str,
        skip_existing: bool,
        max_retries: int = 3,
    ):
        """Returns (message, success_bool)."""
        filename  = link.split("/")[-1]
        file_path = os.path.join(folder, filename)

        if skip_existing and os.path.exists(file_path):
            return t('file_skipped', filename=filename), True

        if not skip_existing and os.path.exists(file_path):
            base, ext = os.path.splitext(filename)
            counter   = 1
            new_name  = f"{base}_copy{ext}"
            new_path  = os.path.join(folder, new_name)
            while os.path.exists(new_path):
                new_name = f"{base}_copy{counter}{ext}"
                new_path = os.path.join(folder, new_name)
                counter += 1
            filename  = new_name
            file_path = new_path

        for attempt in range(max_retries):
            if self._is_stopped():
                return t('file_cancelled', filename=filename), False
            try:
                headers  = {"User-Agent": random.choice(USER_AGENTS)}
                response = requests.get(link, stream=True, timeout=10,
                                        headers=headers, verify=False)
                if response.status_code == 200:
                    with open(file_path, "wb") as f:
                        for chunk in response.iter_content(1024):
                            if self._is_stopped():
                                f.close()
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                return t('file_cancelled', filename=filename), False
                            if chunk:
                                f.write(chunk)
                    return t('file_saved', filename=filename), True
            except Exception:
                pass
            time.sleep(2)

        return t('file_failed', retries=max_retries, filename=filename), False
