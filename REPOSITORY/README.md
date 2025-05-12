# Instance Repository Backend

This project is a unified backend framework for reading, parsing, and structuring **benchmark instances** from classical combinatorial optimization problems. It is designed to process raw instance files, extract useful data, and convert them into compressed, validated `.json.xz` formats using Pydantic models for further use (e.g., frontend visualization or solver integration).

------------------------------------------------------------------------------------------------------------------------------------

##  What are we exactly working on?

In optimization research, *instances* refer to input data files that define a specific problem scenario. Each instance contains structured input like:

- A list of jobs and machines (in **Job Shop Scheduling**)
- Customer locations and vehicle capacity (in **CVRP**)
- Pickup and delivery requests with time windows (in **PDPTW**)

These instances serve as standardized **benchmarks** to test and compare optimization algorithms.

--------------------------------------------------------------------------------------------------------------------------------------

## Problems Supported (Uptil now.. more to be added with time)

We have so far implemented parsing and instance handling for the following problems:

| Problem             | Description                                                                 | Status         |
|---------------------|-----------------------------------------------------------------------------|----------------|
| **Job Shop**        | Scheduling of jobs on machines with fixed operation order                   | ✅ Done         |
| **CVRP**            | Capacitated Vehicle Routing Problem                                         | ✅ Done         |
| **CVRP_2D**         | Simplified 2D-focused version of CVRP that prioritizes customer data        | ✅ Done         |
| **Pickup & Delivery with Time Windows (PDPTW)** | Transportation problem with time constraints and routing logic     | ✅ Done         |
| **Knapsack / Multi-Knapsack** | Classic item-selection problems under capacity constraints                 | ✅ Done         |

--------------------------------------------------------------------------------------------------------------------------------------

## 🔗 Benchmark Sources

| Problem      | Source                                                                                                  |
|--------------|----------------------------------------------------------------------------------------------------------|
| **Job Shop** | [OR-LIB](https://people.brunel.ac.uk/~mastjjb/jeb/orlib/jobshopinfo.html)                |
| **CVRP**     | [Galgos - Augerat CVRP Set A](http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/A/A-n32-k5.vrp)          |
| **PDPTW**    | [Mendeley Dataset (Sartori & Buriol)](https://data.mendeley.com/datasets/wr2ct4r22f/2)                 |
                                                           

--------------------------------------------------------------------------------------------------------------------------------------

## ⚙️ Project Status

This project is **still ongoing**. More features and parsing enhancements are planned to:

- Improve parsing logic or add batch porcessing for remaining problems
- Reduce redundancy or ignoring less important instances

--------------------------------------------------------------------------------------------------------------------------------------

## 🛠️ Batch Processing

To enhance efficiency, we have implemented **batch parsing** capabilities:

-  All `.txt` files in the Job Shop folder are processed in a single run
-  All `.vrp` files in the CVRP and CVRP_2D directories are parsed using a loop

**Result ->** tool scalable and easy to extend to new benchmarks.

--------------------------------------------------------------------------------------------------------------------------------------

## 🧩 CVRP_2D Extension

**CVRP_2D** is a lightweight variant of the traditional CVRP model. It focuses only on:

- **Customer coordinates**
- **Customer demands**

This reduces complexity and allows for faster experimentation with routing-focused models while still preserving the core of the VRP logic.

--------------------------------------------------------------------------------------------------------------------------------------

## 📁 Output Format

Each parsed instance is saved as:

./instances/<instance_uid>.json.xz

--------------------------------------------------------------------------------------------------------------------------------------

## 👤 Maintainers

This project is part of ongoing work at **Technische Universität Braunschweig**, maintained and expanded by research assistants and contributors under supervision.