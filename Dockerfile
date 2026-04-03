# begin Dockerfile

FROM ghcr.io/kangwonlee/edu-base-raw:60dfc33

USER root

# Clone gemini-python-tutor (ai_tutor + prompt_pipeline)
RUN git clone --depth=1 --branch v0.4.0 https://github.com/kangwonlee/gemini-python-tutor /app/temp/ \
    && mkdir -p /app/ai_tutor/ \
    && mv /app/temp/*.py /app/ai_tutor \
    && mv /app/temp/locale/ /app/ai_tutor/locale/ \
    && mv /app/temp/prompt_pipeline/ /app/prompt_pipeline/ \
    && chown -R runner:runner /app/ai_tutor/ /app/prompt_pipeline/

RUN uv pip install --system --requirement /app/temp/requirements.txt \
    && rm -rf /app/temp

COPY pyproject.toml /app/pyproject.toml
RUN uv pip install --no-cache-dir --system /app/

USER runner

WORKDIR /tests/

RUN mkdir -p /tests/

COPY tests/* /tests/

RUN python3 -c "import pytest; import requests; import glob; files = glob.glob('/tests/test_*.py'); print('Found', len(files), 'files:', files); assert files, 'No files in /tests/!'"

WORKDIR /app/

# end Dockerfile
