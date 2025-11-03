import re
import os
import requests
import time
import concurrent.futures
import threading
import webbrowser
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import random
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import scrolledtext
import urllib3
import warnings

warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)

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

class MediaDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Загрузчик медиафайлов 2ch / arhivach / 4chan")
        self.root.geometry("860x630")
        
        self.current_user_agent = None

        self.style = ttk.Style("cosmo")

        self.url_var = tk.StringVar()
        self.folder_var = tk.StringVar(
            value=os.path.join(os.path.dirname(os.path.abspath(__file__)), "Downloads")
        )
        
        self.skip_existing_var = tk.BooleanVar(value=False)
        self.threads_var = tk.IntVar(value=3)
        self.status_var = tk.StringVar(value="Готов к работе")
        self.media_type_var = tk.StringVar(value="all_videos")

        main_frame = ttk.Frame(root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self._create_url_section(main_frame)
        self._create_options_section(main_frame)
        self._create_progress_section(main_frame)
        self._create_log_section(main_frame)
        self._create_status_bar(root)

        self.is_downloading = False
        self.stop_requested = False

    def _create_url_section(self, parent):
        url_frame = ttk.Labelframe(parent, text="URL", padding=5)
        url_frame.pack(fill=tk.X, pady=5)

        ttk.Label(
            url_frame, text="Введите ссылку на тред 2ch.org, arhivach.vc или 4chan.org:"
        ).pack(anchor="w")

        url_entry_frame = ttk.Frame(url_frame)
        url_entry_frame.pack(fill=tk.X, pady=5)

        ttk.Entry(url_entry_frame, textvariable=self.url_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5)
        )
        ttk.Button(
            url_entry_frame, text="URL из буфера", command=self.paste_url
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            url_entry_frame, text="Проверить", command=self.check_url
        ).pack(side=tk.LEFT, padx=5)

    def paste_url(self):
        try:
            clipboard_text = self.root.clipboard_get()
            self.url_var.set(clipboard_text)
        except tk.TclError:
            pass

    def _create_options_section(self, parent):
        options_frame = ttk.Labelframe(parent, text="Настройки", padding=5)
        options_frame.pack(fill=tk.X, pady=5)

        media_frame = ttk.Frame(options_frame)
        media_frame.pack(fill=tk.X, pady=5)

        ttk.Label(media_frame, text="Тип медиафайлов:").pack(
            side=tk.LEFT, padx=(0, 10)
        )

        media_types = [
            ("Все медиафайлы", "all_media"),
            ("Все изображения", "all_images"),
            ("Все видео", "all_videos"),
            ("PNG", "png"),
            ("JPG", "jpg"),
            ("JPEG", "jpeg"),
            ("WEBP", "webp"),
            ("WEBM", "webm"),
            ("MP4", "mp4"),
        ]

        for i, (text, value) in enumerate(media_types):
            ttk.Radiobutton(
                media_frame,
                text=text,
                value=value,
                variable=self.media_type_var,
            ).pack(side=tk.LEFT, padx=5)

        folder_frame = ttk.Frame(options_frame)
        folder_frame.pack(fill=tk.X, pady=5)

        ttk.Label(folder_frame, text="Папка загрузок:").pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Entry(folder_frame, textvariable=self.folder_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5)
        )
        ttk.Button(
            folder_frame, text="Обзор", command=self.browse_folder
        ).pack(side=tk.LEFT)

        advanced_frame = ttk.Frame(options_frame)
        advanced_frame.pack(fill=tk.X, pady=5)

        ttk.Checkbutton(
            advanced_frame,
            text="Пропускать существующие файлы",
            variable=self.skip_existing_var,
        ).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(advanced_frame, text="Количество потоков (лучше больше 3 не ставить):").pack(
            side=tk.LEFT
        )
        ttk.Spinbox(
            advanced_frame,
            from_=1,
            to=20,
            width=5,
            textvariable=self.threads_var,
        ).pack(side=tk.LEFT, padx=5)

        actions_frame = ttk.Frame(options_frame)
        actions_frame.pack(fill=tk.X, pady=10)

        self.download_button = ttk.Button(
            actions_frame,
            text="Начать загрузку",
            style="primary.TButton",
            command=self.start_download,
        )
        self.download_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            actions_frame,
            text="Остановить",
            state=tk.DISABLED,
            command=self.stop_download,
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            actions_frame, text="Открыть папку", command=self.open_folder
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            actions_frame, text="Сохранить лог", command=self.save_log
        ).pack(side=tk.LEFT, padx=5)

    def _create_progress_section(self, parent):
        progress_frame = ttk.Labelframe(
            parent, text="Прогресс загрузки", padding=5
        )
        progress_frame.pack(fill=tk.X, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            mode="determinate",
            length=100,
        )
        self.progress_bar.pack(fill=tk.X, pady=5)

        self.progress_label = ttk.Label(progress_frame, text="0/0 файлов")
        self.progress_label.pack(anchor="w")

    def _create_log_section(self, parent):
        log_frame = ttk.Labelframe(parent, text="Лог загрузки", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, height=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

    def _create_status_bar(self, parent):
        status_bar = ttk.Frame(parent, relief=tk.SUNKEN, padding=(5, 2))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Label(status_bar, textvariable=self.status_var).pack(side=tk.LEFT)

        ttk.Label(status_bar, text="v0.0.2 | ").pack(side=tk.RIGHT)
        website_link = ttk.Label(
            status_bar,
            text="GitHub",
            foreground="blue",
            cursor="hand2"
        )
        website_link.pack(side=tk.RIGHT)
        website_link.bind(
            "<Button-1>",
            lambda e: webbrowser.open("https://github.com/Reborn0Holly/mediachdl"),
        )

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(
            tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n"
        )
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get())
        if folder:
            self.folder_var.set(folder)

    def open_folder(self):
        folder = self.folder_var.get()
        if os.path.exists(folder):
            if os.name == "nt":
                os.startfile(folder)
            elif os.name == "posix":
                os.system(f'xdg-open "{folder}"')
        else:
            messagebox.showwarning(
                "Предупреждение", "Указанная папка не существует"
            )

    def save_log(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=self.folder_var.get(),
            initialfile=f"download_log_{time.strftime('%Y%m%d_%H%M%S')}.txt",
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.log_text.get(1.0, tk.END))
            messagebox.showinfo("Информация", f"Лог сохранен в {file_path}")

    def check_url(self):
        url = self.url_var.get().strip()

        if not url:
            messagebox.showwarning("Предупреждение", "Введите URL")
            return

        if not (
            url.startswith("https://")
            and (
                "2ch.org" in url or 
                "arhivach.vc" in url or 
                "4chan.org" in url or 
                "boards.4chan.org" in url
            )
        ):
            messagebox.showwarning(
                "Предупреждение",
                "Неверный URL. Убедитесь, что ссылка относится к 2ch.org или arhivach.vc",
            )
            return

        self.status_var.set("Проверка URL...")
        self.root.update()

        threading.Thread(
            target=self._check_url_thread, args=(url,), daemon=True
        ).start()

    def _check_url_thread(self, url):
        try:
            image_exts = ["png", "jpg", "jpeg", "webp"]
            video_exts = ["mp4", "webm"]

            image_links = self.get_media_links(url, image_exts)
            video_links = self.get_media_links(url, video_exts)

            self.root.after(
                0,
                lambda: self._update_after_check(
                    url, image_links, video_links
                ),
            )

        except Exception as e:
            self.root.after(
                0, lambda: self.log(f"Ошибка при проверке URL: {e}")
            )
            self.root.after(
                0, lambda: self.status_var.set("Ошибка при проверке URL")
            )

    def _update_after_check(self, url, image_links, video_links):
        total_images = len(image_links)
        total_videos = len(video_links)

        self.log(f"Проверка URL: {url}")
        self.log(f"Найдено изображений: {total_images}")
        self.log(f"Найдено видео: {total_videos}")

        if total_images == 0 and total_videos == 0:
            messagebox.showinfo(
                "Информация",
                "Медиафайлы не найдены. Проверьте URL или выберите другой тред.",
            )
            self.status_var.set("Медиафайлы не найдены")
        else:
            messagebox.showinfo(
                "Информация",
                f"Найдено {total_images} изображений и {total_videos} видео.",
            )
            self.status_var.set(
                f"Готов к загрузке: {total_images} изображений, {total_videos} видео"
            )

    def start_download(self):
        url = self.url_var.get().strip()

        if not url:
            messagebox.showwarning("Предупреждение", "Введите URL")
            return

        if not (
            url.startswith("https://")
            and (
                "2ch.org" in url or 
                "arhivach.vc" in url or 
                "4chan.org" in url or 
                "boards.4chan.org" in url
            )
        ):
            messagebox.showwarning(
                "Предупреждение",
                "Неверный URL. Убедитесь, что ссылка относится к 2ch.org или arhivach.vc",
            )
            return

        folder = self.folder_var.get()
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except Exception as e:
                messagebox.showerror(
                    "Ошибка", f"Не удалось создать папку: {e}"
                )
                return

        self.download_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_downloading = True
        self.stop_requested = False

        threading.Thread(target=self._download_thread, daemon=True).start()

    def _get_thread_id(self, url):

        import re
        match = re.search(r"(?:res/|thread/)(\d+)", url)
        if match:
            return match.group(1)
        match = re.search(r"/thread/(\d+)", url)
        if match:
            return match.group(1)
        return "unknown"

    def _download_thread(self):
        try:
            url = self.url_var.get().strip()
            thread_folder = self.folder_var.get()
            skip_existing = self.skip_existing_var.get()
            max_workers = self.threads_var.get()
            media_type = self.media_type_var.get()

            self.current_user_agent = random.choice(USER_AGENTS)
            self.log(f"Начало загрузки с User-Agent: {self.current_user_agent}")

            image_exts = ["png", "jpg", "jpeg", "webp"]
            video_exts = ["mp4", "webm"]

            thread_id = self._get_thread_id(url)
            source = "4chan" if "4chan.org" in url else ("arhivach" if "arhivach.vc" in url else "2ch")
            self.log(f"Источник: {source}, Тред ID: {thread_id}")
            thread_folder = os.path.join(thread_folder, thread_id)
            if not os.path.exists(thread_folder):
                os.makedirs(thread_folder)

            if media_type == "all_images":
                media_links = self.get_media_links(url, image_exts)
                subfolder = "images"
            elif media_type == "all_videos":
                media_links = self.get_media_links(url, video_exts)
                subfolder = "videos"
            elif media_type == "all_media":
                image_links = self.get_media_links(url, image_exts)
                video_links = self.get_media_links(url, video_exts)

                self.root.after(
                    0,
                    lambda: self.log(
                        f"Найдено изображений: {len(image_links)}"
                    ),
                )
                self.root.after(
                    0, lambda: self.log(f"Найдено видео: {len(video_links)}")
                )

                if len(image_links) > 0:
                    self._download_files(
                        image_links,
                        thread_folder,
                        "images",
                        skip_existing,
                        max_workers,
                    )
                if len(video_links) > 0 and not self.stop_requested:
                    self._download_files(
                        video_links,
                        thread_folder,
                        "videos",
                        skip_existing,
                        max_workers,
                    )

                self.root.after(0, self._finalize_download)
                return
            else:
                media_links = self.get_media_links(url, [media_type])
                subfolder = media_type

            self.root.after(
                0,
                lambda: self.log(
                    f"Найдено файлов {subfolder}: {len(media_links)}"
                ),
            )

            if len(media_links) > 0:
                self._download_files(
                    media_links,
                    thread_folder,
                    subfolder,
                    skip_existing,
                    max_workers,
                )
            else:
                self.root.after(
                    0,
                    lambda: self.log(
                        f"Файлы с указанным расширением не найдены"
                    ),
                )

            self.root.after(0, self._finalize_download)

        except Exception as e:
            self.root.after(0, lambda: self.log(f"Ошибка при загрузке: {e}"))
            self.root.after(0, self._finalize_download)

    def _finalize_download(self):
        self.is_downloading = False
        self.download_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        if self.stop_requested:
            self.status_var.set("Загрузка остановлена пользователем")
            self.log("Загрузка остановлена пользователем")
        else:
            self.status_var.set("Загрузка завершена!")
            self.log("Загрузка завершена!")
            messagebox.showinfo("Информация", "Загрузка завершена!")

    def stop_download(self):
        if self.is_downloading:
            self.stop_requested = True
            self.status_var.set("Остановка загрузки...")
            self.log("Запрошена остановка загрузки...")

    def get_media_links(self, url, media_types):
        try:
            self.root.after(
                0, lambda: self.status_var.set("Получение списка файлов...")
            )
            self.root.after(
                0,
                lambda: self.log(
                    f"Получение ссылок для {', '.join(media_types)}..."
                ),
            )

            headers = {"User-Agent": random.choice(USER_AGENTS)}
            response = requests.get(url, headers=headers, verify=False)
            if response.status_code != 200:
                self.root.after(
                    0,
                    lambda: self.log(
                        f"Ошибка при загрузке страницы: {response.status_code}"
                    ),
                )
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            media_links = set()
            base_url = "https://i.4cdn.org" if "4chan.org" in url else None
            if "4chan.org" in url:
                for thumb in soup.find_all("a", class_="fileThumb"):
                    href = thumb.get("href")
                    if href and any(href.endswith(f".{ext}") for ext in media_types):
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
                        full_url = urljoin(url, href)
                        media_links.add(full_url)

                for file_elem in soup.find_all(class_="file"):
                    for a_tag in file_elem.find_all("a", href=True):
                        href = a_tag["href"]
                        if any(href.endswith(f".{ext}") for ext in media_types):
                           full_url = urljoin(url, href)
                           media_links.add(full_url)

            return list(media_links)

        except Exception as e:
            self.root.after(0, lambda err=e: self.log(f"Ошибка при получении ссылок: {err}"))
            return []

    def _download_files(self, links, thread_folder, subfolder, skip_existing, max_workers):
        if not links:
            return

        folder = os.path.join(thread_folder, subfolder)
        if not os.path.exists(folder):
            os.makedirs(folder)

        total_files = len(links)
        completed_files = 0
        self.root.after(0, lambda: self.progress_var.set(0))
        self.root.after(
            0,
            lambda: self.progress_label.config(text=f"0/{total_files} файлов"),
        )

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers
        ) as executor:
            future_to_link = {}

            for link in links:
                if self.stop_requested:
                    break

                future = executor.submit(
                    self._download_single_file, link, folder, skip_existing
                )
                future_to_link[future] = link

            for future in concurrent.futures.as_completed(future_to_link):
                if self.stop_requested:
                    executor.shutdown(wait=False)
                    break

                link = future_to_link[future]
                try:
                    result = future.result()
                    self.root.after(
                        0, lambda message=result: self.log(message)
                    )

                    completed_files += 1
                    progress_percentage = (completed_files / total_files) * 100

                    self.root.after(
                        0,
                        lambda p=progress_percentage: self.progress_var.set(p),
                    )
                    self.root.after(
                        0,
                        lambda c=completed_files, t=total_files: self.progress_label.config(
                            text=f"{c}/{t} файлов"
                        ),
                    )
                    self.root.after(
                        0,
                        lambda c=completed_files, t=total_files: self.status_var.set(
                            f"Загружено {c} из {t} файлов"
                        ),
                    )

                except Exception as e:
                    self.root.after(
                        0,
                        lambda l=link, e=e: self.log(
                            f"Ошибка при загрузке {l}: {e}"
                        ),
                    )

    def _download_single_file(self, link, folder, skip_existing, max_retries=3):
        filename = link.split("/")[-1]
        file_path = os.path.join(folder, filename)

        if skip_existing and os.path.exists(file_path):
            return f"Файл {filename} уже существует, пропускаю"

        if not skip_existing and os.path.exists(file_path):
            base_name, ext = os.path.splitext(filename)
            new_filename = f"{base_name}_copy{ext}"
            file_path = os.path.join(folder, new_filename)
            counter = 1

            while os.path.exists(file_path):
                new_filename = f"{base_name}_copy{counter}{ext}"
                file_path = os.path.join(folder, new_filename)
                counter += 1
            filename = new_filename 

        retries = 0
        while retries < max_retries:
            if self.stop_requested:
                return f"Загрузка {filename} отменена"

            try:
                headers = {"User-Agent": random.choice(USER_AGENTS)}
                response = requests.get(link, stream=True, timeout=10, headers=headers, verify=False)
                if response.status_code == 200:
                    with open(file_path, "wb") as file:
                        for chunk in response.iter_content(1024):
                            if self.stop_requested:
                                file.close()
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                return f"Загрузка {filename} отменена"

                            if chunk:
                                file.write(chunk)
                    return f"Сохранено: {filename}"
                else:
                    retries += 1
                    time.sleep(2)
            except Exception as e:
                retries += 1
                time.sleep(2)

        return f"Не удалось загрузить {filename} после {max_retries} попыток"

def main():
    root = ttk.Window(themename="cosmo")
    app = MediaDownloaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
