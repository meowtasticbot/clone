FROM nikolaik/python-nodejs:python3.10-nodejs19

# Install ffmpeg safely.
# - Drop optional third-party apt sources inherited from the base image.
# - If an image variant still points to Debian buster (EOL), rewrite sources
#   to Debian archive mirrors so `apt-get update` can succeed.
RUN rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/nodesource.list \
    && if grep -Rqs "buster" /etc/apt/sources.list /etc/apt/sources.list.d/*.list 2>/dev/null; then \
         find /etc/apt -type f \( -name "sources.list" -o -name "*.list" \) -print0 \
           | xargs -0 sed -i \
               -e 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' \
               -e 's|http://deb.debian.org/debian-security|http://archive.debian.org/debian-security|g' \
               -e '/buster-updates/d'; \
         printf 'Acquire::Check-Valid-Until "false";\n' > /etc/apt/apt.conf.d/99no-check-valid-until; \
       fi \
    && apt-get update \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
WORKDIR /app/
RUN pip3 install --no-cache-dir -U -r requirements.txt

CMD bash start
