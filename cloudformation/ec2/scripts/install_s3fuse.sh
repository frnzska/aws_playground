#!/bin/bash
set -x -e

sudo yum update -y
sudo yum install -y automake fuse fuse-devel libxml2-devel
cd /mnt

git clone https://github.com/s3fs-fuse/s3fs-fuse.git
cd s3fs-fuse/
./autogen.sh
./configure
make
sudo make install
echo user_allow_other >> /etc/fuse.conf
mkdir -p /mnt/s3fs-cache

/usr/local/bin/s3fs -o allow_other -o iam_role=auto -o umask=0 -o url=https://s3.amazonaws.com  -o no_check_certificate -o nonempty -o enable_noobj_cache -o use_cache=/mnt/s3fs-cache babbeldataeng-fadler-test /mnt/jupyter-notebooks#!/usr/bin/env bash