#!/bin/sh
systemctl daemon-reload
systemctl enable jokoh_read
systemctl enable jokoh_write
#rename services and edit lines above
