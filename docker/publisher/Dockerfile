# pull base image
FROM python:latest

RUN apt-get update && apt-get install -y \
    wget \
    unzip \
  && rm -rf /var/lib/apt/lists/*

# install terraform 1.5.3
RUN wget --quiet https://releases.hashicorp.com/terraform/1.5.3/terraform_1.5.3_linux_amd64.zip \
  && unzip terraform_1.5.3_linux_amd64.zip \
  && mv terraform /usr/bin \
  && rm terraform_1.5.3_linux_amd64.zip

# copy files
WORKDIR /src 

COPY ./client ./client

COPY requirements.txt .

COPY ./terraform ./terraform

COPY ./lambda_functions ./lambda_functions

# install dependencies 
RUN pip install --no-cache-dir -r requirements.txt

RUN cd ./terraform && terraform init && terraform apply

ENTRYPOINT ["tail"]
CMD ["-f","/dev/null"]

