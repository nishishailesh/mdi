#!/bin/sh
systemctl daemon-reload
systemctl enable quikread_read
systemctl enable quikread_write
#rename services and edit lines above
