import asyncio
import customtkinter as ctk
from tkinter import filedialog, Listbox, Scale, Menu
import re
import os
import sys
import cv2 #pip install opencv-python
import json
import win32gui #pip install pywin32 
import win32con
import requests
import subprocess
import yt_dlp
import pyperclip# System ClipBoard
import pywinctl as window
import comtypes
import ctypes
from PIL import Image
from typing import Literal
from time import sleep, perf_counter_ns 
from datetime import datetime
from pathlib import Path
from numpy import round, sin, cos, radians, random
from pynput import keyboard
from pynput.keyboard import Key, Controller
from pycaw.pycaw import AudioUtilities,  IAudioEndpointVolume, IMMDeviceEnumerator, EDataFlow, DEVICE_STATE
from pycaw.constants import CLSID_MMDeviceEnumerator
from win32api import GetMonitorInfo, MonitorFromPoint, GetFileVersionInfo
from send2trash import send2trash# Recycle Bin
from collections import Counter
version="2026.07.22"
class URLHandler:
    def __init__(self, parent, url):
        self.parent = parent
        self.url = url
    def validate_url(self):#*
        if self.__is_youtube_video_id(self.url):
            self.url = f"https://www.youtube.com/watch?v={self.url}"
        return self.validate_url_link(self.url)
    def validate_url_link(self, url: str):# Validates the given YouTube video URL
        is_valid_link, link_type = self.__is_youtube_link(url)
        if not is_valid_link:
            return False, link_type.lower()
        return is_valid_link, link_type.lower()
    def __is_youtube_link(self, link: str):# Check if the given link is a YouTube video
        is_video = self.__is_youtube_video(link)
        is_short = self.__is_youtube_shorts(link)
        return (is_video, "Videos") if is_video \
            else (is_short, "short") if is_short \
            else (False, "unknown")
    def __is_youtube_shorts(self, link: str):# Check if the given link is a YouTube shorts link.
        shorts_pattern = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|shorts\/|watch\?.*?v=))(?:(?:[^\/\n\s]+\/)?)([a-zA-Z0-9_-]+)"
        shorts_match = re.match(shorts_pattern, link)
        return bool(shorts_match)
    def __is_youtube_video(self, link: str):# Check if the given link is a YouTube video.
        video_pattern = re.compile(
            r"^(?:https?://)?(?:www\.)?(?:youtube(?:-nocookie)?\.com/(?:(watch\?v=|watch\?feature\=share\&v=)|embed/|v/|live_stream\?channel=|live\/)|youtu\.be/)([a-zA-Z0-9_-]{11})")
        return bool(video_pattern.match(link))
    def __is_youtube_video_id(self, video_id: str):# Check if the given string is a valid YouTube video ID.
        return len(video_id) == 11 and all(
            c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in video_id)
    def not_valid_url(self, where):
        title=f'Validate {self.parent.Download_Type.get()} URL '
        msg1=f'The {self.parent.Download_Type.get()}\n'
        msg2='URL Entered Is "Not Invalid"!\n'
        msg3='Please Entered A Valid YouTube URL!'
        msg=msg1+msg2+msg3
        MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="cancel.png")
        YouTube_GUI.URL.set("")
class YouTube_GUI(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__()
        self.parent=parent
        app.withdraw()
        self.num_items=0
        self.last_percentage=0.0
        self.completed_items=0
        self.URL=ctk.StringVar()
        self.Download_Folder=ctk.StringVar()
        self.Download_Type=ctk.StringVar()
        self.Use_Oauth=ctk.BooleanVar()
        self.Use_Oauth.set(False)
        self.User_Name=ctk.StringVar()
        self.User_Password=ctk.StringVar()
        self.Media_Title=ctk.StringVar()
        self.after(300, self.wm_iconbitmap, app.ico_path)
        self.attributes("-topmost", False)
        self.configure(bg="#094983")
        self.title("YouTube Downloader")
        self.resizable(True,True)
        self.protocol("WM_DELETE_WINDOW", self.youtube_destroy)
        pgm_path=Path(__file__).parent.absolute()
        self.download_path=os.path.join(os.path.expanduser("~"),"youtube_downloads.json")
        self.readme_path=os.path.join(pgm_path,"Bound_Keys_en.txt")
        self.youtube_readme=os.path.join(pgm_path,"youtube_downloader_readme_en.txt")
        self.ffmpeg_resources = os.path.abspath(self.resource_path("ffmpeg\\bin\\ffmpeg.exe"))
        self.ffmpeg_path = self.ffmpeg_resources
        self.deno_resources = self.resource_path("deno\\bin") 
        self.deno_path = os.path.join(self.deno_resources, "deno.exe")
        for r in range(9):# Configure Rows For main_frame 
            self.grid_rowconfigure(r, weight=1)
        for c in range(10):# Configure Columns For main_frame 
            self.grid_columnconfigure(c, weight=1)
        self.open_utube = ctk.CTkButton(self, text="Open Youtube", border_width=2, corner_radius=5, font=app.media_font, anchor="center",
                    fg_color=("#a6e7ff", "#0c012e"), hover_color="#00ced1", text_color=("#0c012e", "#ffffff"), command=lambda:self.open_youtube())
        self.open_utube.grid(row=0, column=0, columnspan=1, rowspan=1, sticky="ew", pady=(0, 5), padx=(10, 10))
        self.utube_readme = ctk.CTkButton(self, text="Youtube Help", border_width=2, corner_radius=5, font=app.media_font, anchor="center",
                    fg_color=("#a6e7ff", "#0c012e"), hover_color="#00ced1", text_color=("#0c012e", "#ffffff"), command=lambda:self.open_readme())
        self.utube_readme.grid(row=0, column=1, columnspan=1, rowspan=1, sticky="ew", pady=(0, 5), padx=(0, 0))
        self.conn_lbl = ctk.CTkLabel(self, text='Internet Connection: ',fg_color="transparent", 
                                     font=app.media_font, text_color=("#000000", "#ffffff"), anchor="e")
        self.conn_lbl.grid(row=1, column=0, columnspan=1, rowspan=1, sticky="ew", pady=(0, 5), padx=(0, 0))
        self.conn=self.check_internet_connection(False)
        if self.conn:# Preceed
            text="  There is an Internet Connection  "
            forecolor="#dfdfdf"
            backcolor="#369e09"
        else:# Go No Further
            text="  No Internet Available! Check Your Connection And Try Again!  "
            forecolor="#f70505"
            backcolor="#ffffff"
        self.conn_results=ctk.CTkLabel(self, text=text, fg_color=backcolor, text_color=forecolor, 
                                       font=app.media_font, corner_radius=10, anchor="w")
        self.conn_results.grid(row=1, column=1, columnspan=1, rowspan=1, sticky="ew", pady=(0, 5), padx=(0, 0))
        if not self.conn:
            self.retry_conn = ctk.CTkButton(self, text="Retry Internet Connection", border_width=2, corner_radius=5, 
                                            font=app.media_font, anchor="center", fg_color="transparent", 
                                            hover_color="#00ced1", text_color="#dc143c")
            self.retry_conn.grid(row = 1, column = 1, sticky = 'ew', pady=(0, 5), padx=(0, 0))
            self.retry_conn.bind("<ButtonRelease>",lambda event:self.check_internet_connection(True))
        if app.active_media == "video":folder = "Videos"
        elif app.active_media == "audio":folder = "Audio"
        elif app.active_media == "image": folder = "Pictures"
        else: folder = "Downloads"
        self.Download_Folder.set(str(os.path.join(Path.home(),folder).replace("\\","/")))
        self.download_lbl = ctk.CTkLabel(self, text='Select Destination Folder: ', fg_color="transparent",
                                         text_color=("#000000", "#ffffff"), font=app.media_font, anchor="e")
        self.download_lbl.grid(row = 2, column = 0, columnspan=1 ,sticky = 'ew', pady=(0, 5), padx=(0, 0))
        self.download_txt = ctk.CTkEntry(self, textvariable=self.Download_Folder, corner_radius=5,
                        fg_color=("#a6e7ff", "#0c012e"), text_color=("#0c012e", "#ffffff"), font=app.media_font, state="disabled")
        self.download_txt.grid(row = 2, column = 1, columnspan=5, sticky = 'ew', pady=(0, 5), padx=(0, 0))
        self.download_txt.bind("<ButtonRelease>",lambda event:self.change_download_folder(self.Download_Folder.get()))
        self.yt_user_lbl = ctk.CTkLabel(self, text='YouTube User Name: ',fg_color="transparent", text_color=("#000000", "#ffffff"), font=app.media_font, anchor="e")
        self.yt_user_lbl.grid(row = 3, column = 0, columnspan=1, sticky = 'ew', pady=(0, 5), padx=(0, 0))
        self.yt_user_name = ctk.CTkEntry(self, textvariable=self.User_Name, placeholder_text="",font=app.media_font, corner_radius=5,
                        fg_color=("#a6e7ff", "#0c012e"), text_color=("#0c012e", "#ffffff"),state="disabled")
        self.yt_user_name.grid(row = 3, column = 1, columnspan=1, sticky = 'ew', pady=(0, 5), padx=(0, 0))
        self.oauth_btn = ctk.CTkCheckBox(self, text="Use Oauth Authenication",  border_width=2, variable=self.Use_Oauth,
                                font=app.media_font, checkmark_color="#dfdfdf", command=lambda:self.login_status())
        self.oauth_btn.grid(row = 3, column = 2, columnspan=1, sticky = 'ew', pady=(0, 5), padx=(15, 0))
        self.yt_pass_lbl = ctk.CTkLabel(self, text='YouTube Password: ',fg_color="transparent", text_color=("#000000", "#ffffff"), anchor="e", font=app.media_font)
        self.yt_pass_lbl.grid(row = 4, column = 0, columnspan=1, sticky = 'ew', pady=(0, 5), padx=(0, 0))
        self.yt_user_pass = ctk.CTkEntry(self, textvariable=self.User_Password, placeholder_text="", state="disabled",
                        fg_color=("#a6e7ff", "#0c012e"), text_color=("#0c012e", "#ffffff"), font=app.media_font)
        self.yt_user_pass.grid(row = 4, column = 1, columnspan=1, sticky = 'ew', pady=(0, 5), padx=(0, 0))
        self.type_lbl = ctk.CTkLabel(self, text='Select Download Type: ',fg_color="transparent", text_color=("#000000", "#ffffff"), anchor="e", font=app.media_font)
        self.type_lbl.grid(row = 5, column = 0, columnspan=1, sticky = 'ew', pady=(0, 5), padx=(0, 0))
        types=["Audio Only","Video + Audio"]
        self.Download_Type.set(types[1])
        self.type_select = ctk.CTkComboBox(self, values=types, variable=self.Download_Type, bg_color='transparent', fg_color=("#a6e7ff", "#0c012e"), 
                                           justify="left", font=app.media_font, dropdown_font=app.media_font, corner_radius=5) 
        self.type_select.grid(row = 5, column = 1, columnspan=1, sticky = 'ew', pady=(0, 5), padx=(0, 0))
        self.type_select.bind("<<ComboboxSelected>>",lambda event:self.change_download_type())
        self.url_lbl = ctk.CTkLabel(self, text='Enter YouTube URL: ',fg_color="transparent", text_color=("#000000", "#ffffff"), anchor="e", font=app.media_font)
        self.url_lbl.grid(row = 6, column = 0, columnspan=1, sticky = 'ew', pady=(0, 5), padx=(0, 0))
        self.url_txt = ctk.CTkEntry(self, textvariable=self.URL, placeholder_text="", corner_radius=5,
                        fg_color=("#a6e7ff", "#0c012e"), text_color=("#0c012e", "#ffffff"), font=app.media_font)
        self.url_txt.grid(row = 6, column = 1, columnspan=7, sticky = 'ew', pady=(0, 5), padx=(0, 0))
        self.url_txt.bind("<KeyRelease>",lambda event:self.url_entry)
        self.url_txt.bind("<Button-3>", self.show_context_menu)
        self.context_menu = Menu(self.url_txt, tearoff=False)
        self.context_menu.add_command(label="Paste", command=lambda: self.paste_from_clipboard(self.url_txt))
        self.fetch = ctk.CTkButton(self, text="Download", border_width=2, corner_radius=5, font=app.media_font, anchor="center",
                    fg_color=("#a6e7ff", "#0c012e"), hover_color="#00ced1", text_color=("#0c012e", "#ffffff"))
        self.fetch.grid(row = 6, column = 8, columnspan=2, sticky = 'ew', pady=(0, 5), padx=(10, 10))
        self.fetch.bind("<ButtonRelease>",lambda event:self.download_url(self.URL.get(),self.Download_Folder.get(),self.Download_Type.get()))
        self.title_lbl = ctk.CTkLabel(self, text='Download Title: ', fg_color="transparent", text_color="#ffffff", anchor="e", font=app.media_font)
        self.title_lbl.grid(row = 7, column = 0, columnspan=1, sticky = 'ew', pady=(0, 5), padx=(0, 0))
        self.Media_Title.set("")
        self.URL.set("")
        self.title_name = ctk.CTkEntry(self, textvariable=self.Media_Title, placeholder_text="", corner_radius=5,
                        fg_color=("#a6e7ff", "#0c012e"), text_color=("#0c012e", "#ffffff"), font=app.media_font)
        self.title_name.grid(row = 7, column = 1, columnspan=8, sticky = 'ew', pady=(0, 5), padx=(0, 0))
        if self.URL.get=="":self.fetch.configure(state = 'disabled')
        self.progress_lbl = ctk.CTkLabel(self, text='Download Progress: ',fg_color="transparent", text_color=("#000000", "#ffffff"), anchor="e", font=app.media_font)
        self.progress_lbl.grid(row = 8, column = 0, columnspan=1, sticky = 'ew', pady=(0, 5), padx=(0, 0))
        self.progress_bar = ctk.CTkProgressBar(self, mode="determinate", orientation="horizontal", corner_radius=5, bg_color="transparent")
        self.progress_bar.grid(row = 8, column = 1, columnspan=5, sticky = 'nsew', pady=(10, 10), padx=(10, 10))
        self.progress_bar.set(0)
        self.download_complete = ctk.CTkLabel(self, text='',fg_color="transparent", text_color=("#000000", "#ffffff"), anchor="w", font=app.media_font)
        self.download_complete.grid(row = 8, column = 7 , columnspan=2, sticky = 'ew', pady=(0, 5), padx=(0, 0))
        if self.conn:
            self.open_utube.configure(state="normal")
        else:self.open_utube.configure(state="disabled")
        self.update_idletasks()
        self.req_height = self.winfo_reqheight()
        self.req_width = self.winfo_reqwidth()
        x=int((app.screen_width / 2) - (self.req_width / 2))
        y=int((app.screen_height / 2) - (self.req_height / 2))
        self.attributes("-topmost", False)
        self.geometry('%dx%d+%d+%d' % (self.req_width, self.req_height, x, y, ))
        self.configure(bg="#094983")
        path_dict={}
        self.url_txt.focus_force()
        path_dict={}
        with open(app.shared_download_files, "w") as json_file:# Clear json Object Used For Sharing Downloaded Files
            json.dump(path_dict, json_file)
        json_file.close()
        self.login_status()
        self.update()
        self.mainloop()
    def resource_path(self, relative):
        if getattr(sys, 'frozen', False):
            if hasattr(sys, "_MEIPASS"):
                return os.path.join(sys._MEIPASS, relative)
        else:
            return os.path.join(os.path.abspath("."), relative)
    def show_context_menu(self,event):
            self.context_menu.post(event.x_root, event.y_root)
    def paste_from_clipboard(self,event):
            try:
                clipboard_content=pyperclip.paste()
                if clipboard_content=="":return
                self.URL.set(clipboard_content)
            except:
                pass
    def is_playlist(self,url):
        ydl_opts = {
            'quiet': True,  # Suppress output
            'extract_flat': True}  # Extract metadata without downloading
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if info.get('_type')=='playlist':self.num_items=len(info['entries'])
                else:self.num_items=1
                self.completed_items=0
                title=info.get('title', 'Unknown Title')  # Get the title or fallback
                title=title.replace("/","_")
                self.Media_Title.set(title)
                self.update()
                return info.get('_type')=='playlist'
            except Exception as e:
                title="< Youtube Downloader >"
                msg1="An Error Occured!\n"
                msg2=f"{e}"
                msg=msg1+msg2
                MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="cancel.png")
    def download_url(self,url, path, audio_video):
        self.completed_items=0
        if not self.conn:return
        if self.Use_Oauth.get():
            if self.User_Name.get()=="" or self.User_Password.get()=="":
                title="< YouTube Login Using Oauth Authenication >"
                msg1="YouTube or Google Login is Required\n"
                msg2="For Oauth Authenication! Please Enter\n"
                msg3="a User Name and/or Password To Continue."
                msg=msg1+msg2+msg3
                MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="cancel.png")
                if self.User_Name.get()=="":self.yt_user_name.focus_force()
                elif self.User_Password.get()=="":self.yt_user_pass.focus_force()    
                return
        if url is None or url=="":
            title="< YouTube Downloader URL >"
            msg="Missing URL! Please Enter A Valid  URL!"
            MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="cancel.png")
            self.url_txt.focus_force()
            return
        self.download_complete.configure(text="")
        self.progress_bar.set(0)
        self.Media_Title.set("")
        self.update()
        if not self.is_playlist(url):
            self.num_items=1
            self.rename_video_title()
            url_handler = URLHandler(self, url)# Instantize
            is_valid_link, link_type = url_handler.validate_url()# Only Validates And Returns link_type
            if not is_valid_link or link_type=='unknown':
                url_handler.not_valid_url('URL Link Type')
                return
            if audio_video=="Audio Only":# Single Audio
                if self.Use_Oauth.get():
                    options = {'ffmpeg_location': self.ffmpeg_resources, 'deno': self.deno_path, 
                                'format': 'bestaudio/best', 'retries': 5, 'fragment_retries': 20, 'progress_hooks': [self.update_progressbar],
                                'postprocessors': [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'mp3',
                                'preferredquality': '192',}],
                                'outtmpl': f'{self.Download_Folder.get()}/{self.Media_Title.get()}.%(ext)s',
                                'oauth2': True,  # Enable OAuth2 authentication
                                'username': self.User_Name.get(),  # Your account email
                                'password': self.User_Password.get()}  # Your account password
                else:    
                    options = {'ffmpeg_location': self.ffmpeg_resources, 'deno': self.deno_path, 
                                'format': 'bestaudio/best', 'retries': 5, 'fragment_retries': 20, 'progress_hooks': [self.update_progressbar],
                                'postprocessors': [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'mp3',
                                'preferredquality': '192',}],
                                'outtmpl': f'{self.Download_Folder.get()}/{self.Media_Title.get()}.%(ext)s'}
            elif audio_video=="Video + Audio":# Single Audio/Video
                if self.Use_Oauth.get():
                    options = {'ffmpeg_location': self.ffmpeg_resources, 'deno': self.deno_path, 
                                'format': 'best', 'retries': 5, 'fragment_retries': 20, 'progress_hooks': [self.update_progressbar], 
                                'outtmpl': f'{self.Download_Folder.get()}/{self.Media_Title.get()}.%(ext)s',
                                'oauth2': True,  # Enable OAuth2 authentication
                                'username': self.User_Name.get(),  # Your account email
                                'password': self.User_Password.get()}  # Your account password
                else:    
                    options = {'ffmpeg_location': self.ffmpeg_resources, 'deno': self.deno_path, 'format': 'best',
                                'retries': 5, 'fragment_retries': 20,
                                'progress_hooks': [self.update_progressbar],
                                'outtmpl': f'{self.Download_Folder.get()}/{self.Media_Title.get()}.%(ext)s'}
            else:return
        else:# Play List
            if audio_video=="Audio Only":# All Audio 
                if self.Use_Oauth.get():
                    options = {'ffmpeg_location': self.ffmpeg_resources, 'deno': self.deno_path, 'format': 'bestaudio/best', 
                                'retries': 5, 'fragment_retries': 20, 'progress_hooks': [self.update_progressbar],
                                'postprocessors': [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'mp3',
                                'preferredquality': '192',}],
                                'outtmpl': f'{self.Download_Folder.get()}/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s',
                                'oauth2': True,  # Enable OAuth2 authentication
                                'username': self.User_Name.get(),  # Your account email
                                'password': self.User_Password.get()}  # Your account password
                else:   
                    options = {'ffmpeg_location': self.ffmpeg_resources, 'deno': self.deno_path, 'format': 'bestaudio/best', 
                                'retries': 5, 'fragment_retries': 20, 'progress_hooks': [self.update_progressbar],
                                'postprocessors': [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'mp3',
                                'preferredquality': '192',}],
                                'outtmpl': f'{self.Download_Folder.get()}/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s'}
            elif audio_video=="Video + Audio":# All Audio/Video 
                if self.Use_Oauth.get():
                    options = {'ffmpeg_location': self.ffmpeg_resources, 'deno': self.deno_path, 'format': 'best', 'retries': 5, 
                                'fragment_retries': 20, 'progress_hooks': [self.update_progressbar], 
                                'outtmpl': f'{self.Download_Folder.get()}/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s',
                                'oauth2': True,  # Enable OAuth2 authentication
                                'username': self.User_Name.get(),  # Your account email
                                'password': self.User_Password.get(),  # Your account password
                                'ignoreerrors': True}  # Continue downloading even if some videos fail
                else:    
                    options = {'ffmpeg_location': self.ffmpeg_resources, 'deno': self.deno_path, 'format': 'best', 'retries': 5, 'fragment_retries': 20, 
                                'progress_hooks': [self.update_progressbar],
                                'outtmpl': f'{self.Download_Folder.get()}/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s',
                                'ignoreerrors': True}  # Continue downloading even if some videos fail
            else:return
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])
        except Exception as e:
            title="< Youtube Downloader >"
            msg1="An error occurred!\n"
            msg2=f"{e}"
            msg=msg1+msg2
            MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="cancel.png")
            return
        title="< Download Status >"
        msg1="Your Download Has Completed And\n"
        msg2=f"Saved To:\n"
        msg3=f"{path}"
        msg=msg1+msg2+msg3
        MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="info.png")
        self.progress_bar.set(0)
        num_keys=self.get_json_num_keys()
        with open(app.shared_download_files, "w") as json_file:# Write Download Path and Filename to Shared Json file
            app.path_dict[str(num_keys)]=self.Download_Folder.get()
            app.path_dict[str(num_keys+1)]=self.Media_Title.get()
            json.dump(app.path_dict, json_file)
        json_file.close()
        self.update()
    def update_progressbar(self,d):
        if d['status'] == 'downloading':    
            downloaded_bytes = d.get('downloaded_bytes')
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total_bytes:
                percentage = (downloaded_bytes / total_bytes) * 100
            else:# Fallback to the string representation if the raw number is missing/unreliable
                percentage = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
            if percentage>self.last_percentage:
                self.download_complete.configure(text=f"Downloading: {percentage:.2f}%")
                self.progress_bar.set(percentage)
            self.last_percentage=percentage
        elif d['status'] == 'finished':
            self.last_percentage=0.0
            self.progress_bar.set(100)
            self.completed_items += 1
            self.download_complete.configure(text=f"{self.completed_items} of {self.num_items} Download Complete! 100%")
        elif d['status'] == 'error':
            self.last_percentage=0.0
            title="< Download Status >"
            msg1="Error Downloading From YouTube\n"
            msg2=f"Error: {d.get('error')}"
            msg=msg1+msg2
            MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="cancel.png")
        self.update()
    def rename_video_title(self):
            title="< Rename Video / Audio File >"
            prompt="Rename The File Here If Desired."
            new_title = MyDialog(parent=app, style="entry", title=title, prompt=prompt, choices=self.Media_Title.get(), icon="info.png")
            if new_title.result is not None and new_title.result != '':
                self.Media_Title.set(new_title.result)
    def open_youtube(self):
        subprocess.run(['start', 'https://www.youtube.com'], shell=True)
    def open_readme(self):
        subprocess.Popen(["notepad.exe", self.youtube_readme])
    def url_entry(self):
        if self.URL.get() != "":
            self.fetch.configure(state = 'normal')
    def change_download_type(self):#*
        self.Media_Title.set("")
        self.title_name.configure(text=self.Media_Title.get())
    def change_download_folder(self,init_dir):#*
        folder_path=filedialog.askdirectory(initialdir=init_dir,title=f"Please Select A Folder For YouTube Downloads Or Click 'Select Folder' To Select Default Folder.")  
        if folder_path=="" or folder_path==None:return
        self.Download_Folder.set(folder_path)
        wid=len(self.Download_Folder.get())+1 
        self.download_txt.configure(width=wid)
        self.update()
    def check_internet_connection(self,retry):#*
        try:
            requests.get("https://www.google.com", timeout=15)
            if retry:
                self.retry_conn.destroy()
                self.conn_results.configure(text="  There is an Internet Connection  ",foreground="#ffffff",background="#369e09")
                self.open_utube.configure(state="normal")
                self.update()
            return True
        except Exception:
            return False
    def get_json_num_keys(self,):
        try:
            with open(app.shared_download_files, 'r') as file:
                    data = json.load(file)
                    return len(data.keys())
        except Exception:
            return None
    def login_status(self):
        if self.Use_Oauth.get()==False: 
            self.yt_user_name.configure(state="disabled")
            self.yt_user_pass.configure(state="disabled")
            self.update()
        else:    
            self.yt_user_name.configure(state="normal")
            self.yt_user_pass.configure(state="normal")
            self.yt_user_name.focus_force()
            self.update()
    def youtube_destroy(self,):# X Icon Was Clicked
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkCanvas):widget.destroy()
            else:widget.destroy()
        self.grab_release()
        self.withdraw()
        app.deiconify()
        app.grab_set()
        app.focus_force()
        app.update_databases()
        app.update()
