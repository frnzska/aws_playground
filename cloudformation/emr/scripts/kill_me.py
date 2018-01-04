import boto3
import os

os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"
emr = boto3.client('emr')


def get_cluster_id(name='ClusterWithSparkAndSteps'):
    clusters = emr.list_clusters()['Clusters']
    cluster_id = [c['Id'] for c in clusters if c['Name']==name]
    if cluster_id:
        return cluster_id[0]

id = get_cluster_id()
if id:
    emr.terminate_job_flows(JobFlowIds=[id])