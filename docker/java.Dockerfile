FROM openjdk:17-slim

WORKDIR /code

RUN useradd -m -u 1001 coderunner || adduser --disabled-password --gecos '' coderunner
USER coderunner

CMD ["java"]