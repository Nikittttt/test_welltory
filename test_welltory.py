from glob import glob
import json
from itertools import chain

dict_types = {'str': ['str'],
              'string': ['str'],
              'integer': ['int'],
              'int': ['int'],
              'number': ['int', 'float'],
              'object': ['object']}


def rec_type(event, schema):
    result = ''
    for i, j in schema.items():
        if 'type' in j and type(j['type']) is str and list(j.keys()) == ['type']:
            if type(event[i]).__name__ in j['type']:
                continue
            else:
                result += f"\n\tВ файле тип значения {i} равен {type(event[i]).__name__}, а по схеме ожидался {j[
                    'type']}"
        elif 'type' in j and type(j['type']) is list and list(j.keys()) == ['type']:
            if type(event[i]).__name__ in j['type']:
                continue
            else:
                result += f"\n\tВ файле тип значения {i} равен {type(event[i]).__name__}, а по схеме ожидался один из {
                j['type']}"
        elif 'type' in j and j['type'] == 'array':
            item = j['items']
            if type(item['type']) != list:
                item['type'] = [item['type']]
            for iter_i in range(len(event[i])):
                iter_ = event[i][iter_i]
                item['type'] = list(map(lambda x: dict_types[x], item['type']))
                item['type'] = list(chain(*item['type']))
                if type(iter_) != dict:
                    if type(iter_).__name__ in item['type']:
                        continue
                    else:
                        result += f"\n\t\tВ файле тип значения {i} в списке под номером {iter_} " \
                            f"равен {type(iter_).__name__}, а по схеме ожидался один из {item['type']}"
                elif 'object' in item:
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
    if not data:
        out_ += f'\nФайл {name} оказался пуст'
        continue
    if data['data']:
        if f'./schema\\{data["event"]}.schema' not in glob('./schema/*'):
            out_ += f'\nВ файле {name} упомянута схема {data["event"]} которой не существует'
            continue
        with open(f'./schema/{data["event"]}.schema', "r") as read_file_schema:
            data_schema = json.load(read_file_schema)
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
