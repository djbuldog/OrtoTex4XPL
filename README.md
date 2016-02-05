OrtoTex4XPL
======

<pre>
usage: OrtoTex4XPL.py [-h] [--zl <level>] [--src {gmaps,mapy}] [--base <path>]
                      [--coord2 lat lng] [--remove-logo] [--keep-downloaded]
                      [--dds-textures]
                      lat lng

positional arguments:
  lat                 GPS lattitude --- for ex. 49.15296966
  lng                 GPS longtitude -- for ex. 16.66625977

optional arguments:
  -h, --help          show this help message and exit
  --zl <level>        required map zoom level (10-24) -- default: 18
  --src {gmaps,mapy}  map source (mapy.cz, google maps) -- default: gmaps
  --base <path>       output directory base -- default: /tmp/orto4xpl
  --coord2 lat lng    Second GPS coordinates (lower right corner)
  --remove-logo       try to remove logo merging with higher zoom level
  --keep-downloaded   do not delete temporary img files after processing
  --dds-textures      convert textures to dds (instead of png) -- default: png
</pre>

