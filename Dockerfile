# Pull the base image
FROM ubuntu:22.04



RUN apt update
RUN apt install wget build-essential libssl*  -y

RUN apt-get install libffi-dev nano -y

RUN wget https://www.python.org/ftp/python/3.10.14/Python-3.10.14.tgz
RUN tar -xzvf Python-3.10.14.tgz
RUN cd Python-3.10.14
WORKDIR Python-3.10.14
RUN ./configure --enable-optimizations --with-system-ffi
RUN make -j 16
RUN apt install libespeak-dev zlib1g-dev libmupdf-dev libfreetype6-dev ffmpeg espeak imagemagick git -y
RUN make altinstall

RUN python3.10 -m pip install opencv-python
RUN python3.10 -m pip install numpy
RUN python3.10 -m pip install aeneas
RUN python3.10 -m pip install moviepy
RUN python3.10 -m pip install pathlib
RUN python3.10 -m pip install pysrt
RUN python3.10 -m pip install Django 
RUN python3.10 -m pip install gunicorn 
RUN python3.10 -m pip install Pillow==9.5.0 
RUN python3.10 -m pip install matplotlib
RUN python3.10 -m pip install django-htmx

RUN python3.10 -m pip install django-bootstrap-v5
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y postgresql postgresql-contrib
ENV DEBIAN_FRONTEND=noninteractive
# Configure PostgreSQL (basic setup)


ENV DEBIAN_FRONTEND=noninteractive
# Ensure pip is upgraded
RUN python3.10 -m pip install --upgrade pip
# RUN  python3.10 -m pip install moviepy[optional]


# Install the required Python packages
COPY requirements.txt .
RUN python3.10 -m pip install -r requirements.txt
# Copy the rest of your application files
COPY . /app
RUN apt-get update && apt-get install -y \
    libfreetype6 \
    libfontconfig1 \
    fonts-liberation \
    && apt-get clean
# Set environment variable for ImageMagick
ENV IMAGEMAGICK_BINARY=/usr/bin/convert
RUN sed -i 's/<policy domain="path" rights="none" pattern="@\*"/<!--<policy domain="path" rights="none" pattern="@\*"-->/' /etc/ImageMagick-6/policy.xml || true \
    && sed -i 's/<policy domain="path" rights="none" pattern="@\*"/<!--<policy domain="path" rights="none" pattern="@\*"-->/' /etc/ImageMagick-7/policy.xml || true



ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG DB_PASSWORD
ARG EMAIL_HOST_PASSWORD
ARG EMAIL_HOST_USER

ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
ENV DB_PASSWORD=${DB_PASSWORD}
ENV EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}
ENV EMAIL_HOST_USER=${EMAIL_HOST_USER}
EXPOSE 8000
COPY ./fonts /usr/share/fonts/custom

# Update font cache so the system recognizes the new fonts
RUN fc-cache -f -v

WORKDIR /app

# Your entrypoint or CMD here, for example:
# ENTRYPOINT ["entrypoint.sh"]

# CMD ["python3.10", "manage.py", "runserver", "0.0.0.0:8000"]
CMD [ "python3.10 manage.py migrate && python3.10 manage.py runserver 0.0.0.0:8000"]

