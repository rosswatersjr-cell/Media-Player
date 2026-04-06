# Media-Player For Windows 11
Created Using Python 3.14.3. 
Media Player Program For Playing Audio, Video And Image Files For Windows 11.
There Are 2 Versions Of The Script (English"en" And Spanish "sp").
Make Sure To Select The Correct Text Files For Your Chosen Script.
This Program Uses Gyan FFmpeg For All Video And Audio Files And opencv-python For Image Files.
This Program Also Uses NirSoft SoundVolumeView For Audio Output Device Selection.
Both Of These Dependencies Are Automatically Installed During The Initial Execution.
The Script Also Has A YouTube Downloader Built In. View The youtube_downloader_readme For Details. 
All Libraries In The Media Library Menu Have Their Own Associated Folder In The User Account.
It Is Not Necessary To Use These Folder But Is A Good Way To Keep Things Seperated.
Also Existing Is A Keyboard Interface. View The Bound Keys.txt File For Details.
This Script Requires Microsoft.AppInstaller >= 1.28.190.0,  Gyan.FFmpeg >= 8.0.1,
And NirSoft.SoundVolumeView >= 2.50 Which Is Automatically Installed. Once Your Script Or
Executable Is Setup And Running Ok, If Any Of These 3 Programs Are Updated To A Later Version,
Delete The Config.json File Associated With The Script So The New Paths Can Be Recorded In A 
New Config.json File.

# Notes Before Running Script:
Make Sure You Have An Internet Connection Before Running The Script The First Time. This Is To  
Install And Update Necessary Files. After This, No Internet Is Required Except When Using The  
Built-In YouTube Downloader. If You Have Python Installed, Go To Your Python Path Scripts   
Folder And Delete ffmpeg.exe, ffplay.exe And ffprobe.exe If They Exist. These Files Are Of    
An Older Version And Interfere With The New Version Installed By WinGet. Your Python Path   
Should Look Like "C:\Users\UserName\AppData\Local\Programs\Python\Python314\Scripts".
