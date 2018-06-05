from datetime import datetime, date, timedelta
from pecan import conf

import json
import boto3


s3 = boto3.client('s3')
athena = boto3.client('athena')

query_tmpl = '''
    SELECT
        *
    FROM
        history
    WHERE
        token = '%(token)s'
    AND
        year = %(year)d
    AND
        month = %(month)d
    AND
        day = %(day)d
'''

output_tmpl = 's3://%(bucket)s/rollups/%(token)s/%(year)d/%(month)d/%(day)d'


def rollup_day(token, day, force=False):
    query = query_tmpl % dict(
        token=token,
        year=day.year,
        month=day.month,
        day=day.day
    )

    output_location = output_tmpl % dict(
        bucket=conf.bucket,
        token=token,
        year=day.year,
        month=day.month,
        day=day.day
    )

    if force:
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
                response = s3.delete_object(
                    Bucket=conf.bucket,
                    Key=key['Key']
                )

    # generate our rollup
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': 'locations'
        },
        ResultConfiguration={
            'OutputLocation': output_location
        }
    )


def daily_rollup(event, context):
    '''
    This function will be called at one minute after midnight UTC on a daily
    basis. It will run the rollup operation for the prior day.
    '''

    today = datetime.utcnow()
    yesterday = today - timedelta(days=1)

    for token in conf['tokens']:
        rollup_day(token, yesterday)
