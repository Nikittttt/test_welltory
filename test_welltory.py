from glob import glob
import json
from itertools import chain

# Словарб для приведения строк к python-овскому виду
dict_types = {'str': ['str'],
              'string': ['str'],
              'integer': ['int'],
              'int': ['int'],
              'number': ['int', 'float'],
              'object': ['object']}


def rec_type(event, schema):
    result = ''

    # Проходимся по всем переданным схемам
    for i, j in schema.items():

        # Действие в случае если у нас есть только тип, а значит это один из стандартных значений на подобии строки или числа
        if 'type' in j and type(j['type']) is str and list(j.keys()) == ['type']:
            if type(event[i]).__name__ in j['type']:
                continue
            else:
                result += f"\n\tВ файле тип значения {i} равен {type(event[i]).__name__}" \
                    f", а по схеме ожидался {j['type']}"

        # Действие в случае если у нас есть только тип и он список, а значит это аналог предыдущего, но с несколькими возможными типами
        elif 'type' in j and type(j['type']) is list and list(j.keys()) == ['type']:
            if type(event[i]).__name__ in j['type']:
                continue
            else:
                result += f"\n\tВ файле тип значения {i} равен {type(event[i]).__name__}" \
                    f", а по схеме ожидался один из {j['type']}"

        # Действие в случае если у нас array, а значит список из нескольких значений
        elif 'type' in j and j['type'] == 'array':
            item = j['items']
            if type(item['type']) != list:
                item['type'] = [item['type']]

            # Проходимся по всем элементам списка
            for iter_i in range(len(event[i])):
                iter_ = event[i][iter_i]
                item['type'] = list(map(lambda x: dict_types[x], item['type']))
                item['type'] = list(chain(*item['type']))

                # Действие если у нас стандартный тип(не объект)
                if type(iter_) != dict:
                    if type(iter_).__name__ in item['type']:
                        continue
                    else:
                        result += f"\n\t\tВ файле тип значения {i} в списке под номером {iter_} " \
                            f"равен {type(iter_).__name__}, а по схеме ожидался один из {item['type']}"

                # Действия нам попался объект
                elif 'object' in item:

                    # Если совпадают ключи, то вызывает рекурсивно эту функцию, иначе сообщаем о несовпадении и всё равно вызываем
                    if item['required'] == list(iter_.keys()):
                        result_ = rec_type(iter_, item['properties'])
                        if result_:
                            result += result_
                        else:
                            result += '\n\tНичего'
                    else:
                        r_set = set(item['required'])
                        d_set = set(iter_.keys())
                        t_set = r_set
                        r_set -= d_set
                        d_set -= t_set
                        if r_set:
                            result += f'\nВ привязанной схеме есть данные {r_set} которых нет в файле'
                        if d_set:
                            result += f'\nВ файле есть данные {d_set} которых нет в привязанной схеме'
                            if not r_set:
                                result_ = rec_type(iter_, item['properties'])
                                if result_:
                                    result += result_
                                else:
                                    result += '\n\tНичего'
        elif 'type' in j and j['type'] == 'object':
            item = j['type']
            iter_ = event[i]

            # Если совпадают ключи, то вызывает рекурсивно эту функцию, иначе сообщаем о несовпадении и всё равно вызываем
            if item['required'] == list(iter_.keys()):
                result_ = rec_type(iter_, item['properties'])
                if result_:
                    result += result_
                else:
                    result += '\n\tНичего'
            else:
                r_set = set(item['required'])
                d_set = set(iter_.keys())
                t_set = r_set
                r_set -= d_set
                d_set -= t_set
                if r_set:
                    result += f'\nВ привязанной схеме есть данные {r_set} которых нет в файле'
                if d_set:
                    result += f'\nВ файле есть данные {d_set} которых нет в привязанной схеме'
                    if not r_set:
                        result_ = rec_type(iter_, item['properties'])
                        if result_:
                            result += result_
                        else:
                            result += '\n\tНичего'
    return result


out_ = ''
for i in glob('./event/*'):
    with open(i, "r") as read_file:
        data = json.load(read_file)
    name = i.replace('./event\\', '').replace('.json', '')

    # Проверка файла на отсутствие пустоты
    if not data:
        out_ += f'\nФайл {name} оказался пуст'
        continue

    if data['data']:

        # Проверка на наличие упомянутой схемы
        if f'./schema\\{data["event"]}.schema' not in glob('./schema/*'):
            out_ += f'\nВ файле {name} упомянута схема {data["event"]} которой не существует'
            continue
        with open(f'./schema/{data["event"]}.schema', "r") as read_file_schema:
            data_schema = json.load(read_file_schema)

        # Если совпадают ключи, то вызывает рекурсивно эту функцию, иначе сообщаем о несовпадении и всё равно вызываем
        if data_schema['required'] == list(data['data'].keys()):
            out_ += f'\nВ файле {name} привязанному к {data["event"]} обнаружено:'
            result = rec_type(data['data'], data_schema['properties'])
            if result:
                out_ += result
            else:
                out_ += '\n\tНичего'
        else:
            r_set = set(data_schema['required'])
            d_set = set(data['data'].keys())
            t_set = r_set
            r_set -= d_set
            d_set -= t_set
            if r_set:
                out_ += f'\nВ схеме {data["event"]} есть данные {r_set} которых нет в файле {name}'
            if d_set:
                out_ += f'\nВ файле {name} есть данные {d_set} которых нет в схеме {data["event"]}'
                if not r_set:
                    out_ += f'\nВ файле {name} привязанному к {data["event"]} обнаружено:'
                    result = rec_type(data['data'], data_schema['properties'])
                    if result:
                        out_ += result
                    else:
                        out_ += '\n\tНичего'

    else:
        out_ += f'\nВ файле {name} нет данных в data'


with open('log_welltory.txt', "w") as log:
    log.write(out_)
