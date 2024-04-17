topologies = ["cluster", "cluster with delay"] #, "edge-fog-cloud", "edge-cloud"]
deployments = ["monolith", "2 pod",  "3 pod", "4 pod"]
repetitions = range(1,6)
schedulers = ["KS", "Diktyo"]
sorting_algos = ["khan", "reverse", "alternate", "cycle"]
scenarios = ["initial", "scale-up", "scale-down"]

count = 0
for topology in topologies:
    for deployment in deployments:
        for repetition in repetitions:
            for scheduler in schedulers:
                for sorting_algo in sorting_algos:
                    for scenario in scenarios:
                        if deployment == "monolith" and scheduler == "Diktyo":
                            continue
                        elif scheduler == "KS" and sorting_algo == "khan":
                            count+=1
                            scheduler_val = "" if deployment == "monolith" else scheduler
                            print(f"{count},{topology},{deployment},{repetition},{scheduler_val},,{scenario}")
                        elif scheduler == "Diktyo":
                            count+=1
                            print(f"{count},{topology},{deployment},{repetition},{scheduler},{sorting_algo},{scenario}")
