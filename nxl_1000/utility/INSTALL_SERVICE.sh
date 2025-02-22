#!/bin/sh
systemctl daemon-reload
systemctl enable nxl1000_read
systemctl enable nxl1000_write
#rename services and edit lines above
