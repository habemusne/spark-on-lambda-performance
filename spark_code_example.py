#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import print_function
import os

from pyspark.ml.clustering import KMeans
from pyspark.sql import SparkSession

import boto3
from time import sleep
s3 = boto3.client('s3')
MEASUREMENT_BUCKET = 'mc-cse597cc'
MEASUREMENT_DIR = '/home/ec2-user/project/measurement'
if not os.path.isdir(MEASUREMENT_DIR):
    os.system('mkdir ' + MEASUREMENT_DIR)

"""
An example demonstrating k-means clustering.
Run with:
  bin/spark-submit examples/src/main/python/ml/kmeans_example.py

This example requires NumPy (http://www.numpy.org/).
"""

if __name__ == "__main__":
    # Clean up previous measurement data
    objs = s3.list_objects(Bucket=MEASUREMENT_BUCKET, Prefix='measurement-').get('Contents', [])
    if objs:
        s3.delete_objects(Bucket=MEASUREMENT_BUCKET, Delete={
            'Objects': [{'Key': obj['Key']} for obj in objs],
        })

    spark = SparkSession\
        .builder\
        .appName("KMeansExample")\
        .config('spark.executorEnv.RUN_ID', 'abcde')\
        .getOrCreate()

    # Loads data.
    data_folder = '/home/ec2-user/driver/data/mllib'
    lambda_folder = '/tmp/lambda/spark/data/mllib'
    filename = 'sample_kmeans_data.txt'
    os.system('mkdir -p ' + lambda_folder)
    os.system('cp {}/{} {}/{}'.format(data_folder, filename, lambda_folder, filename))
    dataset = spark.read.format("libsvm").load('{}/{}'.format(lambda_folder, filename))

    # Trains a k-means model.
    kmeans = KMeans().setK(2).setSeed(1)
    model = kmeans.fit(dataset)

    # Evaluate clustering by computing Within Set Sum of Squared Errors.
    wssse = model.computeCost(dataset)
    print("Within Set Sum of Squared Errors = " + str(wssse))

    # Shows the result.
    centers = model.clusterCenters()
    print("Cluster Centers: ")
    for center in centers:
        print(center)

    spark.stop()

    print('Spark stopped. Waiting for a while before collecting data.')
    sleep(5)
    # Gather measurement data
    objs = s3.list_objects(Bucket=MEASUREMENT_BUCKET, Prefix='measure').get('Contents', [])
    for obj in objs:
        filepath = os.path.join(MEASUREMENT_DIR, obj['Key'].split('/')[-1])
        s3.download_file(MEASUREMENT_BUCKET, obj['Key'], filepath)

    data = {}  # Now suppose that "data" contains your analytics result
    for fname in os.listdir(MEASUREMENT_DIR):
        #### Write your data analytics logic here
        filepath = os.path.join(MEASUREMENT_DIR, fname)
        with open(filepath, 'r') as f:
            print(f.read())
        print('------------')
    print(data)
