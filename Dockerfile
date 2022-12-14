FROM python:3.8

# copy application code
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# install dependencies
RUN pip install -r requirements.txt

# Run the app
CMD ["flask", "run", "--host=0.0,0.0", "--port=8080"]