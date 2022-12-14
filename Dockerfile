FROM python:3.8

# copy application code
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# install dependencies
RUN pip install -r requirements.txt

# Run the app
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app