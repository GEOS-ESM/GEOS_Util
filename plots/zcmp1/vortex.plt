function vortexplt (args)
nmod   = subwrd(args,1)
nobs   = subwrd(args,2)
mdesc  = subwrd(args,3)
odesc  = subwrd(args,4)
name   = subwrd(args,5)
output = subwrd(args,6)
clim   = subwrd(args,7)

'c'
'set vpage off'

*** SH (Left Panel: 2 columns, 1 row, panel 1, 1)
'set vpage 0 6.3 0 7.5'
'set grads off'
'set grid  on'
'set xlab %mc'
'set gxout contour'
'set lev 100 .1'
'setlevs'
* OBS
'set clab  on'
'set clevs  0'
'set ccolor 2'
'set cthick 10'
'set cstyle 1'
'd oclmsh'
* OBS Negative Contours (Dashed)
'set clab  on'
'set clevs  -90 -75 -60 -45 -30 -15'
'set ccolor 2'
'set cthick 4'
'set cstyle 2'
'd oclmsh'
* OBS Positive Contours (Solid)
'set clab  on'
'set clevs  15 30 45 60 75 90'
'set ccolor 2'
'set cthick 4'
'set cstyle 1'
'd oclmsh'
* OBS plus STD
'set clab off'
'set clevs  0'
'set ccolor 2'
'set cthick 3'
'set cstyle 3'
*'d oclmpsh'
* OBS minus STD
'set clab off'
'set clevs  0'
'set ccolor 2'
'set cthick 3'
'set cstyle 3'
*'d oclmmsh'
* EXP
'set clab  on'
'set clevs  0'
'set ccolor 4'
'set cthick 10'
'set cstyle 1'
'd mclmsh'
* EXP Negative Contours (Dashed)
'set clab  on'
'set clevs  -90 -75 -60 -45 -30 -15'
'set ccolor 4'
'set cthick 4'
'set cstyle 2'
'd mclmsh'
* EXP Positive Contours (Solid)
'set clab  on'
'set clevs  15 30 45 60 75 90'
'set ccolor 4'
'set cthick 4'
'set cstyle 1'
'd mclmsh'
* EXP plus STD
'set clab off'
'set clevs  0'
'set ccolor 4'
'set cthick 3'
'set cstyle 3'
*'d mclmpsh'
* EXP minus STD
'set clab off'
'set clevs  0'
'set ccolor 4'
'set cthick 3'
'set cstyle 3'
*'d mclmmsh'
'draw ylab Pressure (hPa)'

*** NH (Right Panel: 2 columns, 1 row, panel 2, 1)
'set vpage 5.0 11 0 7.5'
'set grads off'
'set grid  on'
'set xlab %mc'
'set gxout contour'
'set lev 100 .1'
'setlevs'
* OBS
'set clab  on'
'set clevs  0'
'set ccolor 2'
'set cthick 10'
'set cstyle 1'
'd oclmnh'
* OBS Negative Contours (Dashed)
'set clab  on'
'set clevs  -90 -75 -60 -45 -30 -15'
'set ccolor 2'
'set cthick 4'
'set cstyle 2'
'd oclmnh'
* OBS Positive Contours (Solid)
'set clab  on'
'set clevs  15 30 45 60 75 90'
'set ccolor 2'
'set cthick 4' 
'set cstyle 1'
'd oclmnh'
* OBS plus std
'set clab off'
'set clevs  0'
'set ccolor 2'
'set cthick 3'
'set cstyle 3'
*'d oclmpnh'
* OBS minus std
'set clab off'
'set clevs  0'
'set clevs  0'
'set ccolor 2'
'set cthick 3'
'set cstyle 3'
*'d oclmmnh'
* EXP
'set clab  on'
'set clevs  0'
'set ccolor 4'
'set cthick 10'
'set cstyle 1'
'd mclmnh'
* EXP Negative Contours (Dashed)
'set clab  on'
'set clevs  -90 -75 -60 -45 -30 -15'
'set ccolor 4'
'set cthick 4'
'set cstyle 2'
'd mclmnh'
* EXP Positive Contours (Solid)
'set clab  on'
'set clevs  15 30 45 60 75 90'
'set ccolor 4'
'set cthick 4'
'set cstyle 1'
'd mclmnh'
* EXP plus STD
'set clab off'
'set clevs  0'
'set ccolor 4'
'set cthick 3'
'set cstyle 3'
*'d mclmpnh'
* EXP minus STD
'set clab off'
'set clevs  0'
'set clevs  0'
'set ccolor 4'
'set cthick 3'
'set cstyle 3'
*'d mclmmnh'
*'draw ylab Pressure (hPa)'

*** Global Annotations & Shared Header at Top Center ***
'set vpage off'

* Main title
'set string 1 c 6'
'set strsiz .14'
'draw string 5.5  8.3 (Zonal Mean U-Wind)'
* Subtitles above each respective panel
'set string 1 c 6'
'set strsiz .10'
'draw string 4.3  7.25 SH Lat: -30,-70 Average'
'draw string 7.5  7.25 NH Lat:  30, 70 Average'
* Legend
'set strsiz .12'
'set string 4 c 6'
'draw string 5.5  7.8 'mdesc' ('nmod')'
'set string 2 c 6'
'draw string 5.5  7.5 'odesc' ('nobs') 'clim

'myprint -name 'output'/VORTEX_'name
'c'
return
