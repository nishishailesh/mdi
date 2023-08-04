#!/bin/sh
systemctl daemon-reload
systemctl enable rp500_read
systemctl enable rp500_write
#rename services and edit lines above
