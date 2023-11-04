#!/bin/sh
systemctl daemon-reload
systemctl enable rp500K_read
systemctl enable rp500K_write
#rename services and edit lines above
