FROM python:3.10.9
EXPOSE 8501
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "bioavailability.py"]