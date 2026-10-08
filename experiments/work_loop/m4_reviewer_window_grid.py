"""Arrange visible reviewer PowerShell windows in a compact non-overlapping grid.

Only moves windows whose title includes the ORION reviewer marker.
Does not start, stop, or change ownership of any process.
"""
from __future__ import annotations
import ctypes
import time
from ctypes import wintypes

user32=ctypes.WinDLL("user32",use_last_error=True)
EnumWindows=user32.EnumWindows
EnumWindows.argtypes=[ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM),wintypes.LPARAM]
GetWindowTextLengthW=user32.GetWindowTextLengthW
GetWindowTextW=user32.GetWindowTextW
IsWindowVisible=user32.IsWindowVisible
SetWindowPos=user32.SetWindowPos
GetSystemMetrics=user32.GetSystemMetrics
SWP_NOZORDER=0x0004
SWP_NOACTIVATE=0x0010

def layout():
    found=[]
    @ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    def visit(hwnd,param):
        if not IsWindowVisible(hwnd):return True
        size=GetWindowTextLengthW(hwnd)
        if not size:return True
        buf=ctypes.create_unicode_buffer(size+1)
        GetWindowTextW(hwnd,buf,size+1)
        title=buf.value
        if "reviewer" in title.lower() and ("orion" in title.lower() or "cloud" in title.lower()):
            found.append((title,hwnd))
        return True
    EnumWindows(visit,0)
    found.sort(key=lambda item:item[0].lower())
    width=GetSystemMetrics(0);height=GetSystemMetrics(1)
    columns=3
    w=min(640,max(400,(width-60)//columns))
    h=min(430,max(270,(height-90)//2))
    for i,(_,hwnd) in enumerate(found[:6]):
        x=12+(i%columns)*(w+8)
        y=12+(i//columns)*(h+8)
        SetWindowPos(hwnd,0,x,y,w,h,SWP_NOZORDER|SWP_NOACTIVATE)
    print("M4_WINDOWS> ARRANGED",min(len(found),6),"VISIBLE_REVIEWER_WINDOWS","GRID",columns,"x",2,flush=True)
    return len(found)

if __name__=="__main__":
    for _ in range(12):
        if layout()>=5:break
        time.sleep(.75)
