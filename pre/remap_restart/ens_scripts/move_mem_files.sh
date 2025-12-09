#!/bin/bash

SUB="f5295_fp.atmens_ecbkg.20240714_21z"
SRC="/discover/nobackup/projects/gmao/obsdev/eyang2/PBLH/Exp/pblhl/atmens/"$SUB
DST="/discover/nobackup/projects/gmao/obsdev/eyang2/PBLH/Exp/pblhl/atmens/"

for i in "$SRC"/mem*/*; do
  memdir=$(basename "$(dirname "$i")")
  mv "$i" "$DST/$memdir/"
  echo mv "$i" "$DST/$memdir/"
done


#for i in "$SRC"/mem*/*; do
#  memdir=$(basename "$(dirname "$i")")
#  echo mv "$i" "$DST/$memdir/"
#done
