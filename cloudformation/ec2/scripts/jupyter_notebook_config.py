import os
c = get_config()
os.environ['LD_LIBRARY_PATH'] = '/usr/local/cuda-7.5/lib64'
c.Spawner.env.update('LD_LIBRARY_PATH')
c.NotebookApp.certfile = '/home/ec2-user/ssl/cert.pem'
c.NotebookApp.keyfile = '/home/ec2-user/ssl/cert.key'
c.NotebookApp.ip = '*'
c.NotebookApp.open_browser = False
c.NotebookApp.password = 'sha1:914bdd8e4ac9:1880dccd7e1a3a4d90fd1c41ae86dd56efc5926e'
c.NotebookApp.notebook_dir = '/mnt/jupyter-notebooks'