class Timed_Popup(ctk.CTkLabel): # The Popup Is Centered On The Parent Widget. 
    def __init__(self, parent, text, text_color, fg_color, font_size, delay_time): 
        super().__init__(parent)
        self.parent=parent
        self.text=(f"{text}")
        self.text_color=text_color
        self.fg_color=fg_color
        factor = (Default_DPI / 96.0)  # 96 is standard DPI for 1 point
        self.font_size = int(font_size * factor) 
        self.font_size=font_size
        self.delay_time=delay_time
        self.popup_font = ctk.CTkFont(family="Arial", size=self.font_size, weight="normal", slant="roman")
        try:
            self.update_idletasks()
            self.req_width = self.popup_font.measure(f"XX{self.text}XX")
            font_metrics = self.popup_font.metrics()
            self.req_height = int(font_metrics['linespace'] * 1.5)
            parent_wid=self.parent.winfo_width()
            parent_hgt=self.parent.winfo_height()
            self.x_pos = int((parent_wid / 2) - (self.req_width / 2))
            self.y_pos = int((parent_hgt / 2) - (self.req_height / 2))
            self.popup_lbl= ctk.CTkLabel(master=parent, text=self.text, width=self.req_width, text_color=self.text_color,
                                    fg_color=self.fg_color, corner_radius=10, font=self.popup_font)
            self.popup_lbl.place(x=self.x_pos, y=self.y_pos)
            self.update()
            self.after(self.delay_time, self.popup_lbl.destroy)
        except Exception as e:
            self.destroy()    
class Popup_Menu(ctk.CTkToplevel):
    def __init__(self, parent, caption_list, command_list, font_size, x_pos, y_pos, y_ref=None):
        super().__init__(parent)
        self.caption_list=caption_list
        self.command_list=command_list
        self.max_wid=0
        factor = (Default_DPI / 96.0)  # 96 is standard DPI for 1 point
        self.font_size = int(font_size * factor) 
        self.menu_font = ctk.CTkFont(family="Arial", size=self.font_size, weight="normal", slant="roman")
        self.transient(parent)  # Set the dialog to be on top of the self.parent
        try:
            for i in range(len(self.caption_list)):# Get Max Text Length For Menu Width
                txt = f"XXXX{self.caption_list[i]}XXX"
                if len(txt)>self.max_wid:
                    self.max_wid = len(txt)
                    self.text = txt
            self.overrideredirect(True)
            self.attributes("-topmost", True) # Keep the popup on top of the main window
            self.frame = ctk.CTkScrollableFrame(self, width=self.max_wid, corner_radius=10)# Container for scrollable items
            self.frame.pack(fill="both", expand=True, padx=(10, 10), pady=(10, 10))
            self.menu_items=[] 
            for i in range(0, len(self.caption_list)):
                self.menu_items.append([i])
                self.menu_items[i] = ctk.CTkButton(self.frame, text=self.caption_list[i], anchor="w", compound="left", fg_color="transparent", hover_color="#ff8080",  
                                            text_color=("#000000", "#ffffff"), font=self.menu_font, corner_radius=10, command=self.command_list[i])
                self.menu_items[i].pack(side='top', anchor='w', pady=0)
                self.menu_items[i].bind("<Button-1>", lambda e: self.withdraw())
                self.menu_items[i].bind("<Button-3>", lambda e: self.withdraw())
            self.bind("<Button-3>", lambda e: self.withdraw())
            self.bind("<FocusOut>", lambda e: self.withdraw())
            self.update_idletasks()
            self.req_height = self.winfo_reqheight()
            self.req_width = self.menu_font.measure(self.text)
            self.x_pos = int(x_pos - (self.req_width  * 0.5))
            if y_ref == None or y_ref == "top":
                self.y_pos = int(y_pos)
            elif y_ref=="bottom":
                self.y_pos = int(y_pos - self.req_height) 
            self.geometry(f"{self.req_width}x{self.req_height}+{self.x_pos}+{self.y_pos}")
            self.update_idletasks()
            self.focus_set()
        except Exception as e:
            self.withdraw()
class MyDialog(ctk.CTkToplevel):
    def __init__(self, parent, style: Literal["msgbox", "entry"], title, prompt, choices=None, 
                 icon: Literal["setup.png","check.png", "cancel.png", "info.png", "question.png", "warning.png"] = None, 
                 init_val=None, min_val=None, max_val=None):
        super().__init__(parent)
        self.style = style
        self.title(title)
        self.prompt = prompt
        self.choices = choices
        self.icon = icon
        self.init_val = init_val
        self.entry_var = ctk.StringVar(value=self.init_val)
        self.min_val = min_val
        self.max_val = max_val
        font_size = -18
        self.attributes("-topmost", True)
        self.grab_set()
        pgm_path=Path(__file__).parent.absolute()
        self.ico_path=os.path.join(pgm_path, 'player.ico')
        self.after(350, self.wm_iconbitmap, self.ico_path)
        self.update_idletasks()
        self.screen_width = ctypes.windll.user32.GetSystemMetrics(0)
        self.screen_height = ctypes.windll.user32.GetSystemMetrics(1)
        self.min_window = ctypes.windll.user32.GetSystemMetrics(58)
        self.width = int(self.screen_width * 0.3)
        self.height = int(self.screen_height * 0.25)
        factor = (Default_DPI / 96.0)  # 96 is standard DPI for 1 point
        self.font_size = int(font_size * factor) 
        self.font_size=font_size
        self.mydialog_font = ctk.CTkFont(family="Arial", size=self.font_size, weight="normal", slant="roman")
        self.result = None
        if self.icon != None:# Widget for the icon
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")                
            iconfile=os.path.join(base_path, self.icon)
            if iconfile:
                icon_size = self.height * 0.2
                pil_icon = Image.open(iconfile)
                ctk_image = ctk.CTkImage(light_image=pil_icon, dark_image=pil_icon, size=(icon_size, icon_size)) 
                self.icon_label = ctk.CTkLabel(self, image=ctk_image, text="")
                self.icon_label.pack(pady=(5, 0))
        label = ctk.CTkLabel(self, text=prompt, font=self.mydialog_font, anchor="w", justify="left")# Widgets for the dialog
        label.pack(pady=(10, 10))
        if self.style == "entry": 
            if self.choices is not None:
                if type(self.choices)==list:# List
                    pad_x = int(self.width * 0.15)
                    self.combobox = ctk.CTkComboBox(self, values=self.choices, font=self.mydialog_font) 
                    self.combobox.pack(fill= "x", padx=(pad_x, pad_x))
                    self.combobox.focus_set() # Set focus to the entry widget
                    menu = self.combobox._dropdown_menu  # internal tk.Menu object
                    menu.configure(font = self.mydialog_font)  # set dropdown font size
                    if init_val!= None: 
                        self.combobox.set(init_val)
                    self.combobox.update_idletasks()
                else:# String
                    self.entry_var.set(self.choices)
                    self.entry = ctk.CTkEntry(master=self, textvariable=self.entry_var, justify="center", font=self.mydialog_font)
                    self.entry.pack(fill="x", expand=True, pady=(0, 0), padx=(10, 10))
                    self.entry.focus_set() # Set focus to the entry widget
                    self.entry.update_idletasks()
            else:
                self.entry = ctk.CTkEntry(self, textvariable=self.entry_var, font=self.mydialog_font)
                self.entry.pack(pady=(0, 5))
                self.entry.focus_set() # Set focus to the entry widget
                self.entry.update_idletasks()
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(pady=10)
        self.ok_button = ctk.CTkButton(self.button_frame, text="OK", font=self.mydialog_font, command=self.on_ok)
        self.ok_button.pack(side="left", padx=10)
        self.cancel_button = ctk.CTkButton(self.button_frame, text="Cancel", font=self.mydialog_font, command=self.on_cancel)
        self.cancel_button.pack(side="right", padx=10)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.update_idletasks()
        required_height = self.winfo_reqheight()
        self.x = int((self.screen_width / 2) - (self.width / 2))
        self.y = int((self.screen_height / 2) - (required_height / 2))
        self.geometry(f"{self.width}x{required_height}+{self.x}+{self.y}")
        parent.wait_window(self)
    def on_ok(self):
        self.grab_release()
        if self.style == "entry":
            if self.choices is not None:
                if type(self.choices)==list:
                    self.result = self.combobox.get()
                else: 
                    self.result = self.entry_var.get()
            else:self.result = self.entry_var.get()
        else:self.result = None           
        self.destroy() # Close the dialog
        return self.result    
    def on_cancel(self):
        self.grab_release()
        self.result = None
        self.destroy() # Close the dialog
        return self.result    
