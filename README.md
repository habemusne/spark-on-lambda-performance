## Server Setup

- Goto AWS console, at the top right, choose "US East (N.Virginia)"
- Goto S3 console and create a bucket named "\<your-name\>-cse597cc", everything else default
- Goto EC2 console, create an instance, first machine type (Amazon Linux x86), 10GB, security group please open ssh 22 inbound, use a private key pem. Everything else default.
- Goto EC2 console, click Elastic IP on the left, create one and associate it to the instance
- Goto your EC2 instance info and find your public IP if you scroll down.
- connect to server: `ssh -o ServerAliveInterval=60 -i ~/.ssh/cc.pem ubuntu@<your-public-ip>`
- Next we begin the server configuration

```
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user
```

- Please logout and log back in again, then continue
```
sudo yum install git -y
git clone https://github.com/aws/aws-sdk-java
cd aws-sdk-java
sudo yum install maven -y
mvn clean install -pl aws-java-sdk-lambda -am -Dgpg.skip=true
mvn clean install -pl aws-java-sdk-s3 -am -Dgpg.skip=true
cd
git clone https://github.com/qubole/spark-on-lambda
mkdir -p project/data/kmeans/
cp spark-on-lambda/data/mllib/kmeans_data.txt project/data/kmeans/mllib_6lines.txt
cp spark-on-lambda/data/mllib/sample_kmeans_data.txt project/data/kmeans/ml_6lines.txt
wget https://s3.amazonaws.com/public-qubole/lambda/spark-2.1.0-bin-spark-lambda-2.1.0.tgz
tar xvzf spark-2.1.0-bin-spark-lambda-2.1.0.tgz
mv spark-2.1.0-bin-spark-lambda-2.1.0 driver
mkdir ~/.aws
```

- Goto [AWS security credential](https://console.aws.amazon.com/iam/home?#security_credential), create a pair of access key and secret access key. Then edit `~/.aws/credentials`. Content of the file:

```
[default]
aws_access_key_id=PLEASE ENTER
aws_secret_access_key=PLEASE ENTER
```

- Goto [iam](https://console.aws.amazon.com/iam/home#/home), click "Roles"->"Create role"->Choose the service... click "Lambda"->"Next: Permissions"->AmazonEC2FullAccess,AWSLambdaFullAccess,AmazonS3FullAccess,AWSLambdaExecute,AWSLambdaVPCAccessExecutionRole,AWSLambdaRole->"Next: Tags"->"Next: Review"->Role name fill in "cse597cc"->"Create role"

- Create a lambda function, "author from scratch", function name "spark-lambda", runtime "Python 2.7" (if you want to change this, not now). Click "Execution role"->"Use an existing role"->"cse597cc"->"Create function"

- Copy code from [here](https://github.com/qubole/spark-on-lambda/blob/lambda-2.1.0/bin/lambda/spark-lambda-os.py) to the Lambda. Change "Handler" box to "lambda_function.handler". Click "Save"
- In the Lambda console scroll down. At the Network panel, pick "Default vpc..."->choose all subnets->choose all security groups->"Save" **TODO: this part needs more work**

```
aws s3 cp s3://public-qubole/lambda/spark-lambda-149.zip s3://<username>-cse597cc/
aws s3 cp s3://public-qubole/lambda/spark-2.1.0-bin-spark-lambda-2.1.0.tgz s3://<username>-cse597cc/

sudo yum install python-pip -y
sudo pip install numpy -U

cp ~/driver/bin/conf/spark-defauls.conf.template ~/driver/bin/conf/spark-defauls.conf
cd project
```

Edit the file `~/project/ml_kmeans.py`. Content of the file:

```
from __future__ import print_function

# $example on$
from pyspark.ml.clustering import KMeans
# $example off$

from pyspark.sql import SparkSession

if __name__ == "__main__":
    spark = SparkSession\
        .builder\
        .appName("KMeansExample")\
        .getOrCreate()

    # $example on$
    # Loads data.
    dataset = spark.read.format("libsvm").load("/home/ec2-user/project/data/kmeans/ml_6lines.txt")

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
    # $example off$

    spark.stop()
```

- Edit `~/driver/bin/conf/spark-defauls.conf`. Content of the file:
```
spark.shuffle.s3.enabled    true
spark.shuffle.s3.bucket     s3://<your-name>-cse597cc/
spark.lambda.s3.bucket      s3://<your-name>-cse597cc/
spark.lambda.concurrent.requests.max  50
spark.lambda.function.name    spark-lambda
spark.lambda.spark.software.version 149
spark.hadoop.fs.s3n.impl    org.apache.hadoop.fs.s3a.S3AFileSystem
spark.hadoop.fs.s3.impl     org.apache.hadoop.fs.s3a.S3AFileSystem
spark.hadoop.fs.AbstractFileSystem.s3.impl  org.apache.hadoop.fs.s3a.S3A
spark.hadoop.fs.AbstractFileSystem.s3n.impl org.apache.hadoop.fs.s3a.S3A
spark.hadoop.fs.AbstractFileSystem.s3a.impl org.apache.hadoop.fs.s3a.S3A
spark.hadoop.fs.s3n.awsAccessKeyId  <PLEASE ENTER>
spark.hadoop.fs.s3n.awsSecretAccessKey  <PLEASE ENTER>
spark.dynamicAllocation.enabled   true
spark.dynamicAllocation.minExecutors  2
```

## Run

Assume that you are in the project directory: `sudo ./../driver/bin/spark-submit ml_kmeans.py`

**This will run but fail, likely due to VPC configuration to collaborate all of the three parties (Lambda, EC2, S3). I am still working on it**

**It's tough... Try to take a look into this issue if you have time.**
