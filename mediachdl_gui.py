"""
mediachdl_gui.py — CustomTkinter GUI for Media Downloader
Requires: pip install customtkinter requests beautifulsoup4
"""

import os
import time
import threading
import webbrowser
import customtkinter as ctk
from tkinter import filedialog, messagebox

from language_en import LANG
from mediachdl_core import MediaDownloaderCore, is_valid_url

# ── Theme ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT   = "#2D7DD2"
BG_DARK  = "#0F1117"
BG_MID   = "#181C27"
BG_CARD  = "#1E2338"
TEXT     = "#E8EAF0"
TEXT_DIM = "#6B7280"
SUCCESS  = "#22C55E"
ERROR    = "#EF4444"
WARN     = "#F59E0B"

# ─────────────────────────────────────────────────────────────────────────────

MEDIA_TYPES = [
    ("type_all_media",   "all_media"),
    ("type_all_images",  "all_images"),
    ("type_all_videos",  "all_videos"),
    ("type_png",         "png"),
    ("type_jpg",         "jpg"),
    ("type_jpeg",        "jpeg"),
    ("type_webp",        "webp"),
    ("type_webm",        "webm"),
    ("type_mp4",         "mp4"),
]


def t(key: str, **kwargs) -> str:
    s = LANG.get(key, key)
    return s.format(**kwargs) if kwargs else s


class StatCard(ctk.CTkFrame):
    def __init__(self, master, label: str, color: str = TEXT, **kwargs):
        super().__init__(master, fg_color=BG_CARD, corner_radius=10, **kwargs)
        self.value_lbl = ctk.CTkLabel(self, text="0",
                                       font=("Consolas", 24, "bold"),
                                       text_color=color)
        self.value_lbl.pack(pady=(10, 2))
        ctk.CTkLabel(self, text=label, text_color=TEXT_DIM,
                     font=("Consolas", 10)).pack(pady=(0, 10))

    def set(self, val: int):
        self.value_lbl.configure(text=str(val))


class MediaDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(t('title'))
        self.geometry("1200x900")
        self.minsize(860, 620)
        self.configure(fg_color=BG_DARK)

        self._core           = MediaDownloaderCore()
        self._is_downloading = False
        self._log_queue: list[str] = []
        self._stats          = {"found": 0, "downloaded": 0, "errors": 0, "skipped": 0}

        self._build_ui()
        self._poll_log()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color=BG_MID, corner_radius=0, height=56)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=t('header_title'),
                     font=("Consolas", 18, "bold"), text_color=ACCENT).pack(
            side="left", padx=24, pady=14)
        ctk.CTkLabel(header, text=t('header_subtitle'),
                     font=("Consolas", 11), text_color=TEXT_DIM).pack(
            side="left", pady=14)

        # version + github link
        gh_lbl = ctk.CTkLabel(header, text=f"{t('version')}  |  {t('github_link')}",
                               font=("Consolas", 11), text_color=ACCENT, cursor="hand2")
        gh_lbl.pack(side="right", padx=20)
        gh_lbl.bind("<Button-1>", lambda _: webbrowser.open(t('github_url')))

        # ── Body ──
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=14)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(4, weight=1)

        # ── URL card ──
        url_card = ctk.CTkFrame(body, fg_color=BG_CARD, corner_radius=12)
        url_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        url_card.columnconfigure(1, weight=1)

        ctk.CTkLabel(url_card, text=t('url_section'),
                     font=("Consolas", 10, "bold"), text_color=ACCENT).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(12, 6))
        ctk.CTkLabel(url_card, text=t('url_hint'),
                     font=("Consolas", 11), text_color=TEXT_DIM).grid(
            row=1, column=0, columnspan=3, sticky="w", padx=16, pady=(0, 6))

        self.url_entry = ctk.CTkEntry(url_card, placeholder_text=t('url_placeholder'),
                                       fg_color=BG_DARK, border_color="#2A2F45",
                                       text_color=TEXT, font=("Consolas", 12))
        self.url_entry.grid(row=2, column=1, columnspan=1, sticky="ew",
                                padx=(4, 16), pady=(0, 12))

        ctk.CTkButton(url_card, text=t('btn_paste_url'), width=130, height=30,
                      fg_color=ACCENT, hover_color="#1A5FA8",
                      font=("Consolas", 11), command=self._paste_url).grid(
            row=1, column=2, padx=(4, 16), pady=(0, 12))

        ctk.CTkButton(url_card, text=t('btn_check_url'), width=100, height=30,
                      fg_color=ACCENT, hover_color="#1A5FA8",
                      font=("Consolas", 11), command=self._check_url).grid(
            row=2, column=2, padx=(4, 16), pady=(0, 12))

        # ── Options card ──
        opt_card = ctk.CTkFrame(body, fg_color=BG_CARD, corner_radius=12)
        opt_card.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        opt_card.columnconfigure(1, weight=1)

        ctk.CTkLabel(opt_card, text=t('options_section'),
                     font=("Consolas", 10, "bold"), text_color=ACCENT).grid(
            row=0, column=0, columnspan=4, sticky="w", padx=16, pady=(12, 8))

        # Media type radios
        ctk.CTkLabel(opt_card, text=t('label_media_type'), width=130, anchor="w",
                     text_color=TEXT_DIM, font=("Consolas", 12)).grid(
            row=1, column=0, padx=(16, 8), pady=4, sticky="w")

        radio_wrap = ctk.CTkFrame(opt_card, fg_color="transparent")
        radio_wrap.grid(row=1, column=1, columnspan=3, sticky="w", pady=4)

        self.media_type_var = ctk.StringVar(value="all_videos")
        for lang_key, value in MEDIA_TYPES:
            ctk.CTkRadioButton(radio_wrap, text=t(lang_key), value=value,
                               variable=self.media_type_var,
                               text_color=TEXT, font=("Consolas", 11),
                               fg_color=ACCENT).pack(side="left", padx=6)

        # Folder
        ctk.CTkLabel(opt_card, text=t('label_download_folder'), width=130, anchor="w",
                     text_color=TEXT_DIM, font=("Consolas", 12)).grid(
            row=2, column=0, padx=(16, 8), pady=4, sticky="w")

        self.folder_entry = ctk.CTkEntry(opt_card, fg_color=BG_DARK,
                                          border_color="#2A2F45",
                                          text_color=TEXT, font=("Consolas", 12))
        default_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Downloads")
        self.folder_entry.insert(0, default_folder)
        self.folder_entry.grid(row=2, column=1, columnspan=2, sticky="ew",
                                padx=(0, 6), pady=4)

        ctk.CTkButton(opt_card, text=t('btn_browse'), width=36, height=28,
                      fg_color=BG_CARD, hover_color=ACCENT,
                      command=self._browse_folder).grid(
            row=2, column=3, padx=(0, 16), pady=4)

        # Advanced row
        adv_row = ctk.CTkFrame(opt_card, fg_color="transparent")
        adv_row.grid(row=3, column=0, columnspan=4, sticky="w",
                     padx=16, pady=(4, 12))

        self.skip_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(adv_row, text=t('label_skip_existing'),
                        variable=self.skip_var,
                        text_color=TEXT, font=("Consolas", 11),
                        fg_color=ACCENT, hover_color="#1A5FA8").pack(
            side="left", padx=(0, 24))

        self.sequential_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(adv_row, text=t('label_sequential'),
                        variable=self.sequential_var,
                        text_color=TEXT, font=("Consolas", 11),
                        fg_color=ACCENT, hover_color="#1A5FA8").pack(
            side="left", padx=(0, 24))

        ctk.CTkLabel(adv_row, text=t('label_threads'),
                     text_color=TEXT_DIM, font=("Consolas", 11)).pack(side="left")

        self.threads_var = ctk.IntVar(value=3)
        ctk.CTkEntry(adv_row, textvariable=self.threads_var, width=50,
                     fg_color=BG_DARK, border_color="#2A2F45",
                     text_color=TEXT, font=("Consolas", 12)).pack(
            side="left", padx=(8, 0))

        # ── Action buttons ──
        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        self.start_btn = ctk.CTkButton(
            btn_row, text=t('btn_start'),
            font=("Consolas", 13, "bold"), height=40,
            fg_color=ACCENT, hover_color="#1A5FA8",
            command=self._start_download)
        self.start_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = ctk.CTkButton(
            btn_row, text=t('btn_stop'),
            font=("Consolas", 13), height=40,
            fg_color="#3B3F52", hover_color=ERROR,
            state="disabled", command=self._stop_download)
        self.stop_btn.pack(side="left", padx=(0, 20))

        ctk.CTkButton(
            btn_row, text=t('btn_open_folder'),
            font=("Consolas", 12), height=40,
            fg_color="transparent", border_width=1,
            border_color="#2A2F45", hover_color=BG_CARD,
            text_color=TEXT_DIM, command=self._open_folder).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text=t('btn_save_log'),
            font=("Consolas", 12), height=40,
            fg_color="transparent", border_width=1,
            border_color="#2A2F45", hover_color=BG_CARD,
            text_color=TEXT_DIM, command=self._save_log).pack(side="left")

        # ── Progress ──
        self.progress_var = ctk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(body, variable=self.progress_var,
                                                height=6, progress_color=ACCENT,
                                                fg_color=BG_CARD)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=3, column=0, sticky="ew", pady=(0, 4))

        self.status_lbl = ctk.CTkLabel(body, text=t('status_ready'),
                                        font=("Consolas", 11), text_color=TEXT_DIM,
                                        anchor="w")
        self.status_lbl.grid(row=3, column=0, sticky="sw")

        # ── Bottom: log + stats ──
        bottom = ctk.CTkFrame(body, fg_color="transparent")
        bottom.grid(row=4, column=0, sticky="nsew", pady=(8, 0))
        bottom.columnconfigure(0, weight=1)
        bottom.rowconfigure(0, weight=1)

        # Log
        log_wrap = ctk.CTkFrame(bottom, fg_color=BG_CARD, corner_radius=12)
        log_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        log_wrap.columnconfigure(0, weight=1)
        log_wrap.rowconfigure(1, weight=1)
        ctk.CTkLabel(log_wrap, text=t('log_section'),
                     font=("Consolas", 10, "bold"), text_color=ACCENT).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4))

        self.log_box = ctk.CTkTextbox(
            log_wrap, fg_color=BG_DARK, text_color=TEXT,
            font=("Consolas", 11), corner_radius=8,
            border_width=1, border_color="#1A1E2E",
            wrap="word", state="disabled")
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        # Stats column
        stats_col = ctk.CTkFrame(bottom, fg_color="transparent")
        stats_col.grid(row=0, column=1, sticky="ns")

        ctk.CTkLabel(stats_col, text=t('stats_section'),
                     font=("Consolas", 10, "bold"), text_color=ACCENT).pack(
            anchor="w", pady=(0, 8))

        self.card_found      = StatCard(stats_col, t('card_found'),      color=TEXT)
        self.card_downloaded = StatCard(stats_col, t('card_downloaded'), color=SUCCESS)
        self.card_errors     = StatCard(stats_col, t('card_errors'),     color=ERROR)
        self.card_skipped    = StatCard(stats_col, t('card_skipped'),    color=WARN)

        for c in [self.card_found, self.card_downloaded, self.card_errors, self.card_skipped]:
            c.pack(fill="x", pady=4)

        # Progress label below stats
        self.progress_lbl = ctk.CTkLabel(stats_col, text=t('progress_label_init'),
                                          font=("Consolas", 11), text_color=TEXT_DIM)
        self.progress_lbl.pack(anchor="w", pady=(12, 0))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_status(self, msg: str, color: str = TEXT_DIM):
        self.status_lbl.configure(text=msg, text_color=color)

    def _append_log(self, text: str):
        self.log_box.configure(state="normal")
        ts = time.strftime('%H:%M:%S')
        self.log_box.insert("end", f"[{ts}] {text}\n")
        self.log_box.configure(state="disabled")
        self.log_box.see("end")

    def _poll_log(self):
        for msg in self._log_queue:
            self._append_log(msg)
        self._log_queue.clear()
        self.after(80, self._poll_log)

    def _log(self, msg: str):
        self._log_queue.append(msg)

    def _update_progress(self, done: int, total: int):
        pct = (done / total * 100) if total else 0
        self.progress_var.set(pct / 100)
        self.progress_lbl.configure(text=t('progress_label', done=done, total=total))

        # Update stat cards
        if "Saved" in t('file_saved', filename='') or done > 0:
            self.card_downloaded.set(done)

    def _reset_stats(self):
        for card in [self.card_found, self.card_downloaded,
                     self.card_errors, self.card_skipped]:
            card.set(0)
        self.progress_var.set(0)
        self.progress_lbl.configure(text=t('progress_label_init'))

    # ── Actions ───────────────────────────────────────────────────────────────

    def _paste_url(self):
        try:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, self.clipboard_get())
        except Exception:
            pass

    def _browse_folder(self):
        d = filedialog.askdirectory(initialdir=self.folder_entry.get())
        if d:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, d)

    def _open_folder(self):
        folder = self.folder_entry.get()
        if not os.path.exists(folder):
            messagebox.showwarning(t('mb_warn_title'), t('mb_warn_no_folder'))
            return
        if os.name == "nt":
            os.startfile(folder)
        else:
            os.system(f'xdg-open "{folder}"')

    def _save_log(self):
        ts   = time.strftime('%Y%m%d_%H%M%S')
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=self.folder_entry.get(),
            initialfile=t('save_log_filename', timestamp=ts),
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.log_box.get("1.0", "end"))
            messagebox.showinfo(t('mb_info_title'), t('mb_info_log_saved', path=path))

    def _validate_url(self) -> str | None:
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning(t('mb_warn_title'), t('mb_warn_no_url'))
            return None
        if not is_valid_url(url):
            messagebox.showwarning(t('mb_warn_title'), t('mb_warn_invalid_url'))
            return None
        return url

    def _check_url(self):
        url = self._validate_url()
        if not url:
            return
        self._set_status(t('status_checking'), ACCENT)

        def _run():
            self._core.check_url(
                url,
                log_cb=self._log,
                done_cb=lambda imgs, vids: self.after(0, self._on_check_done, imgs, vids),
                error_cb=lambda msg: self.after(0, self._log, msg),
            )

        threading.Thread(target=_run, daemon=True).start()

    def _on_check_done(self, images: int, videos: int):
        if images == 0 and videos == 0:
            messagebox.showinfo(t('mb_info_title'), t('mb_info_check_none'))
            self._set_status(t('mb_info_check_none'), WARN)
        else:
            messagebox.showinfo(t('mb_info_title'),
                                t('mb_info_check_found', images=images, videos=videos))
            self._set_status(
                t('mb_info_check_found', images=images, videos=videos), SUCCESS)
        self.card_found.set(images + videos)

    def _start_download(self):
        url = self._validate_url()
        if not url:
            return

        folder = self.folder_entry.get()
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except Exception as e:
                messagebox.showerror(t('mb_error_title'),
                                     t('mb_err_create_folder', error=e))
                return

        self._reset_stats()
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

        self._is_downloading = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._set_status(t('status_fetching'), ACCENT)

        def _run():
            self._core.download(
                url            = url,
                base_folder    = folder,
                media_type     = self.media_type_var.get(),
                skip_existing  = self.skip_var.get(),
                max_workers    = self.threads_var.get(),
                sequential     = self.sequential_var.get(),
                log_cb         = self._log,
                progress_cb    = lambda d, tot: self.after(0, self._update_progress, d, tot),
                status_cb      = lambda msg: self.after(0, self._set_status, msg, ACCENT),
                done_cb        = lambda: self.after(0, self._on_done),
            )

        threading.Thread(target=_run, daemon=True).start()

    def _stop_download(self):
        self._core.request_stop()
        self._set_status(t('status_stopping'), WARN)
        self._log(t('log_stop_requested'))

    def _on_done(self):
        self._is_downloading = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

        if self._core.stop_requested:
            self._set_status(t('status_stopped'), WARN)
            self._log(t('log_stopped'))
        else:
            self._set_status(t('status_done'), SUCCESS)
            self._log(t('log_done'))
            messagebox.showinfo(t('mb_info_title'), t('mb_done'))


def main():
    app = MediaDownloaderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
