#!/bin/sh
systemctl daemon-reload
systemctl enable tosoh_read
systemctl enable tosoh_write
