FROM python:3.8

# copy application code
WORKDIR /app
COPY . /app

# install dependencies
RUN pip install -r requirements.txt

EXPOSE 5000

# Run the app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]