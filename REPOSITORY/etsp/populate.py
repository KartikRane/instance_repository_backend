import gzip
import io
import tarfile

import requests
from config import PROBLEM_UID, EuclideanTravelingSalesmanInstance

from connector import Connector


def _strtonum(s: str) -> int | float:
    return float(s) if "." in s else int(s)


def extract_points(
    lines: list[str],
) -> tuple[list[tuple[float | int, float | int]] | None, str | None]:
    points = []
    comment = ""
    start_parsing = False
    for line in lines:
        if line.startswith("COMMENT:"):
            comment = line.removeprefix("COMMENT:").strip()
        if line.startswith("NODE_COORD_SECTION"):
            start_parsing = True
            continue
        if start_parsing:
            if line.startswith("EOF"):
                break
            if not line:
                continue
            point_data = line.split()
            if not len(point_data) == 3:
                print(f"error on line: {line}")
                raise ValueError("Instance is not 2d-coordinate based.")
            x = _strtonum(point_data[1])
            y = _strtonum(point_data[2])
            points.append((x, y))
    if not start_parsing:
        if any("EDGE_WEIGHT" in line for line in lines):
            # edge weight, not applicable
            return None, None

        for pline in lines:
            print(pline)
        raise ValueError("Instance is not coordinate based.")
    return points, comment


if __name__ == "__main__":
    url = "http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/ALL_tsp.tar.gz"
    libname = "TSPLIB95"
    resp = requests.get(url)
    assert resp.status_code == 200

    API_KEY = "3456345-456-456"

    connector = Connector(
        base_url="http://127.0.0.1",
        problem_uid=PROBLEM_UID,
        api_key=API_KEY,
    )

    byte_io = io.BytesIO(resp.content)
    with tarfile.open(fileobj=byte_io) as tar:
        for node in tar:
            if (
                node.isfile()
                and not node.name.endswith(".tour.gz")
                and not node.name.endswith(".problems.gz")
            ):
                with tar.extractfile(node) as gzfile:
                    instance_uid = f"{libname}/{node.name.split('.')[0]}"
                    print(f"{node.name} - {instance_uid}: ", end="")

                    f = gzip.GzipFile(fileobj=gzfile)
                    lines = [line.decode().strip() for line in f.readlines()]
                    points, comment = extract_points(lines)
                    if points and comment:
                        is_integral = all(isinstance(c, int) for p in points for c in p)
                        instance = EuclideanTravelingSalesmanInstance(
                            instance_uid=instance_uid,
                            origin=url,
                            comment=comment,
                            num_points=len(points),
                            is_integral=is_integral,
                            points=points,
                        )
                        try:
                            info = connector.get_instance_info(instance_uid)
                        except requests.HTTPError as err:
                            if err.response.status_code != 404:
                                raise err
                        else:
                            continue

                        resp = connector.upload_instance(instance)
                        print("added")
                    else:
                        print("no etsp instance, skipped")
