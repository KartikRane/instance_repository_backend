import io
import tarfile

import requests
from cflpconfig import PROBLEM_UID as CAP_PROBLEM_UID
from cflpconfig import CapacitatedFacilityLocationInstance
from config import PROBLEM_UID as UNCAP_PROBLEM_UID
from config import FacilityLocationInstance

from connector import Connector

API_KEY = "3456345-456-456"


def _process_line(linebytes: bytes) -> str:
    return linebytes.decode().strip().removesuffix(".")


def process_source_lib(
    base_url: str, lib_file: str, uncap_connector: Connector, cap_connector: Connector
):
    url = "".join([base_url, lib_file])
    resp = requests.get(url)
    assert resp.status_code == 200

    byte_io = io.BytesIO(resp.content)

    assert lib_file.endswith(".tgz") or lib_file.endswith(".tbz2")
    with tarfile.open(fileobj=byte_io) as tar:
        for node in tar:
            if (
                node.isfile()
                and not node.name.endswith(".opt")  # opt are opt sol files
                and not node.name.endswith(".lst")  # dir file list
                and not node.name.endswith("/go~")  # what
                and not node.name.endswith("README")  # what
                and not node.name.endswith(".bub")  # some solution files
                and not node.name.endswith(".c")
                and not node.name.endswith(".cpp")
                and not node.name.endswith(".h")
                and not node.name.endswith("capinfo.txt")  # explanations
                and not "capmst" in node.name  # wrong problem
            ):
                with tar.extractfile(node) as f:
                    lines: list[str] = [
                        _process_line(byteline) for byteline in f.readlines()
                    ]
                    if any(line.startswith("capacity ") for line in lines):
                        # part of a ORBLIBCAP-dataset from 1988
                        # -> computationally pointless and ignored
                        continue

                    lines = list(filter(None, lines))
                    instance_uid = (
                        lib_file.split(".")[0] + "/" + node.name.split(".")[0]
                    )
                    instance = parse_flp_instance(lines, instance_uid, url)
                    if isinstance(instance, CapacitatedFacilityLocationInstance):
                        connector = cap_connector
                    elif isinstance(instance, FacilityLocationInstance):
                        connector = uncap_connector
                    else:
                        raise TypeError(instance)

                    try:
                        info = connector.get_instance_info(instance_uid)
                    except requests.HTTPError as err:
                        if err.response.status_code != 404:
                            raise err
                    else:
                        continue

                    resp = connector.upload_instance(instance)


def _strtonum(s: str) -> int | float:
    return float(s) if "." in s else int(s)


def parse_orblibcap(lines: list[str]):
    capacities = []
    opening_costs = []
    demands = []
    distances = []

    # line 1: facilities, cities
    num_facilities, num_cities = [int(e) for e in lines[0].split()]
    # next lines: each facility capacity and opening cost
    for line in lines[1 : 1 + num_facilities]:
        cap, cost = [_strtonum(e) for e in line.split()]
        capacities.append(cap)
        opening_costs.append(cost)

    # next lines by spec: one line demand, next line distances
    # *but*: some orblibcap files do linebreaks in distance lines, so: join them and then chop it up
    remaining_contents = " ".join(lines[1 + num_facilities :]).split()

    # demand of city + city distance to each facility
    segment_length = 1 + num_facilities
    assert len(remaining_contents) == num_cities * segment_length
    for city_idx in range(num_cities):
        demand = _strtonum(remaining_contents[city_idx * segment_length])
        dist = [
            _strtonum(e)
            for e in remaining_contents[
                city_idx * segment_length + 1 : (city_idx + 1) * segment_length
            ]
        ]
        demands.append(demand)
        distances.append(dist)

    return num_facilities, num_cities, capacities, opening_costs, demands, distances


def parse_simple(lines: list[str]):
    opening_costs = []

    # line 1: facilities, cities
    num_facilities, num_cities, zero = [int(e) for e in lines[0].split()]
    distances: list[list[int | float]] = [[] for _ in range(num_cities)]
    assert zero == 0
    # next lines: facility id (starting with **ONE**, )
    for line in lines[1:]:
        numline = [_strtonum(e) for e in line.split()]
        opening_costs.append(numline[1])
        for city_distances, num in zip(distances, numline[2:]):
            city_distances.append(num)
    return num_facilities, num_cities, opening_costs, distances


