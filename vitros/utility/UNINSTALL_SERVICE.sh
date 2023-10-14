#!/bin/sh
systemctl daemon-reload
systemctl disable vitros_read
systemctl disable vitros_write
#rename services and edit lines above
