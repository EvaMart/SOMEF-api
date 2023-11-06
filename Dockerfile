FROM --platform=linux/amd64 python:3.9
COPY ./server web

WORKDIR web 

RUN python -m pip install -r requirements.txt --no-dependencies
RUN python -m nltk.downloader punkt
RUN python -m nltk.downloader wordnet
RUN python -m nltk.downloader omw-1.4
RUN python -m nltk.downloader stopwords

RUN ./installer.sh

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5300"]

EXPOSE 5300
