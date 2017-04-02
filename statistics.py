from datetime import datetime as dt

import sqlite3

from const import database_path

import argparse

from server import CLIENT_PREFIX


class LoadStats:

    connection = None
    cursor = None

    def __init__(self, name, desc, data):
        self.name = name
        self.desc = desc
        self.data = data

    def calculate_average_data(self, mean_time):

        def _get_time_diff(index):
            row = self.data[index]
            next_row = self.data[index + 1]
            time_diff = next_row[0] - row[0]
            return time_diff

        mean_data = []
        mean_data_index = 0

        real_data_index = 0
        max_row_index = len(self.data) - 1
        while real_data_index <= max_row_index:
            row = list(self.data[real_data_index])
            mean_data.append(row.copy())

            try:
                time_diff = _get_time_diff(real_data_index)
            except IndexError:
                return mean_data

            if time_diff < mean_time:

                num_of_sum = 0
                while time_diff < mean_time:
                    try:
                        time_diff += _get_time_diff(real_data_index)
                    except IndexError:
                        return mean_data[:-1]  # discard not finished batch and return

                    num_of_sum += 1
                    next_row = self.data[real_data_index+1]
                    real_data_index += 1
                    for index, d in enumerate(next_row):
                        mean_data[mean_data_index][index] += d

                mean_data[mean_data_index] = [d / (num_of_sum + 1) for d in mean_data[mean_data_index]]
                mean_data_index += 1
                real_data_index += 1  # take next batch of samples
            else:
                real_data_index += 1

        return mean_data

    def print(self, data, history_size):
        title = 'TABLE {} -> {} last records'.format(self.name, history_size if history_size is not None else 'all')
        columns = ''.join('{0: <25}'.format(column_name) for column_name in self.desc)

        body = '\n'.join(dt.fromtimestamp(row[0]).strftime('%Y-%m-%d %H:%M:%S' + ' '*11
                                                           + ''.join(['{0: <20.2f}'.format(d) for d in row[1:]]))
                         for row in data[:history_size])
        return '{}\n{}\n{}'.format(title, columns, body)


def parse_args():

    parser = argparse.ArgumentParser(description='Reads load statistics of clients from database',
                                     prog='Statistics reader')

    parser.add_argument('--show', '-s',
                        help='Shows clients ips for which statistics are saved.',
                        nargs='*',
                        required=True)

    parser.add_argument('--history-size', '-hs',
                        help='Limits output of program to given number of samples.',
                        type=int)

    parser.add_argument('--average-time', '-mt',
                        help='Averages samples in given average-time in [s].',
                        type=int)

    return parser.parse_args()


def create_stats(all_tables, show_tables):
    stats = []
    for table in all_tables:
        for show_table in show_tables:
            if table.upper().find(show_table.upper()) != -1:
                cursor.execute('SELECT * FROM {} '.format(table))
                table_body = cursor.fetchall()

                desc = [d[0] for d in [desc for desc in cursor.description]]
                stats.append(LoadStats(table, desc, table_body))

    return stats


if __name__ == '__main__':
    args = parse_args()
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = [row_tuple[0] for row_tuple in cursor.fetchall() if row_tuple[0].startswith(CLIENT_PREFIX)]

    if args.show == []:
        print(tables)

    else:
        stats = create_stats(tables, args.show)
        for stat in stats:
            data = stat.calculate_average_data(args.average_time) if args.average_time else stat.data
            print(stat.print(data, args.history_size))
