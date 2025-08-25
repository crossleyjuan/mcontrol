import argparse
import os
import subprocess
import pymongo
import time
import yaml
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s [%(levelname)s] %(message)s",
  handlers=[
    logging.StreamHandler()
  ]
)

config = {}

# This script launches mongod processes and manages them.
def parse_arguments():
    parser = argparse.ArgumentParser(description="Manage mongod processes.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")

    # 'init' command
    init_parser = subparsers.add_parser("init", help="Initialize the cluster.")
    init_parser.add_argument("--shards", type=int, default=0, required=False, help="Number of shards.")
    init_parser.add_argument("--replSetName", type=str, default="rs", required=False, help="Name of the replicaset, only usefule when shards is 0")
    init_parser.add_argument("--startPort", type=int, default=27017, required=False, help="Start port to use for the deployment")
    init_parser.add_argument("--nodes", type=int, default=3, required=False, help="Number of nodes per replica set")
    init_parser.add_argument("--arbiters", type=int, default=0, required=False, help="Number of arbiters per replica set")

    # 'start' command
    start_parser = subparsers.add_parser("start", help="Start the cluster.")

    # 'stop' command
    subparsers.add_parser("stop", help="Stop the cluster.")

    return parser.parse_args()

def create_shard_config(i, j):
    workingdir = os.getcwd()

    shard_path =  os.path.join(workingdir, "data", f"shard{i}", f"shard{i}{j}")
    if not os.path.exists(shard_path):
        os.makedirs(shard_path)
    config_file = os.path.join(shard_path, f"mongod.conf")
    with open(config_file, "w") as f:
        port = 27030 + i*config.nodes + j
        config_file_shard = f"""
net:
  bindIp: 0.0.0.0
  port: {port}
processManagement:
  fork: "true"
replication:
  replSetName: sh_{i}
security:
  javascriptEnabled: false
sharding:
  clusterRole: shardsvr
storage:
  dbPath: { shard_path }
  engine: wiredTiger
systemLog:
  destination: file
  path: { shard_path }/mongodb.log
                  """
        f.write(config_file_shard)

def create_replica_set_config(i):
    workingdir = os.getcwd()

    rs_path =  os.path.join(workingdir, "data", f"rs{i}")
    if not os.path.exists(rs_path):
        os.makedirs(rs_path)
    config_file = os.path.join(rs_path, f"mongod.conf")
    with open(config_file, "w") as f:
        port = config["startPort"] + i
        config_file_rs = f"""
net:
  bindIp: 0.0.0.0
  port: {port}
processManagement:
  fork: "true"
replication:
  replSetName: { config["replSetName"] }
security:
  javascriptEnabled: false
storage:
  dbPath: { rs_path }
  engine: wiredTiger
systemLog:
  destination: file
  path: { rs_path }/mongodb.log
                  """
        f.write(config_file_rs)

def create_config_config(i):
    logger.info("Creating cfgsrv config file...")

    workingdir = os.getcwd()
    config_path = os.path.join(workingdir, "data", f"config", f"cfg{i}")
    if not os.path.exists(config_path):
        os.makedirs(config_path)
    config_file = os.path.join(config_path, f"mongod.conf")
    with open(config_file, "w") as f:
        port = 27018 + i
        config_file_shard = f"""
net:
  bindIp: 0.0.0.0
  port: {port}
processManagement:
  fork: "true"
replication:
  replSetName: configRS
security:
  javascriptEnabled: false
sharding:
  clusterRole: configsvr
storage:
  dbPath: {config_path}
  engine: wiredTiger
systemLog:
  destination: file
  path: {config_path}/mongodb.log        """
        f.write(config_file_shard)

def create_config_mongos(args):
    logger.info("Creating mongos config file...")
    workingdir = os.getcwd()

    config_path = os.path.join(workingdir, "data", f"mongos")
    if not os.path.exists(config_path):
        os.makedirs(config_path)
    config_file = os.path.join(config_path, f"mongod.conf")
    with open(config_file, "w") as f:
        port = args.startPort
        config_file_shard = f"""
net:
  bindIp: 0.0.0.0
  port: { args.startPort }
processManagement:
  fork: "true"
security:
  javascriptEnabled: false
sharding:
  configDB: configRS/localhost:27018,localhost:27019,localhost:27020
systemLog:
  destination: file
  path: { config_path }/mongodb.log
"""
        f.write(config_file_shard)

