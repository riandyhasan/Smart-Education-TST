FROM python:3.10-slim

# Set the working directory
WORKDIR /app


# copy application code
COPY . /app

# install dependencies
RUN pip install -r requirements.txt

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_DEBYG=development

# Expose the app's port
EXPOSE 5000

# Run the app
CMD ["flask", "run", "--host=0.0.0.0"]