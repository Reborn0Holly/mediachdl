"""
English language strings for Media Downloader (core + GUI)
"""

LANG = {
    # ── GUI ───────────────────────────────────────────────────────────────────

    # Window
    'title':                    'Media Downloader · 2ch / arhivach / 4chan',

    # Header
    'header_title':             '⬡  Media Downloader',
    'header_subtitle':          '2ch.su · arhivach.vc · 4chan.org',

    # URL section
    'url_section':              'URL',
    'url_hint':                 'Enter thread link from 2ch.su, arhivach.vc or 4chan.org:',
    'url_placeholder':          'https://…',
    'btn_paste_url':            '📋  Paste URL',
    'btn_check_url':            '🔍  Check',

    # Options section
    'options_section':          'OPTIONS',
    'label_media_type':         'Media type',
    'label_download_folder':    'Download folder',
    'btn_browse':               '…',
    'label_skip_existing':      'Skip existing files',
    'label_threads':            'Threads (recommended ≤ 3):',
    'label_sequential':         'Sequential download (post order)',

    # Media type radio buttons
    'type_all_media':           'All media',
    'type_all_images':          'All images',
    'type_all_videos':          'All videos',
    'type_png':                 'PNG',
    'type_jpg':                 'JPG',
    'type_jpeg':                'JPEG',
    'type_webp':                'WEBP',
    'type_webm':                'WEBM',
    'type_mp4':                 'MP4',

    # Buttons
    'btn_start':                '▶  Start download',
    'btn_stop':                 '⏹  Stop',
    'btn_open_folder':          '📁  Open folder',
    'btn_save_log':             '💾  Save log',

    # Progress section
    'progress_section':         'PROGRESS',
    'progress_label_init':      '0/0 files',
    'progress_label':           '{done}/{total} files',

    # Log section
    'log_section':              'LOG',

    # Stats cards
    'stats_section':            'STATISTICS',
    'card_found':               'Found',
    'card_downloaded':          'Downloaded',
    'card_errors':              'Errors',
    'card_skipped':             'Skipped',

    # Status bar
    'status_ready':             'Ready',
    'status_checking':          'Checking URL…',
    'status_fetching':          'Fetching file list…',
    'status_downloading':       'Downloading {done} of {total} files',
    'status_stopped':           'Download stopped by user',
    'status_done':              'Download complete!',
    'status_stopping':          'Stopping download…',

    # Messageboxes
    'mb_warn_title':            'Warning',
    'mb_info_title':            'Info',
    'mb_error_title':           'Error',
    'mb_warn_no_url':           'Please enter a URL.',
    'mb_warn_invalid_url':      'Invalid URL. Make sure the link is from 2ch.su, arhivach.vc or 4chan.org.',
    'mb_warn_no_folder':        'Specified folder does not exist.',
    'mb_info_check_none':       'No media found. Check the URL or try a different thread.',
    'mb_info_check_found':      'Found {images} image(s) and {videos} video(s).',
    'mb_err_create_folder':     'Could not create folder: {error}',
    'mb_info_log_saved':        'Log saved to {path}',
    'mb_done':                  'Download complete!',

    # ── Core (mediachdl_core.py) ──────────────────────────────────────────────

    'log_start_ua':             'Starting download with User-Agent: {ua}',
    'log_source':               'Source: {source}, Thread ID: {thread_id}',
    'log_found_images':         'Images found: {count}',
    'log_found_videos':         'Videos found: {count}',
    'log_found_files':          'Files found ({subfolder}): {count}',
    'log_no_ext_files':         'No files with the specified extension found.',
    'log_fetching_links':       'Fetching links for {types}…',
    'log_page_error':           'Error fetching page: HTTP {code}',
    'log_link_error':           'Error fetching links: {error}',
    'log_download_error':       'Error downloading {link}: {error}',
    'log_general_error':        'Download error: {error}',
    'log_stop_requested':       'Stop requested…',
    'log_stopped':              'Download stopped by user.',
    'log_done':                 'Download complete!',
    'log_checking_url':         'Checking URL: {url}',
    'log_check_error':          'Error checking URL: {error}',
    'log_sequential':           'Sequential mode: links sorted by post order.',

    'file_skipped':             'Skipped (exists): {filename}',
    'file_saved':               'Saved: {filename}',
    'file_cancelled':           'Cancelled: {filename}',
    'file_failed':              'Failed after {retries} retries: {filename}',

    # Save log dialog
    'save_log_filename':        'download_log_{timestamp}.txt',

    # Version / footer
    'version':                  'v0.0.3',
    'github_link':              'GitHub',
    'github_url':               'https://github.com/Reborn0Holly/mediachdl',
}
