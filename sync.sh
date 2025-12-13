#!/bin/bash

# Use MSYS2 SSH (already in PATH)
# export RSYNC_RSH="/usr/bin/ssh"  # optional, usually unnecessary

# Source and destination
DEST="mark@pizero:/home/mark/Robbie-the-Robot/"

rsync -av --progress --no-compress \
  --exclude 'node_modules' \
  --exclude '.venv' \
  --exclude '.git' \
  --exclude '.env' \
  --exclude '__pycache__' \
  --exclude 'robot.log' \
  ./ "$DEST"

rsync -avz --progress \
  ./.asoundrc mark@pizero:/home/mark/.asoundrc
