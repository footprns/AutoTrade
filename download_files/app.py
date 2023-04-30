import json
import requests
import datetime
import zipfile
import io
import pandas as pd
import time
import csv
import tempfile
import logging
import boto3

# Initialize the S3 client
s3 = boto3.client('s3')

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def upload_file(file_path, bucket_name, s3_key):
    file_path = file_path # Local path of the file to upload
    bucket_name = bucket_name # Name of the S3 bucket to upload to
    s3_key = s3_key # Key (path) of the file in the S3 bucket
    
    with open(file_path, 'rb') as file:
        s3.upload_fileobj(file, bucket_name, s3_key)
    
    return {
        'statusCode': 200,
        'body': 'File uploaded successfully'
    }


def lambda_handler(event, context):
    # Define the URL and file name pattern
    url = 'https://data.binance.vision/data/spot/daily/klines/LINKUSDT/1d/LINKUSDT-1d-{}.zip'
    filename_pattern = 'LINKUSDT-1d-{}.zip'

    # Define the date range to download
    # start_date = datetime.date(2022, 3, 1)
    start_date = datetime.date(2023, 3, 30)
    end_date = datetime.date(2023, 3, 31)
    delta = datetime.timedelta(days=1)
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Initialize an empty list to hold the DataFrames
    df_all = pd.DataFrame()

    # Download and read each file in the range
    while start_date <= end_date:
        # Generate the file URL and name for the current date
        date_str = start_date.strftime('%Y-%m-%d')
        url_curr = url.format(date_str, date_str)
        filename_curr = filename_pattern.format(date_str)

        # Send the HTTP GET request and save the content to a file-like object
        logger.info(f"Download from {url_curr}")
        r = requests.get(url_curr)
        while r.status_code != 200:
            time.sleep(1)
            logger.info('Download is in progress')
        with io.BytesIO(r.content) as f:
            # Unzip the file to a new directory
            with zipfile.ZipFile(f, 'r') as zip_ref:
                # zip_ref.extractall(date_str)
                zip_ref.extractall(temp_dir)

            # Read the CSV file into a DataFrame and append it to the list
            csv_file = temp_dir + '/' + filename_curr.replace('.zip', '.csv')
            # combine_csv(input_file=csv_file)
            df = pd.read_csv(csv_file, header=None, names=['Date Time', 'Open','High','Low','Close','Volume','Close time','Quote asset volume','Number of trades','Taker buy base asset volume','Taker buy quote asset volume','Ignore'])
            df_all = pd.concat([df_all, df], ignore_index=True)
            logger.info(f'Read file from {csv_file}')

        # Move to the next date
        start_date += delta

    # Write the combined DataFrame to a CSV file
    df_all['Date Time'] = pd.to_datetime(df_all['Date Time'].div(1000), unit='s').dt.tz_localize('UTC').dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    df_all['Adj Close'] = df_all['Close']
    df_all[['Date Time','Open','High','Low','Close','Volume','Adj Close']].to_csv(temp_dir + 'LINKUSDT-1d-all.csv', index=None)
    # print('Wrote file: LINKUSDT-1d-all.csv')
    # print(df_all)
    upload_file(file_path=temp_dir + 'LINKUSDT-1d-all.csv', bucket_name='imank-pyalgotrade', s3_key='LINKUSDT-1d-all.csv')

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world from download files",
            # "location": ip.text.replace("\n", "")
        }),
    }
