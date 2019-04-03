## connect
user name: ec2-user

ip: 34.219.68.150

## run

run a shell
```
./spark/bin/pyspark \
--conf spark.lambda.s3.bucket=s3://public-qubole/ \
--conf spark.lambda.function.name=spark-lambda \
--conf spark.lambda.spark.software.version=149 \
--conf spark.hadoop.fs.s3n.awsAccessKeyId=AKIAJ2J2SLUWTEUEWNTQ \
--conf spark.hadoop.fs.s3n.awsSecretAccessKey=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
```

run a file
```
(TODO)
```

