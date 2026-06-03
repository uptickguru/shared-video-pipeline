import time
import os
import winsound
import subprocess

def send_windows_notification(title, message):
    try:
        ps_script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$textNodes = $template.GetElementsByTagName("text")
$textNodes[0].AppendChild($template.CreateTextNode("{title}")) | Out-Null
$textNodes[1].AppendChild($template.CreateTextNode("{message}")) | Out-Null
$toast = [Windows.UI.Notifications.ToastNotification]::new($template)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Video Pipeline").Show($toast)
        '''
        subprocess.run(["powershell", "-Command", ps_script], creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        pass

def follow(thefile):
    # Go to the end of the file
    thefile.seek(0, 2)
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.5)
            continue
        yield line

if __name__ == '__main__':
    log_file = "batch_render.log"
    print(f"Monitoring {log_file} for completions...")
    
    # Wait for file to exist
    while not os.path.exists(log_file):
        time.sleep(1)
        
    with open(log_file, "r") as logfile:
        loglines = follow(logfile)
        for line in loglines:
            if "Job completed:" in line:
                scene_name = line.split("Job completed:")[-1].strip()
                print(f"PING: {scene_name} finished!")
                
                # Play a success chime on the computer speakers!
                winsound.Beep(1000, 200)
                winsound.Beep(1500, 200)
                winsound.Beep(2000, 400)
                
                # Send a native Windows 10/11 popup notification
                send_windows_notification("Scene Rendered!", f"Successfully downloaded: {scene_name}")
