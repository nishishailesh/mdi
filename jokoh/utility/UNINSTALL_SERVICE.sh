#!/bin/sh
systemctl daemon-reload
systemctl disable jokoh_read
systemctl disable jokoh_write
#rename services and edit lines above
