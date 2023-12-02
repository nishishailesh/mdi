#!/bin/sh
systemctl daemon-reload
systemctl disable quikread_read
systemctl disable quikread_write
#rename services and edit lines above
