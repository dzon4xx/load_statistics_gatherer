from statistics import LoadStats


def test_should_return_same_data_when_average_time_equal_time_diff():
    # GIVEN
    data = [[6, 4, 1],
            [7, 0, 1],
            [8, 0, 1],
            [9, 0, 1]]

    average_time = 1
    # WHEN
    load_stats = LoadStats(name='test',
                           desc=['time', 'b', 'c'],
                           data=data)
    average_data = load_stats.calculate_average_data(average_time)
    # THEN
    print(average_data)
    assert average_data == data


def test_should_average_data_when_average_time_2_and_4_samples():
    # GIVEN
    data = [(6, 4, 1),
            (7, 0, 1),
            (8, 3, 1),
            (9, 0, 1)]

    average_time = 2
    # WHEN
    load_stats = LoadStats(name='test',
                           desc=['time', 'b', 'c'],
                           data=data)
    average_data = load_stats.calculate_average_data(average_time)
    # THEN
    print(average_data)
    assert average_data == [[6.5, 2, 1], [8.5, 1.5, 1]]


def test_should_discard_left_samples():
    # GIVEN
    data = [[5, 4, 1],
            [6, 0, 1],
            [7, 3, 1],
            [8, 0, 1],
            [9, 0, 1]]

    average_time = 3  # One sample should be discarded
    # WHEN
    load_stats = LoadStats(name='test',
                           desc=['time', 'b', 'c'],
                           data=data)
    average_data = load_stats.calculate_average_data(average_time)
    # THEN
    print(average_data)
    assert average_data == [[(5+6+7)/3, (4+3)/3, (1+1+1)/3]]


def test_should_return_empty_list_if_average_time_longer_than_history():
    # GIVEN
    data = [[5, 4, 1],
            [6, 0, 1],
            [7, 3, 1],
            [8, 0, 1],
            [9, 0, 1]]

    average_time = len(data) + 1  # One sample should be discarded
    # WHEN
    load_stats = LoadStats(name='test',
                           desc=['time', 'b', 'c'],
                           data=data)
    average_data = load_stats.calculate_average_data(average_time)
    # THEN
    print(average_data)
    assert average_data == []


