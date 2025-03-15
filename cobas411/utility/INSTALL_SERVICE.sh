#!/bin/sh
systemctl daemon-reload
systemctl enable xl1000_read
systemctl enable xl1000_write
#rename services and edit lines above
