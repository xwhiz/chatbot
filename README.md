# CHATBOT

## Pre-requisites

1. Node.js (v20.0.0 at least)
2. npm (v6.14.4 at least)
3. Python (v3.10.0 at least)
4. MongoDB (running locally on port 27017)
5. venv (Python virtual environment)
6. Ollama installed on system and its server running locally.

Don't worry, I will have everything for you covered here in the installation section below.

## Installation

First of all, clone the repository

```bash
# If it is not accessible to you, you may need to
# zip download it, and paste it in the client system

git clone git@github.com:CodeWhizHamza/chatbot.git
```

### Setting up the frontend

```bash
cd chatbot/frontend
npm install
```

#### Setup the environment variables

```bash
cp .env.sample .env.local
```

Now, open the `.env.local` file and set the `NEXT_PUBLIC_API_URL` to the backend server URL. typically it is `http://0.0.0.0:8000`.

Also, setup the `NEXT_PUBLIC_JWT_SECRET` to a random string, and remember it for the backend setup too.

#### Build the frontend

```bash
npm run build
```

Now the frontend is ready to be served.

### Setting up the backend

```bash
cd chatbot/api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Setup the environment variables

```bash
cp .env.sample .env
```

Now, open the `.env` file and set the `JWT_SECRET` to the same value as you set in the frontend.

Note: Use this once you have install all the dependencies in the backend.

Change the `SALT` to a randomly generated salt using the following command:

```bash
python -c "import bcrypt; print(bcrypt.gensalt())"
```

Copy this salt and paste it in the `.env` file.

The `MONGODB_URI` should be `mongodb://localhost:27017/` if you are running MongoDB locally. Otherwise, set it to the appropriate URI from the MongoDB provider.

Now the backend is ready to be served.

### Setup the Ollama

First of all, you need to have Ollama installed on your system. If you don't have it, you can download it from [here](https://ollama.com/download/mac)

### Download the required models

Then in the terminal, run the following command to start the Ollama server:

```bash
ollama pull llama3.1
ollama pull deepseek-r1:14b
ollama pull qwen2.5:14b
```

This will install the required dependencies and start the server.

### Setup the MongoDB

If you don't have MongoDB installed, you can download it from [here](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-os-x/)

This will only install the MongoDB server, you will need to start the server by running the following command:

```bash
mongod
```

## Install Python

If you have brew installed, you can install python using the following command:

```bash
brew install python3.10
```

Otherwise, you can download the installer from [here](https://www.python.org/downloads/)

## Running the application

Go to the root directory of the project and run the following command:

### Running the frontend

```bash
cd frontend
npm run start
```

### Running the backend

```bash
cd backend
source venv/bin/activate
fastapi run main.py
```

fastapi run, runs the backend server on `http://0.0.0.0:8000`, so make sure to set the `NEXT_PUBLIC_API_URL` in the frontend to this URL.

### Or run the script to run the whole system at once.

```bash
sudo ./run_application.sh
```

## Resolving bugs

1. Note: if you are running the system after changes, please make sure to empty the database (development).