def initialize_config_files():
    shards = config["shards"]
    workingdir = os.getcwd()
    basepath = os.path.join(workingdir, "data")

    if shards == 0:
        for i in range(config["nodes"]):
            create_replica_set_config(i)

    else:
      if not os.path.exists(basepath):
          os.makedirs("data")
          create_config_mongos()
      for i in range(shards):
          shard_path = os.path.join(basepath, f"shard{i}")
          if not os.path.exists(shard_path):
              for j in range(3):
                  create_shard_config(i, j)

      if not os.path.exists(os.path.join(basepath, "config")):
          for j in range(3):
              create_config_config(j)

def init(args):
  global config
  logger.info("Initializing cluster...")

  config = {
      "shards": args.shards,
      "nodes": args.nodes,
      "replSetName": args.replSetName,
      "startPort": args.startPort,
      "arbiters": args.arbiters,
      "config": 3,
      "mongos": 1
  }

  if not os.path.exists("data"):
      os.makedirs("data")

  with open("data/mcontrol.yml", "w") as f:
      yaml.dump(config, f)
      
  initialize_config_files()

def load_config():
  global config
  with open("data/mcontrol.yml", "r") as f:
      config = yaml.safe_load(f)
  
def initialize_replica_set(rsName, initialPort):
  client = pymongo.MongoClient("localhost", initialPort, directConnection=True)
  
  init_replica_set = {
      "_id": f"{rsName}",
      "members": [
      ]
  }
  for i in range(config["nodes"] - config["arbiters"]):
    init_replica_set["members"].append({"_id": len(init_replica_set["members"]), "host": f"localhost:{initialPort + i}"})

  for i in range(config["arbiters"]):
    init_replica_set["members"].append({"_id": len(init_replica_set["members"]), "host": f'localhost:{initialPort + config["nodes"] + i}', "arbiterOnly": True})

  client.admin.command("replSetInitiate", init_replica_set)
    
def initialize_shard(i):
    logger.info(f"Initializing shard {i}...")
    initialize_replica_set("sh_" + str(i), 27030 + (i*config["nodes"]))

    logger.info(f"Shard {i} initialized")

def initialize_config_rs():
    logger.info(f"Initializing config server...")
    initialize_replica_set("configRS", 27018)
    logger.info(f"Config server initialized")

def initialize_mongos():
    client_mongos = pymongo.MongoClient("localhost", config["startPort"])
    for i in range(config["shards"]):
        client_mongos.admin.command("addShard", f"sh_{i}/localhost:{ 27030 + (i*3)},localhost:{ 27031 + (i*3)},localhost:{ 27032 + (i*3)}")

def initialize():
    if config["shards"] == 0:
      initialize_replica_set(config["replSetName"], config["startPort"])
    else:
      for i in range(config["shards"]):
          initialize_shard(config, i)

      initialize_config_rs(config)

def start_shards():
    working_dir = os.getcwd() 
    for i in range(config["shards"]):
        logger.info(f"Starting shard {i}...")
        for j in range(3):
            subprocess.Popen(f"mongod --config { working_dir }/data/shard{i}/shard{i}{j}/mongod.conf", shell=True, cwd=working_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_replica_set():
    working_dir = os.getcwd() 
    for i in range(config["nodes"]):
        logger.info(f"Starting node {i}...")
        subprocess.Popen(f"mongod --config { working_dir }/data/rs{i}/mongod.conf", shell=True, cwd=working_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_config():
    working_dir = os.getcwd() 
    logger.info("Starting config servers...")
    for j in range(3):
        subprocess.Popen(f"mongod --config { working_dir }/data/config/cfg{j}/mongod.conf", shell=True, cwd=working_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_mongos():
    working_dir = os.getcwd() 
    logger.info("Starting mongos")
    subprocess.Popen(f"mongos --config { working_dir }/data/mongos/mongod.conf", shell=True, cwd=working_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start():
  if config["shards"] == 0:
    start_replica_set()
  else:
    start_shards()
    start_config()
    start_mongos()
    logger.info("Cluster started.")

def stop():
  pass
  
def main():
    args = parse_arguments()
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging is enabled.")
    
    if args.command == "init":
        init(args)
        if args.shards == 0:
          start_replica_set()
          time.sleep(10)
          initialize()
        else:
          start_shards()
          start_config()
          time.sleep(10)
          initialize()
          start_mongos()
          initialize_mongos()

    elif args.command == "start":
        config = load_config()
        start(config)
    elif args.command == "stop":
        config = load_config()
        stop(config)

if __name__ == "__main__":
    main()