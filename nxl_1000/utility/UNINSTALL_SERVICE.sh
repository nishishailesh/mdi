#!/bin/sh
systemctl daemon-reload
systemctl disable xl1000_read
systemctl disable xl1000_write
#rename services and edit lines above
