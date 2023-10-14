#!/bin/sh
systemctl daemon-reload
systemctl disable rp500_read
systemctl disable rp500_write
#rename services and edit lines above
