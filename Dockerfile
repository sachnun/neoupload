# Python image
FROM python:latest

# Install unzip unrar-free p7zip-full
RUN apt-get update && apt-get install -y unzip unrar-free p7zip-full

# Set working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# create temp folder
RUN mkdir /app/temp

# Unlock permission to app and all subfolders
RUN chmod -R 777 /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Make port available to the world outside this container
EXPOSE 7860

# Run app.py when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "4"]