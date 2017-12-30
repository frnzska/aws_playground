import boto3
import os
os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"
emr = boto3.client('emr')

step_definition = {'ActionOnFailure': 'CONTINUE',
                   'HadoopJarStep':
                        {'Args':
                            ['spark-submit',
                             '--deploy-mode', 'client',
                             '--master', 'yarn',
                             '/home/hadoop/some_spark_task.py',
                             ],
                   'Jar': 'command-runner.jar'},
                   'Name': 'test steps'}


def get_cluster_id(name='ClusterWithSparkAndSteps'):
    clusters = emr.list_clusters()['Clusters']
    cluster_id = [c['Id'] for c in clusters if c['Name']==name]
    if cluster_id:
        return cluster_id[0]

id = get_cluster_id()
if id:
    response = emr.add_job_flow_steps(JobFlowId=id, Steps=[step_definition])
