from datetime import datetime
from time import time, sleep

import pandas as pd
import sqlalchemy as sql
import sqlalchemy.exc as sql_exec
from common import logger, today
from db_config import engine_str, use_sqlite, SessionLocal

execute_retry = True
pool = sql.create_engine(engine_str, pool_size=10, max_overflow=5, pool_recycle=67, pool_timeout=30, echo=None)


def insert_data(table: sql.Table, dict_data, engine_address=None, multi=False, ignore=False, truncate=False,
                retry=1, wait_period=5, **kwargs):
    """
    This is used to insert the data in dict format into the table
    :param table: SQLAlchemy Table Object
    :param dict_data: Data to be inserted
    :param engine_address: Define a custom engine string. Use default if None provided.
    :param multi: Whether to use multi query or not
    :param ignore: Use Insert Ignore while insertion
    :param truncate: Truncate table before insertion
    :param retry: Insert Retry Number
    :param wait_period: Time in seconds for retry
    :return: None
    """
    st = time()
    # logger.debug(f'Data Insertion started for {table.name}')
    logger.info(f'Data Insertion started for {table.name}')
    # engine_con_str = engine_address if engine_address is not None else engine_str
    # engine = sql.create_engine(engine_con_str)
    ins = table.insert()
    if ignore:
        if use_sqlite:
            ignore_clause = 'IGNORE' if not use_sqlite else 'OR IGNORE'
            ins = table.insert().prefix_with(ignore_clause)
        else:
            # Considering Postgres
            from sqlalchemy.dialects.postgresql import insert
            # ins = table.insert().on_conflict_do_nothing()  # Not available
            ins = insert(table).on_conflict_do_nothing()

    with pool.connect() as conn:
        if truncate:
            conn.execute(f'TRUNCATE TABLE {table.name}')
        try:
            conn.execute(ins, dict_data, multi=multi)
        except sql_exec.OperationalError as e:
            if retry > 0:
                logger.info(f"Error for {table.name}: {e}")
                logger.info(f'Retrying to insert data in {table.name} after {wait_period} seconds')
                sleep(wait_period)
                insert_data(table=table, dict_data=dict_data, engine_address=engine_address, multi=multi, ignore=ignore,
                            truncate=truncate, retry=retry-1, wait_period=wait_period)
            else:
                logger.error(f"Error for {table.name} insertion: {e}", escalate=True)
        conn.close()

    # logger.debug(f"Data Inserted in {table.name} in: {time() - st} secs")
    logger.info(f"Data Inserted in {table.name} in: {time() - st} secs")


def insert_data_df(table, data: pd.DataFrame, truncate=False):
    conn = pool.connect()
    if truncate:
        conn.execute(f'TRUNCATE TABLE {table.name}')
    response = data.to_sql(table.name, con=conn, if_exists='append', index=False, method='multi')
    conn.close()
    return response


def execute_query(query, retry=2, wait_period=5, params=None):
    if params is None:
        params = {}

    short_query = query[:int(len(query)*0.25)] if type(query) is str else ''
    # logger.debug(f'Executing query...{short_query}...')

    try:
        with pool.connect() as conn:
            try:
                result = conn.execute(query, params)
            except:
                result = conn.execute(sql.text(query), params).mappings() #for login
            # conn.execute(ins, dict_data, multi=multi)
            conn.close()
    except sql_exec.OperationalError as e:
        if retry > 0:
            logger.info(f"Error for Query {short_query}: {e}")
            logger.info(f'Retrying to execute query {short_query} after {wait_period} seconds')
            sleep(wait_period)
            result = execute_query(query=query, retry=retry-1, wait_period=wait_period)
        else:
            logger.error(f"Error for Query {short_query}: {e}", escalate=True)

    # logger.debug(f"Time taken to execute query: {time() - st} secs")
    return result


def read_sql_df(query, params=None, commit=False):
    st = time()
    # logger.debug(f"Reading query..{query[:int(len(query)*0.25)]}...")
    logger.info(f"Reading query..{query[:int(len(query)*0.25)]}...")
    # engine = sql.create_engine(engine_str)
    conn = pool.connect()
    df = pd.read_sql(query, conn, params=params)
    if commit:
        conn.execute('commit')
    conn.close()
    # engine.dispose()
    # logger.debug(f'Data read in {time() - st} secs')
    logger.info(f'Data read in {time() - st} secs')
    return df


