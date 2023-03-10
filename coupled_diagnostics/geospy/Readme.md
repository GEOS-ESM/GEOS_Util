### Coupled diagnostics

This package produces diagnostics for ocean surface/subsurface and sea
ice (coming soon). To use this package at discover/nas, load default
python3 module
```
module load python/GEOSpyD
```
Then, clone the GMAO_Util repository
```
git clone -b git@github.com:GEOS-ESM/GMAO_Util.git
```
Then, edit `ocnconf.yaml` file. A template for ocnconf.yaml is
included in this package. You can run a single set of plots, e.g.
```
GEOS_Util/coupled_diagnostics/geospy/ssh.py path_to_config_file
```
or run a complete diagnostics
```
GEOS_Util/coupled_diagnostics/geospy/mkplots.py path_to_config_file
```
An arbitrary set of plots can be specified in a config file (see
template for ocnconf.yaml).
