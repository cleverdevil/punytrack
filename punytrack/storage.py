from dateutil.parser import parse
from datetime import datetime, timedelta
from pecan import conf
from io import StringIO

import boto3
import json
import csv


s3 = boto3.client('s3')


def normalize(location):
    timestamp = parse(location['properties']['timestamp'])

    return {
        'timestamp': location['properties']['timestamp'],
        'year': timestamp.year,
        'month': timestamp.month,
        'day': timestamp.day,
        'hour': timestamp.hour,
        'minute': timestamp.minute,

        'x': location['geometry']['coordinates'][0],
        'y': location['geometry']['coordinates'][1],
        'altitude': location['properties']['altitude'],

        'motion': location['properties']['motion'],
        'speed': location['properties']['speed'],

        'battery_state': location['properties']['battery_state'],
        'battery_level': location['properties']['battery_level'],

        'wifi': location['properties']['wifi']
    }


def store(token, payload):
    # validate
    if token not in conf.tokens:
        return False

    # normalize all location data
    locations = []
    for location in payload.get('locations', []):
        locations.append(normalize(location))

    # determine the current location
    if 'current' in payload:
        current = normalize(payload['current'])
    else:
        current = locations[-1]

    # store the current location
    key = 'current/token=%s/current.json' % token
    s3.put_object(
        Bucket=conf.bucket,
        Key=key,
        Body=json.dumps(current)
    )

    # store the normalized payload
    body = '\n'.join([json.dumps(location) for location in locations])
    key = 'history/token=%s/%s.json' % (token, datetime.utcnow().isoformat())
    s3.put_object(
        Bucket=conf.bucket,
        Key=key,
        Body=body
    )

    return True


def get_current(token):
    try:
        response = s3.get_object(
            Bucket=conf.bucket,
            Key='current/token=%s/current.json' % token
        )
    except:
        return None
    else:
        return json.loads(response['Body'].read())


def get_day(token, day):
    response = s3.list_objects_v2(
        Bucket=conf.bucket,
        Prefix='rollups/%(token)s/%(year)d/%(month)d/%(day)d' % dict(
            token=token,
            year=day.year,
            month=day.month,
            day=day.day
        )
    )
    if 'Contents' in response:
        for key in response['Contents']:
            if key['Key'].endswith('.csv'):
                response = s3.get_object(
                    Bucket=conf.bucket,
                    Key=key['Key']
                )
                reader = csv.DictReader(
                    StringIO(
                        response['Body'].read().decode('utf-8')
                    )
                )
                return [{
                    'timestamp': line['timestamp'],
                    'year': int(line['year']),
                    'month': int(line['month']),
                    'day': int(line['day']),
                    'hour': int(line['hour']),
                    'minute': int(line['minute']),
                    'battery_level': float(line['battery_level']),
                    'battery_state': line['battery_state'],
                    'motion': line['motion'],
                    'wifi': line['wifi'],
                    'x': float(line['x']),
                    'y': float(line['y']),
                    'altitude': int(line['altitude']),
                    'speed': line['speed']
                } for line in reader]

    return []


def get_range(token, start, end):
    data = []
    for i in range((end - start).days):
        data += get_day(token, start.date() + timedelta(days=i))

    start = start.isoformat()
    end = end.isoformat()

    return [
        point for point in data
        if
            point['timestamp'] >= start
        and
            point['timestamp'] <= end
    ]
