# March Madness Predictor

A machine learning project that simulates and predicts NCAA March Madness tournament outcomes using historical team stats and bracket data.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/mhuxmitmuma/march-madness.git
cd march-madness
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure your database credentials

This project uses a MySQL database. Your credentials are **not** included in the repository for security reasons — they are stored in a `.env` file that is listed in `.gitignore` and never committed.

Create a `.env` file in the project root:

```
DB_HOST=localhost
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=march_madness
```

### 4. Initialize the database

Uncomment `init_database()` in `main.py` and run it once to set up the schema:

```bash
python main.py
```

### 5. Load data

Uncomment `load_all_data()` or `load_year(year)` in `main.py` to populate the database with tournament data.

## Usage

- **Load data**: `load_all_data()` or `load_year(2026)` in `main.py`
- **Run simulations**: `run_simulations(year, n)` — runs `n` Monte Carlo tournament simulations for the given year
- **Train model**: `python train.py`
- **Validate model**: `python validate.py`
