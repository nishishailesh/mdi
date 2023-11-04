#!/bin/sh
systemctl daemon-reload
systemctl disable rp500K_read
systemctl disable rp500K_write
#rename services and edit lines above
