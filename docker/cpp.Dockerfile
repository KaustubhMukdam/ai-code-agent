FROM gcc:13-bookworm

WORKDIR /code

RUN apt-get update && apt-get install -y \
    g++ \
    clang-format \
    cppcheck \
    valgrind \
    clang-tidy \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 coderunner && \
    chown -R coderunner:coderunner /code
USER coderunner

CMD ["g++"]