# this code takes inspiration (and code lines too) from
# https://learn.adafruit.com/diy-wifi-raspberry-pi-touch-cam/overview

import RPi.GPIO as GPIO
import picamera
import yuv2rgb
import fnmatch
import pygame
import atexit
import time
import sys
import os
import io


# Button is a simple tappable screen region.  Each has:
#  - bounding rect ((X,Y,W,H) in pixels)
#  - optional background color and/or Icon (or None), always centered
#  - optional foreground Icon, always centered
#  - optional single callback function
#  - optional single value passed to callback
# Occasionally Buttons are used as a convenience for positioning Icons
# but the taps are ignored.  Stacking order is important; when Buttons
# overlap, lowest/first Button in list takes precedence when processing
# input, and highest/last Button is drawn atop prior Button(s).  This is
# used, for example, to center an Icon by creating a passive Button the
# width of the full screen, but with other buttons left or right that
# may take input precedence (e.g. the Effect labels & buttons).
# After Icons are loaded at runtime, a pass is made through the global
# buttons[] list to assign the Icon objects (from names) to each Button.

class Button:

	def __init__(self, rect, **kwargs):
	  self.rect     = rect # Bounds
	  self.color    = None # Background fill color, if any
	  self.iconBg   = None # Background Icon (atop color fill)
	  self.iconFg   = None # Foreground Icon (atop background)
	  self.bg       = None # Background Icon name
	  self.fg       = None # Foreground Icon name
	  self.callback = None # Callback function
	  self.value    = None # Value passed to callback
	  for key, value in kwargs.iteritems():
	    if   key == 'color': self.color    = value
	    elif key == 'bg'   : self.bg       = value
	    elif key == 'fg'   : self.fg       = value
	    elif key == 'cb'   : self.callback = value
	    elif key == 'value': self.value    = value          

	def selected(self, pos):
	  x1 = self.rect[0]
	  y1 = self.rect[1]
	  x2 = x1 + self.rect[2] - 1
	  y2 = y1 + self.rect[3] - 1
	  if ((pos[0] >= x1) and (pos[0] <= x2) and
	      (pos[1] >= y1) and (pos[1] <= y2)):
	    if self.callback:
	      if self.value is None: self.callback()
	      else:                  self.callback(self.value)
	    return True
	  return False

	def draw(self, screen):
	  if self.color:
	    screen.fill(self.color, self.rect)
	  if self.iconBg:
	    screen.blit(self.iconBg.bitmap,
	      (self.rect[0]+(self.rect[2]-self.iconBg.bitmap.get_width())/2,
	       self.rect[1]+(self.rect[3]-self.iconBg.bitmap.get_height())/2))
	  if self.iconFg:
	    screen.blit(self.iconFg.bitmap,
	      (self.rect[0]+(self.rect[2]-self.iconFg.bitmap.get_width())/2,
	       self.rect[1]+(self.rect[3]-self.iconFg.bitmap.get_height())/2))

	def setBg(self, name):
	  if name is None:
	    self.iconBg = None
	  else:
	    for i in icons:
	      if name == i.name:
	        self.iconBg = i
	        break


def takePicture(channel):
	print "take!"
	if (channel!=18):
		return
	time.sleep(1)
	if not GPIO.input(channel):
		return
	print "continue..."
	return
	dir="/home/pi/Photos"
	max=0
	for file in os.listdir(dir):
		if fnmatch.fnmatch(file, 'rorscham_[0-9][0-9][0-9][0-9].png'):
			i = int(file[-8:-4])
			if(i > max): max = i
	max=max+1
	filename = "/home/pi/Photos" + '/rorscham_' + '%04d' % max + '.png'
	print filename
	camera.resolution=(1280,720)
	camera.capture(filename, use_video_port=False, format='png',thumbnail=None)
	camera.resolution=(320, 240)
#	time.sleep(3)
#  sys.exit()

buttons=  [Button((  0,  0,320,240), bd='gear'           , cb=takePicture, value = 0)]

sizeData = [ # Camera parameters for different size settings
 # Full res      Viewfinder  Crop window
 [(2592, 1944), (320, 240), (0.0   , 0.0   , 1.0   , 1.0   )], # Large
 [(1920, 1080), (320, 180), (0.1296, 0.2222, 0.7408, 0.5556)], # Med
 [(1440, 1080), (320, 240), (0.2222, 0.2222, 0.5556, 0.5556)]] # Small
sizeMode        =  0      # Image size; default = Large
screenMode      =  3      # Current screen mode; default = viewfinder

os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV'      , '/dev/fb1')
os.putenv('SDL_MOUSEDRV'   , 'TSLIB')
os.putenv('SDL_MOUSEDEV'   , '/dev/input/touchscreen')

# Get user & group IDs for file & folder creation
# (Want these to be 'pi' or other user, not root)
s = os.getenv("SUDO_UID")
uid = int(s) if s else os.getuid()
s = os.getenv("SUDO_GID")
gid = int(s) if s else os.getgid()

# Buffers for viewfinder data
rgb = bytearray(320 * 240 * 3)
yuv = bytearray(320 * 240 * 3 / 2)

# Init pygame and screen
pygame.init()
pygame.mouse.set_visible(False)
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)

camera            = picamera.PiCamera()
atexit.register(camera.close)
camera.resolution=(320, 240)
camera.crop       = (0.0, 0.0, 1.0, 1.0)

##GPIO.setmode(GPIO.BCM)

key1=18
key2=23
key3=24

GPIO.setup(key1, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.add_event_detect(key1, GPIO.RISING, callback=takePicture, bouncetime=300)

while(True):

  # Process touchscreen input
  while True:
    for event in pygame.event.get():
      if(event.type is pygame.MOUSEBUTTONDOWN):
        pos = pygame.mouse.get_pos()
        for b in buttons:
          if b.selected(pos): break
    # If in viewfinder or settings modes, stop processing touchscreen
    # and refresh the display to show the live preview.  In other modes
    # (image playback, etc.), stop and refresh the screen only when
    # screenMode changes.
    if screenMode >= 3 or screenMode != screenModePrior: break

  # Refresh display
  if screenMode >= 3: # Viewfinder or settings modes
    stream = io.BytesIO() # Capture into in-memory stream
    camera.capture(stream, use_video_port=True, format='raw')
    stream.seek(0)
    stream.readinto(yuv)  # stream -> YUV buffer
    stream.close()
    yuv2rgb.convert(yuv, rgb, sizeData[sizeMode][1][0],
      sizeData[sizeMode][1][1])
    img = pygame.image.frombuffer(rgb[0:
      (sizeData[sizeMode][1][0] * sizeData[sizeMode][1][1] * 3)],
      sizeData[sizeMode][1], 'RGB')
  elif screenMode < 2: # Playback mode or delete confirmation
    img = scaled       # Show last-loaded image
  else:                # 'No Photos' mode
    img = None         # You get nothing, good day sir

  if img is None or img.get_height() < 240: # Letterbox, clear background
    screen.fill(0)
  if img:
    half=pygame.Surface((img.get_width()/2,img.get_height()))    
    half.blit(img,(0,0))

# here goes the correction
#    arr = pygame.surfarray.pixels3d(half)
#    arr[:,:,0] *= 0.5
#    del arr
# first half
    screen.blit(half, (0, 0))
# second half (mirrored)
    half=pygame.transform.flip(half,True,False)
    screen.blit(half,((img.get_width() ) / 2, 0))
  # Overlay buttons on display and update
    for i,b in enumerate(buttons):
      b.draw(screen)
  pygame.display.update()

  screenModePrior = screenMode
