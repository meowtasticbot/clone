FROM nikolaik/python-nodejs:python3.10-nodejs19

# Install ffmpeg safely.
# Remove third-party apt sources inherited from the base image to avoid
# signature / EOL repository issues during `apt-get update`.
RUN rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
WORKDIR /app/
RUN pip3 install --no-cache-dir -U -r requirements.txt

CMD bash start
