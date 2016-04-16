#!/usr/bin/env python

import os
import sys
import re

def getCoordsFromTer(dirpath):

	lat_min = 361.0
	lat_max = 0.0
	lng_min = 361.0
	lng_max = 0.0

	for f in os.listdir(dirpath):
		if os.path.isfile(dirpath+f):
			terfile = open(dirpath+f, 'r')
			m = re.search("LOAD_CENTER ([0-9]+\.[0-9]+) ([0-9]+\.[0-9]+)",terfile.read())
			if m:
				lat = float(m.group(1))
				lng = float(m.group(2))
				if (lat_min)>lat: lat_min = lat
				if (lat_max)<lat: lat_max = lat
				if (lng_min)>lng: lng_min = lng
				if (lng_max)<lng: lng_max = lng
			else:
				print "cannot found any coords in the file", f
			terfile.close()

	if lat_min>lat_max or lng_min>lng_max:
		return (0,0,0,0)
	else:
		return (lat_max, lng_min, lat_min, lng_max)


if len(sys.argv) != 2:
	print "usage: find_coords.py <path_to_terrain_files>"
	sys.exit(0)

lat1, lng1, lat2, lng2 = getCoordsFromTer(sys.argv[1])
print lat1, lng1, "--coord2", lat2, lng2


