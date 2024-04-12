#!/bin/sh
systemctl daemon-reload
systemctl enable bs600m_read
systemctl enable bs600m_write
#rename services and edit lines above
