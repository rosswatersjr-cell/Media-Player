import tkinter as tk
from tkinter import *
from tkinter import ttk, font, filedialog, messagebox
import asyncio
import re
import os
import sys
import cv2 #pip install opencv-python
import json
import time
import win32gui #pip install pywin32 
import requests
import subprocess
import yt_dlp
import pyperclip# System ClipBoard
import pywinctl as window
import comtypes
import webbrowser
import ctypes
from datetime import datetime
from pathlib import Path
from numpy import round, sin, cos, radians, random
from pynput import keyboard
from pynput.keyboard import Key, Controller
from time import perf_counter_ns
from ctypes import cast, POINTER
from pycaw.pycaw import AudioUtilities,  IAudioEndpointVolume, IMMDeviceEnumerator, EDataFlow, DEVICE_STATE
from pycaw.constants import CLSID_MMDeviceEnumerator
from win32api import GetMonitorInfo, MonitorFromPoint
from send2trash import send2trash# Recycle Bin
from collections import Counter

version="2026.03.12"
ctypes.windll.shcore.SetProcessDpiAwareness(1)
class FFMPEG_Player():
    def __init__(self,parent):
        self.parent=parent
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
        self.duration=0
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
        self.interface = devices.EndpointVolume
        # Initialize Scroll Window
        self.scroll_window=tk.Frame(parent)
        self.scroll_window.config(bg="#bcbcbc",relief="raised",borderwidth=6)
        self.scroll_window.pack(side='left', anchor='nw', fill='both', expand=True, padx=(6,0), pady=(0,6))
        self.vbar=ttk.Scrollbar(self.scroll_window,orient='vertical')
        self.vbar.pack(side='right',fill='y',expand=True,padx=(0,0),pady=(0,0))                                        
        self.ybar=ttk.Scrollbar(self.scroll_window,orient='horizontal')
        self.ybar.pack(side='bottom',fill='y',expand=False,padx=(0,0),pady=(0,0))                                        
        self.media_list=Listbox(self.scroll_window,foreground="#ffffff",background="#000000",selectbackground="#4cffff",
                                selectforeground="#000000",width=45,font=media_font,yscrollcommand=self.vbar.set )  
        self.media_list.pack(side='top',anchor='nw',fill='both',expand=True,padx=(0,0),pady=(0,0))                     
        pgm_path=Path(__file__).parent.absolute()
        self.download_path=os.path.join(os.path.expanduser("~"),"youtube_downloads.json")
        self.readme_path=os.path.join(pgm_path,"Bound_Keys_en.txt")
        # Create All Media Folders
        self.music_folder=os.path.join(Path.home(),"Music")
        self.music_favorite_folder=os.path.join(Path.home(),"Music Favorite")
        self.picture_folder=os.path.join(Path.home(),"Pictures")
        self.picture_family_folder=os.path.join(Path.home(),"Pictures_Family")
        self.picture_favorite_folder=os.path.join(Path.home(),"Pictures_Favorite")
        self.video_folder=os.path.join(Path.home(),"Videos")
        self.video_family_folder=os.path.join(Path.home(),"Videos_Family")
        self.video_music_folder=os.path.join(Path.home(),"Videos_Music")
        self.video_favorite_folder=os.path.join(Path.home(),"Videos_Favorite")
        self.video_karaoke_folder=os.path.join(Path.home(),"Videos_Karaoke")
        # Create Media Folders If Not Exist
        folder_paths=[self.music_folder,self.music_favorite_folder,self.video_folder,self.video_family_folder,self.video_favorite_folder,
                self.video_music_folder,self.video_karaoke_folder,self.picture_folder,self.picture_family_folder,self.picture_favorite_folder]
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
        # Create json Files If Not Exist
        json_files=["Pictures.json","Pictures_family.json","Pictures_favorite.json","Music.json","Music_Favorite.json","Videos.json",
                "Videos_Family.json","Videos_Favorite.json","Videos_Karaoke.json","Videos_Music.json","Setup.json"]
        data={}
        for k in range(len(json_files)):# Create Media json files
            if not os.path.exists(json_files[k]):
                try:
                    with open(json_files[k], "w") as json_file:
                            json.dump(data, json_file, indent=4) # indent=4 for pretty-printing
                except Exception:
                    pass
      # Define All File Extensions
        self.ffmpeg_audio_exts=['mp3','wma','wav','mp2','ac3','aac','eac3','m4a','wmav1','wmav2','opus','ogg','aiff','alac','ape','flac']
        self.ffmpeg_video_exts=['mp4','avi','mov','mkv','mpg','mpeg','wmv','webm','flv','mj2','3gp','3g2']
        self.ffmpeg_image_exts=['bmp','jpg','jpeg','gif','png','ppm','dib']
    def get_ffmpeg_versions(self):
        try:
            result = subprocess.run([ffmpeg_path.get(), '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            ffmpeg_version_info = result.stdout.splitlines()[0]
            result = subprocess.run([ffprobe_path.get(), '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            ffprobe_version_info = result.stdout.splitlines()[0]
            result = subprocess.run([ffplay_path.get(), '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            # Extract the first line of the output
            ffplay_version_info = result.stdout.splitlines()[0]
        except FileNotFoundError as e:
            title="< FFMPEG Files>"
            msg1=f"FFMPEG Files Could Not Be Found. Ending Program!\n"
            msg2=f"Error: '{e}'"
            msg=msg1+msg2
            messagebox.showerror(title,msg)
            self.destroy()
    def get_music_metadata(self,file,data):# Can Return title, artist, album, genre, track or bitrate
        try:
            if data=="bitrate":
                proc=subprocess.Popen([ffprobe_path.get(),"-v","0","-select_streams","a:0","-show_entries","stream=bit_rate","-of","compact=p=0:nk=1", file],
                                    stdout=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
            else:    
                data=f"format_tags={data}"
                proc=subprocess.Popen([ffprobe_path.get(),"-v","error","-of","csv=s=x:p=0","-show_entries",data,file],
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
            messagebox.showerror(title, msg1+msg2)
            self._stop()                
            return None
    def get_duration(self,file):# minutes = "-sexagesimal", seconds = Blank
        try:
            proc=subprocess.Popen([ffprobe_path.get(),"-i",file,"-show_entries","format=duration","-v","quiet","-of","csv=p=0"], 
                                stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
            stdout,stderr=proc.communicate()
            proc.terminate()
            output=stdout.strip()# Capture the standard output as a string
            video_length=output.decode()[:-1]
            err=(stderr.decode()[:-1])
            if err!='' or video_length=='' or proc.returncode!=0:# Try Different Approach
                proc=subprocess.Popen([ffprobe_path.get(),"-v","error","-select_streams","v:0","-show_entries","stream=duration","-of","default=noprint_wrappers=1:nokey=1",file], 
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
    def begin_seeking(self,event):
        clicked=app.time_scale.identify(event.x, event.y)
        if clicked=="":
            self.slider_clicked=True
            return
        if self.ffplay_running:
            if clicked=="trough1":
                self.trough=True
                self.send_keyboard_key("left")
                if app._time_now-10<0.0:
                    app._time_now=0.0
                else:
                    app._time_now-=10.0
            elif clicked=="trough2":
                self.trough=True
                self.send_keyboard_key("right")
                if app._time_now+10>self.duration:
                    app._time_now=self.duration
                else: 
                    app._time_now+=10.0
            elif clicked=="slider": 
                self.pause(self)
                self.seeking=True
        elif self.cv2_running:
            if int(Slide_Show_Delay.get())<=10:
                if clicked=="slider": 
                    self.pause(self)
                    self.seeking=True
            elif int(Slide_Show_Delay.get())>10 and clicked=="trough2":
                if int(Slide_Show_Delay.get())-app._time_now>10:
                    app._time_now+=10.0
            elif int(Slide_Show_Delay.get())>10 and clicked=="trough1":
                if app._time_now>10:
                    app._time_now-=10.0
    def end_seeking(self,event):
        unclicked=app.time_scale.identify(event.x, event.y)
        self.seeking=True    
        if self.trough==True or self.slider_clicked:
            self.trough=False
            self.slider_clicked=False
            return
        if self.ffplay_running:
            if unclicked=="slider" or unclicked=="": 
                basename=os.path.basename(self.active_file)
                ext=str(os.path.splitext(basename)[1].replace(".",""))
                if ext.lower() in self.ffmpeg_image_exts:
                    app.time_scale.set(0.0)
                    self.start_time=app.time_scale.get()
                    return# Image File
                self.start_time=app.time_scale.get()
                app._time_now=float(self.start_time)
                self.pause(self)
                self._stop(True)
                if self.shuffled:
                    app.shuffle_btn.configure(background="#00ffff",foreground="#4cffff")# Active)
                    app.play_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled)
                    app.stop_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                else:
                    app.play_btn.configure(background="#00ffff",foreground="#4cffff")# Active)
                    app.stop_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                    app.shuffle_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled)
                app.root.update()
                self.next_ready=True
                if self.active_media=="music" or self.active_media=="video":self.play_av(self.active_file,self.key_now)
                elif self.active_media=="picture":self.play_images(self.active_file,self.key_now)
        elif self.cv2_running and int(Slide_Show_Delay.get())<=10:
            if unclicked=="slider" or unclicked=="": 
                pos=app.time_scale.get()
                self.start_time=pos
                app._time_now=float(pos)
                self.pause(self)
                self.seeking=False
        elif self.cv2_running and int(Slide_Show_Delay.get())==0:
            app.time_scale.set(0.0)
            app.time_scale.update()
    def bound_keys(self,key):
        if key.keysym=="XF86AudioPlay":self.ctrl_btn_clicked(self,"btn play")
        elif key.keysym=="XF86AudioPrev":self.ctrl_btn_clicked(self,"previous")
        elif key.keysym=="XF86AudioNext":self.ctrl_btn_clicked(self,"next")
        elif key.keysym=="p" or key.keysym=="P" or key.keysym=="XF86AudioPause":self.pause(self)
        elif key.keysym=="r" or key.keysym=="R":self.ctrl_btn_clicked(self,"repeat")
        elif key.keysym=="m" or key.keysym=="M" or key.keysym=="XF86AudioMute":self.ctrl_btn_clicked(self,"mute")
        elif key.keysym=="q" or key.keysym=="Q" or key.keysym=="Escape":self.ctrl_btn_clicked(self,"stop")
        elif key.keysym=="e" or key.keysym=="E":self.destroy()
        elif key.keysym=="XF86AudioLowerVolume":
            level=self.Master_Volume.GetMasterVolumeLevelScalar()# Volume Slider Level / 100
            Level.set(level*100)# Track Volume From Other Sliders (Windows, Sound Card)
        elif key.keysym=="XF86AudioRaiseVolume":
            level=self.Master_Volume.GetMasterVolumeLevelScalar()# Volume Slider Level / 100
            Level.set(level*100)# Track Volume From Other Sliders (Windows, Sound Card)
        elif key.keysym=="Right":
            self.send_keyboard_key("right")
            if app._time_now+10>self.duration:
                app._time_now=self.duration
            else: 
                app._time_now+=10.0
        elif key.keysym=="Left":     
            self.send_keyboard_key("left")
            if app._time_now-10<0.0:
                app._time_now=0.0
            else:
                app._time_now-=10.0
        elif key.keysym=="Up":     
            self.send_keyboard_key("up")
            if app._time_now+60>self.duration:
                app._time_now=self.duration
            else: 
                app._time_now+=60.0
        elif key.keysym=="Down":     
            self.send_keyboard_key("down")
            if app._time_now-60<0.0:
                app._time_now=0.0
            else:
                app._time_now-=60.0
        elif key.keysym=="f" or key.keysym=="F":
            if self.full_screen:self.change_screen("normal screen")
            else:self.change_screen("full screen")    
        elif key.keysym=="w" or key.keysym=="W":self.send_keyboard_key("showmode")
    def on_release(self,key):
        if self.active_media!="picture" and Slide_Show_Delay.get()=="0":return
        try:
            if key.name=="esc":#Stop Slide Show
                self.listener.stop()
                app.root.update()
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
                Level.set(level*100)# Track Volume From Other Sliders (Windows, Sound Card)
                return
        except Exception:
            pass
        try:
            if key.name=="media_volume_down":
                level=self.Master_Volume.GetMasterVolumeLevelScalar()# Volume Slider Level / 100
                Level.set(level*100)# Track Volume From Other Sliders (Windows, Sound Card)
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
                if app._time_now+10>float(Slide_Show_Delay.get()):app._time_now=float(Slide_Show_Delay.get())
                else: app._time_now+=10
                return
        except Exception:
            pass
        try:
            if key.name=="left":
                if app._time_now-10<0.0:app._time_now=0.0
                else:app._time_now-=10
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
                if app._timer_running:app._timer_running=False
                self._stop()
                return False
        except Exception:
            pass
    def set_window_coord(self,wid,hgt):
        if Screen_Position.get()=="Top Left":_x,_y=0,0
        elif Screen_Position.get()=="Top Center":_x,_y=int((app.work_area[2]/2)-(int(wid)/2)),0
        elif Screen_Position.get()=="Top Right":_x,_y=app.work_area[2]-int(wid),0
        elif Screen_Position.get()=="Center Left":_x,_y=0,int((app.work_area[3]/2)-(int(hgt)/2))
        elif Screen_Position.get()=="Center":_x,_y=int((app.work_area[2]/2)-(int(wid)/2)),int((app.work_area[3]/2)-(int(hgt)/2))
        elif Screen_Position.get()=="Center Right":_x,_y=int((app.work_area[2])-(int(wid))),int((app.work_area[3]/2)-(int(hgt)/2))
        elif Screen_Position.get()=="Bottom Left": _x,_y=0,app.work_area[3]-(int(hgt))
        elif Screen_Position.get()=="Bottom Center": _x,_y=int((app.work_area[2]/2)-(int(wid)/2)),app.work_area[3]-(int(hgt))
        elif Screen_Position.get()=="Bottom Right": _x,_y=int((app.work_area[2])-(int(wid))),app.work_area[3]-(int(hgt))
        else:
            Screen_Position.set("Top Center")
            _x,_y=int((app.work_area[2]/2)-(int(wid)/2)),0
            with open("Setup.json", 'r') as file:
                data = json.load(file)
            data["1"]=Screen_Position.get()
            with open("Setup.json", 'w') as file:
                json.dump(data, file, indent=4)
        return _x,_y    
    def play_images(self,file,key):# Images/Photos etc...
        if self.next_ready:
            self.key_now=key
            self.next_ready=False
            self.active_file=file
            if not self.cv2_running:# Not Running
                self.click_next=False
                app.stop_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled))
                self.media_list.select_set(key)
                self.media_list.update()
                app._reset_timer()
                self.seeking=False
            self.listener=keyboard.Listener(on_release=self.on_release)
            self.listener.start()
            time.sleep(0.1)
            if int(Slide_Show_Delay.get())==0:self.load_image_menu()
            elif int(Slide_Show_Delay.get())>0:self.update_time_scale(float(Slide_Show_Delay.get()))
            try: 
                cv2.destroyAllWindows()
            except Exception:
                pass
            while self.listener.running and self.key_now!=None :
                try:
                    app.root.update_idletasks()
                    app.stop_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                    app.title_lbl.configure(text=f"Now Showing: {os.path.basename(self.Media_Dict[str(self.key_now)])}")
                    self.media_list.select_set(self.key_now)
                    self.media_list.update()
                    img=cv2.imread(file,cv2.IMREAD_UNCHANGED)
                    self.active_file=file
                    window_hgt=Screen_Height.get()
                    hgt, wid=img.shape[:2]
                    img_aspect_ratio=wid/hgt
                    if hgt>window_hgt:hgt=window_hgt
                    scale_factor=int(window_hgt)/hgt  # Percent of original size
                    window_hgt=int(hgt * scale_factor)
                    if window_hgt<hgt:window_hgt=hgt
                    window_wid=int(window_hgt * img_aspect_ratio)
                except Exception as e:
                    title="< Play Photos/Images Error >"
                    msg1="Something Went Wrong!\n"
                    msg2=f"Error: {e}\n"
                    msg3="Maybe The File Is Missing!\n"
                    msg4="Do You Wish to Continue To Next Photo/Image?"
                    msg=msg1+msg2+msg3+msg4
                    response=messagebox.askyesno(title,msg)
                    if response:
                        cv2.destroyAllWindows()
                        self.remove_media_file(key,False)# Remove corrupted Image File From Library
                        continue
                    else:    
                        self.listener.stop()
                        cv2.destroyAllWindows()
                        self._stop()
                        app.play_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                        app.stop_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                        app.root.update()
                        break
                if window_wid>app.work_area[2]:window_wid=app.work_area[2]
                if window_hgt>app.work_area[3]:window_hgt=app.work_area[3]
                window_x,window_y=self.set_window_coord(window_wid,window_hgt)
                try:
                    window_title=f"My Media Player: Playing {file}"
                    if self.key_now==0:self.media_list.yview_moveto((1/len(self.Media_Dict))*self.key_now)
                    else:self.media_list.yview_moveto((1/len(self.Media_Dict))*(self.key_now-1))# @ 2 down to show previous song
                    self.media_list.update()
                    if self.active_media=="picture":
                        try:
                            dim=(window_wid, window_hgt)
                            resized_img=cv2.resize(img,dim,interpolation=cv2.INTER_AREA)
                            cv2.setWindowTitle("My Media Player", window_title)
                            cv2.imshow("My Media Player", resized_img)
                            self.ffplay_window=window.getWindowsWithTitle(window_title)[0]# Window
                            global Target_Hwnd 
                            Target_Hwnd=win32gui.FindWindow(None, window_title)# Window Handle
                            win32gui.MoveWindow(Target_Hwnd, window_x, window_y, window_wid, window_hgt, 1)
                            cv2.waitKey(1)
                            self.cv2_running=True
                            self.next_ready=True
                            self.ffplay_running=False
                            Start_Time.set(perf_counter_ns())
                            app._time_now=0.0
                            app._factor=1
                            self.last_key=self.key_now
                            self.ffplay_window.activate()
                            if int(Slide_Show_Delay.get())==0:time_delay=300# 5 Minutes If Slide_Show_Delay=0
                            elif int(Slide_Show_Delay.get())>0:time_delay=int(Slide_Show_Delay.get()) 
                            if time_delay>0:# Time Loop For Catching Button Press's Stop Or Quit 
                                while app._time_now<time_delay and self.listener.running:
                                    time.sleep(0.1)
                                    hwnd=win32gui.FindWindow(None, window_title)
                                    if hwnd==0:break# Window Was Closed
                                    if self.paused:# app._factor Is Correction For Paused Time For Slider
                                        app._paused_time=perf_counter_ns()
                                        app._factor=app._ns_time/app._paused_time
                                        app.root.update()
                                    else:
                                        app._ns_time=perf_counter_ns()*app._factor
                                        app._elapsed_time=(app._ns_time-Start_Time.get())/1000000000
                                        app._time_now+=app._elapsed_time
                                        if time_delay<=120:app.time_scale.set(float(app._time_now))
                                        Start_Time.set(Start_Time.get()+(app._elapsed_time*1000000000))
                                        app.root.update()
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
                                app.root.update()        
                            else:self.listener.stop()
                        except Exception as e:
                            title="< Play Photos/Images Error >"
                            msg1="Something Went Wrong!\n"
                            msg2=f"Error: {e}\n"
                            msg3="Maybe The File Is Missing!\n"
                            msg4="Do You Wish to Continue To Next Photo/Image?"
                            msg=msg1+msg2+msg3+msg4
                            response=messagebox.askyesno(title,msg)
                            if response:
                                cv2.destroyAllWindows()
                                self.remove_media_file(key,False)# Remove corrupted Image File From Library
                                continue
                            else:    
                                self.listener.stop()
                                cv2.destroyAllWindows()
                                self._stop()
                                app.play_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                                app.stop_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                                app.root.update()
                                break
                except Exception:
                    self.listener.stop()
                    cv2.destroyAllWindows()
                    self._stop()
            self.listener.stop()        
            cv2.destroyAllWindows()
    def play_av(self,file,key):# Audio/Video Files
        if self.next_ready:
            self.key_now=key
            self.next_ready=False
            self.active_file=file
            if not self.ffplay_running:# Not Running
                self.click_next=False
                app.stop_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                self.seeking=False
                basename=os.path.basename(self.Media_Dict[str(self.key_now)])
                app.title_lbl.configure(text=f"Now Playing: {basename}")
                try:
                    self.duration,error=self.get_duration(file)# Duration In Seconds
                    if self.duration==None:raise Exception(error)
                    self.update_time_scale(self.duration)
                    window_hgt=str(Screen_Height.get())
                    window_wid=str(int(Screen_Height.get()*app.aspect_ratio))   
                    if int(window_wid)>app.work_area[2]:window_wid=str(app.work_area[2])
                    if int(window_hgt)>app.work_area[3]:window_hgt=str(app.work_area[3])
                    window_x,window_y=self.set_window_coord(window_wid,window_hgt)
                    window_title=f"My Media Player: Playing {file}"
                    if key==0:self.media_list.yview_moveto((1/len(self.Media_Dict))*key)
                    else:self.media_list.yview_moveto((1/len(self.Media_Dict))*(key-1))# @ 2 down to show previous song
                    self.media_list.selection_clear(0, 'end')
                    self.media_list.select_set(key)
                    self.media_list.update()
                    if self.active_media=="video":
                        self.showmode_change=True
                        self.process_ffplay=subprocess.Popen([ffplay_path.get(),"-ss",str(self.start_time),"-t",str(self.duration),"-x",window_wid,"-y",
                                                            window_hgt,"-showmode",self.show_mode,"-autoexit",file,"-window_title", window_title],
                                                            stdin=subprocess.PIPE,stdout=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
                    elif self.active_media=="music":
                        title=self.get_music_metadata(file,"title")# Get Song title. If Missing title, Do Not Use -showmode Because Error Generated At GetWindowTitle
                        if title=="":# No title
                            self.showmode_change=False
                            self.process_ffplay=subprocess.Popen([ffplay_path.get(),"-ss",str(self.start_time),"-t",str(self.duration),"-x",
                                                                window_wid,"-y",window_hgt,"-autoexit",file,"-window_title",window_title],
                                                                stdin=subprocess.PIPE,stdout=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
                        else:# title exist
                            self.showmode_change=True
                            self.process_ffplay=subprocess.Popen([ffplay_path.get(),"-i","-ss",str(self.start_time),"-t",str(self.duration),"-x",window_wid,"-y",
                                                                window_hgt,"-showmode",self.show_mode,file,"-autoexit","-window_title",window_title],
                                                                stdin=subprocess.PIPE,stdout=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
                    if self.showmode_change:self.load_music_menu()
                    else:app.root.config(menu="")
                    poll=""
                    count=0# Exit Backup
                    while poll!=None and count<=40:# 40 = 4 Seconds Max Time For Loop
                        count+=1
                        try:
                            time.sleep(0.1)
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
                                time.sleep(0.1)
                                self.ffplay_window=window.getWindowsWithTitle(window_title)[0]# Window
                                if self.ffplay_window is not None:ready=True
                            except Exception as e:
                                pass
                        if count>=40:raise Exception("getWindowsWithTitle()")# Allow 4 Seconds
                        global Target_Hwnd        
                        Target_Hwnd=win32gui.FindWindow(None, window_title)# Window Handle
                        win32gui.MoveWindow(Target_Hwnd, window_x, window_y, int(window_wid), int(window_hgt), 1)
                        if self.full_screen:self.change_screen("full screen")
                        self.ffplay_window.activate()
                        app._reset_timer()
                        Start_Time.set(perf_counter_ns())
                        app._start_timer()
                    else:raise Exception("ffplay Not Running")
                except Exception as e:
                    title="< Play Audio/Video Error >"
                    msg1="Something Went Wrong!\n"
                    msg2=f"Error: {e}\n"
                    msg3="Maybe The File Is Missing!\n"
                    msg4="Do You Wish to Continue To Next Audio/Video?"
                    msg=msg1+msg2+msg3+msg4
                    response=messagebox.askyesno(title,msg)
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
                        app.play_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                        app.stop_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                        app.root.update()
    def stop_process(self):# Used For Advancing Media Files
            if app._timer_running:
                app._stop_timer=True
                app._timer_running=False
                app._reset_timer()
                time.sleep(0.5)
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
    def _stop(self,skip_menu=None):# Used For Stopping Media File
        if self.cv2_running:
            self.remove_menubar()
            app.root.update()
            self.cv2_running=False    
        elif self.ffplay_running:
            if self.active_media=="music":self.remove_menubar()
            self.stop_process()
        if not self.seeking:
            app.title_lbl.configure(text="")
            app.time_scale.set(0.0)
            self.update_time_scale(0.0)    
            self.last_key=self.key_now
            app.play_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
            app.shuffle_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
            app.stop_btn.configure(background="#00ffff",foreground="#ff0000")# Active
            app.pause_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
            self.paused=False
            self.Master_Volume.SetMute(False, None)
            app.mute_btn.config(text="\U0001F50A",background="#bcbcbc",foreground=F_Color.get())# Disabled
            self.muted=False
            if skip_menu==None :self.load_menubar()
            if self.key_now==None:return
            self.media_list.selection_clear(0, 'end')
            self.key_now=None
            self.last_key=None
            self.media_list.yview_moveto(0)
            app.root.update()
    def update_time_scale(self,sec):
        sec=round(sec)
        if sec>=1:    
            if self.active_media!="picture":sec=sec+1 if sec % 2 !=0 else sec + 2
            interval=sec/10
            app.time_scale.config(from_=0.0,to=sec)
            app.time_scale.config(tickinterval=(interval))
            app.time_scale.config(resolution=0.1)
        else:    
            app.time_scale.config(from_=0.0,to=sec)
            app.time_scale.config(tickinterval=0)
            app.time_scale.config(resolution=0)
    def remove_menubar(self):
        try:
            self.menubar.delete(0, 'end')
            empty_menu=Menu(app.root)
            app.root.config(menu=empty_menu)
            app.root.update()
        except Exception:pass
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
        time.sleep(0.1)
        keyboard.release(key_now)
        if key=="full screen" or key=="normal screen":
            time.sleep(0.1)
            self.change_screen(key,False)
    def slider_released(self):
        try:
            if self.ffplay_running:self.ffplay_window.activate()
        except Exception:pass
    def set_master_volume(self):
        with open("Setup.json", 'r') as file:
            data = json.load(file)
        data["5"]=str(round(Level.get()))
        with open("Setup.json", 'w') as file:
            json.dump(data, file, indent=4)
        self.Master_Volume.SetMasterVolumeLevelScalar(Level.get()/100, None)
        level=self.Master_Volume.GetMasterVolumeLevelScalar()# Volume Slider Level / 100
        if level==0:self.Master_Volume.SetMute(True, None)
        else:self.Master_Volume.SetMute(False, None)
    def ctrl_btn_clicked(self,event,btn):
        if self.Media_Dict:
            if btn=="btn play":
                if self.shuffled:
                    if self.paused:self.pause(self)
                    if self.ffplay_running:self.stop_process()
                    if self.cv2_running:self.listener.stop()
                    self.shuffled=False
                    self.load_library(self.active_database,None,False)
                else:
                    if self.ffplay_running or self.cv2_running:return# If Playing, Do Nothing
                self.start_time=0.0
                app.play_btn.configure(background="#00ffff",foreground="#4cffff")# Active
                app.play_btn.update()
                app.stop_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                app.shuffle_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                app.root.update()
                file=self.Media_Dict["0"]
                self.key_now=0
                if self.active_media=="music" or self.active_media=="video":self.play_av(file,self.key_now)
                elif self.active_media=="picture":self.play_images(file,self.key_now)
            elif btn=="media play":# File Clicked In Window
                if self.paused:self.pause(self)
                if self.ffplay_running:self.stop_process()
                if self.next_ready:# Prevent Multiple Windows
                    if not self.shuffled:
                        app.play_btn.configure(background="#00ffff",foreground="#4cffff")# Active
                        app.stop_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                    else:    
                        app.shuffle_btn.configure(background="#00ffff",foreground="#4cffff")# Active
                        app.play_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                    app.root.update()
                    self.start_time=0.0
                    selection=self.media_list.curselection()
                    self.key_now=selection[0]
                    file=self.Media_Dict[str(self.key_now)]
                    if self.active_media=="music" or self.active_media=="video":self.play_av(file,self.key_now)
                    elif self.active_media=="picture":
                        if not self.cv2_running:self.play_images(file,self.key_now)
            elif btn=="shuffled":
                if self.paused:self.pause(self)
                if self.ffplay_running:self.stop_process()
                if self.cv2_running:self.listener.stop()
                self.shuffled=True
                self.load_library(self.active_database,None,False)
                self.start_time=0.0
                app.shuffle_btn.configure(background="#00ffff",foreground="#4cffff")# Active
                app.play_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                app.stop_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                app.root.update()
                file=self.Media_Dict["0"]
                self.key_now=0
                if self.active_media=="music" or self.active_media=="video":self.play_av(file,self.key_now)
                elif self.active_media=="picture":self.play_images(file,self.key_now)
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
                        app.play_btn.configure(background="#00ffff",foreground="#4cffff")# Active
                        app.stop_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                        app.root.update()
                        file=self.Media_Dict["0"]
                        self.key_now=0
                    if self.active_media=="picture":
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
                        app.play_btn.configure(background="#00ffff",foreground="#4cffff")# Active
                        app.stop_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                        app.root.update()
                        file=self.Media_Dict["0"]
                        self.key_now=0
                    if self.active_media=="picture":
                        if not self.cv2_running:self.play_images(file,self.key_now)
                    elif self.active_media=="music" or self.active_media=="video":self.play_av(file,self.key_now)
            elif btn=="repeat":
                if self.cv2_running and int(Slide_Show_Delay.get())==0:return
                self.start_time=0.0
                if self.repeat==False:
                    self.repeat=True
                    app.repeat_btn.configure(background="#00ffff",foreground="#4cffff")# Active
                    app.repeat_btn.update()
                else:
                    self.repeat=False   
                    app.repeat_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
                    app.repeat_btn.update()
            elif btn=="stop":
                if self.ffplay_running or self.cv2_running:
                    if app._timer_running:app._timer_running=False
                    app.root.update_idletasks()
                    if self.cv2_running:self.listener.stop()
                    self._stop()
            elif btn=="mute":
                if self.muted==False:
                    self.Master_Volume.SetMute(True, None)
                    app.mute_btn.config(text="\U0001F507",background="#00ffff",foreground="#ff0000")# Active
                    self.muted=True
                else:# Unmute Clicked
                    self.Master_Volume.SetMute(False, None)
                    app.mute_btn.config(text="\U0001F50A",background="#bcbcbc",foreground=F_Color.get())# Disabled
                    self.muted=False
                app.root.update()    
    def pause(self,event):
        if self.ffplay_running:
            self.ffplay_window.activate()
            self.send_keyboard_key("pause")
            if self.paused==False:
                self.paused=True
                app.pause_btn.configure(background="#00ffff",foreground="#4cffff")# Active
            else:
                self.paused=False
                app.pause_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
        elif self.cv2_running and int(Slide_Show_Delay.get())>0:
            if self.paused==False:
                self.paused=True
                app.pause_btn.configure(background="#00ffff",foreground="#4cffff")# Active
            else:# Resume Clicked
                self.paused=False
                app.pause_btn.configure(background="#bcbcbc",foreground=F_Color.get())# Disabled
    def restart_program(self,write):
        try:
            self.stop_process()
            cmd=[soundvolumeview_path.get(), "/SetDefault", self.initial_sound_device, "1", "/Unmute", self.initial_sound_device, "/SetVolume", self.initial_sound_device, str(Level.get())]
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if write:self.write_setup()
            self.clear_all()
            for widget in app.root.winfo_children():# Destroys Menu Bars, Frame, Scroll Bars etc...
                if isinstance(widget, tk.Canvas):widget.destroy()
                else:widget.destroy()
            self.process_ffplay.kill()
            os.execl(sys.executable, os.path.abspath("My_Media_Player.exe"), *sys.argv) 
        except Exception as ex:
            pass
            os.execl(sys.executable, os.path.abspath("My_Media_Player.exe"), *sys.argv)
    def destroy(self):
        try:
            self.stop_process()
            txt=get_greeting("close")
            app.title_lbl.config(text=txt)
            root.update()
            time.sleep(1)
            cmd=[soundvolumeview_path.get(), "/SetDefault", self.initial_sound_device, "1", "/Unmute", self.initial_sound_device, "/SetVolume", self.initial_sound_device, str(Level.get())]
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.write_setup()
            self.clear_all()
            for widget in app.root.winfo_children():# Destroys Menu Bars, Frame, Scroll Bars etc...
                if isinstance(widget, tk.Canvas):widget.destroy()
                else:widget.destroy()
            self.process_ffplay.kill()
            os._exit(0)
        except Exception:
            pass
        os._exit(0)
    def rotate_image(self):
        title="<Image Rotation>"
        msg1="Enter Image Rotation In Degrees.\n"
        msg2="Range Is From -360 To 360 Degrees!\n"
        msg3="A Negative Number Rotates The Image Clock-Wise.\n"
        msg4="A Positive Number Rotates The Image Counter Clock-Wise."
        msg=msg1+msg2+msg3+msg4
        angle=my_askinteger(title,msg,180,-360,360)
        if angle!=None:
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
                if self.active_media=="picture":self.play_images(self.active_file,self.key_now)
            except Exception as e:
                title='<Image Rotation>'
                msg1='Rotating Image Failed!\n'
                msg2='This File May Be Corrupted!\n'
                msg3=f"Error: '{e}'"
                msg=msg1+msg2+msg3
                messagebox.showerror(title, msg1+msg2)
    def delete_image_file(self):
        try:
            if len(self.Media_Dict)>0:
                file_to_delete=self.Media_Dict[str(self.key_now)]
                file_name=os.path.basename(file_to_delete)
                if os.path.exists(file_to_delete):
                    path=Path(file_to_delete)
                    send2trash(path)# Recycle Bin
                    title=f'<Delete File {file_name}>'
                    msg=f'{file_name} Was Deleted Successfully!'
                    messagebox.showinfo(title, msg)
                    self.remove_media_file(self.key_now,False)# Remove From Library
        except Exception as e:
            title=f'<Delete File {file_name}>'
            msg1=f'Deleting {file_name} Failed!\n'
            msg2=f"Error: '{e}'"
            msg=msg1+msg2
            messagebox.showerror(title, msg)
    def remove_media_file(self,key=None,show_msg=None):
        try:
            if len(self.Media_Dict)>0:
                if self.cv2_running:self.listener.stop()
                final_key=False
                end_key=False
                file_to_remove=self.Media_Dict[str(self.key_now)]
                file_name=os.path.basename(file_to_remove)
                if self.active_database=="Pictures":db_path="Pictures.json"
                elif self.active_database=="Pictures_Family":db_path="Pictures_family.json"
                elif self.active_database=="Pictures_Favorite":db_path="Pictures_favorite.json"
                elif self.active_database=="Music":db_path="Music.json"
                elif self.active_database=="Music_Favorite":db_path="Music_Favorite.json"
                elif self.active_database=="Videos":db_path="Videos.json"
                elif self.active_database=="Videos_Family":db_path="Videos_Family.json"
                elif self.active_database=="Videos_Favorite":db_path="Videos_Favorite.json"
                elif self.active_database=="Videos_Karaoke":db_path="Videos_Karaoke.json"
                elif self.active_database=="Videos_Music":db_path="Videos_Music.json"
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
                    if self.active_media=="picture":self.listener.stop()
                    self._stop()
                    return
                self.load_library(self.active_database,None,True)
                if end_key:self.key_now-=1
                self.active_file=self.Media_Dict.get(str(self.key_now))
                self.next_ready=True
                temp_dict.clear()
                temp_dict2.clear()
                if show_msg:
                    if os.path.exists(file_to_remove):
                        title=f'<Remove File {file_name}>'
                        msg=f'{file_name} Was Removed Successfully!'
                        messagebox.showinfo(title, msg)
                if self.active_media=="music" or self.active_media=="video":self.play_av(self.active_file,self.key_now)
                elif self.active_media=="picture":self.play_images(self.active_file,self.key_now)
        except Exception as e:
            title=f'<Remove File {file_name}>'
            msg1=f'Removing {file_name} Failed!\n'
            msg2=f"Error: '{e}'"
            msg=msg1+msg2
            messagebox.showerror(title, msg)
    def move_image(self,to_db):
        try:
            if len(self.Media_Dict)>0:
                self.listener.stop()
                final_key=False
                end_key=False
                file_to_move=self.Media_Dict[str(self.key_now)]
                file_name=os.path.basename(file_to_move)
                self.add_files_to_db(to_db,file_to_move)
                if self.active_database=="Pictures":db_path="Pictures.json"
                elif self.active_database=="Pictures_Family":db_path="Pictures_family.json"
                elif self.active_database=="Pictures_Favorite":db_path="Pictures_favorite.json"
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
                del self.Media_Dict[str(self.key_now)]
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
                    self.listener.stop()
                    self._stop()
                    return
                self.load_library(self.active_database,None,True)
                if end_key:self.key_now-=1
                self.active_file=self.Media_Dict.get(str(self.key_now))
                self.next_ready=True
                temp_dict.clear()
                temp_dict2.clear()
                if os.path.exists(file_to_move):
                    title=f'<Move Image File To {to_db} Library>'
                    msg=f'{file_name} Was Moved To {to_db} Library Successfully!'
                    messagebox.showinfo(title, msg)
                if self.active_media=="music" or self.active_media=="video":self.play_av(self.active_file,self.key_now)
                elif self.active_media=="picture":self.play_images(self.active_file,self.key_now)
        except Exception as e:
            title=f'<Move Image File To {to_db} Library>'
            msg1=f'Moving {file_name} To {to_db} Library Failed!\n'
            msg2=f"Error: '{e}'"
            msg=msg1+msg2
            messagebox.showerror(title, msg)# utube_console_Downloader requires Python3.1x Installed 
    def youtube_downloader(self):
        youtube=YouTube_GUI(app.root)
        path_dict={}# Clear Shared Json File
        with open(shared_download_files, "w") as json_file:
            json.dump(path_dict, json_file)
        json_file.close()
        youtube.main()
    def update_databases(self):
        try:
            app.root.deiconify()
            app.root.update()
            # Check If Download Folder Path Is In Media Player Paths
            temp_dict=json.load(open(self.download_path, "r+"))
            file_names = [value for key, value in temp_dict.items() if int(key) % 2 != 0]# Odds, Names
            file_paths = [value for key, value in temp_dict.items() if int(key) % 2 == 0]# Evens, Paths
            db_list=["Music","Music_Favorite","Videos","Videos_Music","Videos_Family",
                        "Videos_Favorite","Videos_Karaoke","Pictures","Pictures_Family","Pictures_Favorite"]
            msgs=[]
            msg=""
            for j in range(0,len(file_names)):
                if file_paths[j]!="" and file_names[j]!="":
                    last_folder=os.path.basename(os.path.normpath(file_paths[j]))
                    if last_folder in db_list:# Add To Database
                        msgs.append(f"{file_names[j]} Was Added To {file_paths[j]}. \n")
                        msg+=msgs[j]
                        self.clear_database(last_folder)
                        self.upload_from_folder(last_folder,file_paths[j],False)
                        app.root.update()
            if len(msgs)>0: 
                messagebox.showinfo("< YouTube Downloader > (Media Files Added To Databases)", msg)
        except Exception as e:
            app.root.focus_force()
            app.root.deiconify()
            return
    def change_showmode(self,display_type):
        app.root.focus_force()
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
            if display_type=="waves" and self.full_screen:
                app.root.geometry('%dx%d+%d+%d' % (app.root_width, app.root_height, app.root_x, app.root_y2))
            elif display_type=="video" and self.full_screen:    
                app.root.geometry('%dx%d+%d+%d' % (app.root_width, app.root_height, app.root_x, app.root_y3))
            else:    
                app.root.geometry('%dx%d+%d+%d' % (app.root_width, app.root_height, app.root_x, app.root_y))
            app.root.update()
    def change_screen(self,screen_type,send_key=True):
        app.root.focus_force()
        try:
            if send_key==False:
                screen_hgt=self.ffplay_window.height
                full_screen=app.work_area[3]+app.taskbar_height
                if screen_hgt==full_screen: 
                    self.full_screen=True
                    self.showmode_menu.entryconfigure(3, label="Normal Screen",command=lambda:self.change_screen('normal screen'))
                elif screen_hgt<full_screen:
                    self.full_screen=False
                    self.showmode_menu.entryconfigure(3, label="Full Screen",command=lambda:self.change_screen('full screen'))
            else:
                if screen_type=="full screen":
                    self.full_screen=True
                    self.showmode_menu.entryconfigure(3, label="Normal Screen",command=lambda:self.change_screen('normal screen'))
                else:      
                    self.full_screen=False
                    self.showmode_menu.entryconfigure(3, label="Full Screen",command=lambda:self.change_screen('full screen'))
                if send_key:self.send_keyboard_key(screen_type)
            if self.show_mode==self.show_modes[1] and self.full_screen:
                app.root.geometry('%dx%d+%d+%d' % (app.root_width, app.root_height, app.root_x, app.root_y2))
            elif self.show_mode==self.show_modes[0] and self.full_screen:    
                app.root.geometry('%dx%d+%d+%d' % (app.root_width, app.root_height, app.root_x, app.root_y3))
            else:    
                app.root.geometry('%dx%d+%d+%d' % (app.root_width, app.root_height, app.root_x, app.root_y))
            app.root.update()
        except Exception as e:
            pass
    def load_music_menu(self):
        self.menubar=Menu(app.root,fg="#000000")# Create Menubar
        self.showmode_menu=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        self.menubar.add_cascade(label=' Show Mode ',menu=self.showmode_menu)
        self.showmode_menu.add_command(label='Video/Art',command=lambda:self.change_showmode('video'))
        self.showmode_menu.add_command(label='Waves',command=lambda:self.change_showmode('waves'))
        self.showmode_menu.add_separator()
        self.showmode_menu.add_command(label='Full Screen',command=lambda:self.change_screen('full screen'))
        app.root.config(menu=self.menubar)
        app.root.update()
    def load_image_menu(self):
        self.menubar=Menu(app.root,fg="#000000")# Create Menubar
        images_menu=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        self.menubar.add_cascade(label=' Edit Picture ',menu=images_menu)
        images_menu.add_command(label='Rotate Picture And Save',command=lambda:self.rotate_image())
        images_menu.add_separator()
        images_menu.add_command(label='Remove Picture From Library',command=lambda:self.remove_media_file(None,True))
        images_menu.add_separator()
        images_menu.add_command(label='Delete Picture To Recycle Bin',command=lambda:self.delete_image_file())
        images_menu.add_separator()
        move_image=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        if self.active_database=="Pictures":
            move_image.add_command(label="Move To Picture Family Image Library",command=lambda:self.move_image("Pictures_Family"))
            move_image.add_separator()
            move_image.add_command(label="Move To Picture Favorite Library",command=lambda:self.move_image("Pictures_Favorite"))
        elif self.active_database=="Pictures_Family":
            move_image.add_command(label="Move To Picture Library",command=lambda:self.move_image("Pictures"))
            move_image.add_separator()
            move_image.add_command(label="Move To Picture Favorite Library",command=lambda:self.move_image("Pictures_Favorite"))
        elif self.active_database=="Pictures_Favorite":
            move_image.add_command(label="Move To Picture Library",command=lambda:self.move_image("Pictures"))
            move_image.add_separator()
            move_image.add_command(label="Move To Picture Family Library",command=lambda:self.move_image("Pictures_Family"))
        images_menu.add_cascade(label='Move Picture',menu=move_image)
        app.root.config(menu=self.menubar)
        app.root.update()
    def load_menubar(self):
        self.menubar=Menu(root,fg="#000000")# Create Menubar
        file_menu=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        self.menubar.add_cascade(label='   File   ',menu=file_menu)
        file_menu.add_command(label="Set To Default State (Requires Restart)",command=lambda:self.clear_config())
        file_menu.add_separator()
        file_menu.add_command(label="Set Slide Show Delay",command=lambda:set_slide_show())
        file_menu.add_separator()
        file_menu.add_command(label="View Bound Keyboard Keys",command=lambda:subprocess.Popen(["notepad.exe", self.readme_path]))
        file_menu.add_separator()
        file_menu.add_command(label='About',command=lambda:about())
        file_menu.add_separator()
        file_menu.add_command(label="Exit",command=lambda:self.destroy())
        music_menu=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        self.menubar.add_cascade(label='     Media Libraries   ',menu=music_menu)
        upload_music=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        upload_music.add_command(label="Load Music Library",command=lambda:self.load_library("Music",None,False))
        upload_music.add_separator()
        upload_music.add_command(label="Upload Folder To Music Library",command=lambda:self.upload_from_folder("Music",None,True))
        upload_music.add_separator()
        upload_music.add_command(label="Upload File/s To Music Library",command=lambda:self.add_files_to_db("Music"))
        upload_music.add_separator()
        upload_music.add_command(label="Clear Music Library",command=lambda:self.clear_database("Music"))
        music_menu.add_cascade(label='Music Library',menu=upload_music)
        favorite_music=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        favorite_music.add_command(label="Load Music Favorite Library",command=lambda:self.load_library("Music_Favorite",None,False))
        favorite_music.add_separator()
        favorite_music.add_command(label="Upload Folder To Music Favorite Library",command=lambda:self.upload_from_folder("Music_Favorite",None,True))
        favorite_music.add_separator()
        favorite_music.add_command(label="Upload File/s To Music Favorite Library",command=lambda:self.add_files_to_db("Music_Favorite"))
        favorite_music.add_separator()
        favorite_music.add_command(label="Clear Music Favorite Library",command=lambda:self.clear_database("Music_Favorite"))
        music_menu.add_cascade(label="Music Favorite Library",menu=favorite_music)
        music_menu.add_separator()
        upload_videos=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        upload_videos.add_command(label="Load Video Library",command=lambda:self.load_library("Videos",None,False))
        upload_videos.add_separator()
        upload_videos.add_command(label="Upload Folder To Video Library",command=lambda:self.upload_from_folder("Videos",None,True))
        upload_videos.add_separator()
        upload_videos.add_command(label="Upload File/s To Video Library",command=lambda:self.add_files_to_db("Videos"))
        upload_videos.add_separator()
        upload_videos.add_command(label="Clear Video Library",command=lambda:self.clear_database("Videos"))
        music_menu.add_cascade(label='Video Library',menu=upload_videos)
        favorite_videos=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        favorite_videos.add_command(label="Load Video Favorite Library",command=lambda:self.load_library("Videos_Favorite",None,False))
        favorite_videos.add_separator()
        favorite_videos.add_command(label="Upload Folder To Video Favorite Library",command=lambda:self.upload_from_folder("Videos_Favorite",None,True))
        favorite_videos.add_separator()
        favorite_videos.add_command(label="Upload File/s To Video Favorite Library",command=lambda:self.add_files_to_db("Videos_Favorite"))
        favorite_videos.add_separator()
        favorite_videos.add_command(label="Clear Video Favorite Library",command=lambda:self.clear_database("Videos_Favorite"))
        music_menu.add_cascade(label='Video Favorite Library',menu=favorite_videos)
        music_videos=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        music_videos.add_command(label="Load Music Videos Library",command=lambda:self.load_library("Videos_Music",None,False))
        music_videos.add_separator()
        music_videos.add_command(label="Upload Folder To Music Videos Library",command=lambda:self.upload_from_folder("Videos_Music",None,True))
        music_videos.add_separator()
        music_videos.add_command(label="Upload File/s To Music Videos Library",command=lambda:self.add_files_to_db("Videos_Music"))
        music_videos.add_separator()
        music_videos.add_command(label="Clear Music Videos Library",command=lambda:self.clear_database("Videos_Music"))
        music_menu.add_cascade(label='Music Videos Library',menu=music_videos)
        karoake_videos=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        karoake_videos.add_command(label="Load Karaoke Videos Library",command=lambda:self.load_library("Videos_Karaoke",None,False))
        karoake_videos.add_separator()
        karoake_videos.add_command(label="Upload Folder To Karaoke Videos Library",command=lambda:self.upload_from_folder("Videos_Karaoke",None,True))
        karoake_videos.add_separator()
        karoake_videos.add_command(label="Upload File/s To Karaoke Videos Library",command=lambda:self.add_files_to_db("Videos_Karaoke"))
        karoake_videos.add_separator()
        karoake_videos.add_command(label="Clear Karaoke Videos Library",command=lambda:self.clear_database("Videos_Karaoke"))
        music_menu.add_cascade(label='Karaoke Videos Library',menu=karoake_videos)
        music_menu.add_separator()
        upload_image=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        upload_image.add_command(label="Load Picture Library",command=lambda:self.load_library("Pictures",None,False))
        upload_image.add_separator()
        upload_image.add_command(label="Upload Folder To Picture Library",command=lambda:self.upload_from_folder("Pictures",None,True))
        upload_image.add_separator()
        upload_image.add_command(label="Upload File/s To Picture Library",command=lambda:self.add_files_to_db("Pictures"))
        upload_image.add_separator()
        upload_image.add_command(label="Clear Picture Library",command=lambda:self.clear_database("Pictures"))
        music_menu.add_cascade(label='Picture Library',menu=upload_image)
        family_image=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        family_image.add_command(label="Load Picture Family Library",command=lambda:self.load_library("Pictures_Family",None,False))
        family_image.add_separator()
        family_image.add_command(label="Upload Folder To Picture Family Library",command=lambda:self.upload_from_folder("Pictures_Family",None,True))
        family_image.add_separator()
        family_image.add_command(label="Upload File/s To Picture Family Library",command=lambda:self.add_files_to_db("Pictures_Family"))
        family_image.add_separator()
        family_image.add_command(label="Clear Picture Family Library",command=lambda:self.clear_database("Pictures_Family"))
        music_menu.add_cascade(label='Picture Family Library',menu=family_image)
        favorite_image=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        favorite_image.add_command(label="Load Picture Favorite Library",command=lambda:self.load_library("Pictures_Favorite",None,False))
        favorite_image.add_separator()
        favorite_image.add_command(label="Upload Folder To Picture Favorite Library",command=lambda:self.upload_from_folder("Pictures_Favorite",None,True))
        favorite_image.add_separator()
        favorite_image.add_command(label="Upload File/s To Picture Favorite Library",command=lambda:self.add_files_to_db("Pictures_Favorite"))
        favorite_image.add_separator()
        favorite_image.add_command(label="Clear Picture Favorite Library",command=lambda:self.clear_database("Pictures_Favorite"))
        music_menu.add_cascade(label='Picture Favorite Library',menu=favorite_image)
        music_menu.add_separator()
        music_menu.add_command(label="Clear All Media Libraries",command=lambda:self.clear_all_libraries())
        download_menu=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        self.menubar.add_cascade(label='   Downloaders   ',menu=download_menu)
        download_menu.add_command(label="YouTube Downloader",command=lambda:self.youtube_downloader())
        screen_menu=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)#
        self.menubar.add_cascade(label='   Media Screen   ',menu=screen_menu)
        screen_menu.add_command(label='Screen Size',command=lambda:set_screen_size())
        screen_menu.add_separator()
        screen_menu.add_command(label='Startup Position',command=lambda:set_screen_position())
        self.device_menu=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        self.device_menu=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        self.menubar.add_cascade(label='   Audio Output Devices   ',menu=self.device_menu)
        self.update_devices()
        theme_menu=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        self.menubar.add_cascade(label='   Color Themes   ',menu=theme_menu)
        theme_menu.add_command(label="Silver Theme",command=lambda:set_theme(self,"silver"))
        theme_menu.add_separator()
        theme_menu.add_command(label="Gold Theme",command=lambda:set_theme(self,"gold"))
        theme_menu.add_separator()
        theme_menu.add_command(label="Blue Theme",command=lambda:set_theme(self,"blue"))
        theme_menu.add_separator()
        theme_menu.add_command(label="Black Theme",command=lambda:set_theme(self,"black"))
        root.config(menu=self.menubar)
    def init_audio(self):
        try:
            default_device = AudioUtilities.GetSpeakers()
            devices=self.MyGetAudioDevices("out")
            result=list(filter(lambda x: default_device.FriendlyName in x, devices))
            self.Active_Device=result[0]
            if self.Active_Device=="":
                self.Active_Device="Default"
            self.initial_sound_device=self.Active_Device.split("(", 1)[0].replace(" ","")
            cmd=[soundvolumeview_path.get(), "/SetDefault", self.initial_sound_device, "1", "/Unmute", self.initial_sound_device, "/SetVolume", self.initial_sound_device, str(Level.get())]
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            devices=AudioUtilities.GetSpeakers()# Initialize Master Volumn Slider
            self.interface = devices.EndpointVolume
            self.Master_Volume=cast(self.interface, POINTER(IAudioEndpointVolume))
            Level.set(50.0)
            self.Master_Volume.SetMasterVolumeLevelScalar(Level.get()/ 100, None)
            self.muted=False
            self.paused=False
        except Exception as ex:
            title='<Interface Initialization>'
            msg1='Initialization Failed. Ending Program!\n'
            msg2=f"Error: '{ex}'"
            messagebox.showerror(title, msg1+msg2)
            self.destroy()
    def clear_config(self):
        setup={}
        with open("Setup.json", "w") as outfile:json.dump(setup, outfile)
        outfile.close()
        self.clear_all_libraries()
        self.restart_program(False)
    def clear_all_libraries(self):
        libs=["Music.json","Music_Favorite.json","Videos.json","Videos_Family.json","Videos_Music.json",
              "Videos_Favorite.json","Videos_Karaoke.json","Pictures.json","Pictures_family.json","Pictures_favorite.json"]
        for db in libs:
            empty={}
            with open(db, "w") as outfile:json.dump(empty, outfile)
            outfile.close()
            self.clear_all()
            self.active_database=""
    def clear_database(self,db,change=True):
        if db=="Music":path="Music.json"
        elif db=="Music_Favorite":path="Music_Favorite.json"
        elif db=="Videos":path="Videos.json"
        elif db=="Videos_Family":path="Videos_Family.json"
        elif db=="Videos_Music":path="Videos_Music.json"
        elif db=="Videos_Favorite":path="Videos_Favorite.json"
        elif db=="Videos_Karaoke":path="Videos_Karaoke.json"
        elif db=="Pictures":path="Pictures.json"
        elif db=="Pictures_Family":path="Pictures_family.json"
        elif db=="Pictures_Favorite":path="Pictures_favorite.json"
        media={}
        with open(path, "w") as outfile:json.dump(media, outfile)
        outfile.close()
        if self.active_database==db:
            self.clear_all()
            if change:self.active_database=""
            self.write_setup()
    def add_files_to_db(self,db,files=None):
        music_exts=['*.mp3','*.wma','*.wav','*.mp2','*.ac3','*.aac','*.eac3','*.m4a',
                    '*.wmav1','*.wmav2','*.opus','*.ogg','*.aiff','*.alac','*.ape','*.flac']
        video_exts=['*.mp4','*.avi','*.mov','*.mkv','*.mpg','*.mpeg','*.wmv','*.webm','*.flv','*.mj2','*.3gp','*.3g2']
        image_exts=['*.bmp','*.jpg','*.jpeg','*.gif','*.png','*.ppm','*.dib']    
        if db=='Music':
            db_path="Music.json"
            exts=music_exts
        elif db=='Music_Favorite':
            db_path="Music_Favorite.json"
            exts=music_exts
        elif db=='Videos':
            db_path="Videos.json"    
            exts=video_exts
        elif db=='Videos_Family':
            db_path="Videos_Family.json"  
            exts=video_exts
        elif db=='Videos_Music':
            db_path="Videos_Music.json"  
            exts=video_exts
        elif db=='Videos_Favorite':
            db_path="Videos_Favorite.json"  
            exts=video_exts
        elif db=='Videos_Karaoke':
            db_path="Videos_Karaoke.json"   
            exts=video_exts
        elif db=='Pictures':
            db_path="Pictures.json"    
            exts=image_exts
        elif db=='Pictures_Family':
            db_path="Pictures_family.json"   
            exts=image_exts
        elif db=='Pictures_Favorite':
            db_path="Pictures_favorite.json"
            exts=image_exts
        if files==None:
            files=filedialog.askopenfilenames(title=f"Please Select Files To Upload To {db} Database.", filetypes=(("Media files", exts),))
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
        if self.active_database==db:self.load_library(db,None,False)
    def upload_from_folder(self,db,init_dir=None,ask=True):
        if db=='Music':
            exts=self.ffmpeg_audio_exts
            db_path="Music.json"
            if init_dir==None:init_dir=self.music_folder
        elif db=='Music_Favorite':
            exts=self.ffmpeg_audio_exts
            db_path="Music_Favorite.json"
            if init_dir==None:init_dir=self.music_favorite_folder
        elif db=='Videos':
            exts=self.ffmpeg_video_exts
            db_path="Videos.json"
            if init_dir==None:init_dir=self.video_folder    
        elif db=='Videos_Family':
            exts=self.ffmpeg_video_exts
            db_path="Videos_Family.json"  
            if init_dir==None:init_dir=self.video_family_folder    
        elif db=='Videos_Favorite':
            exts=self.ffmpeg_video_exts
            db_path="Videos_Favorite.json"  
            if init_dir==None:init_dir=self.video_favorite_folder
        elif db=='Videos_Karaoke':
            exts=self.ffmpeg_video_exts
            db_path="Videos_Karaoke.json"   
            if init_dir==None:init_dir=self.video_karaoke_folder    
        elif db=="Videos_Music":
            exts=self.ffmpeg_video_exts
            db_path="Videos_Music.json"
            if init_dir==None:init_dir=self.video_music_folder    
        elif db=='Pictures':
            exts=self.ffmpeg_image_exts
            db_path="Pictures.json"    
            if init_dir==None:init_dir=self.picture_folder
        elif db=='Pictures_Family':
            exts=self.ffmpeg_image_exts
            db_path="Pictures_family.json"   
            if init_dir==None:init_dir=self.picture_family_folder    
        elif db=='Pictures_Favorite':
            exts=self.ffmpeg_image_exts
            db_path="Pictures_favorite.json"
            if init_dir==None:init_dir=self.picture_favorite_folder    
        else:return
        if ask:
            folder_path=filedialog.askdirectory(initialdir=init_dir,title=f"Please Select A Folder To Upload To {db} Database Or Click 'Select Folder' To Select Default Folder.")  
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
        if self.active_database==db or self.active_database=="":self.load_library(db,path_active,False)
    def MyGetAudioDevices(self, direction="in", State = DEVICE_STATE.ACTIVE.value):
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
    def update_devices(self):# False For Playback Devices, True For Capture
        output_devices = self.MyGetAudioDevices("out")
        self.device_menu.delete(0, 'end')
        for d in range(len(output_devices)):
            self.device_menu.add_command(label=output_devices[d],command=lambda x=output_devices[d]:self.select_output_device(x))
        self.device_menu.add_separator()
        self.device_menu.add_command(label="Refresh Device List",command=lambda:self.update_devices())
        root.update()
    def clear_all(self):# Destroys All Window Widgets
        try:
            self.media_list.delete(0,tk.END)
            self.Media_Dict.clear()
            self.Original_Dict.clear()
            app.root.update()
        except Exception:pass
    def write_setup(self):
        temp_dict={}
        sc=json.load(open("Setup.json", "r"))
        json.dump(sc,open("Setup.json", "w"),indent=4)
        temp_dict[0]=str(Screen_Height.get())
        temp_dict[1]=Screen_Position.get()
        temp_dict[2]=Slide_Show_Delay.get()
        temp_dict[3]=self.active_database
        temp_dict[4]=Theme.get()
        temp_dict[5]=str(round(Level.get()))
        temp_dict[6]=ffmpeg_path.get()
        temp_dict[7]=ffprobe_path.get()
        temp_dict[8]=ffplay_path.get()
        temp_dict[9]=soundvolumeview_path.get()
        with open("Setup.json", "w") as outfile:json.dump(temp_dict, outfile)
        outfile.close()
        temp_dict.clear()
    def set_defaults(self):
        temp_dict=json.load(open("Setup.json", "r+"))
        if len(temp_dict)==0:
            Screen_Position.set("Top Center")
            Slide_Show_Delay.set("0")
            self.active_database=""
            Theme.set("blue")
            PNG_1.set("2000x100_blue.png")
            PNG_2.set("500x100_blue.png")
            B_Color.set("#333333")
            T_Color.set("#094551")
            F_Color.set("#ffffff")#White
            Level.set(50.0)
            self.write_setup()
        else:    
            Theme.set(temp_dict["4"])
            if temp_dict["4"]=="blue":
                PNG_1.set("2000x100_blue.png")
                PNG_2.set("500x100_blue.png")
                B_Color.set("#333333")
                T_Color.set("#094551")
                F_Color.set("#ffffff")#White
            elif temp_dict["4"]=="gold":
                PNG_1.set("2000x100_gold.png")
                PNG_2.set("500x100_gold.png")
                B_Color.set("#001829")
                T_Color.set("#846b1c")
                F_Color.set("#ffffff")#White
            elif temp_dict["4"]=="black":
                PNG_1.set("2000x100_black.png")
                PNG_2.set("500x100_black.png")
                B_Color.set("#000000")
                T_Color.set("#5c5c5c")
                F_Color.set("#ffffff")#White
            elif temp_dict["4"]=="silver":
                PNG_1.set("2000x100_silver.png")
                PNG_2.set("500x100_silver.png")
                B_Color.set("#333333")
                T_Color.set("#808080")
                F_Color.set("#000000")#White
            ffmpeg_path.set(temp_dict["6"])
            ffprobe_path.set(temp_dict["7"])
            ffplay_path.set(temp_dict["8"])
            soundvolumeview_path.set(temp_dict["9"])
            self.active_database=temp_dict["3"]
    def load_setup(self):
        temp_dict=json.load(open("Setup.json", "r+"))
        if temp_dict["0"]=="0" or temp_dict["0"]=="":
            hgt=int(app.screen_height-app.root_height)+int(0.2*app.taskbar_height)
            Screen_Height.set(hgt)
        else:    
            Screen_Height.set(int(temp_dict["0"]))
        if temp_dict["1"]=="":
            Screen_Position.set("Top Center")
        else:        
            Screen_Position.set(temp_dict["1"])
        if temp_dict["2"]=="":
            Slide_Show_Delay.set("0")
        else:
            Slide_Show_Delay.set(temp_dict["2"])    
        self.active_database=temp_dict["3"]
        if temp_dict["4"]=="" or temp_dict["4"]=="blue":
            Theme.set("blue")
            PNG_1.set("2000x100_blue.png")
            PNG_2.set("500x100_blue.png")
            B_Color.set("#333333")
            T_Color.set("#094551")
            F_Color.set("#ffffff")#White
        elif temp_dict["4"]=="gold":
            Theme.set("gold")
            PNG_1.set("2000x100_gold.png")
            PNG_2.set("500x100_gold.png")
            B_Color.set("#001829")
            T_Color.set("#846b1c")
            F_Color.set("#ffffff")#White
        elif temp_dict["4"]=="black":   
            Theme.set("black")
            PNG_1.set("2000x100_black.png")
            PNG_2.set("500x100_black.png")
            B_Color.set("#000000")
            T_Color.set("#5c5c5c")
            F_Color.set("#ffffff")#White
        elif temp_dict["4"]=="silver":   
            Theme.set("silver")
            PNG_1.set("2000x100_silver.png")
            PNG_2.set("500x100_silver.png")
            B_Color.set("#333333")
            T_Color.set("#808080")
            F_Color.set("#000000")#White
        if temp_dict["5"]=="":
            Level.set(50.0)
        else:
            Level.set(float(temp_dict["5"]))
        ffmpeg_path.set(temp_dict["6"])
        ffprobe_path.set(temp_dict["7"])
        ffplay_path.set(temp_dict["8"])
        soundvolumeview_path.set(temp_dict["9"])
        temp_dict.clear()
        self.write_setup()
    def load_library(self,db,active_folder=None,skip=False):
        with open("Setup.json", 'r') as file:
            data = json.load(file)
        data["3"]=db
        with open("Setup.json", 'w') as file:
            json.dump(data, file, indent=4)
        if not skip:self.load_setup()
        if self.active_database=="" and db=="":return
        if db=="Music":
            path="Music.json"
            self.active_media="music"
        elif db=="Music_Favorite":
            path="Music_Favorite.json"
            self.active_media="music"
        elif db=="Videos":
            path="Videos.json"
            self.active_media="video"
        elif db=="Videos_Family":
            path="Videos_Family.json"
            self.active_media="video"
        elif db=="Videos_Favorite":
            path="Videos_Favorite.json"
            self.active_media="video"
        elif db=="Videos_Music":
            path="Videos_Music.json"
            self.active_media="video"
        elif db=="Videos_Karaoke":
            path="Videos_Karaoke.json"
            self.active_media="video"
        elif db=="Pictures":
            path="Pictures.json"
            self.active_media="picture"
        elif db=="Pictures_Family":
            path="Pictures_family.json"
            self.active_media="picture"
        elif db=="Pictures_Favorite":
            path="Pictures_favorite.json"
            self.active_media="picture"
        else:return
        self.active_folder=active_folder    
        self.clear_all()
        self.Original_Dict=json.load(open(path, "r+"))
        self.Media_Dict=json.load(open(path, "r+"))
        if len(self.Media_Dict)==0:
            self.key_now=None
            msg1=f'{db.replace("_"," ")} Library Is Empty! Please Select\n'
            msg2='"Upload Folder Or File/s To Library" First.'
            msg=msg1+msg2
            messagebox.showwarning(f"<{db.replace("_"," ")} Library>",msg)
            return
        else:
            self.active_database=db
            app.root.title(f"My Media Player ({db.replace("_"," ")} Library), Playing On Audio Device: {self.Active_Device}")
            if self.shuffled and not self.repeat:
                temp=list(self.Media_Dict.values())
                self.media_list
                random.shuffle(temp)
                self.Media_Dict=dict(zip(self.Media_Dict, temp))
            elif not self.shuffled:    
                temp=list(self.Original_Dict.values())
                self.Media_Dict=dict(zip(self.Original_Dict, temp))
            for key,self.file in self.Media_Dict.items():
                basename=os.path.basename(self.Media_Dict[key])
                text=os.path.splitext(basename)[0]
                index=f"{int(key)+1}.  {text}" 
                self.media_list.insert(tk.END,index)
            self.media_list.bind("<ButtonRelease-1>",lambda event:self.ctrl_btn_clicked(event,"media play"))
            self.vbar.config(command=self.media_list.yview )  
            self.ybar.config(command=self.media_list.xview ) 
            self.media_list.yview_moveto(0)     
        self.set_master_volume()
    def select_output_device(self,device):
        try:
            devices=self.MyGetAudioDevices("out")
            result=list(filter(lambda x: device in x, devices))
            self.Active_Device=result[0]
            soundview_device=self.Active_Device.split("(", 1)[0].replace(" ","")
            cmd=[soundvolumeview_path.get(), "/SetDefault", soundview_device, "1", "/Unmute", soundview_device, "/SetVolume", soundview_device, str(Level.get())]
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            devices=AudioUtilities.GetSpeakers()# Initialize Master Volumn Slider
            self.interface = devices.EndpointVolume
            self.Master_Volume=cast(self.interface, POINTER(IAudioEndpointVolume))
            self.Master_Volume.SetMasterVolumeLevelScalar(Level.get()/ 100, None)
            app.root.title(f"My Media Player ({self.active_database.replace("_"," ")} Library), Playing On Audio Device: {self.Active_Device}")
        except Exception as ex:
            title='<Audio Output Device>'
            msg1='Initialization Audio Device Failed. Ending Program!\n'
            msg2=f"Error: '{ex}'"
            msg3="Using Default Audio Device."
            messagebox.showerror(title, msg1+msg2+msg3)
            pass
class URLHandler:
    def __init__(self, url):
        self.url = url
    def validate_url(self):#*
        if self.__is_youtube_video_id(self.url):
            self.url = f"https://www.youtube.com/watch?v={self.url}"
        return self.validate_url_link(self.url)
    def validate_url_link(self, url: str):
        # Validates the given YouTube video URL.
        is_valid_link, link_type = self.__is_youtube_link(url)
        if not is_valid_link:
            return False, link_type.lower()
        return is_valid_link, link_type.lower()
    def __is_youtube_link(self, link: str):
        # Check if the given link is a YouTube video.
        is_video = self.__is_youtube_video(link)
        is_short = self.__is_youtube_shorts(link)
        return (is_video, "video") if is_video \
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
        title=f'Validate {Download_Type.get()} URL '
        msg1=f'The {Download_Type.get()} URL Entered Is "Not Invalid"!\n'
        msg2='Please Entered A Valid YouTube URL!'
        msg=msg1+msg2
        messagebox.showerror(title, msg)
        URL.set("")
class YouTube_GUI(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        app.root.withdraw()
        self.num_items=0
        self.last_percentage=0.0
        self.completed_items=0
        self.deiconify()
        self.grab_set() # Receive Events And Prevent root Window Interaction
        width=int(app.work_area[2]*0.6)
        height=int(app.work_area[3]*0.3)
        x=int((app.work_area[2]/2)-(width/2))
        y=int((app.work_area[3]/2)-(height/2))
        self.geometry('%dx%d+%d+%d' % (width, height, x, y, ))
        self.configure(bg="#094983")
        self.ReadMe_File=tk.StringVar()
        self.ReadMe_File.set(os.path.join(Path(__file__).parent.absolute(),"youtube_downloader_readme_en.txt"))
        self.youtube_readme=os.path.join(Path(__file__).parent.absolute(),"youtube_downloader_readme_en.txt")
        self.title("My YouTube GUI Downloader")
        self.resizable(True,True)
        self.protocol("WM_DELETE_WINDOW", self.youtube_destroy)
        self.style = ttk.Style(parent)
        self.style.theme_use('alt')
        self.style.map('TCombobox', background=[('readonly','#002343')])# Arrow Background
        self.style.map('TCombobox', fieldbackground=[('readonly','#dfdfdf')])# Text Background
        self.style.map('TCombobox', selectbackground=[('readonly','#dfdfdf')])
        self.style.map('TCombobox', selectforeground=[('readonly', '#000000')])
        self.style.configure("TCombobox", arrowsize=18, arrowcolor="aqua")
        self.style.configure("Horizontal.TProgressbar", troughcolor ='black', background='aqua')
        self.update()
        self.rowconfigure(9, minsize=30)
        self.columnconfigure(10, minsize=30)
        self.conn_lbl=tk.Label(self,text='Internet Connection: ',background="#094983",foreground="#ffffff",justify='right', anchor='e')
        self.conn_lbl.grid(row = 0, column = 0, sticky = 'e', pady = 2)
        self.conn=self.check_internet_connection(False)
        if self.conn:# Preceed
            text="  There is an Internet Connection  "
            forecolor="#dfdfdf"
            backcolor="#369e09"
        else:# Go No Further
            text="  No Internet Available! Check Your Connection And Try Again!  "
            forecolor="#f70505"
            backcolor="#ffffff"
        self.conn_results=tk.Label(self,text=text,background=backcolor,foreground=forecolor,justify="center",relief='solid')
        self.conn_results.grid(row = 0, column = 1, columnspan=2, sticky = 'w', pady = 3)
        if not self.conn:
            self.retry_conn=tk.Button(self,text="Retry Internet Connection",foreground="#ffffff",background="#094983",justify="center",anchor="w")
            self.retry_conn.grid(row = 0, column = 1, sticky = 'w', pady = 3)
            self.retry_conn.bind("<ButtonRelease>",lambda event:self.check_internet_connection(True))
        Download_Folder.set(str(os.path.join(Path.home(),"Downloads").replace("\\","/")))
        self.download_lbl=tk.Label(self,text='Select Destination Folder: ',background="#094983",foreground="#ffffff",justify="center",anchor='e')
        self.download_lbl.grid(row = 1, column = 0, columnspan=1 ,sticky = 'e', pady = 3)
        wid=len(Download_Folder.get())+1   
        self.download_txt=tk.Entry(self,textvariable=Download_Folder,background="#dfdfdf",foreground="#000000",justify="center",width=wid)
        self.download_txt.grid(row = 1, column = 1, columnspan=5, sticky = 'w', pady = 3)
        self.download_txt.bind("<ButtonRelease>",lambda event:self.change_download_folder(Download_Folder.get()))
        self.yt_user_lbl=tk.Label(self,text='YouTube User Name: ',background="#094983",foreground="#ffffff",justify="center",anchor='e')
        self.yt_user_lbl.grid(row = 2, column = 0, columnspan=1, sticky = 'e', pady = 3)
        self.yt_user_name=tk.Entry(self,textvariable=User_Name,background="#dfdfdf",foreground="#000000",justify="left",width=wid)
        self.yt_user_name.grid(row = 2, column = 1, columnspan=1,sticky = 'w', pady = 3)
        self.oauth_btn=tk.Checkbutton(self,text="Use Oauth Authenication",variable=Use_Oauth,background="#000000",onvalue=1,offvalue=0,
                                bg="#b2ffff",activebackground="#dfdfdf",selectcolor="#dfdfdf",border=2, relief="groove",command=lambda:self.login_status())
        self.oauth_btn.grid(row = 2, column = 2, columnspan=1, sticky = 'w', pady = 3)
        self.yt_pass_lbl=tk.Label(self,text='YouTube Password: ',background="#094983",foreground="#ffffff",justify="center",anchor='e')
        self.yt_pass_lbl.grid(row = 3, column = 0, columnspan=1, sticky = 'e', pady = 3)
        self.yt_user_pass=tk.Entry(self,textvariable=User_Password,background="#dfdfdf",foreground="#000000",justify="left",width=wid)
        self.yt_user_pass.grid(row = 3, column = 1, columnspan=1, sticky = 'w', pady = 3)
        self.type_lbl=tk.Label(self,text='Select Download Type: ',background="#094983",foreground="#ffffff",justify="center",anchor='e')
        self.type_lbl.grid(row = 4, column = 0, columnspan=1, sticky = 'e', pady = 3)
        types=["Audio Only","Video + Audio"]
        Download_Type.set(types[1])
        self.type_select=ttk.Combobox(self, textvariable=Download_Type, state="readonly")
        self.type_select['values'] = types
        self.type_select.grid(row = 4, column = 1, columnspan=1, sticky = 'w', pady = 3)
        self.type_select.bind("<<ComboboxSelected>>",lambda event:self.change_download_type())
        self.url_lbl=tk.Label(self,text='Enter YouTube URL: ',background="#094983",foreground="#ffffff",justify="center",anchor='e')
        self.url_lbl.grid(row = 5, column = 0, columnspan=1, sticky = 'e', pady = 3)
        wid=int(width*0.05)
        self.url_txt=tk.Entry(self,textvariable=URL,background="#dfdfdf",foreground="#000000",justify="left", width=wid)
        self.url_txt.grid(row = 5, column = 1, columnspan=7, sticky = 'w', pady = 3)
        self.url_txt.bind("<KeyRelease>",lambda event:self.url_entry)
        self.url_txt.bind("<Button-3>", self.show_context_menu)
        self.context_menu = tk.Menu(self.url_txt, tearoff=False)
        self.context_menu.add_command(label="Paste", command=lambda: self.paste_from_clipboard(self.url_txt))
        self.fetch=tk.Button(self,text="Download",foreground="#ffffff",background="#094983",justify="center",anchor="center")
        self.fetch.grid(row = 5, column = 8, columnspan=2,sticky = 'w', pady = 3, padx=5)
        self.fetch.bind("<ButtonRelease>",lambda event:self.download_url(URL.get(),Download_Folder.get(),Download_Type.get()))
        self.title_lbl=tk.Label(self,text='Download Title: ',background="#094983",foreground="#ffffff",justify="center",anchor='e')
        self.title_lbl.grid(row = 6, column = 0, columnspan=1, sticky = 'e', pady = 3)
        self.update()
        title_width=self.url_txt.cget("width")
        Title.set("")
        URL.set("")
        self.title_name=tk.Label(self,textvariable=Title,background="#dfdfdf",foreground="#000000",justify="center",anchor="w",width=title_width)
        self.title_name.grid(row = 6, column = 1, columnspan=8, sticky = 'w', pady = 3)
        if URL.get=="":self.fetch["state"] = 'disabled'
        self.progress_lbl=tk.Label(self,text='Download Progress: ',background="#094983",foreground="#ffffff",justify="center")
        self.progress_lbl.grid(row = 7, column = 0, columnspan=1, sticky = 'e', pady = 3)
        self.update()
        p_length=(self.url_txt.winfo_width())
        self.progress_bar = ttk.Progressbar(self,style="Horizontal.TProgressbar",orient=tk.HORIZONTAL, length=p_length,mode="determinate",max=100)
        self.progress_bar.grid(row = 7, column = 1, columnspan=6, sticky = 'w', pady = 6, ipady=5)
        self.download_complete=tk.Label(self,text="",background="#094983",foreground="#ffffff",justify="center",anchor="w")
        self.download_complete.grid(row = 7, column = 8 , columnspan=2, sticky = 'w', pady = 3, padx=5)
        self.menubar=Menu(self,fg="#000000")# Create Menubar
        self.file_menu=Menu(self.menubar,background='aqua',foreground='black',tearoff=0)
        self.menubar.add_cascade(label='            File',menu=self.file_menu)
        self.file_menu.add_command(label="Open YouTube",command=lambda:self.open_youtube())
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Open Readme File",command=lambda:self.open_readme())
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit",command=lambda:self.youtube_destroy())
        self.config(menu=self.menubar)
        self.update()
        if self.conn:
            self.file_menu.entryconfig("Open YouTube", state="normal")
        else:self.file_menu.entryconfig("Open YouTube", state="disabled")
        # Clear Json File, json Object Used For Sharing Downloaded Files
        path_dict={}
        self.url_txt.focus_force()
        path_dict={}
        with open(shared_download_files, "w") as json_file:
            json.dump(path_dict, json_file)
        json_file.close()
        self.login_status()
        self.update()
        self.mainloop()
    def show_context_menu(self,event):
            self.context_menu.post(event.x_root, event.y_root)
    def paste_from_clipboard(self,event):
            try:
                clipboard_content=pyperclip.paste()
                if clipboard_content=="":return
                self.url_txt.insert(tk.INSERT, clipboard_content)
            except tk.TclError:
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
                Title.set(title)
                return info.get('_type')=='playlist'
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
    def download_url(self,url, path, audio_video):
        self.completed_items=0
        if not self.conn:return
        if Use_Oauth.get():
            if User_Name.get()=="" or User_Password.get()=="":
                title="< YouTube Login Using Oauth Authenication >"
                msg1="YouTube or Google Login is Required\n"
                msg2="For Oauth Authenication! Please Enter\n"
                msg3="a User Name and/or Password To Continue."
                msg=msg1+msg2+msg3
                messagebox.showerror(title, msg)
                if User_Name.get()=="":self.yt_user_name.focus_force()
                elif User_Password.get()=="":self.yt_user_pass.focus_force()    
                return
        if url is None or url=="":
            title="< YouTube Downloader URL >"
            msg="Missing URL! Please Enter A Valid  URL!"
            messagebox.showerror(title, msg)
            self.url_txt.focus_force()
            return
        self.download_complete.config(text="")
        self.progress_bar['value'] = 0
        Title.set("")
        app.root.update()
        if not self.is_playlist(url):
            self.num_items=1
            self.rename_video_title()
            url_handler = URLHandler(url)# Instantize
            is_valid_link, link_type = url_handler.validate_url()# Only Validates And Returns link_type
            if not is_valid_link or link_type=='unknown':
                url_handler.not_valid_url('URL Link Type')
                return
            if audio_video=="Audio Only":# Single Audio
                if Use_Oauth.get():
                    options = {'format': 'bestaudio/best', 'retries': 5, 'fragment_retries': 20, 'progress_hooks': [self.update_progressbar],'postprocessors': [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'mp3',
                                'preferredquality': '192',}],
                                'outtmpl': f'{Download_Folder.get()}/{Title.get()}.%(ext)s',
                                'oauth2': True,  # Enable OAuth2 authentication
                                'username': User_Name.get(),  # Your account email
                                'password': User_Password.get()}  # Your account password
                else:    
                    options = {'format': 'bestaudio/best', 'retries': 5, 'fragment_retries': 20, 'progress_hooks': [self.update_progressbar],'postprocessors': [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'mp3',
                                'preferredquality': '192',}],
                                'outtmpl': f'{Download_Folder.get()}/{Title.get()}.%(ext)s'}
            elif audio_video=="Video + Audio":# Single Audio/Video
                if Use_Oauth.get():
                    options = {'format': 'best', 'retries': 5, 'fragment_retries': 20, 'progress_hooks': [self.update_progressbar], 
                            'outtmpl': f'{Download_Folder.get()}/{Title.get()}.%(ext)s',
                                'oauth2': True,  # Enable OAuth2 authentication
                                'username': User_Name.get(),  # Your account email
                                'password': User_Password.get()}  # Your account password
                else:    
                    options = {'format': 'best', 'retries': 5, 'fragment_retries': 20, 'progress_hooks': [self.update_progressbar], 
                            'outtmpl': f'{Download_Folder.get()}/{Title.get()}.%(ext)s'}
            else:return
        else:# Play List
            if audio_video=="Audio Only":# All Audio 
                if Use_Oauth.get():
                    options = {'format': 'bestaudio/best', 'retries': 5, 'fragment_retries': 20, 'progress_hooks': [self.update_progressbar],'postprocessors': [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'mp3',
                                'preferredquality': '192',}],
                                'outtmpl': f'{Download_Folder.get()}/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s',
                                'oauth2': True,  # Enable OAuth2 authentication
                                'username': User_Name.get(),  # Your account email
                                'password': User_Password.get()}  # Your account password
                else:   
                    options = {'format': 'bestaudio/best', 'retries': 5, 'fragment_retries': 20, 'progress_hooks': [self.update_progressbar],'postprocessors': [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'mp3',
                                'preferredquality': '192',}],
                                'outtmpl': f'{Download_Folder.get()}/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s'}
            elif audio_video=="Video + Audio":# All Audio/Video 
                if Use_Oauth.get():
                    options = {'format': 'best', 'retries': 5, 'fragment_retries': 20, 'progress_hooks': [self.update_progressbar], 
                                'outtmpl': f'{Download_Folder.get()}/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s',
                                'oauth2': True,  # Enable OAuth2 authentication
                                'username': User_Name.get(),  # Your account email
                                'password': User_Password.get(),  # Your account password
                                'ignoreerrors': True}  # Continue downloading even if some videos fail
                else:    
                    options = {'format': 'best', 'retries': 5, 'fragment_retries': 20, 'progress_hooks': [self.update_progressbar], 
                                'outtmpl': f'{Download_Folder.get()}/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s',
                                'ignoreerrors': True}  # Continue downloading even if some videos fail
            else:return
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            return
        title="Download Status"
        msg1="Your Download Has Completed And\n"
        msg2=f"Saved To {path}"
        msg=msg1+msg2
        messagebox.showinfo(title, msg)
        self.progress_bar["value"]=0
        num_keys=self.get_json_num_keys()
        with open(shared_download_files, "w") as json_file:# Write Download Path and Filename to Shared Json file
            path_dict[str(num_keys)]=Download_Folder.get()
            path_dict[str(num_keys+1)]=Title.get()
            json.dump(path_dict, json_file)
        json_file.close()
        self.update()
    def update_progressbar(self,d):
        if d['status'] == 'downloading':    
            downloaded_bytes = d.get('downloaded_bytes')
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total_bytes:
                percentage = (downloaded_bytes / total_bytes) * 100
            else:
                # Fallback to the string representation if the raw number is missing/unreliable
                percentage = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
            if percentage>self.last_percentage:
                self.download_complete.config(text=f"Downloading: {percentage:.2f}%")
                self.progress_bar['value'] = percentage
            self.last_percentage=percentage
        elif d['status'] == 'finished':
            self.last_percentage=0.0
            self.progress_bar['value'] = 100
            self.completed_items += 1
            self.download_complete.config(text=f"{self.completed_items} of {self.num_items} Download Complete! 100%")
        elif d['status'] == 'error':
            self.last_percentage=0.0
            msg=f"Error During Download: {d.get('error')}"
            messagebox.showerror("Error Downloading From YouTube", msg)
        app.root.update()
    def rename_video_title(self):
            title=Title.get()
            new_title=my_askstring("Rename Video File","Rename The File Here If Desired.",title)
            if new_title!=None and new_title!='':
                Title.set(new_title)
            elif new_title==None or new_title=='':    
                Title.set(title)
    def open_youtube(self):
        if self.file_menu.entrycget("Open YouTube", 'state')=="normal":
            subprocess.run(['start', 'https://www.youtube.com'], shell=True)
    def open_readme(self):
        subprocess.Popen(["notepad.exe", self.youtube_readme])
    def url_entry(self):
        if URL.get()!="":
            self.fetch["state"]='normal'
    def change_download_type(self):#*
        Title.set("")
    def change_download_folder(self,init_dir):#*
        folder_path=filedialog.askdirectory(initialdir=init_dir,title=f"Please Select A Folder For YouTube Downloads Or Click 'Select Folder' To Select Default Folder.")  
        if folder_path=="" or folder_path==None:return
        Download_Folder.set(folder_path)
        wid=len(Download_Folder.get())+1 
        self.download_txt.config(width=wid)
        self.update()
    def check_internet_connection(self,retry):#*
        try:
            requests.get("https://www.google.com", timeout=5)
            if retry:
                self.retry_conn.destroy()
                self.conn_results.config(text="  There is an Internet Connection  ",foreground="#ffffff",background="#369e09")
                self.file_menu.entryconfig("Open YouTube", state="normal")
                self.update()
            return True
        except Exception:
            return False
    def get_json_num_keys(self,):
        try:
            with open(shared_download_files, 'r') as file:
                    data = json.load(file)
                    return len(data.keys())
        except Exception:
            return None
    def login_status(self):
        if Use_Oauth.get()==False: 
            self.yt_user_name.config(state=tk.DISABLED)
            self.yt_user_pass.config(state=tk.DISABLED)
            self.update()
        else:    
            self.yt_user_name.config(state=tk.NORMAL)
            self.yt_user_pass.config(state=tk.NORMAL)
            self.yt_user_name.focus_force()
            self.update()
    def youtube_destroy(self,):# X Icon Was Clicked
        for widget in self.winfo_children():
            if isinstance(widget, tk.Canvas):widget.destroy()
            else:widget.destroy()
        self.withdraw()
        app.root.deiconify()
        app.root.grab_set()
        app.root.focus_force()
        mm_player.update_databases()
        style=ttk.Style()
        style.theme_use('alt')
        style.configure("Vertical.TScrollbar", background="#094983")
        style.configure("Horizontal.TScrollbar", background="#094983")
        style.configure("Vertical.TScrollbar", arrowsize=20, arrowcolor="aqua")
        style.configure("Horizontal.TScrollbar", arrowsize=20, arrowcolor="aqua")
        app.root.update()
class AsyncTkApp:
    def __init__(self, root):
        self.root = root
        self._stop_timer=False
        self._timer_running=False# Timer Status
        self._time_now=0.0
        self._elapsed_time=0.0
        self._paused_time=0.0
        self._factor=1.0
        self._ns_time=0.0
        self.style=ttk.Style()
        self.style.theme_use('alt')
        self.style.configure("Vertical.TScrollbar", background="#094983")
        self.style.configure("Horizontal.TScrollbar", background="#094983")
        self.style.configure("Vertical.TScrollbar", arrowsize=20, arrowcolor="aqua")
        self.style.configure("Horizontal.TScrollbar", arrowsize=20, arrowcolor="aqua")
        self.primary_monitor=MonitorFromPoint((0, 0))
        self.monitor_info=GetMonitorInfo(self.primary_monitor)
        self.monitor_area=self.monitor_info.get("Monitor")
        self.work_area=self.monitor_info.get("Work")
        self.aspect_ratio=self.work_area[2]/self.work_area[3]
        self.taskbar_height=self.monitor_area[3]-self.work_area[3]
        self.screen_height=(self.work_area[3]-self.taskbar_height)
        self.root_width=int(self.work_area[2]*0.8)
        self.root.wm_attributes("-topmost",True)
        self.root.configure(bg="#094983")
        self.root.resizable(False,False)
        btn_hgt=int(round((30*self.work_area[3])/1032))
        lbl_hgt=int(round((20*self.work_area[3])/1032))
        self.media_font=media_font
        self.media_font2=media_font2
        self.emoji_font=emoji_font
        self.emoji_font2=emoji_font2
        self.title_skin=tk.PhotoImage(file=os.path.join(Path(__file__).parent.absolute(), PNG_1.get()))
        self.btn_skin=tk.PhotoImage(file=os.path.join(Path(__file__).parent.absolute(), PNG_2.get()))
        self.main_frame=tk.Frame(self.root,relief="raised",borderwidth=5)
        self.main_frame.pack(side='top',anchor='nw',fill='x', expand=False, padx=(0,0), pady=(0,0))
        self.main_frame.config(bg="#0b5394")
        self.title_frame=tk.Frame(self.main_frame,relief="sunken",borderwidth=3)
        self.title_frame.pack(side='top',anchor='nw',fill='x', expand=True, padx=(3,3), pady=(3,3))
        self.title_frame.config(bg="#000000")
        pix_wid=int(self.root_width*0.17) #Make Width 17% Of Root Width
        self.volume_lbl=tk.Button(self.title_frame,text='Master Volume',image=self.btn_skin, compound="center",width=pix_wid+2,height=lbl_hgt,activeforeground='#4cffff',
                        background="#bcbcbc",foreground=F_Color.get(),font=self.media_font,justify="center",relief='sunken',borderwidth=5)
        self.volume_lbl.pack(side='left',anchor='nw',fill='both', expand=False, padx=(3,0), pady=(3,3))
        self.title_lbl=tk.Button(self.title_frame,text="",image=self.title_skin, compound="center",height=lbl_hgt,activeforeground='#4cffff',
                        background="#bcbcbc",foreground=F_Color.get(),font=self.media_font,justify="center",relief='sunken',borderwidth=5)
        self.title_lbl.pack(side='right',anchor='ne',fill='both',expand=True,padx=(5,3), pady=(3,3))
        self.slider_frame=tk.Frame(self.main_frame,relief="sunken",borderwidth=3)
        self.slider_frame.pack(side='top',anchor='nw',fill='both', expand=False, padx=(3,3), pady=(0,3))
        self.slider_frame.config(bg="#000000")
        self.volume=tk.Scale(self.slider_frame, variable=Level, from_=0,to=100, orient='horizontal', resolution=1.0, 
                        tickinterval=25,showvalue=1,borderwidth=5,relief="sunken",font=self.media_font,
                        length=pix_wid,bg=B_Color.get(),fg="#ffffff",troughcolor=T_Color.get(), activebackground="#4cffff",
                        highlightthickness=3,command=lambda event:mm_player.set_master_volume())
        self.volume.pack(side='left',anchor='nw',fill='both', expand=False, padx=(3,0), pady=(3,3))
        self.volume.bind("<ButtonRelease-1>",lambda event:mm_player.slider_released())# Sets Video Window aboutctive
        self.time_scale=tk.Scale(self.slider_frame,relief="sunken",orient='horizontal',resolution=0,
                            bg=B_Color.get(),borderwidth=5,font=self.media_font,fg="#ffffff",troughcolor=T_Color.get(),  
                            activebackground="#4cffff",highlightthickness=3)
        self.time_scale.pack(side='left',anchor='nw',fill='both',expand=True, padx=(5,3), pady=(3,3))
        self.time_scale.bind("<ButtonRelease-1>",lambda event:mm_player.end_seeking(event))
        self.time_scale.bind("<ButtonPress-1>",lambda event:mm_player.begin_seeking(event))
        self.ctrl_frame=tk.Frame(self.main_frame,relief="sunken",borderwidth=3)
        self.ctrl_frame.pack(side='right',anchor='ne',fill='both', expand=True, padx=(3,3), pady=(0,3))
        self.ctrl_frame.config(bg="#000000")
        self.quit_btn=tk.Button(self.ctrl_frame,text="Quit",foreground=F_Color.get(),image=self.btn_skin, compound="center",font=self.media_font2,relief="sunken",
                        background="#bcbcbc",borderwidth=5,activeforeground="#4cffff",height=btn_hgt,width=1,justify="center",anchor="center")
        self.quit_btn.pack(side='right',fill='x', expand=True, padx=(5,3), pady=(3,3))
        self.quit_btn.bind("<ButtonRelease>",lambda event:self._close_main())
        self.stop_btn=tk.Button(self.ctrl_frame,text="⏹️",foreground=F_Color.get(),image=self.btn_skin, compound="center",font=self.emoji_font,relief="sunken",
                        background="#bcbcbc",borderwidth=5,activeforeground="#4cffff",height=btn_hgt,width=1,justify="center",anchor="center")
        self.stop_btn.pack(side='right',fill='x', expand=True, padx=(0,0), pady=(3,3))
        self.stop_btn.bind("<ButtonRelease>",lambda event:mm_player.ctrl_btn_clicked(event,"stop"))
        self.mute_btn=tk.Button(self.ctrl_frame,text="\U0001F50A",foreground=F_Color.get(),image=self.btn_skin, compound="center",font=self.emoji_font2,relief="sunken",
                        background="#bcbcbc",borderwidth=5,activeforeground="#4cffff",height=btn_hgt,width=1,justify="center",anchor="center")
        self.mute_btn.pack(side='right',fill='x', expand=True, padx=(5,5), pady=(3,3))
        self.mute_btn.bind("<ButtonRelease>",lambda event:mm_player.ctrl_btn_clicked(event,"mute"))
        self.repeat_btn=tk.Button(self.ctrl_frame,text="🔁",foreground=F_Color.get(),image=self.btn_skin, compound="center",font=self.emoji_font2,relief="sunken",
                        background="#bcbcbc",borderwidth=5,activeforeground="#4cffff",height=btn_hgt,width=1,justify="center",anchor="center")
        self.repeat_btn.pack(side='right',fill='x', expand=True, padx=(0,0), pady=(3,3))
        self.repeat_btn.bind("<ButtonRelease>",lambda event:mm_player.ctrl_btn_clicked(event,"repeat"))
        self.pause_btn=tk.Button(self.ctrl_frame,text="⏸️",foreground=F_Color.get(),image=self.btn_skin, compound="center",font=self.emoji_font,relief="sunken",
                        background="#bcbcbc",borderwidth=5,activeforeground="#4cffff",height=btn_hgt,width=1,justify="center",anchor="center")
        self.pause_btn.pack(side='right',fill='x', expand=True, padx=(5,5), pady=(3,3))
        self.pause_btn.bind("<ButtonRelease>",lambda event:mm_player.pause(event))
        self.next_btn=tk.Button(self.ctrl_frame,text="⏭️",foreground=F_Color.get(),image=self.btn_skin, compound="center",font=self.emoji_font,relief="sunken",
                        background="#bcbcbc",borderwidth=5,activeforeground="#4cffff",height=btn_hgt,width=1,justify="center",anchor="center")
        self.next_btn.pack(side='right',fill='x', expand=True, padx=(0,0), pady=(3,3))
        self.next_btn.bind("<ButtonRelease>",lambda event:mm_player.ctrl_btn_clicked(event,"next"))
        self.previous_btn=tk.Button(self.ctrl_frame,text="⏮️",foreground=F_Color.get(),image=self.btn_skin, compound="center",font=self.emoji_font,relief="sunken",
                        background="#bcbcbc",borderwidth=5,activeforeground="#4cffff",height=btn_hgt,width=1,justify="center",anchor="center")
        self.previous_btn.pack(side='right',fill='x', expand=True, padx=(5,5), pady=(3,3))
        self.previous_btn.bind("<ButtonRelease>",lambda event:mm_player.ctrl_btn_clicked(event,"previous"))
        self.shuffle_btn=tk.Button(self.ctrl_frame,text="🔀"+" ▶",foreground=F_Color.get(),image=self.btn_skin, compound="center",font=self.emoji_font2,relief="sunken",
                        background="#bcbcbc",borderwidth=5,activeforeground="#4cffff",height=btn_hgt,width=1,justify="center",anchor="center")
        self.shuffle_btn.pack(side='right',fill='x', expand=True, padx=(0,0), pady=(3,3))
        self.shuffle_btn.bind("<ButtonRelease>",lambda event:mm_player.ctrl_btn_clicked(event,"shuffled"))
        self.play_btn=tk.Button(self.ctrl_frame,text="▶️",foreground=F_Color.get(),image=self.btn_skin, compound="center",font=self.emoji_font,relief="sunken",
                        background="#bcbcbc",borderwidth=5,activeforeground="#4cffff",height=btn_hgt,width=1,justify="center",anchor="center")
        self.play_btn.pack(side='right',fill='x', expand=True, padx=(3,5), pady=(3,3))
        self.play_btn.bind("<ButtonRelease>",lambda event:mm_player.ctrl_btn_clicked(event,"btn play"))
        self.root.withdraw()
        self.root.update()
        self.root_height=self.main_frame.winfo_reqheight()
        x=(self.work_area[2]/2)-(self.root_width/2)
        self.root_x=int(x-((7/x)*x))# x Not Exactly Centered, Use Correction Factor
        self.root_y=self.screen_height-self.root_height# Just Above Taskbar
        self.root_y2=((self.screen_height/2)-(self.root_height/2))+(self.taskbar_height/2)# Center Screen
        self.root_y3=self.root_y+self.taskbar_height# Covers Taskbar    
        self.root.geometry('%dx%d+%d+%d' % (self.root_width, self.root_height, self.root_x, self.root_y))
        self.ico_path=os.path.join(Path(__file__).parent.absolute(),"movie.ico")
        self.root.iconbitmap(default=self.ico_path)# root and children
        self.root.iconbitmap(self.ico_path)
        self.root.title(f"My Media Player")
        mm_player.load_menubar()
        bind_keyboard()
        self.root.protocol("WM_DELETE_WINDOW", self._close_main)
        self.root.update()
        self.root.deiconify()
        self.root.update()
        txt=get_greeting("open")
        self.title_lbl.config(text=txt)
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)    
    def _reset_timer(self):        
        self._stop_timer=False
        Start_Time.set(0.0)
        self.time_scale.set(float(mm_player.start_time))
        self.time_scale.update()
        self._timer_running=False
        self._time_now=mm_player.start_time
        self._elapsed_time=0.0
        self._paused_time=0.0
        self._factor=1.0
        self._ns_time=0.0
    def _start_timer(self):
        mm_player.next_ready=True
        if mm_player.click_next:
            self._timer_running=True
            mm_player.ctrl_btn_clicked(self,"next")
        else:
            self._timer_running=True
            self.loop.create_task(self._timer_task())
    async def _timer_task(self):
        mm_player.send_keyboard_key("left")# Make Sure Timer Is Zero
        while not self._stop_timer:
            await asyncio.sleep(0.1) # Non-blocking sleep
            if not self._timer_running:break
            if mm_player.active_media=="music" or mm_player.active_media=="video":
                if not mm_player.ffplay_running:break 
            elif mm_player.active_media=="picture":
                if not mm_player.cv2_running:break
            foreground_hwnd = win32gui.GetForegroundWindow()
            if foreground_hwnd==Target_Hwnd:# Keep Focus On root To Capture All Events
                await asyncio.sleep(0.1)
                self.root.focus_force()  
                self.root.update_idletasks()
            if mm_player.paused:# self._factor Is Correction For Paused Time For Slider
                self._paused_time=perf_counter_ns()
                self._factor=self._ns_time/self._paused_time
            else:
                self._ns_time=perf_counter_ns()*self._factor
                self._elapsed_time=(self._ns_time-Start_Time.get())/1000000000
                self._time_now+=self._elapsed_time
                self.time_scale.set(float(self._time_now))
                Start_Time.set(Start_Time.get()+(self._elapsed_time*1000000000))
                if mm_player.ffplay_running:
                    poll=mm_player.process_ffplay.poll()
                    if poll!=None:
                        mm_player.click_next=True# ffplay not running, Terminated By -autoexit, Ready Next File
                        self._stop_timer=True
                        break
            level=mm_player.Master_Volume.GetMasterVolumeLevelScalar()# Volume Slider Level / 100
            Level.set(level*100)# Track Volume From Other Sliders (Windows, Sound Card)
            is_muted=mm_player.Master_Volume.GetMute()
            if is_muted and mm_player.muted==False:mm_player.ctrl_btn_clicked(self,"mute")
            elif not is_muted and mm_player.muted==True:mm_player.ctrl_btn_clicked(self,"mute")
        if mm_player.click_next:mm_player.ctrl_btn_clicked(self,"next")
    def _close_main(self):
        self.loop.stop()
        mm_player.destroy()
    def _run_main(self):
        # Run the Tkinter mainloop and timer loop together
        self._run_asyncio_loop()
        self.root.mainloop()
    def _run_asyncio_loop(self):
        def poll():
            try:
                self.loop.call_soon(self.loop.stop)
                self.loop.run_forever()
            except RuntimeError:
                pass
            self.root.after(10, poll)
        poll()
def my_askinteger(title,prompt,init_val,min_val,max_val):
    d=My_IntegerDialog(title, prompt ,init_val,min_val,max_val)
    answer=d.result
    app.root.update_idletasks()
    return answer  
class My_IntegerDialog(tk.simpledialog._QueryInteger):
    def body(self, master):
        self.attributes("-toolwindow", True)# Remove Min/Max Buttons
        self.bind('<KP_Enter>', self.ok)
        self.bind('<Return>', self.ok)
        pt=tk.Label(master, text=self.prompt, justify="left", font=media_font)
        pad=int((pt.winfo_reqwidth()/2)/2)
        pt.grid(row=2, padx=(5,5),pady=(5,5), sticky='w'+'e')
        self.entry=tk.Entry(master, name="entry", justify='center', bg="#d6ffff", font=media_font)
        self.entry.grid(row=3, padx=(pad,pad), sticky='w'+'e')
        self.entry.bind('<Map>', self.on_map)
        if self.initialvalue is not None:
            self.entry.insert(0, self.initialvalue)
            self.entry.select_range(0, 'end')
        app.root.update_idletasks()
        return self.entry
    def on_map(self, event):
        self.entry.focus_force()    
def set_slide_show():
    title="<Set Slide Show Delay Time In Seconds>"
    msg1='Note:The Edit Picture Menu Is Not Visible When Delay > 0!\n'
    msg2='Enter A Delay Time In Seconds For Picture Slide Show.\n'
    msg3='A Delay Time Of 0 Seconds Indicates No Slide Show.\n'
    msg4='Maximum Delay Time Is 120 Seconds.'
    msg=msg1+msg2+msg3+msg4
    delay=my_askinteger(title,msg,int(Slide_Show_Delay.get()),0,120)
    if delay!=None:
        Slide_Show_Delay.set(str(delay))
        with open("Setup.json", 'r') as file:
            data = json.load(file)
        data["2"]=Slide_Show_Delay.get()
        with open("Setup.json", 'w') as file:
            json.dump(data, file, indent=4)
def set_screen_size():
    scale_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
    height = int(app.work_area[3] * scale_factor)
    default_hgt = int(((app.screen_height-app.root_height)+int(0.2*app.taskbar_height)) * scale_factor) 
    title="<Set Screen Size For Media Window>"
    msg1='Enter A Screen Height For Video Playback.\n'
    msg2=f"Default Screen Height For This Monitor = {default_hgt}.\n"
    msg3='Maximum Height For This Monitor is ' + str(height) +' (Full Screen).\n'
    msg4='The Screen Width Will Be Determined By This Monitors Aspect Ratio!'
    msg=msg1+msg2+msg3+msg4
    hgt=my_askinteger(title,msg,Screen_Height.get(),100,height)
    if hgt!=None:
        Screen_Height.set(hgt)
        with open("Setup.json", 'r') as file:
            data = json.load(file)
        data["0"]=str(Screen_Height.get())
        with open("Setup.json", 'w') as file:
            json.dump(data, file, indent=4)
def my_askstring(title, prompt, init_val=None):
    d=My_StringDialog(title, prompt , init_val)
    answer=d.result
    app.root.update_idletasks()
    return answer  
class My_StringDialog(tk.simpledialog._QueryString):
    def body(self, master):# initialvalue May Be List, String Or None
        self.attributes("-toolwindow", True)# Remove Min/Max Buttons
        self.bind('<KP_Enter>', self.ok)
        self.bind('<Return>', self.ok)
        pt=tk.Label(master, text=self.prompt, justify="left", font=media_font)
        pad=int((pt.winfo_reqwidth()/2)/2)
        pt.grid(row=2, padx=(5,5),pady=(5,5), sticky= 'we')
        if self.initialvalue is not None:
            wid=len(self.initialvalue)+4
            if type(self.initialvalue)==list:# List
                for item in self.initialvalue:
                    w=len(item)
                    if w>wid:wid=w
                self.entry=ttk.Combobox(master, name="entry", state = "readonly",justify="center",width=wid,font=media_font)
                self.entry['values']=self.initialvalue
                self.entry.current(0)
            else:# String
                self.entry=tk.Entry(master, name="entry", justify='center', bg="#d6ffff",width=wid)
                self.entry.insert(0, self.initialvalue)
                self.entry.select_range(0, 'end')
        else:# None
            self.entry=tk.Entry(master, name="entry", justify='center', bg="#d6ffff", font=media_font)
            self.entry.insert(0, "")
            self.entry.select_range(0, 'end')
        self.entry.grid(row=3, padx=(pad,pad), sticky='we')
        self.entry.bind('<Map>', self.on_map)
        app.root.update_idletasks()
        return self.entry
    def on_map(self, event):
        self.entry.focus_force()    
def set_theme(self,theme):
    if theme==Theme.get():return
    if theme=="blue":    
        PNG_1.set("2000x100_blue.png")
        PNG_2.set("500x100_blue.png")
        B_Color.set("#333333")
        T_Color.set("#094551")
        F_Color.set("#ffffff")#White
    elif theme=="gold":    
        PNG_1.set("2000x100_gold.png")
        PNG_2.set("500x100_gold.png")
        B_Color.set("#001829")
        T_Color.set("#846b1c")
        F_Color.set("#ffffff")#White
    elif theme=="black":    
        PNG_1.set("2000x100_black.png")
        PNG_2.set("500x100_black.png")
        B_Color.set("#000000")
        T_Color.set("#5c5c5c")
        F_Color.set("#ffffff")#White
    elif theme=="silver":    
        PNG_1.set("2000x100_silver.png")
        PNG_2.set("500x100_silver.png")
        B_Color.set("#333333")
        T_Color.set("#808080")
        F_Color.set("#000000")#black
    Theme.set(theme)
    with open("Setup.json", 'r') as file:
        data = json.load(file)
    data["4"]=Theme.get()
    with open("Setup.json", 'w') as file:
        json.dump(data, file, indent=4)
    FFMPEG_Player.restart_program(self,True)
def set_screen_position():
    title="<Set Screen Position For Media Window>"
    msg1='Select A Screen Position For Video Playback.\n'
    msg2='The Default Position Is ' + Screen_Position.get()+'.'
    msg=msg1+msg2
    positions=["Top Center","Top Left","Top Right","Center Left","Center","Center Right","Bottom Left","Bottom Center","Bottom Right"]
    pos=my_askstring(title,msg,positions)
    if pos!=None:
        Screen_Position.set(pos)
        with open("Setup.json", 'r') as file:
            data = json.load(file)
        data["1"]=Screen_Position.get()
        with open("Setup.json", 'w') as file:
            json.dump(data, file, indent=4)
def about():
    msg1='Creator: Ross Waters'
    msg2='\nEmail: RossWatersjr@gmail.com'
    msg3=f'\nRevision: {version}'
    msg4='\nCreated For Windows 11'
    msg=msg1+msg2+msg3+msg4
    messagebox.showinfo('My Media Player', msg)
def get_greeting(status):
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
def bind_keyboard():
    keys=['<KeyRelease-p>','<KeyRelease-P>','<KeyRelease-m>','<KeyRelease-M>','<KeyRelease-Right>','<KeyRelease-Left>',
            '<KeyRelease-Up>','<KeyRelease-Down>','<KeyRelease-f>','<KeyRelease-F>','<KeyRelease-q>','<KeyRelease-Q>',
            '<KeyRelease-XF86AudioPlay>','<KeyRelease-XF86AudioPause>','<KeyRelease-e>','<KeyRelease-E>','<KeyRelease-r>',
            '<KeyRelease-R>','<XF86AudioMute>','<KeyRelease-XF86AudioPrev>','<KeyRelease-XF86AudioNext>','<KeyRelease-Escape>',
            '<KeyRelease-XF86AudioRaiseVolume>','<KeyRelease-XF86AudioLowerVolume>']
    for k in range(len(keys)): 
        try:
            root.bind(keys[k], mm_player.bound_keys)
        except Exception:
            continue
def calculate_font_sizes():
    base_font_sizes = [8, 12, 14]
    new_font_sizes=[]
    scale = root.winfo_fpixels('1i') / 72  # Ratio of pixels to points
    root.tk.call('tk', 'scaling', scale)
    for s in range(len(base_font_sizes)):
        scaled_font_size = int(base_font_sizes[s] * scale)
        new_font_sizes.append(scaled_font_size)
    return new_font_sizes
def install_upgrade_appinstaller():
    try:    
        required_version = (1, 28, 190)
        command = ["winget", "upgrade", "Microsoft.AppInstaller"]
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        command = ["winget", "--version"]
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        version_str = proc.stdout.splitlines()[0].replace("v","")
        version_list_str = version_str.split('.')
        version_list_int = map(int, version_list_str)
        version_tuple = tuple(version_list_int)
        if version_tuple >= required_version:
            return True
        else:# If Powershell Upgrade Fails, Try Manual Upgrade
            title="< Upgrade Microsoft AppInstaller >"
            msg1="WinGet Needs To Be Upgraded To >= 1.28.190.\n"
            msg2=f"Current Version Now Is {version_str}.\n"
            msg3=f"When The Following Webpage Appears,\n"
            msg4="Open The Download Link And Install The\n"
            msg5="Latest Version Of Microsoft AppInstaller.\n"
            msg6="After Microsoft AppInstaller Is Upgraded,\n"
            msg7="This Program Will Restart."
            msg=msg1+msg2+msg3+msg4+msg5+msg6+msg7
            messagebox.showinfo(title,msg)
            webbrowser.open("https://aka.ms/getwinget")
            os.execl(sys.executable, os.path.abspath("solar_system_3D_en.exe"), *sys.argv) 
    except Exception as e:# Try Manual Installation
        root.withdraw()
        root.wm_attributes("-topmost", 1)
        webbrowser.open("https://github.com/microsoft/winget-cli/releases") 
        title="< Upgrading Microsoft AppInstaller Failed! >"
        msg1="WinGet Needs To Be Upgraded To >= 1.28.190.\n"
        msg2=f"Before Proceeding. Get The Latest Version Here.\n"
        msg3="Go To Bottom Of Page And Under Assets, Download And Install\n"
        msg4="Microsoft.DesktopAppinstaller_8wekyb3d8bbwe.msix.\n"
        msg5="After The Installation Has Completed, Select OK To Restart Program."
        msg=msg1+msg2+msg3+msg4+msg5
        messagebox.showerror(title, msg, parent=root)
        root.deiconify()
        os.remove("Setup.json")
        os.execl(sys.executable, os.path.abspath("solar_system_3D_en.exe"), *sys.argv) 
def install_soundvolumeview_with_winget():
    try:#Installs SoundVolumeView using the winget package manager.
        command = ["winget", "install", "--id", "NirSoft.SoundVolumeView"]
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        command = ["winget", "list", "--id", "NirSoft.SoundVolumeView", "--details"]
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        version_info = proc.stdout.splitlines()[4]# Version
        pgm_path = ""
        #Example: Installed Location: C:\Users\MiEsp\AppData\Local\Microsoft\WinGet\Packages\NirSoft.SoundVolumeView_Microsoft.Winget.Source_8wekyb3d8bbwe
        for s in range(len(proc.stdout.splitlines())):
            if "Installed Location:" in proc.stdout.splitlines()[s]:
                pgm_path = proc.stdout.splitlines()[s].replace("Installed Location: ","")
                break
        if pgm_path == "":raise Exception("No SoundVolumeView Installed Location Found!") 
        soundvolumeview_path.set(os.path.join(pgm_path,"SoundVolumeView.exe"))
    except Exception as e:
        title="< SoundVolumeView Installation Failed! >"
        msg1=f"Open Powershell Or A Terminal Window An Enter\n"
        msg2="winget install --id NirSoft.SoundVolumeView\n"
        msg3="Then Press Enter!\n"
        msg4=f"Error: '{e}'"
        msg=msg1+msg2+msg3+msg4
        messagebox.showerror(title,msg)
        os.remove("Setup.json")
        os._exit(0)
def install_ffmpeg_with_winget():
    try:#Installs FFmpeg using the winget package manager.
        command = ["winget", "install", "--id", "Gyan.FFmpeg"]
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        command = ["FFmpeg", "-version"]
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        version_info = (proc.stdout.splitlines()[0]).replace(" version ","-").replace("-www.gyan.dev Copyright (c) 2000-2025 the FFmpeg developers","")
        command = ["winget", "list", "--id", "Gyan.FFmpeg", "--details"]
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        pgm_path = ""
        #Example: Installed Location: "C:/Users/MiEsp/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.0.1-full_build/bin/ffmpeg.exe"
        for s in range(len(proc.stdout.splitlines())):
            if "Installed Location:" in proc.stdout.splitlines()[s]:
                pgm_path = (proc.stdout.splitlines()[s]).replace("Installed Location: ","")
                #break
        if pgm_path == "":raise Exception("No FFmpeg Installed Location Found!") 
        ffmpeg_path.set(os.path.join(pgm_path,f"{version_info}/bin/ffmpeg.exe"))
        ffplay_path.set(os.path.join(pgm_path,f"{version_info}/bin/ffplay.exe"))
        ffprobe_path.set(os.path.join(pgm_path,f"{version_info}/bin/ffprobe.exe"))
    except Exception as e:
        title="< FFmpeg Installation Failed! >"
        msg1=f"Open Powershell Or A Terminal Window An Enter\n"
        msg2="winget install --id Gyan.FFmpeg\n"
        msg3="Then Press Enter!\n"
        msg4=f"Error: '{e}'"
        msg=msg1+msg2+msg3+msg4
        messagebox.showerror(title,msg)
        os.remove("Setup.json")
        os._exit(0)
if __name__ == '__main__':
    root=tk.Tk()
    sizes = calculate_font_sizes()# Get Font Sizes Depending On Monitor Resolution
    media_font=font.Font(family='Times New Romans', size=sizes[0], weight='normal', slant='italic')
    media_font2=font.Font(family='Times New Romans', size=sizes[1], weight='normal', slant='italic')
    emoji_font=font.Font(family='Noto Emoji', size=sizes[1], weight='normal', slant='roman')
    emoji_font2=font.Font(family='Noto Emoji', size=sizes[2], weight='normal', slant='roman')
    shared_download_files=os.path.join(os.path.expanduser("~"),"youtube_downloads.json")# Store Folder And Song Title Here For Sharing
    Start_Time=DoubleVar()
    Level=DoubleVar()# Volume Meter
    Screen_Height=IntVar()
    Screen_Position=StringVar()
    Slide_Show_Delay=StringVar()
    Theme=tk.StringVar()
    PNG_1=tk.StringVar()
    PNG_2=tk.StringVar()
    T_Color=tk.StringVar()
    B_Color=tk.StringVar()
    F_Color=tk.StringVar()
    Download_Folder=tk.StringVar()
    Download_Type=tk.StringVar()
    Use_Oauth=tk.BooleanVar()
    Use_Oauth.set(False)
    User_Name=tk.StringVar()
    User_Password=tk.StringVar()
    URL=tk.StringVar()
    Title=tk.StringVar()
    path_dict={}
    ffmpeg_path=tk.StringVar()
    ffprobe_path=tk.StringVar()
    ffplay_path=tk.StringVar()
    soundvolumeview_path=tk.StringVar()
    mm_player=FFMPEG_Player(root)
    with open('Setup.json', 'r') as file:
        data = json.load(file)
    if len(data)==0:# Install Dependencies On First Execution
        try:
            requests.get("https://www.google.com", timeout=5)
            root.withdraw()
            title = "< Installing Dependency Files >"
            msg1=f"Please Be Patient While This Process Completes!\n"
            msg2="This Process Only Occurs During Initial Execution.\n"
            msg3="This Program May Or May Not Restart On Completion!"
            msg=msg1+msg2+msg3
            messagebox.showinfo(title,msg)
            install_upgrade_appinstaller()
            install_ffmpeg_with_winget()
            install_soundvolumeview_with_winget()
            mm_player.set_defaults()
            mm_player.write_setup()
            mm_player.get_ffmpeg_versions()# Just To Initialize Executables On First Run
            root.deiconify()
        except Exception:
            title = "< No Internet Connection Detected! >"
            msg1=f"Check Internet Connection And Restart Program.\n"
            msg2="Exiting Program!"
            msg=msg1+msg2
            messagebox.showerror(title,msg)
            os._exit(0)
    mm_player.init_audio()
    mm_player.set_defaults()
    app=AsyncTkApp(root)
    mm_player.load_library(mm_player.active_database,None,False)
    app._run_main()
