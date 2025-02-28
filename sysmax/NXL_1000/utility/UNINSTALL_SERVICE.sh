#!/bin/sh
systemctl daemon-reload
systemctl disable NXL_1000_read
systemctl disable NXL_1000_write
#rename services and edit lines above
