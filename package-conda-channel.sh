#!/bin/bash

echo "packaging local conda channel into an artifact"
rm -rf /app/local_channel.tar.gz
tar -zcvf /app/local_channel.tar.gz /app/conda/env/local_channel
