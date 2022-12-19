FROM python
EXPOSE 8888
COPY ./main.py main.py
COPY ./constants.py constants.py
COPY ./handlers.py handlers.py
COPY ./modules.py modules.py
COPY ./models.py models.py
COPY ./service.py service.py
COPY ./take_photo.py take_photo.py
COPY cards cards
COPY ./requirements.txt requirements.txt
RUN pip install --requirement /requirements.txt
CMD ["python", "main.py"]