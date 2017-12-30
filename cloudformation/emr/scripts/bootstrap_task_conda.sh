#!/usr/bin/env bash

set -x -e

TASK=${1:-"s3://franziska-adler-deployments/production/aws_playground/cloudformation/emr/scripts/some_spark_task.py"}

wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/conda


echo '\nexport PATH=$HOME/conda/bin:$PATH' >> $HOME/.bashrc && source $HOME/.bashrc

conda config --set always_yes yes --set changeps1 no
conda install conda=4.2.13
conda config -f --add channels conda-forge
conda config -f --add channels defaults

conda install toolz boto3
conda install conda=4.2.13

rm ~/miniconda.sh

IS_MASTER=false
if grep isMaster /mnt/var/lib/info/instance.json | grep true;
then
  IS_MASTER=true
  aws s3 cp $TASK ~/some_spark_task.py
fi
echo Done
