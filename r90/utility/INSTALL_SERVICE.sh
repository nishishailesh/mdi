#!/bin/sh
systemctl daemon-reload
systemctl enable r90_read
systemctl enable r90_write
#rename services and edit lines above
