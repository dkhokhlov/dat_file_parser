import click
import pygrok as pg
import copy
import json
from dotted_dict import DottedDict
import datetime as dt

APP_NAME = 'dat_file_parser'
__version__ = '1.0'

doc_t = {
    "Wafer ID": "",
    "Time": "",
    "System Parameters": {
        "Voltage": {
            "Value": 0.0,
            "Units": ""
        },
        "Humidity": {
            "Value": 0.0,
            "Units": ""
        }
    },
    "Instruments": [
        #  instrument_t
    ],
    "Measurements": {
        # "1000": [
        #     {
        #         "Instrument ID": 1,
        #         "VOLTAGE": 1.28,
        #         "FREQUENCY": 125441,
        #         "IMPEDANCE": 574.12
        #     },
        #     {
        #         "Instrument ID": 2,
        #         "VOLTAGE": 0.6,
        #         "RESISTANCE": 575.16
        #     }
        # ],
    }
}

instrument_t = {
    "ID": 0,
    "Vendor": "",
    "Type": "",
    "Model": "",
    "Serial": "",
    "Quantities": [
        # quantity_t
    ]
}

quantity_t = {
    "Name": "",
    "Units": ""
}


def match(grok_pattern, str, must_match=True):
    m = pg.Grok(grok_pattern).match(str)
    if not m and must_match:
        raise click.ClickException(f"Match failed: '{grok_pattern}' => '{str}'")
    return DottedDict(m)


def clone(doc_t):
    return copy.deepcopy(doc_t)

def num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)


def parse_dat_file(file):
    """
    Returns: JSON doc
    """
    doc = clone(doc_t)
    port_inst = {}
    s = file.readline().strip()
    m = match("VOLTAGE %{NUMBER:value} %{WORD:units}", s)
    doc['System Parameters']['Voltage'] = {"Value": float(m.value), "Units": m.units}
    s = file.readline().strip()
    m = match("HUMIDITY %{NUMBER:value}\%", s)
    doc['System Parameters']['Humidity'] = {"Value": float(m.value), "Units": "%"}
    #
    # instruments
    #
    s = file.readline().strip()
    id = 1
    instruments = []
    while not match("WAFER %{NUMBER:wafer}", s, must_match=False):
        inst = clone(instrument_t)
        m = match("%{WORD:vendor} %{WORD:type} %{WORD:model} %{USERNAME:serial}", s)
        inst['ID'] = id
        inst['Vendor'] = m.vendor
        inst['Type'] = m.type
        inst['Model'] = m.model
        inst['Serial'] = m.serial
        s = file.readline().strip()
        m = match("CONNECTION> COM PORT %{NUMBER:port:int}", s)
        port = m.port
        s = file.readline().strip()
        m = match("SCHEME>(?<scheme>.+)", s)
        quantities = []
        qs = m.scheme.split(',')
        for s in  qs:
            m = match("(?<Name>.+) \(%{WORD:Units}\)", s.strip())
            quantities.append(m)
        inst["Quantities"] = quantities
        instruments.append(inst)
        port_inst[port] = inst
        id += 1
        s = file.readline().strip()
    doc["Instruments"] = instruments
    m = match("WAFER %{NUMBER:wafer}", s)
    doc["Wafer ID"] = m.wafer
    s = file.readline().strip()
    m = match("TIME %{NUMBER:epoch_time}", s)
    doc["Time"] = dt.datetime.utcfromtimestamp(int(m.epoch_time)).isoformat()
    #
    # measurements
    #
    s = file.readline().strip()
    measurements = {}
    while s:
        m = match("%{NUMBER:seq},%{NUMBER:id},%{NUMBER:port:int},(?<values>.+)", s)
        msl = measurements.get(m.id, [])
        msl.append(m)
        measurements[m.id] = msl
        s = file.readline().strip()
    # resolve measurements
    for id, msl in measurements.items():
        new_msl = []
        for ms in msl:
            inst = port_inst[ms.port]
            names = ["Instrument ID"] + [it.Name for it in inst["Quantities"]]
            values = [inst["ID"]] + [num(it) for it in  ms.values.split(",")]
            new_ms = dict(zip(names, values))
            new_msl.append(new_ms)
        measurements[id] = new_msl
    doc['Measurements'] = measurements
    return doc


# ############################################################### CLI

@click.command()
@click.version_option(version=__version__, prog_name=APP_NAME)
@click.option('--in', 'in_file', help='Input file. Default: <stdin>', default="-",
              type=click.File(mode='r'))
@click.option('--out', 'out_file', help='Output JSON file. Default: <stdout>', default="-",
              type=click.File(mode='w'))
def main(in_file, out_file):
    """ DAT file parser: parses DAT files produced by Fab metrology Probers, outputs parsed data in JSON fomat."""
    doc = parse_dat_file(in_file)
    json.dump(doc, out_file, indent=4)


if __name__ == '__main__':
    main(prog_name=APP_NAME)
