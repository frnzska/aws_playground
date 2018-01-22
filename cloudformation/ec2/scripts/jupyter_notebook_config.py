import os
c = get_config()
os.environ['LD_LIBRARY_PATH'] = '/usr/local/cuda-8.0/lib64:/home/ec2-user/src/torch/install/lib:/lib:/home/ec2-user/src/cntk/bindings/python/cntk/libs:/usr/local/cuda/lib64:/usr/local/lib:/usr/lib:/usr/local/cuda/extras/CUPTI/lib64:/usr/local/mpi/lib:/home/ec2-user/src/mxnet/mklml_lnx_2017.0.1.20161005/lib:/home/ec2-user/src/cntk/bindings/python/cntk/libs:/usr/local/cuda/lib64:/usr/local/lib:/usr/lib:/usr/local/cuda/extras/CUPTI/lib64:/usr/local/mpi/lib:/home/ec2-user/src/mxnet/mklml_lnx_2017.0.1.20161005/lib'
c.Spawner.env.update('LD_LIBRARY_PATH')
c.NotebookApp.certfile = '/home/ec2-user/certs/cert.pem'
c.NotebookApp.keyfile = '/home/ec2-user/certs/cert.key'
c.NotebookApp.ip = '*'
c.NotebookApp.open_browser = False
c.NotebookApp.password = 'sha1:914bdd8e4ac9:1880dccd7e1a3a4d90fd1c41ae86dd56efc5926e'
c.NotebookApp.notebook_dir = '/mnt/jupyter-notebooks'