def parse_flp_instance(
    lines: list[str], instance_uid: str, url: str
) -> FacilityLocationInstance | CapacitatedFacilityLocationInstance:
    if lines[0].startswith("FILE:"):
        lines = lines[1:]
    if len(lines[0].split()) == 2:
        format = "ORLIB-cap"
    elif len(lines[0].split()) == 3 and lines[0].split()[2] == "0":
        format = "Simple"
    else:
        format = "unknown"
    print(f"{instance_uid}: ", end="")
    print(format, end="")
    comment = ""
    if format == "ORLIB-cap":
        num_facilities, num_cities, capacities, opening_costs, demands, distances = (
            parse_orblibcap(lines)
        )

        if all(cap == 0 for cap in capacities) and all(
            demand == 0 for demand in demands
        ):
            is_capacitated = False
        elif all(cap == 0 for cap in capacities):
            comment += "All capacities are zero, but there are nonzero demands => assumed uncapacitated"
            is_capacitated = False
        elif all(demand == 0 for demand in demands):
            comment += "All demands are zero, but there are nonzero capacities => uncapactiated"
            is_capacitated = False
        else:
            is_capacitated = True
    elif format == "Simple":
        num_facilities, num_cities, opening_costs, distances = parse_simple(lines)
        is_capacitated = False
    else:
        print(f"\n{lines}")
        raise ValueError(f"did not recognize instance format for: {instance_uid}")
    if is_capacitated:
        assert len(capacities) == num_facilities
        assert len(demands) == num_cities
    assert len(opening_costs) == num_facilities
    assert len(distances) == num_cities
    assert all(len(dist) == num_facilities for dist in distances)

    is_integral = True
    is_integral &= all(o.is_integer() for o in opening_costs)
    is_integral &= all(d.is_integer() for cd in distances for d in cd)

    if is_capacitated:
        is_integral &= all(c.is_integer() for c in capacities)
        is_integral &= all(d.is_integer() for d in demands)
        print(" => capacitated instance")
        return CapacitatedFacilityLocationInstance(
            instance_uid=instance_uid,
            origin=url,
            comment=comment,
            num_cities=num_cities,
            num_facilities=num_facilities,
            is_integral=is_integral,
            capacities=capacities,
            opening_cost=opening_costs,
            path_cost=distances,
            demand=demands,
        )
    else:
        print(" => uncapacitated instance")
        return FacilityLocationInstance(
            instance_uid=instance_uid,
            origin=url,
            comment=comment,
            num_cities=num_cities,
            num_facilities=num_facilities,
            is_integral=is_integral,
            opening_cost=opening_costs,
            path_cost=distances,
        )


if __name__ == "__main__":
    # For the local example configuration

    base_url = "https://resources.mpi-inf.mpg.de/departments/d1/projects/benchmarks/UflLib/data/bench/"
    lib_files = [
        "BildeKrarup.tgz",
        "Chess.tgz",
        "Euklid.tgz",
        "FPP11.tgz",
        "FPP17.tgz",
        "GalvaoRaggi.tgz",
        "KoerkelGhosh-sym.tbz2",
        "KoerkelGhosh-asym.tbz2",
        "kmedian.tbz2",
        "CLSA.tgz",
        "CLSB.tgz",
        "CLSC.tgz",
        "M.tgz",
        "ORLIB.tgz",
        "PCodes.tgz",
        "Uniform.tgz",
    ]

    uncap_connector = Connector(
        base_url="http://127.0.0.1",
        problem_uid=UNCAP_PROBLEM_UID,
        api_key=API_KEY,
    )
    cap_connector = Connector(
        base_url="http://127.0.0.1",
        problem_uid=CAP_PROBLEM_UID,
        api_key=API_KEY,
    )
    for lib_file in lib_files:
        process_source_lib(base_url, lib_file, uncap_connector, cap_connector)
