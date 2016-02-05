#!/usr/bin/env python

'''
OrtoTex4XPL - Orto textures for X-Plane script

Author: Jan Bariencik (lktb@bari2.eu)
Version: 20160203

THIS SCRIPT IS FOR STUDYING PURPOSE ONLY!!! USE AT YOUR OWN RISK!! 

Data are downloaded from Google Maps or Mapy.cz web service.
Plase, check Map source license conditions before use.


License:

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

# TODO: use request with keep-alive for whole square instead of single conn urllib2
#       http://docs.python-requests.org/en/latest/
#       http://stackoverflow.com/questions/13030095/how-to-save-requests-python-cookies-to-a-file        

import argparse
import os
import platform
import sys
import urllib2
import cookielib
import re
from PIL import Image
import cv2
import thread
import time

# https://raw.githubusercontent.com/hrldcpr/mercator.py/master/mercator.py
import mercator

# -------- Variables ----------------

# path to dsftool binary
DSFBIN="./DSFTool"
DDSBIN="./DDSTool"

# base output directory
OUTPUT="/tmp/orto4xpl/"

if platform.system() == "Windows": 
	DSFBIN="DSFTool.exe"
	DSFBIN="DDSTool.exe"	
	OUTPUT="C:/orto4xpl"

# output sub directories
TEX="texture"
POL="pol"
DSF="Earth nav data"
TMP="tmp"

# -------- Classes ----------------

class MapSource:

	def init_hook(self,data):
		pass
	
	def init_down(self):

		cj = cookielib.LWPCookieJar()
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
  
		req = urllib2.Request(self.url_init)
		req.add_header('accept-language', 'cs-CZ,cs;q=0.8')
		req.add_header('user-agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36')

		try:
			f = opener.open(req)
			self.init_hook(f.read())
			f.close()
		except urllib2.URLError, err:
			print "init_down error:", err.reason, sys.exc_info()[0]
			sys.exit(1)

		cj.save("{0}/test.cook".format(OUTTMP))	


	def down_tile(self,zl,x,y,out):

		cj = cookielib.LWPCookieJar()
		cj.load("{0}/test.cook".format(OUTTMP))
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

		req = urllib2.Request(self.url_req.format(zl,x,y,self.c1))
		req.add_header('accept', 'image/webp,*/*;q=0.8')
		req.add_header('accept-encoding', 'gzip,deflate,sdch')
		req.add_header('accept-language', 'cs-CZ,cs;q=0.8')
		req.add_header('user-agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36')
		req.add_header('referer', self.referer)

		try:
			f = opener.open(req)

			webfile = open(out, 'wb')
			webfile.write(f.read())
			webfile.close()

			#cj.save("{0}/test.cook") # it is saved automatically!!
			f.close()

		except urllib2.URLError, err:
			print "down_tile error:", err.reason, sys.exc_info()[0]
			return False
		except SocketError, err:
			print "down_tile error:", err.reason, sys.exc_info()[0]
			return False
		except:
			print "down_tile error: unknown", sys.exc_info()[0]
			return False
		
		return True
		

class GMaps(MapSource):

	def __init__(self):
		self.url_init='http://maps.google.com/maps?&output=classic'
		self.url_req='https://khms0.google.com/kh/v={3}&src=app&x={1}&y={2}&z={0}&s=Gali'
		self.referer='https://maps.google.com'
		self.c1=''

	# assign version to custom1 url req attr
	def init_hook(self,data):
		m = re.search("/kh/v=([0-9]+)",data)
		if m:
			self.c1=m.group(1)
		else:
			self.c1=145

class MapyCZ(MapSource):

	def __init__(self):
		self.url_init='http://mapy.cz'
		self.url_req='http://m2.mapserver.mapy.cz/ophoto-m/{0}-{1}-{2}'
		self.referer='http://mapy.cz/letecka?x=16.6708841&y=49.1532619&z=18'
		self.c1=''
  
# -------- Functions ----------------

def fixY(zl,y):

 	# filename correction for g2xpl format

	if zl == 17:
		y=131064-y

	if zl == 16:
		y=65528-y  # round(131064/2/8) *8
		
	return y

def down_square(zl,x,y,ms,cnt=8):
	print "Downloading square ({0},{1}) {2}x{2} images".format(x,y,cnt)
	
	skip=0
	for yi in range(y,y+cnt):
		for xi in range(x,x+cnt):
			if not os.path.isfile(FILEIMGTMP.format(zl,x,y,xi,yi)):
				max_try = 3
				done = False
				while (done == False):
					done = ms.down_tile(zl,xi,yi, FILEIMGTMP.format(zl,x,y,xi,yi))
					if not done:
						print "Waiting 3s for re-download"
						time.sleep(3)
						max_try -= 1
						if max_try == 0: done = True
			else:
				skip+=1
	
	if skip:
		print "- skipped",skip,"of",cnt*cnt,"(already downloaded)"


def merge_square(zl,x,y,cnt=8):
	print "Merging square ({0},{1}) {2}x{2} images".format(x,y,cnt)

	final = Image.new('RGB', (256*cnt,256*cnt))
	for yi in range(y,y+cnt):
		for xi in range(x,x+cnt):
			if os.path.isfile(FILEIMGTMP.format(zl,x,y,xi,yi)):
				one = Image.open(FILEIMGTMP.format(zl,x,y,xi,yi))
				final.paste(one, ((xi-x)*256,(yi-y)*256))
				
				if not args.keep_downloaded:
					os.remove(FILEIMGTMP.format(zl,x,y,xi,yi))
					
			else:
				print "Img",FILEIMGTMP.format(zl,x,y,xi,yi),"not found!!!"

	# change size
	if cnt>8:
		final.thumbnail((2048,2048), Image.ANTIALIAS)

	final.save(FILEIMG.format(zl,x,fixY(zl,y)))

def remove_logo(orig, child):
	print "Removing logo in square"
	
	im_o = cv2.imread(orig)
	im_c = cv2.imread(child)
	#cv2.imwrite(orig+'6.png',(im_o*0.5)+(im_c*0.5))    # 50% transparency
	#cv2.imwrite(orig+'7.png',(im_o*0.35)+(im_c*0.65))  # 65% transparency
	#cv2.imwrite(orig+'8.png',cv2.min(im_o,im_c))       # darken only?? http://gimp-savvy.com/BOOK/index.html?node55.html
	cv2.imwrite(orig,cv2.min(im_o,im_c))
	os.remove(child)

def create_pol(zl,x,y):

	print "Creating square ({0},{1}) polygon".format(x,y)

	pol = open(FILEPOL.format(zl,x,y), 'w')
	pol.write("A\n")
	pol.write("850\n")
	pol.write("DRAPED_POLYGON\n\n")
	pol.write("TEXTURE_NOWRAP ../"+TEX+"/"+FILEBASE.format(zl,x,y)+".png\n")
	pol.write("LAYER_GROUP airports -1\n")
	pol.write("SCALE 25 25\n")
	pol.close()
	
	dsfin = open(OUTTMP+"/dsf.in.txt", 'a')
	dsfin.write(POL+"/"+FILEBASE.format(zl,x,y)+".pol, ")
		
	leftUpLat, leftUpLng = mercator.get_tile_lat_lng(zl,x,y)
	rightDownLat, rightDownLng = mercator.get_tile_lat_lng(zl,x+8,y+8)
	
	dsfin.write("{0:.8f}, {1:.8f}, {2:.8f}, {3:.8f}, \n".format(leftUpLat,rightDownLat,leftUpLng,rightDownLng))
	dsfin.close()

def convert_to_dds(tile_fname,dds_fname):

	print "Converting img to DDS"

	if not os.path.isfile(DDSBIN):
		print "- cannot find DDSTool binary (" + DDSBIN + ")"
		return None

	cmd="\"" + DDSBIN + "\" --png2dxt1 arg1 arg2 \"" + tile_fname + "\" \"" + dds_fname + "\""
	print "- command:", cmd
	newRef=os.fork()
	if newRef==0:
		os.system(cmd)
		os.remove(tile_fname)
		sys.exit(0)
	#print "-----------------------------------------------"
	print "- forking... child pid is", newRef
	return newRef
	
def prepare_dsf():
	print "Creating DSF"

	if not os.path.isfile(OUTTMP+"/dsf.in.txt"):
		if os.path.isfile(OUTTMP+"/dsf.txt"):
			print "- skipped dsf file (already created)"
		else:
			print "- dsf.in file is missing"
		sys.exit(0)

	dsf = open(OUTTMP+"/dsf.txt",'w')
	dsfin = open(OUTTMP+"/dsf.in.txt", 'r')

	lines = dsfin.readlines()
	words = lines[0].split(', ')
	lat = int(words[1].split('.')[0])
	lng = int(words[3].split('.')[0])
	
	dsf.write("PROPERTY sim/planet earth\n")
	dsf.write("PROPERTY sim/overlay 1\n")
	dsf.write("PROPERTY sim/require_object 1/0\n")
	dsf.write("PROPERTY sim/require_facade 1/0\n")
	dsf.write("PROPERTY sim/creation_agent main.py\n")
	dsf.write("PROPERTY sim/west {0:.0f}".format(lng)+"\n")
	dsf.write("PROPERTY sim/east {0}".format(lng+1)+"\n")
	dsf.write("PROPERTY sim/north {0}".format(lat+1)+"\n")
	dsf.write("PROPERTY sim/south {0}".format(lat)+"\n\n\n")

	for line in lines:
		words = line.split(', ')
		dsf.write("POLYGON_DEF "+words[0]+"\n")

	i=0		
	dsf.write('\n')
	for line in lines:
		words = line.split(', ')
		
		dsf.write("BEGIN_POLYGON {0} 65535 4\n".format(i))
		dsf.write("BEGIN_WINDING\n")
		dsf.write("POLYGON_POINT {0}	{1}	0.00000000	0.00000000\n".format(words[3],words[2]))
		dsf.write("POLYGON_POINT {0}	{1}	1.00000000	0.00000000\n".format(words[4],words[2]))
		dsf.write("POLYGON_POINT {0}	{1}	1.00000000	1.00000000\n".format(words[4],words[1]))
		dsf.write("POLYGON_POINT {0}	{1}	0.00000000	1.00000000\n".format(words[3],words[1]))
		dsf.write("END_WINDING\n")
		dsf.write("END_POLYGON\n\n")
		i+=1

	dsfin.close()
	dsf.close()
   
	os.remove(OUTTMP+"/dsf.in.txt")
	
	cmd="\""+DSFBIN+"\" --text2dsf \""+OUTTMP+"/dsf.txt\" \""+OUTDSF+"/+"+str(lat)+"+"+str(lng)+".dsf\""
	print "Command:", cmd
	os.system(cmd)
	print "-----------------------------------------------"

# -------- Main ----------------

parser = argparse.ArgumentParser()
parser.add_argument('--zl', metavar='<level>', type=int, default=18, help='required map zoom level (10-24) -- default: 18')
parser.add_argument('--src', choices=['gmaps', 'mapy'], default='gmaps', help='map source (mapy.cz, google maps) -- default: gmaps')
parser.add_argument('--base', metavar='<path>', default=OUTPUT, help='output directory base -- default: /tmp/orto4xpl')
#parser.add_argument('--coord1', nargs=2, type=float, metavar=('lat','lng'), default=[49.15296966,16.66625977], help='GPS lattitude and longtitude -- default: 49.15296966,16.66625977')
parser.add_argument('lat', type=float, help='GPS lattitude --- for ex. 49.15296966')
parser.add_argument('lng', type=float, help='GPS longtitude -- for ex. 16.66625977')
parser.add_argument('--coord2', nargs=2, type=float, metavar=('lat','lng'), help='Second GPS coordinates (lower right corner)')
parser.add_argument('--remove-logo', action='store_true', help='try to remove logo merging with higher zoom level')
parser.add_argument('--keep-downloaded', action='store_true', help='do not delete temporary img files after processing')
parser.add_argument('--dds-textures', action='store_true', help='convert textures to dds (instead of png) -- default: png')
args = parser.parse_args()

Zl=args.zl
Lat1=args.lat
Lng1=args.lng

if args.coord2 is not None:
	Lat2=args.coord2[0]
	Lng2=args.coord2[1]
else:
	Lat2=Lat1
	Lng2=Lng1

print "--- Input:"
print "Zl="+str(Zl)
print "Lat1="+str(Lat1)
print "Lng1="+str(Lng1)
print "Lat2="+str(Lat2)
print "Lng2="+str(Lng2)
	
if Lat2>Lat1 or Lng2<Lng1:
	print "Info: Right corrner must be lower or equal to left"
	parser.help();
	sys.exit(0)

if args.src == "gmaps":
	ms = GMaps()
else:
	ms = MapyCZ()

OUTPUT=args.base+'/'

# output dirs
OUTPOL=OUTPUT+POL
OUTTEX=OUTPUT+TEX
OUTTMP=OUTPUT+TMP
OUTDSF=OUTPUT+DSF

# output filenames
FILEBASE="g2xpl_8_{0}_{1}_{2}"
FILEIMGTMP=OUTTMP+"/"+FILEBASE+"-{3}-{4}.jpg"
FILEIMG=OUTTEX+"/"+FILEBASE+".png"
FILEPOL=OUTPOL+"/"+FILEBASE+".pol"

print "--- Mercators"
xy1=mercator.get_lat_lng_tile(Lat1,Lng1,Zl)
print 'x1=',xy1[0],'y1=',xy1[1]
xyr1=((int(xy1[0])/8)*8, (int(xy1[1])/8)*8)
print 'xr1=',xyr1[0],'yr1=',xyr1[1]

xy2=mercator.get_lat_lng_tile(Lat2,Lng2,Zl)
print 'x2=',xy2[0],'y2=',xy2[1]
xyr2=((int(xy2[0])/8)*8, (int(xy2[1])/8)*8)
print 'xr2=',xyr2[0],'yr2=',xyr2[1]

print "--- Min/Max Lat/Lng"
latlng1=mercator.get_tile_box(Zl,xyr1[0],xyr1[1])
latlng2=mercator.get_tile_box(Zl,xyr2[0],xyr2[1])
print latlng1
print latlng2

print "--- Processing"

if not os.path.isdir(OUTPUT):os.mkdir(OUTPUT)
if not os.path.isdir(OUTPOL):os.mkdir(OUTPOL)
if not os.path.isdir(OUTTEX):os.mkdir(OUTTEX)
if not os.path.isdir(OUTTMP):os.mkdir(OUTTMP)
if not os.path.isdir(OUTDSF):os.mkdir(OUTDSF)
	
ms.init_down()
dds_pid = None

for y in range(xyr1[1],xyr2[1]+8,8):
	for x in range(xyr1[0],xyr2[0]+8,8):

		tile_fname = FILEIMG.format(int(Zl),int(x),int(fixY(Zl,y)))
		dds_fname = os.path.splitext(tile_fname)[0] + ".dds"
		child_fname= FILEIMG.format(int(Zl+1),int(x*2),int(fixY(Zl+1,y*2)))

		if args.dds_textures and os.path.isfile(dds_fname):
			print "- skipped file", dds_fname, "(already exits)"
			continue

		# preparing child tile (zl+1) for removing logo
		if args.remove_logo:	

			if (not os.path.isfile(child_fname)) and (not os.path.isfile(tile_fname)):
				down_square(int(Zl+1),x*2,y*2,ms,16)
				merge_square(int(Zl+1),x*2,y*2,16)
			else:
				print "- skipped file", child_fname, "(already exits or merged)"

		# preparing tile
		if not os.path.isfile(tile_fname):
			down_square(int(Zl),x,y,ms)
			merge_square(int(Zl),x,y)
			create_pol(int(Zl),x,y)
		else:
			print "- skipped file", tile_fname, "(already exits)"

		# removing logo
		if args.remove_logo and os.path.isfile(child_fname):
			remove_logo(tile_fname,child_fname)
		
		# convert img to dds	
		if args.dds_textures:
			if dds_pid != None:
				print "Waiting for pid", dds_pid, "(convert to DDS)"
				os.waitpid(dds_pid,0)
			dds_pid = convert_to_dds(tile_fname,dds_fname)

prepare_dsf()

if dds_pid != None:
	print "Waiting for pid", dds_pid, "(convert to DDS)"
	os.waitpid(dds_pid,0)
	

