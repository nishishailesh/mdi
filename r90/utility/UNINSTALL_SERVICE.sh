#!/bin/sh
systemctl daemon-reload
systemctl disable r90_read
systemctl disable r90_write
#rename services and edit lines above
