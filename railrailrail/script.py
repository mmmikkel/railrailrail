"""Routes every pair of stations on one stage of the network, into all_routes.csv, for Metrograf.

    uv run python railrailrail/script.py config/network_ccl_6.toml

The network file is the stage open in the month routed (config/ holds copies of config_examples/).
"""
import csv
import json
import sys
from railrailrail.railgraph import RailGraph

if len(sys.argv) != 2:
    sys.exit(__doc__)

# Setup
rail_graph = RailGraph.from_file(
    sys.argv[1],
    "config/station_coordinates.csv"
)

# Get all valid station codes (exclude pseudo station codes)
stations = [
    code for code, station in rail_graph.station_code_to_station.items()
    if not station.has_pseudo_station_code
]

rows = []
count = 0
for start in stations:
    for end in stations:
        if start == end:
            continue
        try:
            pathinfo = rail_graph.find_shortest_path(start, end)
        except Exception:
            continue  # skip invalid pairs
        if not pathinfo or not pathinfo.nodes:
            continue
        # Real station codes only: a network can run a line through another's platforms under stand-in
        # codes (before Circle Line Stage 6, the extension's trains ran through Promenade, Nicoll Highway
        # and Stadium as CE0Z, CE0Y and CE0X). Each becomes its real code, and a step between a stand-in and
        # its real code (a change of platforms there) folds into the next step from that station, or at the
        # end into the last one, so each step's cost stays the time to the next station and they still add
        # up to the total.
        real = [rail_graph.station_code_to_station[code].real_station_code for code in pathinfo.nodes]
        nodes, edges, costs = [real[0]], [], []
        carried = 0
        for i, cost in enumerate(pathinfo.costs):
            if real[i + 1] == nodes[-1]:
                carried += cost
                continue
            nodes.append(real[i + 1])
            edges.append(pathinfo.edges[i])
            costs.append(cost + carried)
            carried = 0
        if carried and costs:
            costs[-1] += carried
        total_cost = pathinfo.total_cost
        row = {
            "origin": start,
            "destination": end,
            "total_cost": total_cost,
            "nodes": json.dumps(nodes).replace('"', "'"),
            "edges": json.dumps(edges),
            "costs": json.dumps(costs)
        }
        rows.append(row)
        count += 1
        if count % 100 == 0:
            print(f"Processed {count} routes...")

# Write all results to a single CSV
if rows:
    with open("all_routes.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Done: all_routes.csv generated with {len(rows)} routes.")
else:
    print("No routes found.")