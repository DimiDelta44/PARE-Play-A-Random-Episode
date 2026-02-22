import os
import random
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import requests
import subprocess
import json
import sys
from PIL import Image, ImageTk

# Determine base directory for assets
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_asset_path(filename):
    """Get absolute path to asset"""
    return os.path.join(BASE_DIR, 'assets', filename)

# Config file
CONFIG_FILE = "config.json"

class Config:
    """Manage application configuration"""
    def __init__(self):
        self.series_folder = ""
        self.tvdb_api_key = ""
        self.tvdb_series_id = ""
        self.series_name = ""
        self.load()
    
    def load(self):
        """Load config from file"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.series_folder = data.get('series_folder', '')
                    self.tvdb_api_key = data.get('tvdb_api_key', '')
                    self.tvdb_series_id = data.get('tvdb_series_id', '')
                    self.series_name = data.get('series_name', '')
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def save(self):
        """Save config to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({
                    'series_folder': self.series_folder,
                    'tvdb_api_key': self.tvdb_api_key,
                    'tvdb_series_id': self.tvdb_series_id,
                    'series_name': self.series_name
                }, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def is_configured(self):
        """Check if app is configured"""
        return bool(self.series_folder and os.path.exists(self.series_folder))

def find_vlc():
    """Find VLC installation directory"""
    possible_paths = [
        r"C:\Program Files\VideoLAN\VLC",
        r"C:\Program Files (x86)\VideoLAN\VLC",
        r"D:\Program Files\VideoLAN\VLC",
        r"D:\Programs\VLC",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

# Set up VLC environment
vlc_dir = find_vlc()
if vlc_dir and sys.platform.startswith('win'):
    os.environ['VLC_PLUGIN_PATH'] = os.path.join(vlc_dir, 'plugins')
    if hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(vlc_dir)
        except Exception as e:
            print(f"Error adding DLL directory: {e}")

try:
    import vlc
    VLC_AVAILABLE = True
    print("✓ VLC Python bindings loaded successfully")
except ImportError as e:
    VLC_AVAILABLE = False
    print(f"⚠ VLC Import Error: {e}")
    
    # Check for architecture mismatch
    import struct
    python_arch = 64 if sys.maxsize > 2**32 else 32
    print(f"  Python Architecture: {python_arch}-bit")
    
    if vlc_dir:
        if "x86" in vlc_dir and python_arch == 64:
            print("  ⚠ CRTICAL: Architecture Mismatch!")
            print("  You are using 64-bit Python but 32-bit VLC (in Program Files x86)")
            print("  To fix embedding: Install VLC 64-bit from videolan.org")
except Exception as e:
    VLC_AVAILABLE = False
    print(f"⚠ Unexpected VLC error: {e}")

def get_all_episodes(folder):
    """Get all video files from folder"""
    video_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.m4v', '.wmv', '.flv')
    episodes = []
    
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(video_extensions):
                episodes.append(os.path.join(root, file))
    
    return episodes

def parse_episode_info(filename):
    """Extract season and episode number from filename"""
    patterns = [
        r'[Ss](\d+)[Ee](\d+)',  # S01E01
        r'(\d+)x(\d+)',          # 1x01
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            return int(match.group(1)), int(match.group(2))
    
    return None, None

def get_tvdb_token(api_key):
    """Get TVDB authentication token"""
    try:
        url = "https://api4.thetvdb.com/v4/login"
        headers = {"Content-Type": "application/json"}
        data = {"apikey": api_key}
        response = requests.post(url, json=data, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return response.json()['data']['token']
    except Exception as e:
        print(f"Error getting TVDB token: {e}")
    return None

def fetch_episode_info(api_key, series_id, season, episode):
    """Fetch episode info from TVDB"""
    if not api_key or not series_id:
        return {
            'title': f'Season {season}, Episode {episode}',
            'description': 'Configure TVDB API key in settings to get episode info.',
            'air_date': 'Unknown',
            'rating': 'N/A'
        }
    
    token = get_tvdb_token(api_key)
    if not token:
        return {
            'title': f'Season {season}, Episode {episode}',
            'description': 'Could not authenticate with TVDB.',
            'air_date': 'Unknown',
            'rating': 'N/A'
        }
    
    try:
        url = f"https://api4.thetvdb.com/v4/series/{series_id}/episodes/default"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"season": season, "episodeNumber": episode}
        
        response = requests.get(url, headers=headers, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']['episodes']) > 0:
                ep_data = data['data']['episodes'][0]
                return {
                    'title': ep_data.get('name', 'Unknown'),
                    'description': ep_data.get('overview', 'No description available.'),
                    'air_date': ep_data.get('aired', 'Unknown'),
                    'rating': ep_data.get('averageRating', 'N/A')
                }
    except Exception as e:
        print(f"Error fetching TVDB data: {e}")
    
    return {
        'title': f'Season {season}, Episode {episode}',
        'description': 'Could not fetch episode information.',
        'air_date': 'Unknown',
        'rating': 'N/A'
    }

class SettingsWindow:
    """Settings configuration window"""
    def __init__(self, parent, config, on_save):
        self.config = config
        self.on_save = on_save
        
        self.window = tk.Toplevel(parent)
        self.window.title("PARE Settings")
        self.window.geometry("600x400")
        self.window.configure(bg='#2b2b2b')
        self.window.transient(parent)
        self.window.grab_set()
        
        # Set window icon
        try:
            icon_path = get_asset_path('logo_solid.png')
            if os.path.exists(icon_path):
                self.icon_img = ImageTk.PhotoImage(file=icon_path)
                self.window.iconphoto(False, self.icon_img)
        except:
            pass
        
        self.build_ui()
    
    def build_ui(self):
        """Build settings UI"""
        # Title
        tk.Label(
            self.window,
            text="⚙️ Settings",
            font=('Arial', 20, 'bold'),
            bg='#2b2b2b',
            fg='#00C8FF'
        ).pack(pady=20)
        
        # Form frame
        form = tk.Frame(self.window, bg='#2b2b2b')
        form.pack(padx=30, fill='both', expand=True)
        
        # Series name
        tk.Label(form, text="Series Name:", bg='#2b2b2b', fg='#FFFFFF', font=('Arial', 11)).grid(row=0, column=0, sticky='w', pady=10)
        self.series_name_entry = tk.Entry(form, font=('Arial', 11), width=40)
        self.series_name_entry.insert(0, self.config.series_name)
        self.series_name_entry.grid(row=0, column=1, pady=10, padx=10)
        
        # Series folder
        tk.Label(form, text="Series Folder:", bg='#2b2b2b', fg='#FFFFFF', font=('Arial', 11)).grid(row=1, column=0, sticky='w', pady=10)
        folder_frame = tk.Frame(form, bg='#2b2b2b')
        folder_frame.grid(row=1, column=1, pady=10, padx=10, sticky='ew')
        
        self.folder_entry = tk.Entry(folder_frame, font=('Arial', 10), width=30)
        self.folder_entry.insert(0, self.config.series_folder)
        self.folder_entry.pack(side='left', fill='x', expand=True)
        
        tk.Button(
            folder_frame,
            text="Browse",
            command=self.browse_folder,
            bg='#00C8FF',
            fg='#000000',
            relief='flat'
        ).pack(side='left', padx=5)
        
        # TVDB API Key
        tk.Label(form, text="TVDB API Key:", bg='#2b2b2b', fg='#FFFFFF', font=('Arial', 11)).grid(row=2, column=0, sticky='w', pady=10)
        self.api_key_entry = tk.Entry(form, font=('Arial', 11), width=40)
        self.api_key_entry.insert(0, self.config.tvdb_api_key)
        self.api_key_entry.grid(row=2, column=1, pady=10, padx=10)
        
        # TVDB Series ID
        tk.Label(form, text="TVDB Series ID:", bg='#2b2b2b', fg='#FFFFFF', font=('Arial', 11)).grid(row=3, column=0, sticky='w', pady=10)
        self.series_id_entry = tk.Entry(form, font=('Arial', 11), width=40)
        self.series_id_entry.insert(0, self.config.tvdb_series_id)
        self.series_id_entry.grid(row=3, column=1, pady=10, padx=10)
        
        # Help text
        help_text = tk.Label(
            form,
            text="Get free TVDB API key at: https://thetvdb.com/api-information\nFind Series ID on TheTVDB website",
            bg='#2b2b2b',
            fg='#808080',
            font=('Arial', 9),
            justify='left'
        )
        help_text.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Buttons
        btn_frame = tk.Frame(self.window, bg='#2b2b2b')
        btn_frame.pack(pady=20)
        
        tk.Button(
            btn_frame,
            text="Save",
            command=self.save,
            font=('Arial', 12),
            bg='#32DC64',
            fg='#000000',
            padx=30,
            pady=10,
            relief='flat'
        ).pack(side='left', padx=10)
        
        tk.Button(
            btn_frame,
            text="Cancel",
            command=self.window.destroy,
            font=('Arial', 12),
            bg='#DC3232',
            fg='#FFFFFF',
            padx=30,
            pady=10,
            relief='flat'
        ).pack(side='left', padx=10)
    
    def browse_folder(self):
        """Browse for series folder"""
        folder = filedialog.askdirectory(title="Select TV Series Folder")
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
    
    def save(self):
        """Save settings"""
        self.config.series_name = self.series_name_entry.get().strip()
        self.config.series_folder = self.folder_entry.get().strip()
        self.config.tvdb_api_key = self.api_key_entry.get().strip()
        self.config.tvdb_series_id = self.series_id_entry.get().strip()
        
        if not self.config.series_folder:
            messagebox.showerror("Error", "Please select a series folder")
            return
        
        if not os.path.exists(self.config.series_folder):
            messagebox.showerror("Error", "Series folder does not exist")
            return
        
        self.config.save()
        self.on_save()
        self.window.destroy()
        messagebox.showinfo("Success", "Settings saved successfully!")

class PlayerWindow:
    """Video player window"""
    def __init__(self, parent, episode_path, season, episode, config, on_next=None):
        self.episode_path = episode_path
        self.season = season
        self.episode = episode
        self.config = config
        self.on_next = on_next
        self.is_seeking = False
        self.is_fullscreen = False
        
        self.window = tk.Toplevel(parent)
        self.window.bind("<Escape>", self.exit_fullscreen)
        self.window.title(f"PARE - {config.series_name or 'Playing Episode'}")
        self.window.geometry("1400x900")
        self.window.configure(bg='#1a1a1f')
        
        # Set window icon
        try:
            icon_path = get_asset_path('logo_solid.png')
            if os.path.exists(icon_path):
                self.icon_img = ImageTk.PhotoImage(file=icon_path)
                self.window.iconphoto(False, self.icon_img)
        except:
            pass
        
        if VLC_AVAILABLE:
            self.instance = vlc.Instance('--no-xlib')
            self.player = self.instance.media_player_new()
        else:
            self.instance = None
            self.player = None
        
        self.build_ui()
        self.load_video()
    
    def build_ui(self):
        """Build player UI"""
        # Info panel (left)
        info_panel = tk.Frame(self.window, bg='#2b2b2b', width=400)
        info_panel.pack(side='left', fill='y', padx=10, pady=10)
        info_panel.pack_propagate(False)
        self.info_panel = info_panel
        
        # Series title
        tk.Label(
            info_panel,
            text=f"📺 {self.config.series_name or 'TV Series'}",
            font=('Arial', 18, 'bold'),
            bg='#2b2b2b',
            fg='#00C8FF'
        ).pack(pady=20)
        
        # Fetch episode info
        if self.season and self.episode:
            info = fetch_episode_info(
                self.config.tvdb_api_key,
                self.config.tvdb_series_id,
                self.season,
                self.episode
            )
            
            tk.Label(
                info_panel,
                text=f"S{self.season:02d}E{self.episode:02d}",
                font=('Arial', 14),
                bg='#2b2b2b',
                fg='#808080'
            ).pack(pady=5)
            
            tk.Label(
                info_panel,
                text=info['title'],
                font=('Arial', 16, 'bold'),
                bg='#2b2b2b',
                fg='#FFFFFF',
                wraplength=360
            ).pack(pady=10)
            
            tk.Label(
                info_panel,
                text=f"📅 {info['air_date']}  |  ⭐ {info['rating']}/10",
                font=('Arial', 11),
                bg='#2b2b2b',
                fg='#00C8FF'
            ).pack(pady=5)
            
            tk.Label(
                info_panel,
                text="Synopsis:",
                font=('Arial', 12, 'bold'),
                bg='#2b2b2b',
                fg='#FFFFFF'
            ).pack(pady=(20, 10))
            
            desc_text = tk.Text(
                info_panel,
                font=('Arial', 10),
                bg='#3b3b3b',
                fg='#CCCCCC',
                wrap='word',
                height=20,
                padx=10,
                pady=10,
                relief='flat'
            )
            desc_text.pack(fill='both', expand=True, padx=10)
            desc_text.insert('1.0', info['description'])
            desc_text.config(state='disabled')
        
        # Video panel (right)
        video_panel = tk.Frame(self.window, bg='#1a1a1f')
        video_panel.pack(side='right', fill='both', expand=True, padx=10, pady=10)
        self.video_panel = video_panel
        
        self.video_frame = tk.Frame(video_panel, bg='#000000')
        self.video_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Controls
        if VLC_AVAILABLE:
            # Progress Slider Frame
            progress_frame = tk.Frame(video_panel, bg='#1a1a1f')
            progress_frame.pack(fill='x', padx=10, pady=(0, 5))
            
            self.progress_var = tk.DoubleVar()
            self.progress_slider = tk.Scale(
                progress_frame,
                from_=0,
                to=1000,
                orient='horizontal',
                variable=self.progress_var,
                command=self.on_seek,
                bg='#1a1a1f',
                fg='#00C8FF',
                troughcolor='#3b3b3b',
                activebackground='#00C8FF',
                showvalue=0,
                highlightthickness=0,
                bd=0
            )
            self.progress_slider.pack(fill='x')
            
            # Bind mouse events to avoid jitter while dragging
            self.progress_slider.bind("<ButtonPress-1>", self.on_slider_press)
            self.progress_slider.bind("<ButtonRelease-1>", self.on_slider_release)
            
            # Buttons Frame
            control_frame = tk.Frame(video_panel, bg='#2b2b2b', height=70)
            control_frame.pack(fill='x')
            control_frame.pack_propagate(False)
            
            # Left side controls (Play/Pause, Next)
            btn_frame_left = tk.Frame(control_frame, bg='#2b2b2b')
            btn_frame_left.pack(side='left', padx=20, pady=10)
            
            self.play_btn = tk.Button(
                btn_frame_left,
                text="⏸",
                command=self.toggle_play,
                font=('Arial', 16),
                bg='#00C8FF',
                fg='#000000',
                width=4,
                relief='flat',
                cursor='hand2'
            )
            self.play_btn.pack(side='left', padx=(0, 10))
            
            tk.Button(
                btn_frame_left,
                text="⏭ Next Random",
                command=self.play_next_episode,
                font=('Arial', 11, 'bold'),
                bg='#32DC64',
                fg='#000000',
                padx=15,
                pady=5,
                relief='flat',
                cursor='hand2'
            ).pack(side='left')
            
            # Right side controls (Volume, Time)
            btn_frame_right = tk.Frame(control_frame, bg='#2b2b2b')
            btn_frame_right.pack(side='right', padx=20)
            
            tk.Label(
                btn_frame_right,
                text="🔊",
                font=('Arial', 14),
                bg='#2b2b2b',
                fg='#FFFFFF'
            ).pack(side='left', padx=(0, 5))
            
            self.volume_slider = tk.Scale(
                btn_frame_right,
                from_=0,
                to=100,
                orient='horizontal',
                command=self.set_volume,
                length=150,
                bg='#2b2b2b',
                fg='#00C8FF',
                troughcolor='#3b3b3b',
                activebackground='#00C8FF',
                showvalue=0,
                highlightthickness=0,
                bd=0
            )
            self.volume_slider.set(70)
            self.volume_slider.pack(side='left', padx=(0, 20))
            
            self.time_label = tk.Label(
                btn_frame_right,
                text="00:00 / 00:00",
                font=('Arial', 11, 'bold'),
                bg='#2b2b2b',
                fg='#00C8FF'
            )
            self.time_label.pack(side='left')
            
            self.fullscreen_btn = tk.Button(
                btn_frame_right,
                text="⛶",
                command=self.toggle_fullscreen,
                font=('Arial', 14),
                bg='#2b2b2b',
                fg='#FFFFFF',
                relief='flat',
                cursor='hand2',
                padx=5,
                pady=0,
                borderwidth=0,
                highlightthickness=0
            )
            self.fullscreen_btn.pack(side='left', padx=(15, 0))
            
            def on_enter_fs(e):
                self.fullscreen_btn.config(fg='#00C8FF')
            def on_leave_fs(e):
                self.fullscreen_btn.config(fg='#FFFFFF')
            self.fullscreen_btn.bind('<Enter>', on_enter_fs)
            self.fullscreen_btn.bind('<Leave>', on_leave_fs)
    
    def load_video(self):
        """Load and play video"""
        if VLC_AVAILABLE and self.player:
            media = self.instance.media_new(self.episode_path)
            self.player.set_media(media)
            
            if sys.platform.startswith('win'):
                self.player.set_hwnd(self.video_frame.winfo_id())
            else:
                self.player.set_xwindow(self.video_frame.winfo_id())
            
            self.player.play()
            self.update_time()
        else:
            # Fallback to external VLC
            vlc_dir = find_vlc()
            if vlc_dir:
                vlc_exe = os.path.join(vlc_dir, 'vlc.exe')
                if os.path.exists(vlc_exe):
                    print(f"Launching external VLC: {vlc_exe}")
                    # Use absolute path and ensure it's normalized
                    abs_path = os.path.abspath(self.episode_path)
                    try:
                        # Add flags to ensure it plays
                        subprocess.Popen([vlc_exe, '--no-video-title-show', abs_path])
                    except Exception as e:
                        messagebox.showerror("Playback Error", f"Failed to launch VLC: {e}")
                else:
                    messagebox.showerror("Error", f"VLC executable not found at: {vlc_exe}")
            else:
                messagebox.showerror("Error", "VLC not found. Please install VLC Media Player.")
    
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        self.is_fullscreen = not self.is_fullscreen
        self.window.attributes('-fullscreen', self.is_fullscreen)
        
        if self.is_fullscreen:
            self.fullscreen_btn.config(text="🗗")
            self.info_panel.pack_forget()
            self.video_panel.pack(side='right', fill='both', expand=True, padx=0, pady=0)
            self.video_frame.pack(fill='both', expand=True, pady=0)
        else:
            self.fullscreen_btn.config(text="⛶")
            # Restore
            self.info_panel.pack(side='left', fill='y', padx=10, pady=10)
            self.video_panel.pack(side='right', fill='both', expand=True, padx=10, pady=10)
            self.video_frame.pack(fill='both', expand=True, pady=(0, 10))
                
    def exit_fullscreen(self, event=None):
        if self.is_fullscreen:
            self.toggle_fullscreen()
    
    def play_next_episode(self):
        """Play next random episode"""
        print("Playing next random episode...")
        if self.player:
            self.player.stop()
        if self.on_next:
            # Pass self (the window) to be destroyed
            print("Calling on_next callback...")
            self.on_next(old_window=self.window)
        else:
            print("Error: on_next callback not set")
    
    def on_slider_press(self, event):
        self.is_seeking = True
    
    def on_slider_release(self, event):
        self.is_seeking = False
        # Final seek to ensure accuracy
        if self.player:
            val = self.progress_var.get()
            length = self.player.get_length()
            if length > 0:
                target_time = int((val / 1000) * length)
                self.player.set_time(target_time)

    def on_seek(self, val):
        """Handle scrub"""
        # Only seek if user is dragging (is_seeking)
        # However, command triggers on set() too, so we check checks
        if self.is_seeking and self.player:
            length = self.player.get_length()
            if length > 0:
                target_time = int((float(val) / 1000) * length)
                # Don't set_time constantly on drag if it causes stutter, but for VLC python bytes it's usually ok
                if abs(self.player.get_time() - target_time) > 1000: # 1 sec threshold
                    self.player.set_time(target_time)
    
    def toggle_play(self):
        """Toggle play/pause"""
        if self.player and self.player.is_playing():
            self.player.pause()
            self.play_btn.config(text="▶")
        elif self.player:
            self.player.play()
            self.play_btn.config(text="⏸")
    
    def set_volume(self, val):
        """Set volume"""
        if self.player:
            self.player.audio_set_volume(int(float(val)))
    
    def update_time(self):
        """Update time display and slider"""
        if self.player:
            current = self.player.get_time()
            total = self.player.get_length()
            
            # Update slider if not seeking
            if not self.is_seeking and total > 0:
                pos = (current / total) * 1000
                self.progress_var.set(pos)
            
            # Format time strings
            cur_sec = current // 1000
            tot_sec = total // 1000
            current_str = f"{cur_sec // 60:02d}:{cur_sec % 60:02d}"
            total_str = f"{tot_sec // 60:02d}:{tot_sec % 60:02d}" if total > 0 else "00:00"
            
            self.time_label.config(text=f"{current_str} / {total_str}")
        
        # Check if window still exists before scheduling next update
        if self.window.winfo_exists():
            self.window.after(500, self.update_time)

class MainWindow:
    """Main application window"""
    def __init__(self):
        self.config = Config()
        
        self.window = tk.Tk()
        self.window.title("PARE - Play A Random Episode")
        self.window.geometry("650x550")
        self.window.configure(bg='#1a1a1f')
        
        # Set window icon
        try:
            icon_path = get_asset_path('logo_solid.png')
            if os.path.exists(icon_path):
                self.icon_img = ImageTk.PhotoImage(file=icon_path)
                self.window.iconphoto(True, self.icon_img)
        except Exception as e:
            print(f"Could not set window icon: {e}")
        
        self.build_ui()
    
    def build_ui(self):
        """Build main UI"""
        # Try to load logo (use solid background version)
        logo_img = None
        try:
            if os.path.exists('assets/logo_solid.png'):
                img = Image.open('assets/logo_solid.png')
                img = img.resize((140, 140), Image.Resampling.LANCZOS)
                logo_img = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Could not load logo: {e}")
        
        # Settings cog button (top-right corner) - using Unicode
        settings_btn = tk.Button(
            self.window,
            text="⚙",
            command=self.open_settings,
            font=('Arial', 20),
            bg='#1a1a1f',
            fg='#808080',
            relief='flat',
            cursor='hand2',
            padx=8,
            pady=8,
            borderwidth=0,
            highlightthickness=0
        )
        settings_btn.place(x=595, y=8)
        
        # Hover effect
        def on_enter(e):
            settings_btn.config(fg='#00C8FF')
        def on_leave(e):
            settings_btn.config(fg='#808080')
        settings_btn.bind('<Enter>', on_enter)
        settings_btn.bind('<Leave>', on_leave)
        
        # Logo - using Unicode dice emoji
        tk.Label(
            self.window,
            text="🎲",
            font=('Arial', 80),
            bg='#1a1a1f'
        ).pack(pady=(40, 10))
        
        # Title
        tk.Label(
            self.window,
            text="PARE",
            font=('Arial', 42, 'bold'),
            bg='#1a1a1f',
            fg='#00C8FF'
        ).pack(pady=(5 if logo_img else 30, 2))
        
        tk.Label(
            self.window,
            text="Play A Random Episode",
            font=('Arial', 15),
            bg='#1a1a1f',
            fg='#FFFFFF'
        ).pack(pady=2)
        
        # Creator credit
        tk.Label(
            self.window,
            text='Created by Dimi D. "Delta"',
            font=('Arial', 9, 'italic'),
            bg='#1a1a1f',
            fg='#505050'
        ).pack(pady=(2, 15))
        
        # Series info
        if self.config.is_configured():
            episodes = get_all_episodes(self.config.series_folder)
            info_text = f"📺 {self.config.series_name or 'Series'}\n{len(episodes)} episodes found"
            
            # Show VLC warning if applicable
            if not VLC_AVAILABLE and sys.maxsize > 2**32 and "x86" in (find_vlc() or ""):
                info_text += "\n\n⚠ VLC Architecture Mismatch\nInstall VLC 64-bit for embedded playback"
                
        else:
            info_text = "⚠️ Not configured\nClick Settings to get started"
        
        self.info_label = tk.Label(
            self.window,
            text=info_text,
            font=('Arial', 14),
            bg='#1a1a1f',
            fg='#808080' if VLC_AVAILABLE else '#DC3232'
        )
        self.info_label.pack(pady=30)
        
        # Buttons
        btn_frame = tk.Frame(self.window, bg='#1a1a1f')
        btn_frame.pack(pady=15)
        
        # Play button (centered, larger) - using Unicode
        self.play_btn = tk.Button(
            btn_frame,
            text="▶  Play Random Episode",
            command=self.play_random,
            font=('Arial', 14, 'bold'),
            bg='#32DC64',
            fg='#000000',
            padx=35,
            pady=15,
            relief='flat',
            cursor='hand2',
            state='normal' if self.config.is_configured() else 'disabled'
        )
        self.play_btn.pack(pady=10)
    
    def open_settings(self):
        """Open settings window"""
        SettingsWindow(self.window, self.config, self.on_settings_saved)
    
    def on_settings_saved(self):
        """Callback after settings saved"""
        # Update UI
        if self.config.is_configured():
            episodes = get_all_episodes(self.config.series_folder)
            self.info_label.config(text=f"📺 {self.config.series_name or 'Series'}\n{len(episodes)} episodes found")
            self.play_btn.config(state='normal')
        else:
            self.info_label.config(text="⚠️ Not configured\nClick Settings to get started")
            self.play_btn.config(state='disabled')
    
    def play_random(self, old_window=None):
        """Play a random episode"""
        # Close old player window if exists
        if old_window:
            try:
                old_window.destroy()
            except:
                pass
            # Schedule the next play with a small delay to allow resource cleanup
            self.window.after(200, lambda: self._play_random_logic())
            return
            
        self._play_random_logic()
    
    def _play_random_logic(self):
        """Internal logic to pick and play episode"""
        if not self.config.is_configured():
            messagebox.showerror("Error", "Please configure settings first")
            return
        
        episodes = get_all_episodes(self.config.series_folder)
        
        if not episodes:
            messagebox.showerror("Error", "No episodes found in folder")
            return
        
        episode = random.choice(episodes)
        season, ep_num = parse_episode_info(os.path.basename(episode))
        
        print(f"Playing: {os.path.basename(episode)}")
        if season and ep_num:
            print(f"Season {season}, Episode {ep_num}")
        
        # Pass self.play_random as the play_next callback
        PlayerWindow(self.window, episode, season, ep_num, self.config, on_next=self.play_random)
    
    def run(self):
        """Start the application"""
        self.window.mainloop()

if __name__ == "__main__":
    print("=" * 70)
    print("🎬 PARE - Play A Random Episode")
    print("=" * 70)
    
    if not VLC_AVAILABLE:
        print("⚠️  VLC Python bindings not available")
        print("   Will use external VLC player")
    
    app = MainWindow()
    app.run()
