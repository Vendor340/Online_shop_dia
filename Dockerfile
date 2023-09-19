FROM python:3.9-slim
ADD . python_app/source/
WORKDIR python_app/source/
RUN pip install -r requirements.txt
RUN set FLASK_APP=run_app.py
EXPOSE 5000
CMD "python -u run_app.py"