import smart_open
import time
import boto3


def time_me(trails):
    def time_mee(f):
        def timing(*args, **kw):
            sum_time, avg = 0, 0
            for i in range(1, trails + 1):
                start = time.time()
                result = f(*args, **kw)
                sum_time += time.time() - start
                avg = sum_time / i
            print(f'avg time: {avg} with {trails} trails')
            return result

        return timing

    return time_mee


@time_me(trails=1)
def do_smart_open(dest):
    return [line for line in smart_open.smart_open(dest)]

@time_me(trails=1)
def do_boto3(bucket, obj_key):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key=obj_key)
    data = obj['Body'].read().decode('utf-8')
    events = data.split('\n')
    #if events[-1] == '':
    #    events = events[:-1]
    return events




dest = 's3://franziska-adler-test-bucket/events/events133236'
do_smart_open(dest)
# ~ 0.95 sec 10 trails, 11 events per file
# ~ 12.42 sec 1 trail, 133236 events per file


#do_boto3(bucket='franziska-adler-test-bucket', obj_key='events/events133236')
# ~ 0.51 sec 10 trails, 11 events per file
# ~196.67 sec 1 trail, 133236 events per file