class App(ctk.CTk):#CustomTkinter window controlled by asyncio instead of mainloop().
    def __init__(self):
        super().__init__()
        self._stop_timer=False# Timer Stop
        self._timer_running=False# Timer Status
        self.loop = asyncio.new_event_loop()# Timer Loop
        self._time_now=0.0
        self._elapsed_time=0.0
        self._paused_time=0.0
        self._factor=1.0
        self._ns_time=0.0
        self.ffplay_window=None# ffplay Window
        self.process_ffplay=None# ffmplay Process
        self.ffplay_running=False# ffplay Process Status
        self.cv2_running=False# CV2 Image Status
        self.click_next=False# Media File Finished, Simulate Next Button Click
        self.next_ready=True
        self.listener=None# Keyboard Listener For Show Images
        self.Media_Dict={}# Shuffled Or UnShuffled Song,Video,Image Dictionary
        self.Original_Dict={}# Original Sorted Unshuffled
        self.active_database=""
        self.active_media=""
        self.active_file=""
        self.active_folder=""
        self.initial_sound_device=""
        self.key_now=None# Active Media File Key
        self.last_key=None
        self.repeat=False
        self.shuffled=False
        self.seeking=False
        self.duration=100.00
        self.start_time=0.0
        self.trough=False
        self.muted=False
        self.paused=False
        self.show_modes=["video","waves","rdft"]
        self.show_mode=self.show_modes[0]
        self.full_screen=False
        self.showmode_change=True
        self.slider_clicked=False
        devices=AudioUtilities.GetSpeakers()# Initialize Master Volumn Slider
        self.output_devices=[]
        self.active_device=None
        self.interface = devices.EndpointVolume
        pgm_path=Path(__file__).parent.absolute()
        self.download_path=os.path.join(os.path.expanduser("~"),"youtube_downloads.json")
        self.readme_path=os.path.join(pgm_path,"Bound_Keys_en.txt")
        self.music_folder=Path(os.path.join(Path.home(),"Music"))
        self.picture_folder=Path(os.path.join(Path.home(),"Pictures"))
        self.video_folder=Path(os.path.join(Path.home(),"Videos"))
        # Create Media Folders If Not Exist
        folder_paths=[self.music_folder, self.video_folder, self.picture_folder]
        for k in range(len(folder_paths)):# Create Media Folders And Pin To Quick Access 
            if not os.path.exists(folder_paths[k]):
                os.makedirs(folder_paths[k])
                try:# Pin Folders To Quick Access
                    qa_cmd = f"""
                        $o = new-object -com shell.application
                        $o.Namespace('{folder_paths[k]}').Self.InvokeVerb('pintohome')
                        """
                    subprocess.run(["powershell", "-Command", qa_cmd], capture_output=True)
                except Exception:
                    pass
        json_files=["Pictures.json", "Music.json", "Videos.json"]
        data={}
        for k in range(len(json_files)):# Create Media json files
            if not os.path.exists(json_files[k]):
                try:
                    with open(json_files[k], "w") as json_file:
                            json.dump(data, json_file, indent=4) # indent=4 for pretty-printing
                except Exception:
                    pass
      # Define All Supported File Extensions
        self.ffmpeg_audio_exts=['mp3','wma','wav','mp2','ac3','aac','eac3','m4a','wmav1','wmav2','opus','ogg','aiff','alac','ape','flac']
        self.ffmpeg_video_exts=['mp4','avi','mov','mkv','mpg','mpeg','wmv','webm','flv','mj2','3gp','3g2']
        self.ffmpeg_image_exts=['bmp','jpg','jpeg','gif','png','ppm','dib']
        self.user=os.getlogin()
        self.title_txt=[f"{self.user}'s Media Player:", "Right Click Media List For Options"]
        self.title(self.title_txt[0] + self.title_txt[1].rjust(40+len(self.title_txt[1])))
        self.configure(fg_color=("#00416a","#555555"))
        self.wm_attributes("-topmost",True)
        self.protocol("WM_DELETE_WINDOW", self._close_main)
        self.resizable(True, True)
        self.appearance_mode=ctk.get_appearance_mode()
        temp_dict=json.load(open("Config.json", "r+"))
        global Default_DPI
        if len(temp_dict)==1:# Only Theme Exist
            Default_DPI = self.winfo_fpixels('1i')
        else:
            Default_DPI = temp_dict["6"]    
        std_sizes=[-12, -14, -16, -18, -26, -30]
        sizes=[]
        factor = (Default_DPI / 96.0)  # 96 is standard DPI for 1 point
        for f in range(len(std_sizes)):
            sizes.append(int(std_sizes[f] * factor))  # adjust for high‑DPI        
        self.slider_font=ctk.CTkFont(family='Times New Romans', size=sizes[0], weight='normal', slant='italic')# Play List
        self.title_font=ctk.CTkFont(family='Times New Romans', size=sizes[1], weight='bold', slant='italic')# Play List
        self.media_font=ctk.CTkFont(family='Times New Romans', size=sizes[2], weight='normal', slant='italic')# Play List
        self.quit_font=ctk.CTkFont(family='Times New Romans', size=sizes[3], weight='normal', slant='italic')# Quit Button Text
        self.emoji_font=ctk.CTkFont(family='Noto Emoji', size=sizes[4], weight='normal', slant='roman')# All Other Buttons
        self.emoji_font2=ctk.CTkFont(family='Noto Emoji', size=sizes[5], weight='normal', slant='roman')# All Other Buttons
        self.shared_download_files=os.path.join(os.path.expanduser("~"),"youtube_downloads.json")# Store Folder And Song Title Here For Sharing
        self.Start_Time=ctk.DoubleVar()
        self.Time_Now=ctk.DoubleVar()
        self.Time_Now_Txt=ctk.StringVar()
        self.Volume_Level=ctk.DoubleVar()# Volume Meter
        self.Volume_Now_Txt=ctk.StringVar()
        self.Screen_Height=ctk.IntVar()
        self.Screen_Position=ctk.StringVar()
        self.Slide_Show_Delay=ctk.DoubleVar()
        self.Image_Size=ctk.StringVar()
        self.Theme=ctk.StringVar()
        self.Theme.set(self.appearance_mode)
        self.T_Color=ctk.StringVar()
        self.B_Color=ctk.StringVar()
        self.F_Color=ctk.StringVar()
        self.ffmpeg_resources = self.resource_path("ffmpeg\\bin")
        self.ffprobe_path = os.path.join(self.ffmpeg_resources, "ffprobe.exe")
        self.ffplay_path = os.path.join(self.ffmpeg_resources, "ffplay.exe")
        self.svv_resources = self.resource_path("soundvolumeview\\bin")
        self.soundvolumeview_path=os.path.join(self.svv_resources,"SoundVolumeView.exe")
        self.deno_resources = self.resource_path("deno\\bin")
        self.deno_path=os.path.join(self.deno_resources,"deno.exe")
        self.keys_path=os.path.join(pgm_path,"Bound_Keys_en.txt")
        self.output_devices=[]
        self.path_dict={}
        self.ico_path=os.path.join(pgm_path, 'player.ico')
        self.iconbitmap(default=self.ico_path)# self.and children
        self.iconbitmap(self.ico_path)
        self.update_idletasks()
        self.Image_Size.set("Normal Screen")
        self.target_handle = None
        self.taskbar_height=self.get_taskbar_height()
        self.titlebar_height = self.get_titlebar_height()
        self.screen_width = ctypes.windll.user32.GetSystemMetrics(0)
        self.screen_height = ctypes.windll.user32.GetSystemMetrics(1)
        self.work_height = self.screen_height - self.taskbar_height
        self.aspect_ratio=self.screen_width / self.work_height
        self.height = int((self.screen_height) * 0.17) 
        self.default_height = int((self.work_height-self.height) - 0.5 * self.taskbar_height) 
        self.width = int(self.default_height * self.aspect_ratio)# Make GUI Width Same As Play Window Width   
        x_correction = self.screen_width * 0.005# Correction For GUI X1 Little Off From Play Window X1
        self._x = int(((self.screen_width / 2) - ((self.width) / 2)) - x_correction)
        self._y= int((self.work_height - self.height) - self.titlebar_height)# GUI Just Above Taskbar
        self._y2=((self.screen_height / 2) - (self.height / 2))# GUI Center Screen
        self._y3=self._y + self.taskbar_height# GUI Covers Taskbar    
        self.geometry(f"{self.width}x{self.height}+{self._x}+{self._y}")
        self.update()
        self.withdraw()
        for r in range(4):# Configure Rows For main_frame 
            self.grid_rowconfigure(r, weight=1)
        for c in range(14):# Configure Columns For main_frame 
            self.grid_columnconfigure(c, weight=1)
        self.media_frame = ctk.CTkFrame(self)# Frame to hold listbox + scrollbars
        self.media_frame=ctk.CTkFrame(self, fg_color="#b3b3b3", border_width=3, corner_radius=10) 
        self.media_frame.grid(row=0, column=0, sticky="nsew", rowspan=3, columnspan=3, pady=(10, 10), padx=(10, 10))
        self.media_frame.grid_rowconfigure(0, weight=1)# Make frame expandable
        self.media_frame.grid_columnconfigure(0, weight=1)
        self.media_frame.grid_rowconfigure(0, weight=1)
        self.media_frame.grid_columnconfigure(0, weight=1)
        self.media_frame.update_idletasks()
        if self.appearance_mode=="Light":# Colors For tkListbox
            list_bg="#ffffff"
            list_fg="#0c012e"
        else:        
            list_bg="#0c012e"
            list_fg="#ffffff"
        self.media_list = Listbox(self.media_frame, bg=list_bg, fg=list_fg,font=self.media_font, selectmode="single", exportselection=False)
        self.media_list.grid(row=0, column=0, sticky="nsew", pady=(5, 0), padx=(5, 0))
        self.media_list.bind("<Button-3>", self.show_menu)
        self.v_scroll = ctk.CTkScrollbar(self.media_frame, orientation="vertical", fg_color="#b3b3b3", button_hover_color="#32cd32",
                                button_color="#00416a", corner_radius=10, command=self.media_list.yview)
        self.v_scroll.grid(row=0, column=1, sticky="ns", pady=(5, 5), padx=(0, 5))
        self.h_scroll = ctk.CTkScrollbar(self.media_frame, orientation="horizontal", fg_color="#b3b3b3", button_hover_color="#32cd32",
                                button_color="#00416a", corner_radius=10, command=self.media_list.xview)
        self.h_scroll.grid(row=1, column=0, sticky="ew", pady=(0, 5), padx=(5, 5))
        self.media_list.config(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        self.main_frame=ctk.CTkFrame(self, fg_color=("#f8f8ff","#1e90ff"), border_width=3, corner_radius=10) 
        self.main_frame.grid(row=0, column=3, rowspan=6, columnspan=11, sticky="nsew", pady=(10, 10), padx=(0, 10))
        self.main_frame.grid_propagate(False) 
        for r in range(3):# Configure Rows For main_frame 
            self.main_frame.grid_rowconfigure(r, weight=1)
        for c in range(4, 13):# Configure Columns For main_frame 
            self.main_frame.grid_columnconfigure(c, weight=1)
        self.main_frame.update_idletasks()    
        title_txt = self.get_greeting("open")
        self.title_lbl = ctk.CTkLabel(self.main_frame, text=title_txt, corner_radius=5, font=self.quit_font, anchor="center",
                        fg_color="transparent", text_color=("#0c012e","#000000"))
        self.title_lbl.grid(row=0, column=4, sticky="nsew", rowspan=1, columnspan=9, pady=(5, 0), padx=(5, 5))
        self.volume_lbl = ctk.CTkEntry(self.main_frame, fg_color="transparent", justify="center",state="disabled", border_width=0, 
                                         textvariable=self.Volume_Now_Txt, font=self.media_font, text_color=("#0c012e","#000000"))
        self.volume_lbl.grid(row=1, column=4, sticky="nsew", rowspan=1, columnspan=4, pady=(0, 0), padx=(5, 5))
        if self.appearance_mode=="Light":# Colors For tkScales
            slider_bg="#ffffff"
            slider_fg="#f8f8ff"
            slider_tc="#a9a9a9"
        else:        
            slider_bg="#0c012e"
            slider_fg="#1e90ff"
            slider_tc="#555555"
        self.volume_scale = Scale(self.main_frame, variable=self.Volume_Level, relief="sunken",orient='horizontal',resolution=0.01,from_=0.0, to=100.0,
                            bg=slider_fg,borderwidth=0,font=self.slider_font,troughcolor=slider_tc, showvalue=0,  
                            foreground="black",tickinterval=20, activebackground="#4cffff",highlightthickness=0, command=self.set_master_volume)
        self.volume_scale.grid(row=2, column=4, sticky="nsew", rowspan=1, columnspan=4, pady=(0, 0), padx=(10, 10))
        self.volume_scale.bind("<ButtonRelease-1>",lambda event:self.slider_released(event))# Sets Video Window active
        self.time_lbl = ctk.CTkEntry(self.main_frame, fg_color="transparent", justify="center",state="disabled", border_width=0, 
                                         textvariable=self.Time_Now_Txt, font=self.media_font, text_color=("#0c012e","#000000"))
        self.time_lbl.grid(row=1, column=8, sticky="nsew", rowspan=1, columnspan=6, pady=(0, 0), padx=(5, 5))
        self.time_scale = Scale(self.main_frame, variable=self.Time_Now, relief="sunken",orient='horizontal',resolution=0.01,from_=0.0, to=100.0,
                            bg=slider_fg,borderwidth=0, font=self.slider_font, troughcolor=slider_tc, showvalue=0,  
                            foreground="black",tickinterval=10, activebackground="#4cffff", highlightthickness=0, command=self.on_slide)
        self.time_scale.grid(row=2, column=8, sticky="nsew", rowspan=1, columnspan=6, pady=(0, 0), padx=(10, 10))
        self.time_scale.bind("<ButtonRelease-1>",lambda event:self.end_seeking(event))
        self.time_scale.bind("<ButtonPress-1>",lambda event:self.begin_seeking(event))
        self.btn_frame=ctk.CTkFrame(self.main_frame, fg_color=("#f8f8ff","#1e90ff"), border_width=3, corner_radius=5, height=40) 
        self.btn_frame.grid(row=3, column=4, columnspan=10, rowspan=1, sticky="nsew", pady=(0, 10), padx=(10, 10)) 
        self.btn_frame.grid_propagate(True)
        self.play_btn = ctk.CTkButton(self.btn_frame, text="     ▶️", border_width=2, corner_radius=5, font=self.emoji_font2, anchor="center",
                    fg_color=("#a6e7ff", "#0c012e"), hover_color="#00ced1", text_color=("#0c012e", "#ffffff"))
        self.play_btn.grid(row=0, column=0, columnspan=1, rowspan=1, sticky="nsew", pady=(5, 5), padx=(5, 2))
        self.play_btn.bind("<ButtonRelease>",lambda event:self.ctrl_btn_clicked(event,"btn play"))
        self.btn_frame.grid_columnconfigure(0, weight=1)
        self.shuffle_btn = ctk.CTkButton(self.btn_frame, text="🔀", border_width=2, corner_radius=5, font=self.emoji_font2, anchor="center",
                    fg_color=("#a6e7ff", "#0c012e"), hover_color="#00ced1", text_color=("#0c012e", "#ffffff"))
        self.shuffle_btn.grid(row=0, column=1, columnspan=1, rowspan=1, sticky="nsew", pady=(5, 5), padx=(5, 2))
        self.shuffle_btn.bind("<ButtonRelease>",lambda event:self.ctrl_btn_clicked(event,"shuffled"))
        self.btn_frame.grid_columnconfigure(1, weight=1)
        self.previous_btn = ctk.CTkButton(self.btn_frame, text="⏮️", border_width=2, corner_radius=5, font=self.emoji_font, anchor="center",
                    fg_color=("#a6e7ff", "#0c012e"), hover_color="#00ced1", text_color=("#0c012e", "#ffffff"))
        self.previous_btn.grid(row=0, column=2, columnspan=1, rowspan=1, sticky="nsew", pady=(5, 5), padx=(5, 2))
        self.previous_btn.bind("<ButtonRelease>",lambda event:self.ctrl_btn_clicked(event,"previous"))
        self.btn_frame.grid_columnconfigure(2, weight=1)
        self.next_btn = ctk.CTkButton(self.btn_frame, text="⏭️", border_width=2, corner_radius=5, font=self.emoji_font, anchor="center",
                    fg_color=("#a6e7ff", "#0c012e"), hover_color="#00ced1", text_color=("#0c012e", "#ffffff"))
        self.next_btn.grid(row=0, column=3, columnspan=1, rowspan=1, sticky="nsew", pady=(5, 5), padx=(5, 2))
        self.next_btn.bind("<ButtonRelease>",lambda event:self.ctrl_btn_clicked(event,"next"))
        self.btn_frame.grid_columnconfigure(3, weight=1)
        self.pause_btn = ctk.CTkButton(self.btn_frame, text="⏸️", border_width=2, corner_radius=5, font=self.emoji_font, anchor="center",
                    fg_color=("#a6e7ff", "#0c012e"), hover_color="#00ced1", text_color=("#0c012e", "#ffffff"))
        self.pause_btn.grid(row=0, column=4, columnspan=1, rowspan=1, sticky="nsew", pady=(5, 5), padx=(5, 2))
        self.pause_btn.bind("<ButtonRelease>",lambda event:self.pause(event))
        self.btn_frame.grid_columnconfigure(4, weight=1)
        self.repeat_btn = ctk.CTkButton(self.btn_frame, text="🔁", border_width=2, corner_radius=5, font=self.emoji_font2, anchor="center",
                    fg_color=("#a6e7ff", "#0c012e"), hover_color="#00ced1", text_color=("#0c012e", "#ffffff"))
        self.repeat_btn.grid(row=0, column=5, columnspan=1, rowspan=1, sticky="nsew", pady=(5, 5), padx=(5, 2))
        self.repeat_btn.bind("<ButtonRelease>",lambda event:self.ctrl_btn_clicked(event,"repeat"))
        self.btn_frame.grid_columnconfigure(5, weight=1)
        self.mute_btn = ctk.CTkButton(self.btn_frame, text="\U0001F50A", border_width=2, corner_radius=5, font=self.emoji_font2, anchor="center",
                    fg_color=("#a6e7ff", "#0c012e"), hover_color="#00ced1", text_color=("#0c012e", "#ffffff"))
        self.mute_btn.grid(row=0, column=6, columnspan=1, rowspan=1, sticky="nsew", pady=(5, 5), padx=(5, 2))
        self.mute_btn.bind("<ButtonRelease>",lambda event:self.ctrl_btn_clicked(event,"mute"))
        self.btn_frame.grid_columnconfigure(6, weight=1)
        self.stop_btn = ctk.CTkButton(self.btn_frame, text="⏹️", border_width=2, corner_radius=5, font=self.emoji_font, anchor="center",
                    fg_color=("#a6e7ff", "#0c012e"), hover_color="#00ced1", text_color=("#0c012e", "#ffffff"))
        self.stop_btn.grid(row=0, column=7, columnspan=1, rowspan=1, sticky="nsew", pady=(5, 5), padx=(5, 2))
        self.stop_btn.bind("<ButtonRelease>",lambda event:self.ctrl_btn_clicked(event,"stop"))
        self.btn_frame.grid_columnconfigure(7, weight=1)
        self.quit_btn = ctk.CTkButton(self.btn_frame, text="Quit", border_width=2, corner_radius=5, font=self.quit_font, anchor="center",
                    fg_color=("#a6e7ff", "#0c012e"), hover_color="#00ced1", text_color=("#0c012e", "#ffffff"))
        self.quit_btn.grid(row=0, column=8, columnspan=1, rowspan=1, sticky="nsew", pady=(5, 5), padx=(5, 5))
        self.btn_frame.grid_columnconfigure(8, weight=1)
        self.quit_btn.bind("<ButtonRelease>",lambda event:self._close_main())
        self.quit_btn.update_idletasks()
        new_height=int(self.play_btn.winfo_height() + 10)
        self.btn_frame.configure(height = new_height)
        self.btn_frame.update_idletasks()
        self.deiconify()
        self.update()
        self.bind_keyboard()
        self.set_defaults()
        self.read_setup()
        self.init_audio()
        self.load_library(self.active_database, None)
    def resource_path(self, relative):
        if getattr(sys, 'frozen', False):
            if hasattr(sys, "_MEIPASS"):
                return os.path.join(sys._MEIPASS, relative)
        else:
            return os.path.join(os.path.abspath("."), relative)
    def get_titlebar_height(self):
        user32 = ctypes.windll.user32
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            return None
        SM_CYCAPTION = 4
        SM_CYFRAME = 33
        SM_CXPADDEDBORDER = 92
        titlebar_height = (user32.GetSystemMetrics(SM_CYFRAME) +
                user32.GetSystemMetrics(SM_CYCAPTION) +
                user32.GetSystemMetrics(SM_CXPADDEDBORDER))
        return titlebar_height
    def get_taskbar_height(self):
        try:
            h_monitor = MonitorFromPoint((0, 0))
            monitor_info = GetMonitorInfo(h_monitor)
            rc_monitor = monitor_info.get("Monitor")
            rc_work = monitor_info.get("Work")
            if not rc_monitor or not rc_work:
                raise RuntimeError("Monitor information not available.")
            full_height = rc_monitor[3] - rc_monitor[1]
            work_height = rc_work[3] - rc_work[1]
            # Taskbar height (only valid if taskbar is horizontal)
            taskbar_height = full_height - work_height
            full_width = rc_monitor[2] - rc_monitor[0]
            work_width = rc_work[2] - rc_work[0]
            taskbar_width = full_width - work_width
            if taskbar_height > 0:  # Taskbar at top or bottom
                return taskbar_height
            else:  # Taskbar on left or right
                return taskbar_width
        except Exception as e:
            return None
    def get_greeting(self, status):
        user=os.getlogin()
        current_datetime = datetime.now()
        if current_datetime.hour<12:
            if status=="open":greeting=f"Good Morning {user} and Welcome!"
            else:greeting=f"Goodbye {user}, Have a Wonderful Morning!"    
        elif current_datetime.hour>=12 and current_datetime.hour<18:
            if status=="open":greeting=f"Good Afternoon {user} and Welcome!"
            else:greeting=f"Goodbye {user}, Have a Wonderful Afternoon!"    
        elif current_datetime.hour>=18 and current_datetime.hour<=24:
            if status=="open":greeting=f"Good Evening {user} and Welcome!"
            else:greeting=f"Goodbye {user}, Have a Wonderful Night!"
        return greeting        
    def give_greeting(self, status):
        current_datetime = datetime.now()
        if status == "open":
            if current_datetime.hour<12:
                greeting=f"Good Morning {self.user}."
            elif current_datetime.hour>=12 and current_datetime.hour<17:
                greeting=f"Good Afternoon {self.user}."
            elif current_datetime.hour>=17 and current_datetime.hour<=24:
                greeting=f"Good Evening {self.user}."
        elif status == "close":        
            if current_datetime.hour<12:
                greeting=f"Goodbye {self.user}. Have a Wonderful Morning!"
            elif current_datetime.hour>=12 and current_datetime.hour<17:
                greeting=f"Goodbye {self.user}. Have a Wonderful Afternoon!"
            elif current_datetime.hour>=17 and current_datetime.hour<=24:
                greeting=f"Goodbye {self.user}. Have a Wonderful Evening!"
        elif status == "restart":
            greeting = "Restarting Program!"
        else:            
            if current_datetime.hour<12:
                greeting=f"Good Morning {self.user}."
            elif current_datetime.hour>=12 and current_datetime.hour<17:
                greeting=f"Good Afternoon {self.user}."
            elif current_datetime.hour>=17 and current_datetime.hour<=24:
                greeting=f"Good Evening {self.user}."
        self.title_lbl.configure(text = "")        
        self.greet_popup = Timed_Popup(self.title_lbl, text=greeting, text_color="#000000", 
                            fg_color="#14fafa", font_size=-20, delay_time=1500)
    def read_setup(self):
        with open('Config.json', 'r') as json_file:
            data = json.load(json_file)
            self.Screen_Height.set(data.get("0"))
            self.Screen_Position.set(data.get("1"))
            self.Slide_Show_Delay.set(data.get("2"))
            self.active_database = data.get("3")
            self.Theme.set(data.get("4"))
            self.Volume_Level.set(data.get("5"))
            global Default_DPI
            Default_DPI = data.get("6")
    def write_setup(self):
        temp_dict={}
        sc=json.load(open("Config.json", "r"))
        json.dump(sc,open("Config.json", "w"),indent=4)
        temp_dict[0]=self.Screen_Height.get()
        temp_dict[1]=self.Screen_Position.get()
        temp_dict[2]=self.Slide_Show_Delay.get()
        temp_dict[3]=self.active_database
        temp_dict[4]=self.Theme.get()
        temp_dict[5]=self.Volume_Level.get()
        temp_dict[6]=Default_DPI
        with open("Config.json", "w") as outfile:json.dump(temp_dict, outfile)
        outfile.close()
        temp_dict.clear()
    def set_defaults(self):
        temp_dict=json.load(open("Config.json", "r+"))
        if len(temp_dict)==1:# Only Theme Exist
            self.Screen_Height.set(self.default_height)
            self.Screen_Position.set("Top Center")
            self.Slide_Show_Delay.set(0.0)
            self.active_database=""
            ctk.set_appearance_mode("Dark")
            self.Volume_Level.set(30.0)
            self.Theme.set(ctk.get_appearance_mode())
            self.write_setup()
            self.init_dependencies()# Initialize ffmpeg files with PC Matic
        else:    
            self.active_database=temp_dict["3"]
    def get_audio_devices(self, direction="in", State = DEVICE_STATE.ACTIVE.value):
        devices = []
        # for all use EDataFlow.eAll.value
        if direction == "in":
            Flow = EDataFlow.eCapture.value# 1
        else:
            Flow = EDataFlow.eRender.value# 0
        deviceEnumerator = comtypes.CoCreateInstance(
            CLSID_MMDeviceEnumerator,
            IMMDeviceEnumerator,
            comtypes.CLSCTX_INPROC_SERVER)
        if deviceEnumerator is None:
            return devices
        collection = deviceEnumerator.EnumAudioEndpoints(Flow, State)
        if collection is None:
            return devices
        count = collection.GetCount()
        for i in range(count):
            dev = collection.Item(i)
            if dev is not None:
                if not ": None" in str(AudioUtilities.CreateDevice(dev)):
                    self.output_devices.append(AudioUtilities.CreateDevice(dev).id)
                    devices.append(AudioUtilities.CreateDevice(dev).FriendlyName)
        return devices
    def config_video_library(self):
        title = "< Configure Video Library >"
        msg = 'Select The Desired Task To Perform To Video Library.'
        args = ["Set Video Library As Active Library","Upload Folder To Video Library","Add Files To Video Library","Clear Video Library"]
        response = MyDialog(self, title=title, style="entry", prompt=msg, choices=args, init_val=None, icon="setup.png")
        if response.result in args:
            index = args.index(response.result)
            if index == 0:
                self.load_library("Videos", None)
            elif index == 1:
                self.upload_from_folder("Videos", None, True)
            elif index == 2:
                self.add_files_to_db("Videos")
            elif index == 3:
                self.clear_database("Videos")
            else:return        
    def config_music_library(self):
        title = "< Configure Music Library >"
        msg = 'Select The Desired Task To Perform To Music Library.'
        args = ["Set Music Library As Active Library","Upload Folder To Music Library","Add Files To Music Library","Clear Music Library"]
        response = MyDialog(self, title=title, style="entry", prompt=msg, choices=args, init_val=None, icon="setup.png")
        if response.result in args:
            index = args.index(response.result)
            if index == 0:
                self.load_library("Music", None)
            elif index == 1:
                self.upload_from_folder("Music", None, True)
            elif index == 2:
                self.add_files_to_db("Music")
            elif index == 3:
                self.clear_database("Music")
            else:return        
    def config_image_library(self):
        title = "< Configure Picture Library >"
        msg = 'Select The Desired Task To Perform To Picture Library.'
        args = ["Set Picture Library As Active Library","Upload Folder To Picture Library",
                "Add Files To Picture Library","Clear Picture Library", "Set Slide Show Delay For Picture Library", 
                "Set Image Size"]
        response = MyDialog(self, title=title, style="entry", prompt=msg, choices=args, init_val=None, icon="setup.png")
        if response.result in args:
            index = args.index(response.result)
            if index == 0:
                self.load_library("Pictures", None)
            elif index == 1:
                self.upload_from_folder("Pictures", None, True)
            elif index == 2:
                self.add_files_to_db("Pictures")
            elif index == 3:
                self.clear_database("Pictures")
            elif index == 4:
                self.set_slide_show()
            elif index == 5:
                self.set_image_size()
            else:return        
    def set_screen_size(self):
        title = "< Set Video Screen Size >"
        msg1 = 'Enter A Screen Height For Video Playback.\n'
        msg2 = f"Default Screen Height For This Monitor = {self.default_height}.\n"
        msg3 = f'Maximum Height Leaving Taskbar Visible is {str(self.work_height)}.\n'
        msg4 = 'The Screen Width Will Be Determined By\n'
        msg5 = 'This Monitors Aspect Ratio!'
        msg = msg1+msg2+msg3+msg4+msg5
        hgt = MyDialog(self, title=title, style="entry", prompt=msg, choices=None, init_val=self.Screen_Height.get(), icon="setup.png")
        if hgt.result is not None:
            self.Screen_Height.set(hgt.result)
            with open("Config.json", 'r') as json_file:
                data = json.load(json_file)
            data["0"] = self.Screen_Height.get()
            with open("Config.json", 'w') as json_file:
                json.dump(data, json_file, indent=4)
            json_file.close()    
    def set_screen_position(self):
        title = "< Set Video Position >"
        msg1 = 'Select A Screen Position For Video Playback.\n'
        msg2 = 'The Default Position Is ' + self.Screen_Position.get()+'.'
        msg = msg1+msg2
        positions = ["Top Center","Top Left","Top Right","Center Left","Center","Center Right","Bottom Left","Bottom Center","Bottom Right"]
        msg = "Select The Desired Video Screen Position, Then Click OK."
        pos = MyDialog(self, title=title, style="entry", prompt=msg, choices=positions, init_val=self.Screen_Position.get(), icon="setup.png")
        if pos.result is not None:
            self.Screen_Position.set(pos.result)
            with open("Config.json", 'r') as json_file:
                data = json.load(json_file)
            data["1"] = self.Screen_Position.get()
            with open("Config.json", 'w') as json_file:
                json.dump(data, json_file, indent=4)
            json_file.close()    
    def select_audio_device(self, device=None):
        try:
            devices=self.get_audio_devices("out")
            result=list(filter(lambda x: device in x, devices))
            self.active_database=result[0]
            soundview_device=result[0].split("(", 1)[0].replace(" ","")
            cmd=[self.soundvolumeview_path, "/SetDefault", soundview_device, "1", "/Unmute", soundview_device, "/SetVolume", soundview_device, str(self.Volume_Level.get())]
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            devices=AudioUtilities.GetSpeakers()# Initialize Master Volumn Slider
            self.interface = devices.EndpointVolume
            self.Master_Volume=ctypes.cast(self.interface, ctypes.POINTER(IAudioEndpointVolume))
            self.Master_Volume.SetMasterVolumeLevelScalar(self.Volume_Level.get() / 100, None)
            self.title(f"{self.title_txt[0]} Playing ({self.active_database.replace("_"," ")} Library), Playing On Audio Device: {result[0]} {self.title_txt[1].rjust(30+len(self.title_txt[1]))}")
        except Exception as ex:
            title='<Audio Output Device>'
            msg1='Initialization Audio Device Failed. Ending Program!\n'
            msg2=f"Error: '{ex}'"
            msg3="Using Default Audio Device."
            msg=msg1+msg2+msg3
            MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="cancel.png")
            pass
    def _close_main(self):
        self.loop.stop()
        self.destroy()
    def _run_main(self):# Run the mainloop and timer loop together
        self._run_asyncio_loop()
        self.mainloop()
    def _run_asyncio_loop(self):
        def poll():
            try:
                self.loop.call_soon(self.loop.stop)
                self.loop.run_forever()
            except RuntimeError:
                pass
            self.after(10, poll)
        poll()
    def _reset_timer(self):        
        self._stop_timer=False
        self.Start_Time.set(0.0)
        self.Time_Now.set(float(self.start_time))
        self._timer_running=False
        self._time_now=self.start_time
        self._elapsed_time=0.0
        self._paused_time=0.0
        self._factor=1.0
        self._ns_time=0.0
    def _start_timer(self):
        self.next_ready=True
        if self.click_next:
            self._timer_running=True
            self.ctrl_btn_clicked(self,"next")
        else:
            try:
                self._timer_running=True
                self.loop.create_task(self._timer_task())
            except Exception as e:
                pass
    async def _timer_task(self):
        self.send_keyboard_key("left")# Make Sure Timer Is Zero
        if self.duration > 0.0:
            while not self._stop_timer:
                await asyncio.sleep(0.01) # Non-blocking sleep For events
                if not self._timer_running:break
                if self.active_media=="music" or self.active_media=="video":
                    if not self.ffplay_running:break 
                elif self.active_media=="image":
                    if not self.cv2_running:break
                foreground_hwnd = win32gui.GetForegroundWindow()
                if foreground_hwnd==self.target_handle:# Keep Focus On root To Capture All Events
                    await asyncio.sleep(0.01) # Non-blocking sleep For events
                    self.focus_force()  
                    self.update_idletasks()
                if self.paused:# self._factor Is Correction For Paused Time For Slider
                    self._paused_time=perf_counter_ns()
                    self._factor=self._ns_time/self._paused_time
                else:
                    self._ns_time=perf_counter_ns()*self._factor
                    self._elapsed_time=(self._ns_time-self.Start_Time.get())/1000000000
                    self._time_now+=self._elapsed_time
                    self.Time_Now.set(float(self._time_now))
                    remaining = self.duration - self._time_now
                    if remaining < 0.0:
                        self._time_now = self.duration 
                        remaining = 0.0
                    self.Time_Now_Txt.set(f"Total Time:{round(self.duration, 1)} sec., Elapsed Time:{round(self._time_now, 1)} sec., Remaining Time: {round(remaining, 1)} sec.")
                    self.Start_Time.set(self.Start_Time.get()+(self._elapsed_time*1000000000))
                    if self.ffplay_running:
                        poll=self.process_ffplay.poll()
                        if poll!=None:
                            self.click_next=True# ffplay not running, Terminated By -autoexit, Ready Next File
                            self._stop_timer=True
                            break
                level=self.Master_Volume.GetMasterVolumeLevelScalar()# Volume Slider Level / 100
                self.Volume_Level.set(level * 100)# Track Volume From Other Sliders (Windows, Sound Card)
                is_muted=self.Master_Volume.GetMute()
                if is_muted and self.muted==False:self.ctrl_btn_clicked(self,"mute")
                elif not is_muted and self.muted==True:self.ctrl_btn_clicked(self,"mute")
            if self.click_next:self.ctrl_btn_clicked(self,"next")
    def change_showmode(self, display_type):
        self.focus_force()
        if self.showmode_change:
            if self.show_mode==self.show_modes[0]:# Video
                if display_type=='waves':self.show_mode=self.show_modes[1]# Waves
                else:return    
            elif self.show_mode==self.show_modes[1]:# Waves, Skip showmode[2]
                if display_type=='video':
                    self.show_mode=self.show_modes[0]# Video
                    self.send_keyboard_key("showmode")
                else:return    
            self.send_keyboard_key("showmode")
            if self.show_mode==self.show_modes[0] and self.full_screen: window_y = self._y3#Video GUI Covers Taskbar    
            elif self.show_mode==self.show_modes[0] and not self.full_screen: window_y = self._y# GUI Just Above Taskbar
            elif self.show_mode==self.show_modes[1] and self.full_screen: window_y = self._y2#Wave GUI Center Screen
            elif self.show_mode==self.show_modes[1] and not self.full_screen: window_y = self._y# GUI Just Above Taskbar
            else: window_y = self._y
            self.geometry('%dx%d+%d+%d' % (self.width, self.height, self._x, window_y))
            self.update()
    def change_screen(self, screen_type, send_key=True):
        self.focus_force()
        try:
            if self.full_screen and screen_type == "normal screen":
                self.full_screen = False
            elif not self.full_screen and screen_type == "full screen":     
                self.full_screen = True
            if send_key:self.send_keyboard_key(screen_type)
            if self.show_mode==self.show_modes[0] and self.full_screen: window_y = self._y3#Video GUI Covers Taskbar    
            elif self.show_mode==self.show_modes[0] and not self.full_screen: window_y = self._y# GUI Just Above Taskbar
            elif self.show_mode==self.show_modes[1] and self.full_screen: window_y = self._y2#Wave GUI Center Screen
            elif self.show_mode==self.show_modes[1] and not self.full_screen: window_y = self._y# GUI Just Above Taskbar
            else: window_y = self._y
            self.geometry('%dx%d+%d+%d' % (self.width, self.height, self._x, window_y))
            self.update()
        except Exception as e:
            pass
    def set_slide_show(self):
        title='< Set Slide Show Delay Time In Seconds >'
        msg1='Note: The Edit Picture Menu Is Not Visible When Delay > 0.0!\n'
        msg2='Enter A Delay Time In Seconds For Picture Slide Show. A Delay\n'
        msg3='Time Of 0.0 Seconds Indicates No Slide Show But, The Pictures\n'
        msg4='Will Advance Every 5 Minutes For Screen Protection. Minimum\n'
        msg5='Delay Time Is 0.5 Seconds And Maximum is 30 Seconds.'
        msg=msg1+msg2+msg3+msg4+msg5
        delay=MyDialog(self, title=title, style="entry", prompt=msg, choices=None, init_val=self.Slide_Show_Delay.get(), min_val=0.0, max_val=30.0, icon="setup.png")
        if delay.result is not None:
            while float(delay.result) < 0.0 or float(delay.result) > 30.0: 
                delay=MyDialog(self, title=title, style="entry", prompt=msg, choices=None, init_val=self.Slide_Show_Delay.get(), min_val=0.0, max_val=30.0, icon="setup.png")
            self.Slide_Show_Delay.set(float(delay.result))
    def set_color_theme(self, theme):
        title = " < Set Color Theme >"
        msg = "Select The Desired Color Theme, Then Click OK."
        theme=MyDialog(self, title=title, style="entry", prompt=msg, choices=["System", "Dark", "Light"], init_val=self.Theme.get(), icon="setup.png")
        if theme.result is not None:
            if self.Theme.get() != theme.result:
                self.Theme.set(theme.result)
                with open('Config.json', 'r') as json_file:
                    data = json.load(json_file)
                data["4"] = self.Theme.get()
                with open('Config.json', 'w') as json_file:
                    json.dump(data, json_file, indent=4)
                json_file.close()
                self.grab_release()
                self.restart_program()
            else:self.grab_release()     
        else:self.grab_release()    
    def show_menu(self, event):
        if not self.ffplay_running and not self.cv2_running:
            captions=["Configure Video Library", "Configure Music Library", "Configure Picture Library", "Set Video Screen Size", 
                      "Set Video Screen Position", "Set Picture Screen Size", "Select Audio Output Device", "Open Youtube Downloader", 
                      "Set Slide Show Delay", "Set Color Theme", "Clear All Libraries", "View Keyboard Keys", "About Media Player"]
            commands=[lambda: self.config_video_library(), lambda: self.config_music_library(), 
                      lambda: self.config_image_library(), lambda: self.set_screen_size(), 
                      lambda: self.set_screen_position(),lambda: self.set_image_size(), 
                      lambda: self.update_audio_devices(), lambda: self.youtube_downloader(), 
                      lambda:self.set_slide_show(), lambda arg='color_theme': self.set_color_theme(arg),
                      lambda:self.clear_all_libraries(), lambda: subprocess.Popen(["notepad.exe", self.keys_path]), lambda: self.about()] 
        elif self.cv2_running and not self.ffplay_running:
            if self.Slide_Show_Delay.get() == 0.0:
                captions = ["Rotate Image And Save", "Remove Image From Picture Library", "Delete Image To Recycle Bin"]
                commands = [lambda:self.rotate_image(), lambda:self.remove_media_file(None,True), lambda:self.delete_image_file()]
            else: return    
        elif self.ffplay_running and not self.cv2_running:
            if self.full_screen:
                title = "Show Normal Screen"
                txt = "normal screen"
            else:
                title = "Show Full Screen"
                txt = "full screen"    
            captions = ["Show Video/Art", "Show Waves", title]
            commands = [lambda:self.change_showmode('video'), lambda:self.change_showmode('waves'), lambda:self.change_screen(txt, True)]
        else:return
        self.popup_menu = Popup_Menu(self, captions , commands, -18, self.winfo_pointerx(), self.winfo_pointery(), "bottom")
        self.popup_menu.bind("<Button-3>", lambda e: self.popup_menu.withdraw())
        if self.cv2_running:
            self.popup_menu.bind("<Button-3>", lambda e: self.popup_menu.grab_release())
            self.popup_menu.bind("<Button-3>", lambda e: self.popup_menu.destroy())
        self.wait_window(self.popup_menu)
        try:
            self.popup_menu.grab_release()
            self.popup_menu.destroy()
        except:pass    
    def set_master_volume(self, value):
        if float(value) > 50:
            self.volume_scale.configure(activebackground="#ff033e")
        else:    
            self.volume_scale.configure(activebackground="#4cffff")
        with open("Config.json", 'r') as file:
            data = json.load(file)
        data["5"]=round(self.Volume_Level.get())
        with open("Config.json", 'w') as file:
            json.dump(data, file, indent=4)
        self.Master_Volume.SetMasterVolumeLevelScalar(self.Volume_Level.get() / 100, None)
        level=self.Master_Volume.GetMasterVolumeLevelScalar()# Volume Slider Level / 100
        db_level=self.Master_Volume.GetMasterVolumeLevel()
        if level==0:self.Master_Volume.SetMute(True, None)
        else:self.Master_Volume.SetMute(False, None)
        self.Volume_Now_Txt.set(f"Level: {int(float(value))} %  /  {round(db_level, decimals=2)} dB")
    def on_slide(self, value):
        try:
            if self.duration > 0.0:
                remaining = self.duration - float(value)
                self.Time_Now_Txt.set(f"Total Time:{round(self.duration, 1)} sec., Elapsed Time:{float(value)} sec., Remaining Time: {round(remaining, 1)} sec.")
        except Exception as e:
            pass
    def about(self):
        title = "< ABOUT MEDIA PLAYER >"
        msg1='Creator: Ross Waters'
        msg2='\nEmail: RossWatersjr@gmail.com'
        msg3=f'\nRevision: {version}'
        msg4='\nCreated For Windows 11'
        msg=msg1+msg2+msg3+msg4
        MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="info.png")
    def clear_display(self):
        self.media_list.delete(0,"end")
        self.media_list.update()
    def clear_all(self):# Clear Window Widget
        try:
            self.clear_display()
            self.Media_Dict.clear()
            self.Original_Dict.clear()
            self.title_txt = [f"{self.user}'s Media Player:", "Right Click Media List For Options"]
            self.title(self.title_txt[0] + self.title_txt[1].rjust(40+len(self.title_txt[1])))
            self.update()
        except Exception as e:
            pass
    def clear_all_libraries(self):
        libs=["Music.json","Videos.json","Pictures.json"]
        for db in libs:
            empty={}
            with open(db, "w") as outfile:json.dump(empty, outfile)
            outfile.close()
            self.clear_all()
            self.active_database=""
    def init_dependencies(self):
        # Notes: This Function Only Used To Initialize Dependencies With Your AntiVirus Pgm.
        # For Allowing An Unknown Program To Execute!
        try:
            title = "< Initializing FFMPEG >"
            msg1=f"ffmpeg.exe Could Not Be Found. Ending Program!\n"
            FFMPEG_path = os.path.join(self.ffmpeg_resources, "ffmpeg.exe")
            result = subprocess.run([FFMPEG_path, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            ffmpeg_version_info = result.stdout.splitlines()[0]
            title = "< Initializing FFPROBE >"
            msg1=f"ffprobe.exe Could Not Be Found. Ending Program!\n"
            result = subprocess.run([self.ffprobe_path, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            ffprobe_version_info = result.stdout.splitlines()[0]
            title = "< Initializing FFPPLAY >"
            msg1=f"ffplay.exe Could Not Be Found. Ending Program!\n"
            result = subprocess.run([self.ffplay_path, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            ffplay_version_info = result.stdout.splitlines()[0]
            title = "< Initializing SoundVolumeView >"
            msg1=f"soundvolumeview.exe Could Not Be Found. Ending Program!\n"
            result = GetFileVersionInfo(self.soundvolumeview_path, '\\')
            ms = result['FileVersionMS']
            ls = result['FileVersionLS']
            version = f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
            title = "< Initializing Deno >"
            msg1=f"deno.exe Could Not Be Found. Ending Program!\n"
            result = GetFileVersionInfo(self.deno_path, '\\')
            ms = result['FileVersionMS']
            ls = result['FileVersionLS']
            version = f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
        except FileNotFoundError as e:
            msg2=f"Error: '{e}'"
            msg=msg1+msg2
            MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="cancel.png")
            self.grab_release()
            self._close_main()
    def get_music_metadata(self,file,data):# Can Return title, artist, album, genre, track or bitrate
        try:
            if data=="bitrate":
                proc=subprocess.Popen([self.ffprobe_path,"-v","0","-select_streams","a:0","-show_entries","stream=bit_rate","-of","compact=p=0:nk=1", file],
                                    stdout=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
            else:    
                data=f"format_tags={data}"
                proc=subprocess.Popen([self.ffprobe_path,"-v","error","-of","csv=s=x:p=0","-show_entries",data,file],
                                    stdout=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
            stdout,_=proc.communicate()
            proc.terminate()
            output=stdout.strip()# Capture the standard output as a string
            return_data=output.decode()
            return return_data
        except Exception as e:
            title='<FFPROBE Get Album, Artist Or Title>'
            msg1='Retrieving Album, Artist Or Title Failed!\n'
            msg2=f"Error: '{e}'"
            msg=msg1+msg2
            err_dialog=MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="cancel.png")
            self._stop()                
            return None
    def get_duration(self,file):# minutes = "-sexagesimal", seconds = Blank
        try:
            proc=subprocess.Popen([self.ffprobe_path,"-i",file,"-show_entries","format=duration","-v","quiet","-of","csv=p=0"], 
                                stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
            stdout,stderr=proc.communicate()
            proc.terminate()
            output=stdout.strip()# Capture the standard output as a string
            video_length=output.decode()[:-1]
            err=(stderr.decode()[:-1])
            if err!='' or video_length=='' or proc.returncode!=0:# Try Different Approach
                proc=subprocess.Popen([self.ffprobe_path,"-v","error","-select_streams","v:0","-show_entries","stream=duration","-of","default=noprint_wrappers=1:nokey=1",file], 
                                        stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
                stdout,stderr=proc.communicate()
                proc.terminate()
                output=stdout.strip()# Capture the standard output as a string
                video_length=output.decode()[:-1]
                err=(stderr.decode()[:-1])
                if err!='' or video_length=='' or proc.returncode!=0:raise Exception("ffprobe Get Stream Duration")# Try Different Approach
            video_length=round(float(video_length),3)
            return video_length,err
        except Exception as e:
            return None,err
    def begin_seeking(self, event):
        clicked=self.time_scale.identify(event.x, event.y)
        if clicked=="":
            self.slider_clicked=True
            return
        if self.ffplay_running:
            if clicked=="slider": 
                self.pause(self)
                self.seeking=True
        elif self.cv2_running:
            if self.Slide_Show_Delay.get() <= 10.0:
                if clicked=="slider": 
                    self.pause(self)
                    self.seeking=True
            elif self.Slide_Show_Delay.get() > 10.0 and clicked=="trough2":
                if self.Slide_Show_Delay.get() - self._time_now > 10.0:
                    self._time_now+=10.0
            elif self.Slide_Show_Delay.get() > 10.0 and clicked=="trough1":
                if self._time_now>10:
                    self._time_now-=10.0
    def end_seeking(self, event):
        unclicked=self.time_scale.identify(event.x, event.y)
        self.seeking=True    
        if self.trough==True or self.slider_clicked:
            self.trough=False
            self.slider_clicked=False
            return
        sleep(0.05)
        if self.ffplay_running:
            if unclicked=="slider" or unclicked=="": 
                basename=os.path.basename(self.active_file)
                ext=str(os.path.splitext(basename)[1].replace(".",""))
                if ext.lower() in self.ffmpeg_image_exts:
                    self.Time_Now.set(0.0)
                    self.start_time=self.Time_Now.get()
                    return# Image File
                self.start_time=self.Time_Now.get()
                self._time_now=float(self.start_time)
                self.pause(self)
                self._stop()
                self.update()
                self.next_ready=True
                if self.active_media=="music" or self.active_media=="video":self.play_av(self.active_file, self.key_now)
                elif self.active_media=="image":self.play_images(self.active_file,self.key_now)
        elif self.cv2_running and self.Slide_Show_Delay.get() <= 10.0:
            if unclicked=="slider" or unclicked=="": 
                pos=self.Time_Now.get()
                self.start_time=pos
                self._time_now=float(pos)
                self.pause(self)
                self.seeking=False
        elif self.cv2_running and self.Slide_Show_Delay.get() == 0.0:
            self.Time_Now.set(0.0)
    def bound_keys(self, key):
        if key.keysym=="XF86AudioPlay":self.ctrl_btn_clicked(self,"btn play")
        elif key.keysym=="XF86AudioPrev":self.ctrl_btn_clicked(self,"previous")
        elif key.keysym=="XF86AudioNext":self.ctrl_btn_clicked(self,"next")
        elif key.keysym=="p" or key.keysym=="P" or key.keysym=="XF86AudioPause":self.pause(self)
        elif key.keysym=="r" or key.keysym=="R":self.ctrl_btn_clicked(self,"repeat")
        elif key.keysym=="m" or key.keysym=="M" or key.keysym=="XF86AudioMute":self.ctrl_btn_clicked(self,"mute")
        elif key.keysym=="q" or key.keysym=="Q" or key.keysym=="Escape":self.ctrl_btn_clicked(self,"stop")
        elif key.keysym=="e" or key.keysym=="E":self.destroy()
        elif key.keysym=="XF86AudioLowerVolume" or key.keysym=="XF86AudioRaiseVolume":
            level=self.Master_Volume.GetMasterVolumeLevelScalar()# Volume Slider Level / 100
            db_level=self.Master_Volume.GetMasterVolumeLevel()
            self.Volume_Level.set(level * 100)# Track Volume From Other Sliders (Windows, Sound Card)
            self.Volume_Now_Txt.set(f"Level: {int(self.Volume_Level.get())} %  /  {round(db_level, decimals=2)} dB")
        elif key.keysym=="Right":
            self.send_keyboard_key("right")
            if self._time_now+10>self.duration:
                self._time_now=self.duration
            else: 
                self._time_now+=10.0
        elif key.keysym=="Left":     
            self.send_keyboard_key("left")
            if self._time_now-10<0.0:
                self._time_now=0.0
            else:
                self._time_now-=10.0
        elif key.keysym=="Up":     
            self.send_keyboard_key("up")
            if self._time_now+60>self.duration:
                self._time_now=self.duration
            else: 
                self._time_now+=60.0
        elif key.keysym=="Down":     
            self.send_keyboard_key("down")
            if self._time_now-60<0.0:
                self._time_now=0.0
            else:
                self._time_now-=60.0
        elif key.keysym=="f" or key.keysym=="F":
            if self.full_screen:self.change_screen("normal screen")
            else:self.change_screen("full screen")    
        elif key.keysym=="w" or key.keysym=="W":self.send_keyboard_key("showmode")
    def bind_keyboard(self):
        keys=['<KeyRelease-p>','<KeyRelease-P>','<KeyRelease-m>','<KeyRelease-M>','<KeyRelease-Right>','<KeyRelease-Left>',
                '<KeyRelease-Up>','<KeyRelease-Down>','<KeyRelease-f>','<KeyRelease-F>','<KeyRelease-q>','<KeyRelease-Q>',
                '<KeyRelease-XF86AudioPlay>','<KeyRelease-XF86AudioPause>','<KeyRelease-e>','<KeyRelease-E>','<KeyRelease-r>',
                '<KeyRelease-R>','<XF86AudioMute>','<KeyRelease-XF86AudioPrev>','<KeyRelease-XF86AudioNext>','<KeyRelease-Escape>',
                '<KeyRelease-XF86AudioRaiseVolume>','<KeyRelease-XF86AudioLowerVolume>']
        for k in range(len(keys)): 
            try:
                self.bind(keys[k], self.bound_keys)
            except Exception:
                continue
    def on_release(self,key):
        if self.active_media!="image" and self.Slide_Show_Delay.get() == 0.0:return
        try:
            if key.name=="esc":#Stop Slide Show
                self.listener.stop()
                self.update()
                self._stop()
                return False
        except Exception:
            pass
        try:
            if key.name=="media_play_pause":
                self.pause(self)
                return
        except Exception:
            pass
        try:
            if key.char=="p":
                self.pause(self)
                return
        except Exception:
            pass
        try:
            if key.name=="media_previous":
                self.cv2_running==False
                self.ctrl_btn_clicked(self,"previous")
                return
        except Exception:
            pass
        try:
            if key.name=="media_next":
                self.cv2_running==False
                self.ctrl_btn_clicked(self,"next")
                return
        except Exception:
            pass
        try:
            if key.name=="media_volume_up":
                level=self.Master_Volume.GetMasterVolumeLevelScalar()# Volume Slider Level / 100
                self.Volume_Level.set(level * 100)# Track Volume From Other Sliders (Windows, Sound Card)
                return
        except Exception:
            pass
        try:
            if key.name=="media_volume_down":
                level=self.Master_Volume.GetMasterVolumeLevelScalar()# Volume Slider Level / 100
                self.Volume_Level.set(level * 100)# Track Volume From Other Sliders (Windows, Sound Card)
                return
        except Exception:
            pass
        try:
            if key.name=="media_volume_mute":
                self.ctrl_btn_clicked(self,"mute")
                return
        except Exception:
            pass
        try:
            if key.name=="right":
                if self._time_now + 10 > self.Slide_Show_Delay.get():self._time_now = self.Slide_Show_Delay.get()
                else: self._time_now+=10
                return
        except Exception:
            pass
        try:
            if key.name=="left":
                if self._time_now-10<0.0:self._time_now=0.0
                else:self._time_now-=10
                return
        except Exception:
            pass
        try:
            if key.char=="r":
                self.ctrl_btn_clicked(self,"repeat")
                return
        except Exception:
            pass
        try:
            if key.char=="f":
                return
        except Exception:
            pass
        try:
            if key.char=="q":
                if self.listener.running:self.listener.stop()
                if self._timer_running:self._timer_running=False
                self._stop()
                return False
        except Exception:
            pass
    def set_window_coord(self,wid,hgt):
        self.aspect_ratio=self.screen_width/self.work_height
        if self.Screen_Position.get()=="Top Left":_x,_y=0,0
        elif self.Screen_Position.get()=="Top Center":_x,_y=int((self.screen_width/2)-(int(wid)/2)),0
        elif self.Screen_Position.get()=="Top Right":_x,_y=self.screen_width-int(wid),0
        elif self.Screen_Position.get()=="Center Left":_x,_y=0,int((self.work_height/2)-(int(hgt)/2))
        elif self.Screen_Position.get()=="Center":_x,_y=int((self.screen_width/2)-(int(wid)/2)),int((self.work_height/2)-(int(hgt)/2))
        elif self.Screen_Position.get()=="Center Right":_x,_y=int((self.screen_width)-(int(wid))),int((self.work_height/2)-(int(hgt)/2))
        elif self.Screen_Position.get()=="Bottom Left": _x,_y=0,self.work_height-(int(hgt))
        elif self.Screen_Position.get()=="Bottom Center": _x,_y=int((self.screen_width/2)-(int(wid)/2)),self.work_height-(int(hgt))
        elif self.Screen_Position.get()=="Bottom Right": _x,_y=int((self.screen_width)-(int(wid))),self.work_height-(int(hgt))
        else:
            self.Screen_Position.set("Top Center")
            _x,_y=int((self.screen_width/2)-(int(wid)/2)),0
            with open("Config.json", 'r') as file:
                data = json.load(file)
            data["1"]=self.Screen_Position.get()
            with open("Config.json", 'w') as file:
                json.dump(data, file, indent=4)
        return _x,_y    
    def play_images(self, file, key):# Images/Photos etc...
        if self.next_ready:
            self.key_now=key
            self.next_ready=False
            self.active_file=file
            if not self.cv2_running:# Not Running
                self.click_next=False
                self.media_list.select_set(key)
                self.media_list.update()
                self._reset_timer()
                self.seeking=False
            self.listener=keyboard.Listener(on_release=self.on_release)
            self.listener.start()
            sleep(0.1)
            self.update_time_scale(self.Slide_Show_Delay.get())
            try: 
                cv2.destroyAllWindows()
            except Exception:
                pass
            while self.listener.running and self.key_now!=None :
                try:
                    self.update_idletasks()
                    self.title_lbl.configure(text=f"Now Showing: {os.path.basename(self.Media_Dict[str(self.key_now)])}")
                    self.media_list.select_set(self.key_now)
                    self.media_list.update()
                    img=cv2.imread(file,cv2.IMREAD_UNCHANGED)
                    self.active_file=file
                    window_hgt=self.default_height
                    hgt, wid=img.shape[:2]
                    img_aspect_ratio=wid/hgt
                    if hgt>window_hgt:hgt=window_hgt
                    scale=int(window_hgt) / hgt  # Percent of original size
                    window_hgt=int(hgt * scale)
                    if window_hgt<hgt:window_hgt=hgt
                    window_wid=int(window_hgt * img_aspect_ratio)
                except Exception as e:
                    title="< Play Photos/Images Error >"
                    msg1="Something Went Wrong!\n"
                    msg2=f"Error: {e}\n"
                    msg3="Maybe The File Is Missing!\n"
                    msg4="Do You Wish to Continue To Next Photo/Image?"
                    msg=msg1+msg2+msg3+msg4
                    response=MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="question.png")
                    if response:
                        cv2.destroyAllWindows()
                        self.remove_media_file(key,False)# Remove corrupted Image File From Library
                        continue
                    else:    
                        self.listener.stop()
                        cv2.destroyAllWindows()
                        self._stop()
                        break
                try:
                    window_title=f"My Media Player: Playing {file}"
                    if self.key_now==0:self.media_list.yview_moveto((1/len(self.Media_Dict))*self.key_now)
                    else:self.media_list.yview_moveto((1/len(self.Media_Dict))*(self.key_now-1))# @ 2 down to show previous song
                    self.media_list.update()
                    if self.active_media=="image":
                        try:
                            if self.Image_Size.get() == "Full Screen":
                                window_name = "Media Player"
                                cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                                img_h, img_w = img.shape[:2]
                                scale = min(self.screen_width / img_w, self.work_height / img_h)
                                new_w, new_h = int(img_w * scale), int(img_h * scale)
                                resized_img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
                                cv2.setWindowTitle(window_name, window_title)
                                self.target_handle = win32gui.FindWindow(None, window_title)
                                win32gui.SetWindowPos(self.target_handle, win32con.HWND_TOP, 0, 0, self.screen_width, self.work_height, 0)
                                cv2.imshow(window_name, img)
                                self.ffplay_window=window.getWindowsWithTitle(window_title)[0]# Wi
                                cv2.waitKey(1)
                            else:    
                                if window_wid>self.screen_width:window_wid=self.screen_width
                                if window_hgt>self.work_height:window_hgt=self.work_height
                                window_x,window_y=self.set_window_coord(window_wid,window_hgt)
                                dim=(window_wid, window_hgt)
                                resized_img=cv2.resize(img,dim,interpolation=cv2.INTER_AREA)
                                cv2.setWindowTitle("Media Player", window_title)
                                cv2.imshow("Media Player", resized_img)
                                self.ffplay_window=window.getWindowsWithTitle(window_title)[0]# Window
                                self.target_handle=win32gui.FindWindow(None, window_title)# Window Handle
                                win32gui.MoveWindow(self.target_handle, window_x, window_y, window_wid, window_hgt, 1)
                                cv2.waitKey(1)
                            self.cv2_running=True
                            self.next_ready=True
                            self.ffplay_running=False
                            self.Start_Time.set(perf_counter_ns())
                            self._time_now=0.0
                            self._factor=1
                            self.last_key=self.key_now
                            self.ffplay_window.activate()
                            if self.Slide_Show_Delay.get() == 0.0:time_delay=300.0# 5 Minutes If self.Slide_Show_Delay=0
                            elif self.Slide_Show_Delay.get() > 0.0:time_delay=self.Slide_Show_Delay.get() 
                            if time_delay > 0.0:# Time Loop For Catching Button Press's Stop Or Quit 
                                self._reset_timer()
                                self.Start_Time.set(perf_counter_ns())
                                self.duration = time_delay
                                while self._time_now<time_delay and self.listener.running:
                                    self.target_handle=win32gui.FindWindow(None, window_title)
                                    if self.target_handle==0:break# Window Was Closed
                                    if self.paused:# self._factor Is Correction For Paused Time For Slider
                                        self._paused_time=perf_counter_ns()
                                        self._factor=self._ns_time/self._paused_time
                                        self.update()
                                    else:
                                        self._ns_time=perf_counter_ns() * self._factor
                                        self._elapsed_time=(self._ns_time-self.Start_Time.get())/1000000000
                                        self._time_now+=self._elapsed_time
                                        if time_delay <= 300.0:self.Time_Now.set(self._time_now)
                                        remaining = self.duration - self._time_now
                                        if remaining < 0.0:
                                            self._time_now = self.duration 
                                            remaining = 0.0
                                        self.Start_Time.set(self.Start_Time.get()+(self._elapsed_time*1000000000))
                                        self.Time_Now_Txt.set(f"Total Time:{round(self.duration, 1)} sec., Elapsed Time:{round(self._time_now, 1)} sec., Remaining Time: {round(remaining, 1)} sec.")
                                        self.update()
                                        if self.key_now!=self.last_key:break
                                cv2.destroyAllWindows()        
                                if self.key_now!=self.last_key and self.key_now!=None:
                                    self.media_list.selection_clear(0, 'end')
                                    if not self.repeat:
                                        file=self.Media_Dict[str(self.key_now)]
                                    else:
                                        self.key_now=self.last_key
                                        file=self.Media_Dict[str(self.last_key)]        
                                elif self.key_now!=None:
                                    self.media_list.selection_clear(0, 'end')
                                    if not self.repeat:
                                        if self.key_now==len(self.Media_Dict)-1:
                                            file=self.Media_Dict["0"]
                                            self.key_now=0
                                        else:    
                                            self.key_now+=1
                                            file=self.Media_Dict[str(self.key_now)]
                                    else:file=self.Media_Dict[str(self.key_now)]
                                self.update()        
                            else:self.listener.stop()
                        except Exception as e:
                            title="< Play Photos/Images Error >"
                            msg1="Something Went Wrong!\n"
                            msg2=f"Error: {e}\n"
                            msg3="Maybe The File Is Missing!\n"
                            msg4="Do You Wish to Continue To Next Photo/Image?"
                            msg=msg1+msg2+msg3+msg4
                            response=MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="question.png")
                            if response:
                                cv2.destroyAllWindows()
                                self.remove_media_file(key,False)# Remove corrupted Image File From Library
                                continue
                            else:    
                                self.listener.stop()
                                cv2.destroyAllWindows()
                                self._stop()
                                break
                except Exception:
                    self.listener.stop()
                    cv2.destroyAllWindows()
                    self._stop()
            self.listener.stop()        
            cv2.destroyAllWindows()
    def play_av(self, file, key):# Audio/Video Files
        if self.next_ready:
            self.key_now=key
            self.next_ready=False
            self.active_file=file
            if not self.ffplay_running:# Not Running
                self.click_next=False
                self.seeking=False
                basename=os.path.basename(self.Media_Dict[str(self.key_now)])
                self.title_lbl.configure(text=f"Now Playing: {basename}")
                try:
                    self.duration,error=self.get_duration(self.active_file)# Duration In Seconds
                    if self.duration==None:raise Exception(error)
                    self.update_time_scale(self.duration)
                    window_hgt=str(self.Screen_Height.get())
                    window_wid=str(int(self.Screen_Height.get() * self.aspect_ratio))   
                    if int(window_wid)>self.screen_width:window_wid=str(self.screen_width)
                    if int(window_hgt)>self.work_height:window_hgt=str(self.work_height)
                    window_x,window_y=self.set_window_coord(window_wid,window_hgt)
                    window_title=f"My Media Player: Playing {self.active_file}"
                    if key==0:self.media_list.yview_moveto((1/len(self.Media_Dict))*key)
                    else:self.media_list.yview_moveto((1/len(self.Media_Dict))*(key-1))# @ 2 down to show previous song
                    self.media_list.selection_clear(0, 'end')
                    self.media_list.select_set(key)
                    self.media_list.update()
                    if self.active_media=="video":
                        self.showmode_change=True
                        self.process_ffplay=subprocess.Popen([self.ffplay_path,"-ss",str(self.start_time),"-t",str(self.duration),"-x",window_wid,"-y",
                                                            window_hgt,"-showmode",self.show_mode,"-autoexit",self.active_file,"-window_title", window_title],
                                                            stdin=subprocess.PIPE,stdout=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
                    elif self.active_media=="music":
                        title=self.get_music_metadata(self.active_file,"title")# Get Song title. If Missing title, Do Not Use -showmode Because Error Generated At GetWindowTitle
                        if title=="":# No title
                            self.showmode_change=False
                            self.process_ffplay=subprocess.Popen([self.ffplay_path,"-ss",str(self.start_time),"-t",str(self.duration),"-x",
                                                                window_wid,"-y",window_hgt,"-autoexit",self.active_file,"-window_title",window_title],
                                                                stdin=subprocess.PIPE,stdout=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
                        else:# title exist
                            self.showmode_change=True
                            self.process_ffplay=subprocess.Popen([self.ffplay_path,"-i","-ss",str(self.start_time),"-t",str(self.duration),"-x",window_wid,"-y",
                                                                window_hgt,"-showmode",self.show_mode,self.active_file,"-autoexit","-window_title",window_title],
                                                                stdin=subprocess.PIPE,stdout=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
                    poll=""
                    count=0# Exit Backup
                    while poll!=None and count<=40:# 40 = 4 Seconds Max Time For Loop
                        count+=1
                        try:
                            sleep(0.1)
                            poll=self.process_ffplay.poll()
                        except Exception as e:
                            pass
                    if count>=40:raise Exception(e)
                    if poll==None:# None = ffplay Running
                        self.ffplay_running=True
                        self.cv2_running=False
                        ready=False
                        count=0# Exit Backup
                        while ready==False and count<=40:# 40 = 4 Seconds Max Time For Loop
                            count+=1
                            try:
                                sleep(0.1)
                                self.ffplay_window=window.getWindowsWithTitle(window_title)[0]# Window
                                if self.ffplay_window is not None:ready=True
                            except Exception as e:
                                pass
                        if count>=40:raise Exception("getWindowsWithTitle()")# Allow 4 Seconds
                        self.target_handle = win32gui.FindWindow(None, window_title)# Window Handle
                        win32gui.MoveWindow(self.target_handle, window_x, window_y, int(window_wid), int(window_hgt), 1)
                        if self.full_screen:self.change_screen("full screen")
                        self.ffplay_window.activate()
                        self._reset_timer()
                        self.Start_Time.set(perf_counter_ns())
                        self._start_timer()
                    else:raise Exception("ffplay Not Running")
                except Exception as e:
                    title="< Play Audio/Video Error >"
                    msg1="Something Went Wrong!\n"
                    msg2=f"Error: {e}\n"
                    msg3="Maybe The File Is Missing!\n"
                    msg4="Do You Wish to Continue To Next Audio/Video?"
                    msg=msg1+msg2+msg3+msg4
                    response=MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="question.png")
                    if response:
                        if self.ffplay_running:
                            self.process_ffplay.terminate()
                            self.process_ffplay.kill()
                            self.ffplay_running=False
                        self.next_ready=True
                        self.remove_media_file(self.key_now)# Remove From Database And Go To Next File
                    else:    
                        if self.ffplay_running:
                            self.process_ffplay.terminate()
                            self.process_ffplay.kill()
                        self.ffplay_running=False
                        self.next_ready=False
    def stop_process(self):# Used For Advancing Media Files
            if self._timer_running:
                self._stop_timer=True
                self._timer_running=False
                self._reset_timer()
                sleep(0.5)
            try:    
                if self.ffplay_running:
                    poll=self.process_ffplay.poll()
                    while poll==None:
                        self.send_keyboard_key("quit")
                        poll=self.process_ffplay.poll()
                    self.process_ffplay.terminate()
                    self.process_ffplay.kill()
                    self.ffplay_running=False
                if self.key_now!=None:
                    self.last_key=self.key_now
                self.next_ready=True    
            except Exception:pass
    def _stop(self):# Used For Stopping Media File
        if self.cv2_running:
            self.cv2_running=False    
        elif self.ffplay_running:
            self.stop_process()
        if not self.seeking:
            self.title_lbl.configure(text="")
            self.Time_Now.set(0.0)
            self.update_time_scale(0.0)    
            self.last_key=self.key_now
            self.pause_btn.configure(text_color=("#0c012e", "#ffffff"))
            self.stop_btn.configure(text_color="#ff0000")
            self.paused=False
            self.Master_Volume.SetMute(False, None)
            self.muted=False
            self.repeat=False
            if self.key_now==None:return
            self.media_list.selection_clear(0, 'end')
            self.key_now=None
            self.last_key=None
            self.media_list.yview_moveto(0)
            self.update()
    def update_time_scale(self,sec):
        sec=round(sec ,1)
        if sec == 0.0:sec = 300.0
        if sec >= 0.5 and sec < 1.0:    
            if self.active_media!="image":sec=sec+ 0.1 if sec % 2 !=0 else sec + 0.2
            interval=sec/10
            self.time_scale.configure(from_=0.0,to=sec)
            self.time_scale.configure(tickinterval=(interval))
            self.time_scale.configure(resolution=0.01)
        elif sec >= 1:    
            if self.active_media!="image":sec=sec+1 if sec % 2 !=0 else sec + 2
            interval=sec/10
            self.time_scale.configure(from_=0.0,to=sec)
            self.time_scale.configure(tickinterval=(interval))
            self.time_scale.configure(resolution=0.1)
        else:    
            self.time_scale.configure(from_=0.0,to=sec)
            self.time_scale.configure(tickinterval=0)
            self.time_scale.configure(resolution=0)
        self.time_scale.update()   
    def send_keyboard_key(self,key):
        keyboard=Controller()
        mykeys=[Key.left,Key.right,Key.up,Key.down,"p","q","w","s","f"]
        if self.ffplay_running:self.ffplay_window.activate()
        if key=="left":key_now=mykeys[0]
        elif key=="right":key_now=mykeys[1]
        elif key=="up":key_now=mykeys[2]
        elif key=="down":key_now=mykeys[3]
        elif key=="pause":key_now=mykeys[4]
        elif key=="quit":key_now=mykeys[5]
        elif key=="showmode":key_now=mykeys[6]
        elif key=="stop":key_now=mykeys[7]
        elif key=="full screen" or key=="normal screen":key_now=mykeys[8]
        keyboard.press(key_now)
        sleep(0.05)
        keyboard.release(key_now)
        sleep(0.05)
        if key_now == mykeys[6] or key_now == mykeys[8]:
            if self.show_mode==self.show_modes[0] and self.full_screen: window_y = self._y3#Video GUI Covers Taskbar    
            elif self.show_mode==self.show_modes[0] and not self.full_screen: window_y = self._y# GUI Just Above Taskbar
            elif self.show_mode==self.show_modes[1] and self.full_screen: window_y = self._y2#Wave GUI Center Screen
            elif self.show_mode==self.show_modes[1] and not self.full_screen: window_y = self._y# GUI Just Above Taskbar
            else: window_y = self._y
            self.geometry('%dx%d+%d+%d' % (self.width, self.height, self._x, window_y))
            self.update()
        self.update_idletasks()
    def slider_released(self, event):
        try:
            if self.ffplay_running:self.ffplay_window.activate()
        except Exception:pass
    def ctrl_btn_clicked(self, event, btn):
        if self.Media_Dict:
            if btn=="btn play":
                if self.shuffled:
                    if self.paused:self.pause(self)
                    if self.ffplay_running:self.stop_process()
                    if self.cv2_running:self.listener.stop()
                    self.shuffled=False
                    self.load_library(self.active_database, None)
                self.stop_btn.configure(text_color=("#0c012e", "#ffffff"))
                self.pause_btn.configure(text_color=("#0c012e", "#ffffff"))
                if self.paused:self.pause(self)
                if self.ffplay_running:self.stop_process()
                if self.cv2_running:self.listener.stop()
                self.shuffled=False
                self.load_library(self.active_database, None)
                self.start_time=0.0
                file=self.Media_Dict["0"]
                self.key_now=0
                if self.active_media=="music" or self.active_media=="video":self.play_av(file,self.key_now)
                elif self.active_media=="image":self.play_images(file,self.key_now)
            elif btn=="media play":# File Clicked In Window
                try:
                    if self.paused:self.pause(self)
                    if self.ffplay_running:self.stop_process()
                    if self.next_ready:# Prevent Multiple Windows
                        self.stop_btn.configure(text_color=("#0c012e", "#ffffff"))
                        self.pause_btn.configure(text_color=("#0c012e", "#ffffff"))
                        self.start_time=0.0
                        selection=self.media_list.curselection()
                        self.key_now=selection[0]
                        file=self.Media_Dict[str(self.key_now)]
                        if self.active_media=="music" or self.active_media=="video":self.play_av(file,self.key_now)
                        elif self.active_media=="image":
                            if not self.cv2_running:self.play_images(file,self.key_now)
                except:pass            
            elif btn=="shuffled":
                if self.paused:self.pause(self)
                if self.ffplay_running:self.stop_process()
                if self.cv2_running:self.listener.stop()
                self.stop_btn.configure(text_color=("#0c012e", "#ffffff"))
                self.pause_btn.configure(text_color=("#0c012e", "#ffffff"))
                self.shuffled=True
                self.load_library(self.active_database, None)
                self.start_time=0.0
                file=self.Media_Dict["0"]
                self.key_now=0
                if self.active_media=="music" or self.active_media=="video":self.play_av(file,self.key_now)
                elif self.active_media=="image":self.play_images(file,self.key_now)
            elif btn=="next":
                if self.paused:self.pause(self)
                if self.ffplay_running:self.stop_process()
                if self.next_ready:# Prevent Multiple Windows
                    self.start_time=0.0
                    if self.last_key!=None:
                        if self.repeat:
                            self.key_now=self.last_key   
                            file=self.Media_Dict[str(self.key_now)]
                        elif self.last_key==len(self.Media_Dict)-1:
                            file=self.Media_Dict["0"]
                            self.key_now=0
                        else:    
                            self.key_now=self.last_key+1    
                            file=self.Media_Dict[str(self.key_now)]
                    else:
                        self.stop_btn.configure(text_color=("#0c012e", "#ffffff"))
                        self.pause_btn.configure(text_color=("#0c012e", "#ffffff"))
                        file=self.Media_Dict["0"]
                        self.key_now=0
                    if self.active_media=="image":
                        if not self.cv2_running:self.play_images(file,self.key_now)
                    elif self.active_media=="music" or self.active_media=="video":self.play_av(file,self.key_now)
            elif btn=="previous":
                if self.paused:self.pause(self)
                if self.ffplay_running:self.stop_process()
                if self.next_ready:# Prevent Multiple Windows
                    self.start_time=0.0
                    self.click_next=False
                    if self.last_key!=None:
                        if self.repeat:
                            self.key_now=self.last_key   
                            file=self.Media_Dict[str(self.key_now)]
                        elif self.last_key!=0:
                            self.key_now=self.last_key-1    
                            file=self.Media_Dict[str(self.key_now)]
                        else:# self.last_key=0
                            self.key_now=len(self.Media_Dict)-1
                            file=self.Media_Dict[str(self.key_now)]
                    else:
                        self.stop_btn.configure(text_color=("#0c012e", "#ffffff"))
                        self.pause_btn.configure(text_color=("#0c012e", "#ffffff"))
                        file=self.Media_Dict["0"]
                        self.key_now=0
                    if self.active_media=="image":
                        if not self.cv2_running:self.play_images(file,self.key_now)
                    elif self.active_media=="music" or self.active_media=="video":self.play_av(file,self.key_now)
            elif btn=="repeat":
                if self.cv2_running and self.Slide_Show_Delay.get() == 0.0:return
                self.start_time=0.0
                if self.repeat==False:
                    self.repeat=True
                    self.repeat_btn.configure(text_color='red')
                else:
                    self.repeat=False   
                    self.repeat_btn.configure(text_color=("#0c012e", "#ffffff"))
                self.repeat_btn.update()
            elif btn=="stop":
                if self.ffplay_running or self.cv2_running:
                    self.Time_Now_Txt.set("")
                    self.mute_btn.configure(text_color=("#0c012e", "#ffffff"))
                    if self._timer_running:self._timer_running=False
                    self.update_idletasks()
                    if self.cv2_running:self.listener.stop()
                    self._stop()
            elif btn=="mute":
                if self.muted==False:
                    self.Master_Volume.SetMute(True, None)
                    self.mute_btn.configure(text_color='red')
                    self.muted=True
                else:# Unmute Clicked
                    self.Master_Volume.SetMute(False, None)
                    self.mute_btn.configure(text_color=("#0c012e", "#ffffff"))
                    self.muted=False
                self.update()    
    def pause(self,event):
        if self.ffplay_running:
            self.ffplay_window.activate()
            self.send_keyboard_key("pause")
            if self.paused==False:
                self.paused=True
                self.pause_btn.configure(text_color='red')
            else:
                self.paused=False
                self.pause_btn.configure(text_color=("#0c012e", "#ffffff"))
        elif self.cv2_running:
            if self.paused==False:
                self.paused=True
                self.pause_btn.configure(text_color='red')
            else:# Resume Clicked
                self.paused=False
                self.pause_btn.configure(text_color=("#0c012e", "#ffffff"))
    def restart_program(self):
        self.popup_menu.withdraw()
        self.update()
        self.give_greeting("restart")
        sleep(1)
        try:
            for widget in self.winfo_children():# Destroys Widgets
                if isinstance(widget, ctk.CTkCanvas):widget.destroy()
                else:widget.destroy()
            os.execl(sys.executable, os.path.abspath("ctkCalculator.exe"), *sys.argv) 
        except:
            pass
            os.execl(sys.executable, os.path.abspath("ctkCalculator.exe"), *sys.argv)
    def clear_restart_program(self, write):
        try:
            self.stop_process()
            cmd=[self.soundvolumeview_path, "/SetDefault", self.initial_sound_device, "1", "/Unmute", self.initial_sound_device, "/SetVolume", self.initial_sound_device, str(self.Volume_Level.get())]
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if write:self.write_setup()
            self.clear_all()
            for widget in self.winfo_children():# Destroy Widgets
                if isinstance(widget, ctk.CTkCanvas):widget.destroy()
                else:widget.destroy()
            self.process_ffplay.kill()
            os.execl(sys.executable, os.path.abspath("My_Media_Player.exe"), *sys.argv) 
        except Exception as ex:
            pass
            os.execl(sys.executable, os.path.abspath("My_Media_Player.exe"), *sys.argv)
    def load_library(self, db, active_folder=None):
        with open("Config.json", 'r') as file:
            data = json.load(file)
        data["3"]=db
        with open("Config.json", 'w') as file:
            json.dump(data, file, indent=4)
        if self.active_database=="" and db=="":return
        if db=="Music":
            path="Music.json"
            self.active_media="music"
        elif db=="Videos":
            path="Videos.json"
            self.active_media="video"
        elif db=="Pictures":
            path="Pictures.json"
            self.active_media="image"
        else:return
        self.active_folder=active_folder    
        self.clear_all()
        self.Original_Dict=json.load(open(path, "r+"))
        self.Media_Dict=json.load(open(path, "r+"))
        if len(self.Media_Dict)==0:
            self.key_now=None
            title=f"<{db.replace("_"," ")} Library>"
            msg1=f'{db.replace("_"," ")} Library Is Empty! Please Select\n'
            msg2='"Upload Folder Or File/s To Library" First.'
            msg=msg1+msg2
            MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="warning.png")
            return
        else:
            self.active_database=db
            self.title(f"{self.title_txt[0]} Playing ({self.active_database.replace("_"," ")} Library), Playing On Audio Device: {self.active_device} {self.title_txt[1].rjust(30+len(self.title_txt[1]))}")
            if self.shuffled and not self.repeat:
                temp=list(self.Media_Dict.values())
                random.shuffle(temp)
                self.Media_Dict=dict(zip(self.Media_Dict, temp))
            elif not self.shuffled:    
                temp=list(self.Original_Dict.values())
                self.Media_Dict=dict(zip(self.Original_Dict, temp))
            for key,self.file in self.Media_Dict.items():
                basename=os.path.basename(self.Media_Dict[key])
                text=os.path.splitext(basename)[0]
                index=f"{int(key)+1}.  {text}" 
                self.media_list.insert("end",index)
            self.media_list.bind("<ButtonRelease-1>",lambda event:self.ctrl_btn_clicked(event,"media play"))
            self.v_scroll.configure(command=self.media_list.yview)  
            self.h_scroll.configure(command=self.media_list.xview) 
            self.media_list.yview_moveto(0)
            self.update()     
        self.set_master_volume(self.Volume_Level.get())
    def destroy(self):
        try:
            if self.ffplay_running or self.cv2_running: 
                self.stop_process()
            txt=self.get_greeting("close")
            self.title_lbl.configure(text=txt)
            self.update()
            sleep(1)
            cmd=[self.soundvolumeview_path, "/SetDefault", self.initial_sound_device, "1", "/Unmute", self.initial_sound_device, "/SetVolume", self.initial_sound_device, str(self.Volume_Level.get())]
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.write_setup()
            self.clear_all()
            for widget in self.winfo_children():# Destroys Menu Bars, Frame, Scroll Bars etc...
                if isinstance(widget, ctk.CTkCanvas):widget.destroy()
                else:widget.destroy()
            self.process_ffplay.kill()
            os._exit(0)
        except Exception as e:
            pass
        os._exit(0)
    def rotate_image(self):
        title="< Image Rotation >"
        msg1="Enter Image Rotation In Degrees.\n"
        msg2="Range Is From -360 To 360 Degrees!\n"
        msg3="A Negative Number Rotates The Image Clock-Wise.\n"
        msg4="A Positive Number Rotates The Image Counter Clock-Wise."
        msg=msg1+msg2+msg3+msg4
        rotation=MyDialog(self, title=title, style="entry", prompt=msg, choices=None, init_val=180, min_val=-360, max_val=360, icon="setup.png")
        if rotation.result is not None:
            angle = float(rotation.result)
            try:
                img=cv2.imread(self.active_file,cv2.IMREAD_UNCHANGED)
                h, w = img.shape[:2]
                center = (w // 2, h // 2)
                abs_cos, abs_sin = abs(cos(radians(angle))), abs(sin(radians(angle)))
                bound_w = int(h * abs_sin + w * abs_cos)
                bound_h = int(h * abs_cos + w * abs_sin)
                rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotation_matrix[0, 2] += bound_w / 2 - center[0]
                rotation_matrix[1, 2] += bound_h / 2 - center[1]
                rotated_img = cv2.warpAffine(img, rotation_matrix, (bound_w, bound_h))
                cv2.imwrite(self.active_file, rotated_img)
                self.listener.stop()
                if self.active_media=="image":self.play_images(self.active_file,self.key_now)
            except Exception as e:
                title='< Image Rotation >'
                msg1='Rotating Image Failed!\n'
                msg2='This File May Be Corrupted!\n'
                msg3=f"Error: '{e}'"
                msg=msg1+msg2+msg3
                MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="cancel.png")
    def set_image_size(self):
        title = " < Set Image Displayed Size >"
        msg = "Select The Desired Size For Image Displayed, Then Click OK."
        size=MyDialog(self, title=title, style="entry", prompt=msg, choices=["Normal Screen", "Full Screen"], init_val=self.Image_Size.get(), icon="setup.png")
        if size.result is not None:
            self.Image_Size.set(size.result)
    def delete_image_file(self):
        try:
            if len(self.Media_Dict)>0:
                file_to_delete=self.Media_Dict[str(self.key_now)]
                file_name=os.path.basename(file_to_delete)
                if os.path.exists(file_to_delete):
                    path=Path(file_to_delete)
                    send2trash(path)# Recycle Bin
                    title=f'< Delete Image File {file_name} >'
                    msg1=f'Image File {file_name}\n'
                    msg2='Was Deleted Successfully!'
                    msg=msg1+msg2
                    MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="info.png")
                    self.remove_media_file(self.key_now,False)# Remove From Library
        except Exception as e:
            title=f'< Delete Image File {file_name} >'
            msg1=f'Deleting {file_name} Failed!\n'
            msg2=f"Error: '{e}'"
            msg=msg1+msg2
            MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="cancel.png")
    def remove_media_file(self, key=None, show_msg=None):
        try:
            if len(self.Media_Dict)>0:
                database = self.active_database
                if self.cv2_running:self.listener.stop()
                final_key=False
                end_key=False
                file_to_remove=self.Media_Dict[str(self.key_now)]
                file_name=os.path.basename(file_to_remove)
                if self.active_database=="Pictures":db_path="Pictures.json"
                elif self.active_database=="Music":db_path="Music.json"
                elif self.active_database=="Videos":db_path="Videos.json"
                if key==None:key=self.key_now
                dict_len=len(self.Media_Dict)
                end_key=dict_len-1
                if dict_len==0:return
                elif dict_len==1:
                    if self.key_now==end_key:
                        end_key=True
                        final_key=True
                    else:final_key=False
                elif dict_len>1 and self.key_now==end_key:
                    end_key=True
                    final_key=False    
                else:
                    end_key=False
                    final_key=False        
                del self.Media_Dict[str(key)]
                temp_dict=self.Media_Dict.copy()
                self.Media_Dict.clear()
                count=0
                temp_dict2={}
                for _, value in temp_dict.items():
                    temp_dict2[str(count)]=value
                    count+=1
                self.clear_database(self.active_database,False)
                with open(db_path, "w") as outfile:json.dump(temp_dict2, outfile)
                outfile.close()
                if final_key:
                    self.send_keyboard_key("stop")
                    if self.active_media=="image":self.listener.stop()
                    self._stop()
                    return
                self.load_library(database, None)
                if end_key:self.key_now-=1
                self.active_file=self.Media_Dict.get(str(self.key_now))
                self.next_ready=True
                temp_dict.clear()
                temp_dict2.clear()
                if show_msg:
                    if os.path.exists(file_to_remove):
                        title=f'< Remove Image File From Database >'
                        msg1=f'Image File {file_name}\n'
                        msg2='Was Removed Successfully!'
                        msg=msg1+msg2
                        MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="info.png")
                if self.active_media=="music" or self.active_media=="video":self.play_av(self.active_file,self.key_now)
                elif self.active_media=="image":self.play_images(self.active_file,self.key_now)
        except Exception as e:
            title=f'< Remove Image File From Database >'
            msg1=f'Removing {file_name} Failed!\n'
            msg2=f"Error: '{e}'"
            msg=msg1+msg2
            MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="cancel.png")
    def youtube_downloader(self):
        root = ctk.CTk()
        youtube=YouTube_GUI(root)
        path_dict={}# Clear Shared Json File
        with open(self.shared_download_files, "w") as json_file:
            json.dump(path_dict, json_file)
        json_file.close()
        youtube.main()
    def update_databases(self):
        try:
            self.deiconify()
            self.update()
            # Check If Download Folder Path Is In Media Player Paths
            temp_dict=json.load(open(self.download_path, "r+"))
            file_names = [value for key, value in temp_dict.items() if int(key) % 2 != 0]# Odds, Names
            file_paths = [value for key, value in temp_dict.items() if int(key) % 2 == 0]# Evens, Paths
            db_list=["Music","Videos", "Pictures"]
            msgs=[]
            msg=""
            for j in range(0,len(file_names)):
                if file_paths[j]!="" and file_names[j]!="":
                    last_folder=os.path.basename(os.path.normpath(file_paths[j]))
                    if last_folder in db_list:# Add To Database
                        msgs.append(f"{file_names[j]} Was Added To:\n"
                                     f"{file_paths[j]}.\n")
                        msg+=msgs[j]
                        self.clear_database(last_folder)
                        self.upload_from_folder(last_folder,file_paths[j], False)
                        self.update()
            if len(msgs)>0:
                title="< YouTube Downloader >"
                MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="info.png")
        except Exception as e:
            self.focus_force()
            self.deiconify()
            return
    def clear_config(self):
        setup={}
        with open("Config.json", "w") as outfile:json.dump(setup, outfile)
        outfile.close()
        self.clear_all_libraries()
        self.clear_restart_program(False)
    def clear_database(self, db, change=True):
        if db=="Music":path="Music.json"
        elif db=="Videos":path="Videos.json"
        elif db=="Pictures":path="Pictures.json"
        media={}
        with open(path, "w") as outfile:json.dump(media, outfile)
        outfile.close()
        if self.active_database==db:
            self.clear_all()
            self.active_database=""
            self.write_setup()
    def add_files_to_db(self, db, files=None):
        music_exts=['*.mp3','*.wma','*.wav','*.mp2','*.ac3','*.aac','*.eac3','*.m4a',
                    '*.wmav1','*.wmav2','*.opus','*.ogg','*.aiff','*.alac','*.ape','*.flac']
        video_exts=['*.mp4','*.avi','*.mov','*.mkv','*.mpg','*.mpeg','*.wmv','*.webm','*.flv','*.mj2','*.3gp','*.3g2']
        image_exts=['*.bmp','*.jpg','*.jpeg','*.gif','*.png','*.ppm','*.dib']    
        if db=='Music':
            db_path="Music.json"
            type="Music Files"
            exts=music_exts
            type="Video Files"
        elif db=='Videos':
            db_path="Videos.json"    
            type="Video Files"
            exts=video_exts
        elif db=="Pictures":
            db_path="Pictures.json"    
            type="Image Files"
            exts=image_exts
        if files==None:
            files=filedialog.askopenfilenames(title=f"Please Select Files To Upload To {db} Database.", filetypes=((type, exts),))
            if files=="" or files==None:return
        else:files=[files]
        temp_dict=json.load(open(db_path, "r+"))
        temp_list=[]
        for _, value in temp_dict.items():# Load List With temp_dict File Names 
            value=str(os.path.basename(value))
            temp_list.append(value)
        count=len(temp_dict)
        for _, name in enumerate(files):
            try:
                file_ext=os.path.splitext(name)[1].replace(".","*.")
                file_path=name[0].upper() + name[1:]# Make Sure Drive Letter Always Capitalized
                file_name=str(os.path.basename(file_path))
                if file_ext.lower() in exts:# Check For Duplicates Using Only File Name
                    c=Counter(temp_list)
                    duplicate=c[file_name]
                    if duplicate==0:
                        temp_list.append(file_name)
                        temp_dict[count]=file_path
                        count+=1
            except Exception:continue
        with open(db_path, "w") as outfile:json.dump(temp_dict, outfile)
        outfile.close()
        temp_dict.clear()
        temp_list.clear()
        if self.active_database==db:self.load_library(db, None)
    def upload_from_folder(self, db, init_dir=None, ask=True):
        if db=='Music':
            exts=self.ffmpeg_audio_exts
            db_path="Music.json"
        elif db=='Videos':
            exts=self.ffmpeg_video_exts
            db_path="Videos.json"
        elif db=="Pictures":
            exts=self.ffmpeg_image_exts
            db_path="Pictures.json"    
        else:return
        if ask:
            folder_path=filedialog.askdirectory(initialdir="C:\\", title=f"Please Select A Folder To Upload To {db} Database Or Click 'Select Folder' To Select Default Folder.")  
            if folder_path=="" or folder_path==None:return
        else:folder_path=init_dir
        path_active=folder_path    
        temp_dict=json.load(open(db_path, "r+"))
        temp_list=[]
        for _, value in temp_dict.items():# Load List With temp_dict File Names 
            value=str(os.path.basename(value))
            temp_list.append(value)
        count=len(temp_dict)
        for root, _, files in os.walk(folder_path):
            files.sort()
            try:
                for _, name in enumerate(files):
                    folder_path=os.path.join(root, name).replace("\\","/")
                    file_ext=os.path.splitext(name)[1].replace(".","")
                    file_path=folder_path[0].upper() + folder_path[1:]# Make Sure Drive Letter Always Capitalized
                    file_name=str(os.path.basename(file_path))
                    if file_ext.lower() in exts:# Check For Duplicates Using Only File Name
                        c=Counter(temp_list)
                        duplicate=c[file_name]
                        if duplicate==0:
                            temp_list.append(file_name)
                            temp_dict[count]=file_path
                            count+=1
            except Exception:continue
        with open(db_path, "w") as outfile:json.dump(temp_dict, outfile)
        outfile.close()
        temp_dict.clear()
        temp_list.clear()
        if self.active_database==db or self.active_database=="":self.load_library(db, path_active)
    def get_audio_devices(self, direction="in", State = DEVICE_STATE.ACTIVE.value):
        devices = []
        # for all use EDataFlow.eAll.value
        if direction == "in":
            Flow = EDataFlow.eCapture.value     # 1
        else:
            Flow = EDataFlow.eRender.value      # 0
        deviceEnumerator = comtypes.CoCreateInstance(
            CLSID_MMDeviceEnumerator,
            IMMDeviceEnumerator,
            comtypes.CLSCTX_INPROC_SERVER)
        if deviceEnumerator is None:
            return devices
        collection = deviceEnumerator.EnumAudioEndpoints(Flow, State)
        if collection is None:
            return devices
        count = collection.GetCount()
        for i in range(count):
            dev = collection.Item(i)
            if dev is not None:
                if not ": None" in str(AudioUtilities.CreateDevice(dev)):
                    self.output_devices.append(AudioUtilities.CreateDevice(dev).id)
                    devices.append(AudioUtilities.CreateDevice(dev).FriendlyName)
        return devices
    def init_audio(self):
        try:
            default_device = AudioUtilities.GetSpeakers()
            devices=self.get_audio_devices("out")
            result=list(filter(lambda x: default_device.FriendlyName in x, devices))
            self.active_device=result[0]
            if self.active_device=="":
                self.active_device="Default"
            self.initial_sound_device=self.active_device.split("(", 1)[0].replace(" ","")
            cmd=[self.soundvolumeview_path, "/SetDefault", self.initial_sound_device, "1", "/Unmute", 
                 self.initial_sound_device, "/SetVolume", self.initial_sound_device, str(self.Volume_Level.get())]
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            devices=AudioUtilities.GetSpeakers()# Initialize Master Volumn Slider
            self.interface = devices.EndpointVolume
            self.Master_Volume=ctypes.cast(self.interface, ctypes.POINTER(IAudioEndpointVolume))
            self.Master_Volume.SetMasterVolumeLevelScalar(self.Volume_Level.get() / 100, None)
            db_level=self.Master_Volume.GetMasterVolumeLevel()
            self.Volume_Now_Txt.set(f"Level: {int(self.Volume_Level.get())} %  /  {round(db_level, decimals=2)} dB")
            self.muted=False
            self.paused=False
        except Exception as ex:
            title='<Interface Initialization>'
            msg1='Initialization Failed. Ending Program!\n'
            msg2=f"Error: '{ex}'"
            msg=msg1+msg2
            MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="cancel.png")
            self.grab_release()
            self.destroy()
    def select_audio_device(self, device):
        try:
            devices=self.get_audio_devices("out")
            result=list(filter(lambda x: device in x, devices))
            self.active_device=result[0]
            soundview_device=result[0].split("(", 1)[0].replace(" ","")
            cmd=[self.soundvolumeview_path, "/SetDefault", soundview_device, "1", "/Unmute", soundview_device, "/SetVolume", soundview_device, str(self.Volume_Level.get())]
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            devices=AudioUtilities.GetSpeakers()# Initialize Master Volumn Slider
            self.interface = devices.EndpointVolume
            self.Master_Volume=ctypes.cast(self.interface, ctypes.POINTER(IAudioEndpointVolume))
            self.Master_Volume.SetMasterVolumeLevelScalar(self.Volume_Level.get()/ 100, None)
            self.title(f"{self.user}'s Media Player: Playing ({self.active_database.replace("_"," ")} Library), Playing On Audio Device: {result[0]}")
        except Exception as ex:
            title='<Audio Output Device>'
            msg1='Initialization Audio Device Failed. Ending Program!\n'
            msg2=f"Error: '{ex}'"
            msg3="Using Default Audio Device."
            msg=msg1+msg2+msg3
            MyDialog(parent=self, style="msgbox", title=title, prompt=msg, icon="cancel.png")
            pass
    def update_audio_devices(self):# False For Playback Devices, True For Capture
        captions = []
        commands = []
        output_devices = self.get_audio_devices("out")
        for d in range(len(output_devices)):
            captions.append(output_devices[d])
            commands.append(lambda x=output_devices[d]:self.select_audio_device(x))
        self.popup_menu = Popup_Menu(self, captions , commands, -18, self.winfo_pointerx(), self.winfo_pointery(), "bottom")
        self.popup_menu.bind("<Button-3>", lambda e: self.popup_menu.withdraw())
        if self.cv2_running:
            self.popup_menu.bind("<Button-3>", lambda e: self.popup_menu.grab_release())
            self.popup_menu.bind("<Button-3>", lambda e: self.popup_menu.destroy())
        self.wait_window(self.popup_menu)
        try:
            self.popup_menu.grab_release()
            self.popup_menu.destroy()
        except:pass    
if __name__ == "__main__":
    root=ctk
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    ctk.DrawEngine.preferred_drawing_method = "circle_shapes"
    scale_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
    ctk.set_widget_scaling(1.0 / scale_factor)
    ctk.set_window_scaling(1.0 / scale_factor)
    ctk.set_default_color_theme("blue")
    if os.path.exists("Config.json"):# Get Color Theme
        with open('Config.json', 'r') as json_file:
            data = json.load(json_file)
            json_file.close()
        try:        
            if data["4"]:
                theme = data.get("4")
                ctk.set_appearance_mode(theme)  # Options: "System", "Dark", "Light"
        except:pass
    else:# Create json File And Set Default Theme
        data = {}                
        data["4"] = "Dark"
        with open("Config.json", "w") as outfile:json.dump(data, outfile)
        outfile.close()
        ctk.set_appearance_mode("Dark")
    app = App()
    app._run_main()# Run asyncio the mainloop and timer loop together
 