import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
    QMessageBox, QProgressBar, QFileDialog
)
from PyQt5.QtCore import QThread, pyqtSignal
import yt_dlp
import re

class DownloadThread(QThread):
    progress = pyqtSignal(int)  # Signal to update the progress bar
    finished = pyqtSignal(str)  # Signal when download finishes, with message for success or error

    def __init__(self, url, ffmpeg_path, downloads_folder):
        super().__init__()
        self.url = url
        self.ffmpeg_path = ffmpeg_path
        self.downloads_folder = downloads_folder

    def run(self):
        # yt-dlp options with progress hook
        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best',  # Highest resolution up to 1080p
            'outtmpl': os.path.join(self.downloads_folder, '%(title)s.%(ext)s'),  # Output path
            'merge_output_format': 'mp4',  # Merge audio and video into mp4
            'ffmpeg_location': self.ffmpeg_path,  # Specify ffmpeg path
            'progress_hooks': [self.progress_hook],  # Hook for download progress
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            self.finished.emit("Video downloaded successfully!")
        except Exception as e:
            self.finished.emit(f"An error occurred: {str(e)}")

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            # Extract percentage completed, removing ANSI codes
            percentage_str = d.get('_percent_str', '0%')
            percentage_str = re.sub(r'\x1b\[[0-9;]*m', '', percentage_str)  # Remove ANSI escape sequences
            try:
                percentage = int(float(percentage_str.strip('%')))  # Convert to integer
                self.progress.emit(percentage)  # Emit progress signal
            except ValueError:
                pass


class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")  # Default folder
        self.initUI()

    def initUI(self):
        self.setWindowTitle("YouTube Video Downloader (yt-dlp)")
        self.setGeometry(400, 200, 450, 350)
        
        layout = QVBoxLayout()

        # Label and input field for YouTube URL
        self.label = QLabel("Enter YouTube URL:")
        layout.addWidget(self.label)
        
        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        layout.addWidget(self.url_input)

        # Directory selection
        self.dir_label = QLabel(f"Download Directory: {self.downloads_folder}")
        self.dir_label.setWordWrap(True)
        layout.addWidget(self.dir_label)

        self.dir_button = QPushButton("Choose Download Directory", self)
        self.dir_button.clicked.connect(self.choose_directory)
        layout.addWidget(self.dir_button)
        
        # Progress bar for download progress
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Download button
        self.download_button = QPushButton("Download", self)
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)

        self.setLayout(layout)

        # Apply stylesheet for better design
        self.setStyleSheet("""
            QWidget {
                font-family: 'Arial';
                font-size: 14px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
                background-color: #fff;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005ea2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 3px;
            }
            QLabel {
                color: #333;
            }
        """)

    def choose_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Directory", self.downloads_folder)
        if folder:
            self.downloads_folder = folder
            self.dir_label.setText(f"Download Directory: {self.downloads_folder}")

    def start_download(self):
        url = self.url_input.text().strip()
        
        if not (url.startswith("https://www.youtube.com/") or url.startswith("https://youtu.be/")):
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid YouTube URL.")
            return
        
        # Specify FFmpeg location (customize this path if needed)
        ffmpeg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg.exe')
        # Option: Specify a custom path to ffmpeg.exe
        # ffmpeg_path = r"C:\Path\To\Your\FFmpeg\ffmpeg.exe"

        # Log the expected FFmpeg path for debugging
        print(f"Looking for FFmpeg at: {ffmpeg_path}")

        # Verify FFmpeg exists
        if not os.path.exists(ffmpeg_path):
            QMessageBox.critical(
                self, 
                "Error", 
                f"FFmpeg not found at: {ffmpeg_path}\nPlease place ffmpeg.exe in the same directory as this program or specify a custom path in the code."
            )
            return

        # Disable the download button to prevent multiple clicks
        self.download_button.setEnabled(False)

        # Create and start the download thread
        self.download_thread = DownloadThread(url, ffmpeg_path, self.downloads_folder)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)  # Update progress bar

    def download_finished(self, message):
        QMessageBox.information(self, "Download Status", message)
        self.progress_bar.setValue(0)  # Reset progress bar after download
        self.download_button.setEnabled(True)  # Re-enable the download button


# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    downloader = YouTubeDownloader()
    downloader.show()
    sys.exit(app.exec_())