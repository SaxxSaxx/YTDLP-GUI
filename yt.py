# YouTube Downloader GUI using yt-dlp
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import os
import json
from datetime import datetime
import requests
from PIL import Image, ImageTk
from io import BytesIO
import queue
import time

class DownloadQueue:
    def __init__(self):
        self.queue = queue.Queue()
        self.history = []
        self.max_history = 50

    def add(self, item):
        self.queue.put(item)
        self.history.append({
            'url': item['url'],
            'format': item['format'],
            'quality': item['quality'],
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'status': 'Queued'
        })
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def get(self):
        return self.queue.get()

    def empty(self):
        return self.queue.empty()

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader - Powered by yt-dlp")
        self.root.geometry("1000x700")
        
        # Variables
        self.url_var = tk.StringVar()
        self.output_dir = tk.StringVar(value=os.getcwd())
        self.format_var = tk.StringVar(value="bestvideo+bestaudio")
        self.quality_var = tk.StringVar(value="best")
        self.subtitles_var = tk.BooleanVar(value=False)
        self.playlist_var = tk.BooleanVar(value=False)
        self.dark_mode_var = tk.BooleanVar(value=True)  # Dark mode by default
        self.audio_only_var = tk.BooleanVar(value=False)
        self.filename_template_var = tk.StringVar(value="%(title)s.%(ext)s")
        
        # Download queue
        self.download_queue = DownloadQueue()
        self.current_download = None
        
        # Style configuration
        self.style = ttk.Style()
        self.configure_styles()
        
        self.build_ui()
        self.apply_theme()

    def configure_styles(self):
        # Configure common styles
        self.style.configure("TButton", padding=6, font=('Helvetica', 10))
        self.style.configure("TLabel", padding=6, font=('Helvetica', 10))
        self.style.configure("TLabelframe", padding=10)
        self.style.configure("TLabelframe.Label", font=('Helvetica', 10, 'bold'))
        self.style.configure("Treeview", font=('Helvetica', 9))
        self.style.configure("Treeview.Heading", font=('Helvetica', 9, 'bold'))
        
        # Custom styles
        self.style.configure("Theme.TButton", padding=8)
        self.style.configure("Download.TButton", padding=10, font=('Helvetica', 11, 'bold'))
        self.style.configure("Info.TLabel", font=('Helvetica', 9))

    def build_ui(self):
        # Main container
        self.main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left panel
        left_panel = ttk.Frame(self.main_container)
        self.main_container.add(left_panel, weight=1)
        
        # Right panel
        right_panel = ttk.Frame(self.main_container)
        self.main_container.add(right_panel, weight=1)
        
        # Left panel content
        self.build_left_panel(left_panel)
        
        # Right panel content
        self.build_right_panel(right_panel)

    def build_left_panel(self, parent):
        # Theme toggle button
        theme_frame = ttk.Frame(parent)
        theme_frame.pack(fill=tk.X, pady=(0, 10))
        self.theme_btn = ttk.Button(theme_frame, text="🌙", style="Theme.TButton", 
                                  command=self.toggle_theme, width=3)
        self.theme_btn.pack(side=tk.RIGHT)
        
        # URL input
        url_frame = ttk.LabelFrame(parent, text="Video Information", padding=10)
        url_frame.pack(fill=tk.X, pady=5)
        
        url_container = ttk.Frame(url_frame)
        url_container.pack(fill=tk.X, pady=5)
        
        ttk.Label(url_container, text="Video URL:").pack(side=tk.LEFT, padx=5)
        url_entry = ttk.Entry(url_container, textvariable=self.url_var, width=60)
        url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(url_container, text="Fetch Info", command=self.fetch_video_info).pack(side=tk.LEFT, padx=5)
        
        # Thumbnail preview
        self.thumbnail_label = ttk.Label(parent)
        self.thumbnail_label.pack(pady=10)
        
        # Video info
        self.info_text = tk.Text(parent, height=6, wrap=tk.WORD)
        self.info_text.pack(fill=tk.X, pady=5)
        
        # Format and Quality selection
        format_frame = ttk.LabelFrame(parent, text="Download Options", padding=10)
        format_frame.pack(fill=tk.X, pady=5)
        
        # Format selection
        format_container = ttk.Frame(format_frame)
        format_container.pack(fill=tk.X, pady=5)
        
        ttk.Label(format_container, text="Format:").pack(side=tk.LEFT, padx=5)
        format_combo = ttk.Combobox(format_container, textvariable=self.format_var, width=30)
        format_combo['values'] = (
            'bestvideo+bestaudio',
            'best',
            'worst',
            'bestvideo',
            'bestaudio',
            'mp4',
            'webm',
            'mp3',
            'm4a'
        )
        format_combo.pack(side=tk.LEFT, padx=5)
        
        # Quality selection
        quality_container = ttk.Frame(format_frame)
        quality_container.pack(fill=tk.X, pady=5)
        
        ttk.Label(quality_container, text="Quality:").pack(side=tk.LEFT, padx=5)
        quality_combo = ttk.Combobox(quality_container, textvariable=self.quality_var, width=30)
        quality_combo['values'] = ('best', 'worst', '720p', '1080p', '480p', '360p')
        quality_combo.pack(side=tk.LEFT, padx=5)
        
        # Options frame
        options_frame = ttk.Frame(format_frame)
        options_frame.pack(fill=tk.X, pady=5)
        
        ttk.Checkbutton(options_frame, text="Audio Only", variable=self.audio_only_var, 
                       command=self.toggle_audio_only).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(options_frame, text="Download Subtitles", 
                       variable=self.subtitles_var).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(options_frame, text="Download Playlist", 
                       variable=self.playlist_var).pack(side=tk.LEFT, padx=5)
        
        # Output directory
        output_frame = ttk.LabelFrame(parent, text="Output", padding=10)
        output_frame.pack(fill=tk.X, pady=5)
        
        output_container = ttk.Frame(output_frame)
        output_container.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_container, text="Save To:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(output_container, textvariable=self.output_dir).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(output_container, text="Browse", command=self.browse_dir).pack(side=tk.LEFT, padx=5)
        
        # Download button
        self.download_btn = ttk.Button(parent, text="Add to Queue", style="Download.TButton", 
                                     command=self.add_to_queue)
        self.download_btn.pack(pady=10)

    def build_right_panel(self, parent):
        # Progress section
        progress_frame = ttk.LabelFrame(parent, text="Current Download", padding=10)
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=300)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(progress_frame, text="Ready", style="Info.TLabel")
        self.status_label.pack(fill=tk.X)
        
        self.speed_label = ttk.Label(progress_frame, text="", style="Info.TLabel")
        self.speed_label.pack(fill=tk.X)
        
        # Download history
        history_frame = ttk.LabelFrame(parent, text="Download History", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create Treeview
        columns = ('url', 'format', 'quality', 'timestamp', 'status')
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=10)
        
        # Define headings
        self.history_tree.heading('url', text='URL')
        self.history_tree.heading('format', text='Format')
        self.history_tree.heading('quality', text='Quality')
        self.history_tree.heading('timestamp', text='Time')
        self.history_tree.heading('status', text='Status')
        
        # Define columns
        self.history_tree.column('url', width=200)
        self.history_tree.column('format', width=100)
        self.history_tree.column('quality', width=80)
        self.history_tree.column('timestamp', width=150)
        self.history_tree.column('status', width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def toggle_theme(self):
        self.dark_mode_var.set(not self.dark_mode_var.get())
        self.apply_theme()
        self.theme_btn.configure(text="☀️" if not self.dark_mode_var.get() else "🌙")

    def toggle_audio_only(self):
        if self.audio_only_var.get():
            self.format_var.set('bestaudio')
            self.quality_var.set('best')
        else:
            self.format_var.set('bestvideo+bestaudio')
            self.quality_var.set('best')

    def fetch_video_info(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a valid URL.")
            return

        try:
            cmd = [
                "yt-dlp",
                "--dump-json",
                "--no-playlist",
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                info = json.loads(result.stdout)
                
                # Update info text
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, f"Title: {info.get('title', 'N/A')}\n")
                self.info_text.insert(tk.END, f"Duration: {info.get('duration_string', 'N/A')}\n")
                self.info_text.insert(tk.END, f"Uploader: {info.get('uploader', 'N/A')}\n")
                self.info_text.insert(tk.END, f"Views: {info.get('view_count', 'N/A')}\n")
                
                # Fetch and display thumbnail
                if 'thumbnail' in info:
                    response = requests.get(info['thumbnail'])
                    img = Image.open(BytesIO(response.content))
                    img = img.resize((320, 180), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.thumbnail_label.configure(image=photo)
                    self.thumbnail_label.image = photo
            else:
                messagebox.showerror("Error", "Failed to fetch video information.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def add_to_queue(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a valid URL.")
            return

        download_item = {
            'url': url,
            'format': self.format_var.get(),
            'quality': self.quality_var.get(),
            'output_dir': self.output_dir.get(),
            'subtitles': self.subtitles_var.get(),
            'playlist': self.playlist_var.get(),
            'audio_only': self.audio_only_var.get(),
            'filename_template': self.filename_template_var.get()
        }
        
        self.download_queue.add(download_item)
        self.update_history_display()

    def process_queue(self):
        while True:
            if not self.download_queue.empty():
                self.current_download = self.download_queue.get()
                self.download_video(self.current_download)
            time.sleep(1)

    def update_history_display(self):
        for item in self.download_queue.history:
            self.history_tree.insert('', 'end', values=(
                item['url'],
                item['format'],
                item['quality'],
                item['timestamp'],
                item['status']
            ))

    def download_video(self, download_item):
        self.download_btn.config(state=tk.DISABLED)
        self.progress_bar['value'] = 0
        self.status_label.config(text="Preparing download...")
        self.speed_label.config(text="")

        try:
            cmd = [
                "yt-dlp",
                "-f", f"{download_item['format']}[height<={download_item['quality'].replace('p', '')}]" 
                      if download_item['quality'] != 'best' and download_item['quality'] != 'worst' 
                      else download_item['format'],
                "-o", os.path.join(download_item['output_dir'], download_item['filename_template']),
                "--newline",
                "--progress",
                "--no-colors"
            ]

            if download_item['subtitles']:
                cmd.extend(["--write-sub", "--sub-lang", "en"])
            
            if download_item['playlist']:
                cmd.append("--yes-playlist")
            else:
                cmd.append("--no-playlist")

            process = subprocess.Popen(
                cmd + [download_item['url']],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    try:
                        if '%' in output:
                            percentage = float(output.split('%')[0].strip())
                            self.progress_bar['value'] = percentage
                            self.status_label.config(text=f"Downloading... {percentage:.1f}%")
                    except:
                        pass

            if process.returncode == 0:
                self.status_label.config(text="✅ Download complete")
                self.progress_bar['value'] = 100
                self.update_download_status(download_item['url'], "Completed")
            else:
                error = process.stderr.read()
                self.status_label.config(text="❌ Download failed")
                self.update_download_status(download_item['url'], "Failed")
                messagebox.showerror("Error", f"Download failed: {error}")

        except Exception as e:
            self.status_label.config(text="❌ Download failed")
            self.update_download_status(download_item['url'], "Failed")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self.download_btn.config(state=tk.NORMAL)
            self.current_download = None

    def update_download_status(self, url, status):
        for item in self.download_queue.history:
            if item['url'] == url:
                item['status'] = status
                break
        self.update_history_display()

    def apply_theme(self):
        if self.dark_mode_var.get():
            # Dark theme colors
            bg_color = '#1e1e1e'
            fg_color = '#ffffff'
            accent_color = '#2d2d2d'
            text_color = '#e0e0e0'
            
            self.root.configure(bg=bg_color)
            self.style.configure("TFrame", background=bg_color)
            self.style.configure("TLabel", background=bg_color, foreground=text_color)
            self.style.configure("TLabelframe", background=bg_color, foreground=text_color)
            self.style.configure("TLabelframe.Label", background=bg_color, foreground=text_color)
            self.style.configure("Treeview", background=accent_color, foreground=text_color, fieldbackground=accent_color)
            self.style.configure("Treeview.Heading", background=bg_color, foreground=text_color)
            self.style.map("Treeview", background=[("selected", "#404040")])
            self.info_text.configure(bg=accent_color, fg=text_color, insertbackground=text_color)
            self.style.configure("TButton", background=accent_color, foreground=text_color)
            self.style.map("TButton", background=[("active", "#404040")])
        else:
            # Light theme colors
            bg_color = '#f0f0f0'
            fg_color = '#000000'
            accent_color = '#ffffff'
            text_color = '#000000'
            
            self.root.configure(bg=bg_color)
            self.style.configure("TFrame", background=bg_color)
            self.style.configure("TLabel", background=bg_color, foreground=text_color)
            self.style.configure("TLabelframe", background=bg_color, foreground=text_color)
            self.style.configure("TLabelframe.Label", background=bg_color, foreground=text_color)
            self.style.configure("Treeview", background=accent_color, foreground=text_color, fieldbackground=accent_color)
            self.style.configure("Treeview.Heading", background=bg_color, foreground=text_color)
            self.style.map("Treeview", background=[("selected", "#e0e0e0")])
            self.info_text.configure(bg=accent_color, fg=text_color, insertbackground=text_color)
            self.style.configure("TButton", background=accent_color, foreground=text_color)
            self.style.map("TButton", background=[("active", "#e0e0e0")])

    def browse_dir(self):
        selected = filedialog.askdirectory()
        if selected:
            self.output_dir.set(selected)

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()
