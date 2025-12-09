#!/bin/bash

SRC="/discover/nobackup/projects/gmao/obsdev/eyang2/PBLH/Exp/pblhl/atmens_reg"
DST="/discover/nobackup/projects/gmao/obsdev/eyang2/PBLH/Exp/pblhl/atmens"

#for i in "$SRC"/mem*/*.bkg.eta.*; do
for i in "$SRC"/mem*/*rst*nc4; do
#for i in "$SRC"/mem*/*fvcore*.nc4; do
#for i in "$SRC"/mem*/*.nc4; do
  memdir=$(basename "$(dirname "$i")")
  cp -f "$i" "$DST/$memdir/"
  echo cp "$i" "$DST/$memdir/"
done


#for i in "$SRC"/mem*/*; do
#  memdir=$(basename "$(dirname "$i")")
#  echo mv "$i" "$DST/$memdir/"
#done
