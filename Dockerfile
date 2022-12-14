FROM python:3.10-slim

# Set the working directory
WORKDIR /app


# copy application code
COPY . /app

# install dependencies
RUN pip install -r requirements.txt

# Run the app
CMD ["flask", "run"]