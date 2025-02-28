#!/bin/sh
systemctl daemon-reload
systemctl enable NXL_1000_read
systemctl enable NXL_1000_write
#rename services and edit lines above
