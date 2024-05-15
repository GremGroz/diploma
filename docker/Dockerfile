FROM python:3.12



WORKDIR /app

# Копирование файлов проекта
COPY . .
# Установка зависимостей
RUN pip install -r requirements.txt

CMD ["/bin/bash", "-c", "python run.py; python copy_master.py"]
