#!/bin/sh
systemctl daemon-reload
systemctl disable bs600m_read
systemctl disable bs600m_write
#rename services and edit lines above
