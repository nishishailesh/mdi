#!/bin/sh
systemctl daemon-reload
systemctl enable astmbi_read
systemctl enable astmbi_write
#rename services and edit lines above
