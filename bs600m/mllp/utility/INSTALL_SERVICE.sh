#!/bin/sh
systemctl daemon-reload
systemctl enable hl7_general__read
systemctl enable hl7_general_write
#rename services and edit lines above
