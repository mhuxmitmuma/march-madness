import mysql.connector
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS teams (
        team_id               INT AUTO_INCREMENT PRIMARY KEY,
        name                  VARCHAR(100) NOT NULL,
        seed                  INT,
        year                  INT NOT NULL,
        region                VARCHAR(50),
        adj_oe                FLOAT,
        adj_de                FLOAT,
        sos                   FLOAT,
        win_rate              FLOAT,
        srs                   FLOAT,
        possessions_per_game  FLOAT,
        ft_pct                FLOAT,
        tov_rate              FLOAT,
        orb_rate              FLOAT,
        fga_per_game          FLOAT,
        three_pa_per_game     FLOAT,
        fta_per_game          FLOAT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS games (
        game_id     INT AUTO_INCREMENT PRIMARY KEY,
        year        INT NOT NULL,
        round       VARCHAR(200),
        team_a_id   INT NOT NULL,
        team_b_id   INT NOT NULL,
        winner_id   INT NOT NULL,
        FOREIGN KEY (team_a_id) REFERENCES teams(team_id),
        FOREIGN KEY (team_b_id) REFERENCES teams(team_id),
        FOREIGN KEY (winner_id) REFERENCES teams(team_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sim_runs (
        sim_run_id   INT AUTO_INCREMENT PRIMARY KEY,
        year         INT NOT NULL,
        n_iterations INT NOT NULL,
        model_used   VARCHAR(100),
        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sim_results (
        result_id   INT AUTO_INCREMENT PRIMARY KEY,
        sim_run_id  INT NOT NULL,
        team_id     INT NOT NULL,
        rounds_won  INT NOT NULL,
        champion    BOOLEAN NOT NULL,
        FOREIGN KEY (sim_run_id) REFERENCES sim_runs(sim_run_id),
        FOREIGN KEY (team_id)    REFERENCES teams(team_id)
    )
    """
]
DROP_ORDER = ["sim_results", "sim_runs", "games", "teams"]

# Connect to SQL server
def get_server_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD
    )

# Connect to SQL database
def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# Initialize database with schema
def init_database():
    conn = get_server_connection()
    cursor = conn.cursor()

    # Create database if it doesn't exist
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")

    cursor.close()
    conn.close()

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Iterate through schema structure and execute
    for statement in SCHEMA:
        cursor.execute(statement)

    cursor.close()
    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' initialized with all tables.")

# Drop tables from database
def drop_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    # Iterate through table order to drop
    for table in DROP_ORDER:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"  Dropped table: {table}")

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    cursor.close()
    conn.close()
    print("All tables dropped.")
 
# Reset table to schema, removing all data
def rebuild_tables():
    drop_tables()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Iterate through schema structure
    for statement in SCHEMA:
        cursor.execute(statement)

    conn.commit()
    cursor.close()
    conn.close()
    print("All tables rebuilt successfully.")
 
# Clear all data from tables
def truncate_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    # Iterate through table order to truncate
    for table in DROP_ORDER:
        cursor.execute(f"TRUNCATE TABLE {table}")
        print(f"  Truncated table: {table}")

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    cursor.close()
    conn.close()
    print("All tables truncated.")

# Clear a specific year from games and teams
def delete_year(year):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM games WHERE year = %s", (year,))
    cursor.execute("DELETE FROM teams WHERE year = %s", (year,))

    conn.commit()
    cursor.close()
    conn.close()
 
# Clear simulation tables to reset with reloading data
def truncate_sim_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("TRUNCATE TABLE sim_results")
    cursor.execute("TRUNCATE TABLE sim_runs")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    conn.commit()
    cursor.close()
    conn.close()
    print("Sim tables truncated.")

# Reset full database
def reset_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("TRUNCATE TABLE sim_results")
    cursor.execute("TRUNCATE TABLE games")
    cursor.execute("TRUNCATE TABLE sim_runs")
    cursor.execute("TRUNCATE TABLE teams")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    
    conn.commit()
    cursor.close()
    conn.close()

# Reset simulation tables
def reset_sim_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("TRUNCATE TABLE sim_results")
    cursor.execute("TRUNCATE TABLE sim_runs")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    
    conn.commit()
    cursor.close()
    conn.close()

# Insert team data into SQL database
def insert_teams(data):
    # Set up SQL connection
    conn = get_db_connection()
    cursor = conn.cursor()
 
    # Prep SQL query
    query = """
        INSERT INTO teams (
            name, seed, year, adj_oe, adj_de, sos, win_rate, srs,
            possessions_per_game, ft_pct, tov_rate, orb_rate,
            fga_per_game, three_pa_per_game, fta_per_game
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    # Iterate through data columns to insert
    for _, row in data.iterrows():
        values = (
            row['team_name'], row['seed'], row['year'], row['off_eff'],
            row['def_eff'], row['SOS'], row['win_rate'], row['SRS'],
            row['pos_per_game'], row['ft_pct'], row['tov_rate'], row['orb_rate'],
            row['fga_per_game'], row['three_pa_per_game'], row['fta_per_game']
        )
        cursor.execute(query, values)

    conn.commit()
    cursor.close()
    conn.close()

# Update region from ESPN data
def update_region(name, region, year):
    # Set up SQL connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Prep SQL query
    query = """UPDATE teams SET region = %s WHERE name = %s AND year = %s"""

    # Iterate through data columns to insert
    values = (region, name, year)
    cursor.execute(query, values)

    conn.commit()
    cursor.close()
    conn.close()

# Find offensive/defensive averages per year
def get_averages(year):
    # Set up SQL connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Prep SQL query
    query = """SELECT AVG(adj_oe), AVG(adj_de) FROM teams WHERE year = %s"""

    # Execute query and return
    cursor.execute(query, (year,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

# Find teams per year
def get_teams(year):
    # Set up SQL connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Prep SQL query
    query = """SELECT * FROM teams WHERE year = %s"""

    # Execute query and return
    cursor.execute(query, (year,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

# Return a team's ID per year
def get_team_id(name, year):
    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)

    # Find team_id
    cursor.execute("SELECT team_id FROM teams WHERE name = %s AND year = %s", (name, year))

    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    # Return team or none
    return row[0] if row else None

# Insert game data into games table
def insert_game(year, round_name, team_a_id, team_b_id, winner_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Prep SQL query
    query = """
        INSERT INTO games (year, round, team_a_id, team_b_id, winner_id)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, (year, round_name, team_a_id, team_b_id, winner_id))

    conn.commit()
    cursor.close()
    conn.close()

# Insert run data per simulation ran
def insert_sim_run(year, n_iterations, model_used):
    # Set up SQL connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Prep SQL query
    query = """INSERT INTO sim_runs (year, n_iterations, model_used) VALUES (%s, %s, %s)"""

    # Execute query with values
    values = (year, n_iterations, model_used)
    cursor.execute(query, values)

    sim_run_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return sim_run_id

# Insert simulation results per sim_run_id
def insert_sim_results(sim_run_id, results):
    # Set up SQL connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Prep SQL query
    query = """INSERT INTO sim_results (sim_run_id, team_id, rounds_won, champion) VALUES (%s, %s, %s, %s)"""

    # Execute many queries with values
    values = [(sim_run_id, result['team_id'], result['rounds_won'], result['champion']) for result in results]
    cursor.executemany(query, values)

    # Commit and close
    conn.commit()
    cursor.close()
    conn.close()

# Grab all games with both team's stats attached
def get_games_with_stats(testing_years=None, year=None):
    conditions = []
    params = []

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
 
    # Prep the SQL query
    query = """
        SELECT
            g.game_id,
            g.year,
            g.round,
            -- Team A Stats
            ta.team_id     AS a_team_id,
            ta.name        AS a_name,
            ta.seed        AS a_seed,
            ta.adj_oe      AS a_oe,
            ta.adj_de      AS a_de,
            ta.sos         AS a_sos,
            ta.win_rate    AS a_win_rate,
            ta.srs         AS a_srs,
            ta.tov_rate    AS a_tov_rate,
            ta.orb_rate    AS a_orb_rate,
            ta.ft_pct      AS a_ft_pct,
            ta.possessions_per_game AS a_pos_per_game,
            ta.fga_per_game         AS a_fga_per_game,
            ta.three_pa_per_game    AS a_three_pa_per_game,
            ta.fta_per_game         AS a_fta_per_game,
            -- Team B Stats
            tb.team_id     AS b_team_id,
            tb.name        AS b_name,
            tb.seed        AS b_seed,
            tb.adj_oe      AS b_oe,
            tb.adj_de      AS b_de,
            tb.sos         AS b_sos,
            tb.win_rate    AS b_win_rate,
            tb.srs         AS b_srs,
            tb.tov_rate    AS b_tov_rate,
            tb.orb_rate    AS b_orb_rate,
            tb.ft_pct      AS b_ft_pct,
            tb.possessions_per_game AS b_pos_per_game,
            tb.fga_per_game         AS b_fga_per_game,
            tb.three_pa_per_game    AS b_three_pa_per_game,
            tb.fta_per_game         AS b_fta_per_game,
            -- Wining Team
            CASE WHEN g.winner_id = g.team_a_id THEN 1 ELSE 0 END AS team_a_won
        FROM games g
        JOIN teams ta ON ta.team_id = g.team_a_id
        JOIN teams tb ON tb.team_id = g.team_b_id
    """

    # Take out training years
    if testing_years:
        placeholders = ', '.join(['%s'] * len(testing_years))
        conditions.append(f"g.year NOT IN ({placeholders})")
        params.extend(testing_years)

    # Add single year in
    if year:
        conditions.append("g.year = %s")
        params.append(year)

    # If both are met, combine
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    # Execute final query
    cursor.execute(query, tuple(params))

    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result
