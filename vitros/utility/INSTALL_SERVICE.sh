#!/bin/sh
systemctl daemon-reload
systemctl enable vitros_read
systemctl enable vitros_write
#rename services and edit lines above
