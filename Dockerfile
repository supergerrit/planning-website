# The first instruction is what image we want to base our container on
# We Use an official Python runtime as a parent image
FROM python:3.11

# The enviroment variable ensures that the python output is set straight
# to the terminal with out buffering it first
ENV PYTHONUNBUFFERED 1

# Install Java
RUN apt-get update && apt-get -y install default-jre

# create root directory for our project in the container
RUN mkdir /jumbo_website

# Set the working directory to /jumbo_website
WORKDIR /jumbo_website

# Copy the current directory contents into the container at /jumbo_website
ADD . /jumbo_website/

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

EXPOSE 80
CMD ["gunicorn", "--chdir", "JumboWebsite", "--bind", ":80", "JumboWebsite.wsgi:application"]
