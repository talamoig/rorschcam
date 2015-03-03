# this code takes inspiration (and code lines too) from
# https://learn.adafruit.com/diy-wifi-raspberry-pi-touch-cam/overview

import RPi.GPIO as GPIO
import picamera
import yuv2rgb
import fnmatch
import pygame
import atexit
import Image
import time
import sys
import os
import io

wanatake=False
def wanaTake(channel):
	global wanatake
	print "channel %s"%channel
	if (channel!=18):
		return
	time.sleep(1)
	if not GPIO.input(channel):
		return
	wanatake=True

def takePicture():
	dir="/home/pi/Photos"
	max=0
	for file in os.listdir(dir):
		if fnmatch.fnmatch(file, 'rorschcam_[0-9][0-9][0-9][0-9].png'):
			i = int(file[-8:-4])
			if(i > max): max = i
	max=max+1
	basename = "/home/pi/Photos" + '/rorschcam_' + '%04d' % max
	filename = basename + '-raw.png'
	print filename
	camera.resolution=(1280,720)
	camera.capture(filename, use_video_port=False, format='png',thumbnail=None)
	camera.resolution=(320, 240)
	img = Image.open(filename).convert('LA')
	print 'loading...',
	pix=img.load()
	print 'done'
	k=0
	for i in range(img.size[0]/2,img.size[0]):
		if k==0:
			print '.',
		for j in range(img.size[1]):
			pix[i,j]=pix[img.size[0]-i,j]
		k=(k+1)%1000
	img.save(basename+'.png')
	time.sleep(1)
	print "!"


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

GPIO.add_event_detect(key1, GPIO.RISING, callback=wanaTake, bouncetime=300)

while(True):
  if wanatake:
      takePicture()
      wanatake=False

  stream = io.BytesIO() # Capture into in-memory stream
  camera.capture(stream, use_video_port=True, format='raw')
  stream.seek(0)
  stream.readinto(yuv)  # stream -> YUV buffer
  stream.close()
  yuv2rgb.convert(yuv, rgb, 320, 240)
  img = pygame.image.frombuffer(rgb[0:320*240*3], (320,240), 'RGB')

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
  pygame.display.update()


