import io
import tarfile
from tarfile import TarInfo

import requests
from config import PROBLEM_UID, FacilityLocationInstance

from connector import Connector


def load_source_lib(base_url, lib_file):
    url = "".join([base_url, lib_file])
    resp = requests.get(url)
    assert resp.status_code == 200

    byte_io = io.BytesIO(resp.content)
    if lib_file.endswith(".tgz") or lib_file.endswith(".tbz2"):
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
                ):
                    with tar.extractfile(node) as f:
                        lines = [line.decode().strip() for line in f.readlines()]
                        lines = [line for line in lines if line]
                        lines = [
                            line[:-1] if line.endswith(".") else line for line in lines
                        ]
                        parse_flp_instance(lines, node, url)

    else:
        raise ValueError(f"unsupported file type {lib_file}")


def _strtonum(s: str) -> int | float:
    return int(s) if float(s).is_integer() else float(s)


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

    for upper, lower in zip(
        lines[1 + num_facilities :: 2], lines[1 + num_facilities + 1 :: 2]
    ):
        demand = _strtonum(upper)
        dist = [_strtonum(e) for e in lower.split()]
        demands.append(demand)
        distances.append(dist)
    assert len(lines) == 1 + num_facilities + 2 * num_cities
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


def parse_flp_instance(lines: list[str], node: TarInfo, url: str):
    if lines[0].startswith("FILE:"):
        lines = lines[1:]
    if len(lines[0].split()) == 2:
        format = "ORLIB-cap"
    elif len(lines[0].split()) == 3 and lines[0].split()[2] == "0":
        format = "Simple"
    else:
        format = "unknown"
    print(f"{node.name}:", end="")
    print(format)
    if format == "ORLIB-cap":
        num_facilities, num_cities, capacities, opening_costs, demands, distances = (
            parse_orblibcap(lines)
        )
        is_capacitated = True
        if all(cap == 0 for cap in capacities) or all(
            demand == 0 for demand in demands
        ):
            is_capacitated = False
        else:
            is_capacitated = True
    elif format == "Simple":
        num_facilities, num_cities, opening_costs, distances = parse_simple(lines)
        is_capacitated = False
    else:
        print(lines)
        raise ValueError(f"did not recognize instance format for: {node.name}")
    if is_capacitated:
        assert len(capacities) == num_facilities
        assert len(demands) == num_cities
    assert len(opening_costs) == num_facilities
    assert len(distances) == num_cities
    assert all(len(dist) == num_facilities for dist in distances)

    if (
        (is_capacitated and any(isinstance(c, float) for c in capacities))
        or (is_capacitated and any(isinstance(d, float) for d in demands))
        or any(isinstance(o, float) for o in opening_costs)
        or any(isinstance(d, float) for cd in distances for d in cd)
    ):
        is_integral = False
    else:
        is_integral = True

    if is_capacitated:
        pass
    else:
        return FacilityLocationInstance(
            instance_uid=node.name,
            origin=url,
            num_cities=num_cities,
            num_facilities=num_facilities,
            is_integral=is_integral,
            opening_cost=opening_costs,
            path_cost=distances,
        )
    raise ValueError()


if __name__ == "__main__":
    # For the local example configuration
    connector = Connector(
        base_url="http://127.0.0.1", problem_uid=PROBLEM_UID, api_key=None
    )

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
    for lib_file in lib_files:
        load_source_lib(base_url, lib_file)