def calculate_table_data(df):
    df1 = df.copy()
    live = (df1['combined_premium'].iloc[-1]).round(2)
    max_straddle = (df1['combined_premium'].max()).round(2)
    min_straddle = (df1['combined_premium'].min()).round(2)
    live_min = (live - min_straddle).round(2)
    max_live = (max_straddle - live).round(2)
    ret_dict = [{
        'Live': live,
        'Live-Min': live_min,
        'Max-Live': max_live,
        'Max': max_straddle,
        'Min': min_straddle
    }]
    logger.info(f'\nret_dict is {ret_dict}')
    # ret_df = pd.DataFrame.from_dict(ret_dict)
    # dict_to_json = [{i:ret_dict[i]} for i in ret_dict]
    # logger.info(f'\n dict_to_json is {dict_to_json}')
    return ret_dict


class DBHandler:

    """
    Meant to handle Signal related stuff only.
    """

    @classmethod
    def build_users_params(cls, users: list):
        users_in = {f"users_{_i}": _u for _i, _u in enumerate(users)}
        params_in = ",".join([f"%({i})s" for i in users_in.keys()])
        return users_in, params_in


    @classmethod
    def AddNewUser(cls, params):
        query = sql.text("""
            INSERT INTO users (contactnumber, username, email, pwd, dob, role, ipaddress, active, eventname, eventdate, eventlocation)
            VALUES (:contactnumber, :username, :email, :pwd, :dob, :role, :ipaddress, :active, :eventname, :eventdate, :eventlocation)
            RETURNING id;
        """)
        return execute_query(query, params=params)

    @classmethod
    def get_user_data(cls, contactnumber):
        query = sql.text('''SELECT * FROM users WHERE contactnumber = :contactnumber''')
        return execute_query(query, params={"contactnumber": contactnumber}).fetchone()


    @classmethod
    def delete_user(cls, contactnumber):
        query = sql.text('''delete from users where contactnumber = :contactnumber;''')
        return execute_query(query, params={"contactnumber": contactnumber, "active" : False})

    @classmethod
    def get_allusers(cls):
        query = '''select contactnumber, username, email, dob, role, eventname, eventlocation, eventdate, created_at as registrationtime from users'''
        return execute_query(query).fetchall()

    @classmethod
    def update_user_info(cls, update_values, contactnumber):
        set_clause = ", ".join([f"{key} = :{key}" for key in update_values.keys()])
        query = sql.text(f"UPDATE users SET {set_clause} WHERE contactnumber = :contactnumber;")

        update_values['contactnumber'] = contactnumber

        return execute_query(query, params=update_values)


    @classmethod
    def verifyuser(cls, username):
        query = sql.text("select id from users where contactnumber = :username")
        return execute_query(query, params={"username": username}).fetchone()[0]

    @classmethod
    def create_newevent(cls, event):
        query = sql.text("""
            INSERT INTO events (title, description, location, datetime_from, datetime_to, max_attendees, organizer_id)
            VALUES (:title, :description, :location, :datetime_from, :datetime_to, :max_attendees, :organizer_id)
            RETURNING id;
        """)

        return execute_query(query, params={  # Pass query directly
            "title": event.title,
            "description": event.description,
            "location": event.location,
            "datetime_from": event.datetime_from,
            "datetime_to": event.datetime_to,
            "max_attendees": event.max_attendees,  # Ensure this field exists
            "organizer_id": event.userid
        }).fetchone()

    @classmethod
    def getallevents(cls):
        query = sql.text("select * from events")
        return execute_query(query)

    @classmethod
    def update_event_details(cls, eventinfo, eventid):
        set_clause = ", ".join([f"{key} = :{key}" for key in eventinfo.keys()])
        query = sql.text(f"UPDATE event SET {set_clause} WHERE id = :id")
        return execute_query(query, params={"id": eventid})

    @classmethod
    def delete_event(cls, eventid, userid):
        query = sql.text('''delete from event where id = :eventid and organizer_id = :userid;''')
        return execute_query(query, params={"eventid": eventid, "userid" : userid})




























