#!/bin/sh
systemctl daemon-reload
systemctl disable tosoh_read
systemctl disable tosoh_write
