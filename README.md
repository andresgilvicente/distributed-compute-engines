<p align="center">
  <img src="docs/assets/banner.svg" alt="Distributed Compute Engines — Benchmarking Ray, Dask, Spark and AWS EMR" width="100%">
</p>

<p align="center">
    <img alt="Amazon EC2" src="https://img.shields.io/badge/Amazon%20EC2-FF9900?logo=amazonec2&logoColor=black">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white">
  <img alt="Dask" src="https://img.shields.io/badge/Dask-FBBF24">
  <img alt="Ray" src="https://img.shields.io/badge/Ray-22D3EE">
  <img alt="Apache Spark" src="https://img.shields.io/badge/Apache%20Spark-E25A1C?logo=apachespark&logoColor=white">
  <img alt="AWS EMR" src="https://img.shields.io/badge/AWS%20EMR-FF9900?logo=amazonaws&logoColor=white">
  <img alt="Docker" src="https://img.shields.io/badge/docker-compose-2496ED?logo=docker&logoColor=white">
</p>

# Distributed Compute Engines

**Development period:** September-December 2025

A hands-on benchmark of three distributed computing engines (**Ray**, **Dask** and **Apache Spark**) across four deployments on **AWS**. Each engine runs the same Monte Carlo workload in Docker clusters on an Amazon EC2 instance, and Spark also runs on a managed **Amazon EMR** cluster.

The project was developed for the **Big Data Architectures course at Universidad Pontificia Comillas (ICAI)** and was built incrementally over four sprints, each adding a new engine or deployment target.

## Overview

All engines estimate **π with the Monte Carlo method**. The work is split into 200 independent tasks; each task samples random points in the unit square and counts how many fall inside the quarter circle:

```
π ≈ 4 × (points inside the circle / total points)
```

Because the algorithm is identical across engines, differences in execution time and throughput reflect the engines and their deployment, not the workload. Each run reports the estimated π, wall-clock time and throughput in points per second.

| Sprint | Engine | Deployment | Workload sizes |
|:------:|--------|------------|----------------|
| 1 | Ray | Amazon EC2 + Docker Compose — 1 head and 3 workers | 5, 10, 50 M points |
| 2 | Dask | Amazon EC2 + Docker Compose — 1 scheduler and 3 workers | 5, 10, 50 M points |
| 3 | Apache Spark and HDFS | Amazon EC2 + Docker Compose — master, worker, namenode, datanode, Jupyter | 5, 10, 50 M points |
| 4 | Apache Spark on AWS EMR | CloudFormation — 1 master and up to 3 core nodes (`m8g.xlarge`) | 50, 100, 500 M points |

## Architecture

Every deployment follows the same coordinator–worker pattern: a driver submits tasks to a coordinator (Ray head, Dask scheduler, Spark master or YARN), which distributes them across workers and gathers the partial counts.

```mermaid
flowchart LR
    dev(["Developer"])

    subgraph aws["AWS Cloud"]
        direction TB

        subgraph ec2["Amazon EC2 instance — sprints 1 to 3"]
            direction TB
            driver["Driver script<br/>Python"]
            subgraph cluster["Docker Compose cluster<br/>Ray · Dask · Spark"]
                direction TB
                coord["Coordinator<br/>head · scheduler · master"]
                w1["Worker 1"]
                w2["Worker 2<br/>Ray · Dask"]
                w3["Worker 3<br/>Ray · Dask"]
            end
            driver --> coord
            coord --> w1 & w2 & w3
        end

        subgraph emr["Amazon EMR — sprint 4"]
            direction TB
            master["Master node<br/>Spark on YARN"]
            core["Core nodes<br/>1 to 3 × m8g.xlarge"]
            master --> core
        end

        cfn["AWS CloudFormation"] -. provisions .-> emr
        emr -. logs .-> s3[("Amazon S3")]
    end

    dev -- SSH --> ec2
    dev -- "spark-submit" --> emr
```

- **Sprints 1–3** run on a single EC2 instance. Each engine is deployed as a Docker Compose cluster, and each container is pinned to a CPU.
- **Sprint 4** moves the Spark job to a managed Amazon EMR cluster, provisioned as infrastructure as code with CloudFormation.

## Repository structure

```
|
├── 01-ray/          Ray cluster and driver script
├── 02-dask/         Dask cluster and driver script
├── 03-spark/        Spark and HDFS cluster, driver script
├── 04-aws-emr/      CloudFormation template and Spark job for EMR
└── docs/            Project documentation and sprint reports
```

## Getting started

**Requirements:** an AWS account, an EC2 instance with Python 3.10 or later and Docker with Compose (sprints 1–3), and permissions to create CloudFormation stacks (sprint 4).

```bash
git clone https://github.com/<your-username>/distributed-compute-engines.git
cd distributed-compute-engines

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Sprint 1 — Ray

```bash
cd 01-ray
cp .env.example .env             # adjust values if needed
docker compose up -d
python montecarlo_ray.py
```

### Sprint 2 — Dask

```bash
cd 02-dask
docker compose up -d
python montecarlo_dask.py        # dashboard on port 8787 of the instance
```

### Sprint 3 — Spark

```bash
cd 03-spark
cp .env.example .env             # set a Jupyter password and token
docker compose up -d --build
```

Run `montecarlo_spark.py` with `spark-submit` against `spark://spark-master:7077`, or from the Jupyter container. The Spark UI is available at `http://<instance-address>:8080`.

The compose file builds its images from the `hadoop/`, `spark/` and `jupyter/` directories, which are not included in this repository. These directories must be provided before the sprint 3 cluster can be started. In addition, the `JAVA_HOME` path in the Jupyter service targets an ARM64 image and should be adjusted for other architectures.

### Sprint 4 — AWS EMR

```bash
aws cloudformation deploy \
  --template-file 04-aws-emr/emr-cluster.yaml \
  --stack-name distributed-compute-emr \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides VpcId=<vpc-id> SubnetId=<subnet-id> KeyName=<key-pair> InstanceCount=3
```

Submit `04-aws-emr/montecarlo_spark_emr.py` as a Spark step, or run it from the master node. Replace the log bucket in the template with your own.

## Documentation

Project documents are in [`docs/`](docs) and are written in Spanish:

- [User stories](docs/user-stories.pdf)
- [Architecture project](docs/architecture-project.pdf)
- Sprint reports: [1](docs/reports/sprint-1.pdf) · [2](docs/reports/sprint-2.pdf) · [4](docs/reports/sprint-4.pdf)
- [Docker deployment guide](docs/reports/docker-deployment.pdf)

## Security

Credentials, `.env` files and private keys must never be committed. They are excluded through `.gitignore`; configuration templates are provided as `.env.example`.

## Authors

- Jorge Carnicero Príncipe
- Jorge González Pérez
- Andrés Gil Vicente

## License

Released under the [MIT License](LICENSE).
