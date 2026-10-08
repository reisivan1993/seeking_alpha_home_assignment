FROM python:3.12-slim
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
WORKDIR /home/work
EXPOSE 8888
# No token: the port is bound to 127.0.0.1 only (see docker-compose.yml). Local sandbox, not for shared machines.
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", \
     "--ServerApp.token=", "--ServerApp.password=", "--ServerApp.root_dir=/home/work"]
