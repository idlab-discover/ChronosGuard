import argparse
import re
from typing import Dict

def main(args):
    topology = parseMetricsTxt(args.filename, args.bidirectional)
    writeDotFile(topology, args.output, args.bidirectional)

def writeDotFile(topology: Dict[tuple, list], filename: str, bidirectional: bool) -> None:
    edge_op = "->" if bidirectional else "--"
    with open(filename, "w") as dot_file:
        dot_file.write("digraph" if bidirectional else "graph" + " network_topology {\n")
        for key, value in topology.items():
            weight = value[0] if bidirectional else round(sum(value)/len(value))
            dot_file.write(f"{key[0]} {edge_op} {key[1]} [label={weight}]\n")
        dot_file.write("}\n")

def parseMetricsTxt(filename: str, bidirectional: bool) -> Dict[tuple, list]:
    topology = {}
    regex= "netperf\.p90\.latency\.(.*)\.origin\.(.*)\.ids\.ilabt-imec-be\.wall2\.ilabt\.iminds\.be\.destination\.(.*)\.ids\.ilabt-imec-be\.wall2\.ilabt\.iminds\.be=(.*)"
    with open(filename, "r") as metrics_file:
        for line in metrics_file:
            matches = re.search(regex, line)
            topology.setdefault(getKey(matches.group(2), matches.group(3), bidirectional), []).append(int(matches.group(4)))
    return topology

def getKey(str1: str, str2: str, bidirectional: bool) -> str:
    if bidirectional:
        return (str1, str2)
    return (str1, str2) if str1 < str2 else (str2, str1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Program to visualize the netperfMetrics.")
    parser.add_argument("-f", "--filename", type=str, required=True, help="Location of netperfMetrics.txt")
    parser.add_argument("-o", "--output", type=str, default="netperfMetrics.dot", help="Output location for dot-file")
    parser.add_argument("-b", "--bidirectional", action="store_true", help="Bidirectional links are not averaged when this flag is set")
    args = parser.parse_args()
    main(args)