#!/usr/bin/python3

import re

KMS_PER_MILE = 1.60934

def get_time_str(hours, mins, secs):
    if hours > 0:
        time_str = '%02d:%02d:%05.2f' % (hours, mins, secs)
    else:
        time_str = '%02d:%05.2f' % (mins, secs)

    return time_str

def get_total_sec(hours, mins, secs):
    return hours * 60 * 60 + mins * 60 + secs

def break_time(total_sec):
    hours = int( total_sec / (60 * 60) )
    total_sec -= (hours * 60 * 60)
    mins = int( total_sec / 60 )
    secs = total_sec - (mins * 60)

    return (hours, mins, secs)

def get_avg_unit_time(dist, total_sec):
    return break_time(total_sec / float(dist))

def get_input(prompt, regex):
    result = None
    while result is None:
        input_str = input('%s: ' % (prompt))
        match = re.match(regex, input_str)
        if match:
            result = input_str
        else:
            print('Invalid response.')

    return result

def get_time():
    input_str = get_input('Enter total time', r'^(\d{1,2}\:)?(\d{1,2}\:)?\d+(\.\d+)?$')
    result = None
    
    if input_str:
        chunks = input_str.split(':')

        secs = float(chunks[-1])
        mins = int(chunks[-2]) if len(chunks) >= 2 else 0
        hours = int(chunks[-3]) if len(chunks) >= 3 else 0
        result = (hours, mins, secs)

    return result

def get_avg_speed(dist, total_sec):
    return ( dist / float(total_sec) ) * 60 * 60

def to_kms(miles):
    return miles * KMS_PER_MILE

def get_miles():
    input_str = get_input('Enter total miles', r'\d+(\.\d+)?')
    result = None

    if input_str:
        result = float(input_str)

    return result

def main():
    try:
        while True:
            total_sec = get_total_sec( *get_time() )
            miles = get_miles()
            kms = to_kms(miles)

            avg_mile_time = get_avg_unit_time(miles, total_sec)
            avg_km_time = get_avg_unit_time(kms, total_sec)

            print('')
            print('Total time: %s' % ( get_time_str(*break_time(total_sec)) ))
            print('Total Miles: %0.2f' % (miles))
            print('Total Kms: %0.2f' % (kms))
            print('Avg Mile Time: %s' % ( get_time_str(*avg_mile_time) ))
            print('Avg Km Time: %s' % ( get_time_str(*avg_km_time) ))
            print('Avg Mph: %0.2f' % ( get_avg_speed(miles, total_sec) ))
            print('Avg Kmph: %0.2f' % ( get_avg_speed(kms, total_sec) ))
            print('-' * 20)
            print('')
            
    except EOFError:
        print('\nBye!')

main()
